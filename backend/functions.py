"""Custom UDFs and helper functions for the recommendation engine."""

import asyncio
import json
import logging
import os
from typing import TypedDict

import httpx
import numpy as np
import pixeltable as pxt
from pixeltable.functions.twelvelabs import (
    TWELVELABS_INLINE_LIMIT_BYTES,
    _asset_uploads,
    _embed_av_content,
    _twelvelabs_client,
)

import config

logger = logging.getLogger(__name__)

VALID_STYLES = frozenset(
    {
        "interview",
        "documentary",
        "essay",
        "tutorial",
        "conversation",
        "analysis",
        "performance",
        "explainer",
    }
)

VALID_TONES = frozenset(
    {
        "serious",
        "casual",
        "playful",
        "contemplative",
        "energetic",
        "analytical",
    }
)


class VideoAttributes(TypedDict):
    topic: list[str]
    style: str
    tone: str


DEFAULT_ATTRIBUTES: VideoAttributes = {"topic": [], "style": "", "tone": ""}

_EMBED_ATTEMPTS = 8
_EMBED_BACKOFF_SEC = 2.0


def _is_asset_not_ready(exc: BaseException) -> bool:
    chunks = [str(exc)]
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        chunks.append(str(body.get("code") or ""))
        chunks.append(str(body.get("message") or ""))
    elif body is not None:
        chunks.append(str(getattr(body, "code", "") or ""))
        chunks.append(str(getattr(body, "message", "") or ""))
        chunks.append(str(body))
    blob = " ".join(chunks).lower()
    return "asset_not_ready" in blob or "being processed" in blob


def _parse_analyze_text(resp: httpx.Response) -> str:
    text = resp.text.strip()
    if not text:
        return ""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            data = obj.get("data")
            if isinstance(data, str) and data:
                return data
            if "topic" in obj:
                return text
    except json.JSONDecodeError:
        pass
    text_parts: list[str] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") == "text_generation":
            text_parts.append(event.get("text", ""))
        elif event.get("event_type") == "stream_end" and isinstance(event.get("data"), str):
            text_parts.append(event["data"])
    return "".join(text_parts) if text_parts else text


def _coerce_attrs_json(full_text: str) -> dict:
    text = full_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


async def _lookup_asset_id(video_id: str) -> str:
    url = (
        f"{config.TWELVELABS_BASE_URL}/indexes/{config.TWELVELABS_INDEX_ID}/videos/{video_id}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url, headers={"x-api-key": config.TWELVELABS_API_KEY}, timeout=30.0
        )
        if resp.status_code >= 400:
            logger.warning(
                "Analyze asset lookup failed for video %s: status=%s body=%s",
                video_id,
                resp.status_code,
                resp.text[:1000],
            )
        resp.raise_for_status()
        asset_id = resp.json().get("asset_id")
    if not asset_id:
        raise RuntimeError(f"No asset_id on indexed video {video_id}")
    return asset_id


@pxt.udf(is_deterministic=False)
async def analyze_video(video_id: str) -> VideoAttributes:
    """Call Twelve Labs Analyze API to extract topic, style, and tone."""
    url = f"{config.TWELVELABS_BASE_URL}/analyze"
    headers = {
        "x-api-key": config.TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        asset_id = await _lookup_asset_id(video_id)
        payload = {
            "model_name": "pegasus1.5",
            "video": {"type": "asset_id", "asset_id": asset_id},
            "prompt": config.ANALYZE_PROMPT,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=180.0)
            if resp.status_code >= 400:
                logger.warning(
                    "Analyze API failed for video %s: status=%s body=%s",
                    video_id,
                    resp.status_code,
                    resp.text[:1000],
                )
            resp.raise_for_status()

        attrs = _coerce_attrs_json(_parse_analyze_text(resp))

        topic = attrs.get("topic", [])
        if not isinstance(topic, list):
            topic = [str(topic)]

        style = str(attrs.get("style", "")).lower()
        if style not in VALID_STYLES:
            style = ""

        tone = str(attrs.get("tone", "")).lower()
        if tone not in VALID_TONES:
            tone = ""

        return {"topic": topic, "style": style, "tone": tone}

    except Exception as e:
        logger.warning("Analyze API failed for video %s: %s", video_id, e)
        return dict(DEFAULT_ATTRIBUTES)


async def _create_video_embed(cl, video_req) -> np.ndarray:
    last_exc: BaseException | None = None
    for attempt in range(1, _EMBED_ATTEMPTS + 1):
        try:
            res = await cl.embed.v_2.create(
                input_type="video", model_name="marengo3.0", video=video_req
            )
            if not res.data:
                raise RuntimeError(f"Empty embed response: {res}")
            return np.array(res.data[0].embedding, dtype="float32")
        except Exception as e:
            last_exc = e
            if not _is_asset_not_ready(e) or attempt == _EMBED_ATTEMPTS:
                raise
            logger.info(
                "Video embed asset not ready (attempt %d/%d), retrying in %.1fs: %s",
                attempt,
                _EMBED_ATTEMPTS,
                _EMBED_BACKOFF_SEC,
                e,
            )
            await asyncio.sleep(_EMBED_BACKOFF_SEC)
    assert last_exc is not None
    raise last_exc


async def _embed_video_marengo(file_path: str) -> np.ndarray:
    import twelvelabs

    size_bytes = os.stat(file_path).st_size
    if size_bytes <= TWELVELABS_INLINE_LIMIT_BYTES:
        vec = await _embed_av_content(
            file_path=file_path,
            input_type="video",
            request_cls=twelvelabs.VideoInputRequest,
            model_name="marengo3.0",
            start_sec=None,
            end_sec=None,
            embedding_option=None,
        )
        if vec is None:
            raise RuntimeError(f"Didn't receive embedding for video: {file_path}")
        return np.asarray(vec, dtype="float32")

    cl = _twelvelabs_client()
    async with _asset_uploads(input_type="video", files=[file_path]) as asset_ids:
        video_req = twelvelabs.VideoInputRequest(
            media_source=twelvelabs.MediaSource(asset_id=asset_ids[0])
        )
        return await _create_video_embed(cl, video_req)


@pxt.udf(is_deterministic=False, resource_pool="request-rate:twelvelabs")
async def embed_video_retry(video: pxt.Video) -> pxt.Array[(512,), np.float32] | None:
    """Marengo 3.0 video embed with retries while Twelve Labs processes a multipart upload."""
    if not video:
        return None
    return await _embed_video_marengo(video)


# ---------------------------------------------------------------------------
# Recommendation reason generation
# ---------------------------------------------------------------------------


def generate_reason(
    source_video: dict,
    target_video: dict,
    rec_source: str,
    subscriptions: set[str],
) -> str:
    """Generate a natural-language explanation for a recommendation."""
    parts: list[str] = []

    source_title = source_video.get("title", "")
    if source_title:
        parts.append(f"Because you watched '{source_title}'")

    src_topics = set(source_video.get("topic") or [])
    tgt_topics = set(target_video.get("topic") or [])
    overlap = src_topics & tgt_topics
    if overlap:
        parts.append(f"Also covers {', '.join(list(overlap)[:2])}")

    src_style = source_video.get("style")
    tgt_style = target_video.get("style")
    if src_style and tgt_style and src_style == tgt_style:
        parts.append(f"Similar {tgt_style} format")

    src_tone = source_video.get("tone")
    tgt_tone = target_video.get("tone")
    if src_tone and tgt_tone and src_tone == tgt_tone:
        parts.append(f"Matching {tgt_tone} tone")

    target_creator = target_video.get("creator_id", "")
    if target_creator in subscriptions:
        parts.append("From a creator you subscribe to")
    elif rec_source == "discovery":
        parts.append("Discover a new creator")

    if not parts:
        return "Recommended for you"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} — {' · '.join(parts[1:])}"
