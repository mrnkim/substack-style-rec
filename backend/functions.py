"""Custom UDFs and helper functions for the recommendation engine."""

import json
import logging
from typing import TypedDict

import httpx
import numpy as np
import pixeltable as pxt

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


@pxt.udf(is_deterministic=False)
async def embed_video_retry(video: pxt.Video) -> pxt.Array[(512,), np.float32] | None:
    """Retired Marengo 3.0 scene embedding. Do not use.

    Databases created before the Marengo 3.5 upgrade store an index that names this
    UDF. Pixeltable must be able to import it to load those tables, so that
    `pxt schema update app.py substack_rec --allow-destructive` can drop the old index
    and build the 3.5 one. Remove this stub once no such database remains.
    """
    raise RuntimeError(
        "embed_video_retry is retired. Run `pxt schema update app.py substack_rec "
        "--allow-destructive` to rebuild the scene index with Marengo 3.5."
    )


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
