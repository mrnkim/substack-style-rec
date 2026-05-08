"""Custom UDFs and helper functions for the recommendation engine."""

import json
import logging
import os
from pathlib import Path

import httpx
import pixeltable as pxt

import config

logger = logging.getLogger(__name__)

# Pre-computed summary/chapters cache.
#
# /analyze on Render Starter (512 MB) keeps OOM-killing during setup, and the
# /summarize endpoint was retired so generating these on-the-fly is the slow
# path now. Locally we already produced the data, so we ship it as JSON in
# `backend/data/summaries.json` and let the UDFs prefer the cache. New
# videos that aren't in the JSON still hit the API.
_CACHE_PATH = Path(__file__).resolve().parent / "summaries.json"
_SUMMARIES_CACHE: dict[str, dict] = {}
try:
    if _CACHE_PATH.exists():
        with _CACHE_PATH.open() as _f:
            _SUMMARIES_CACHE = json.load(_f)
        logger.info(
            "Loaded summary/chapter cache for %d videos from %s",
            len(_SUMMARIES_CACHE), _CACHE_PATH,
        )
except Exception as _e:
    logger.warning("Could not load summary cache (%s): %s", _CACHE_PATH, _e)

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


@pxt.udf
def fetch_tl_segments(video_id: str) -> list:
    """Pull precomputed visual scene embeddings from Twelve Labs.

    Each TL-indexed asset already has Marengo visual segment embeddings
    generated at upload time. Calling /indexed-assets/{id}?embedding_option=visual
    returns them as a list of {start, end, vec} segments — no recomputation.

    Returns a list of {start_sec, end_sec, vec} dicts (vec is a 512-float list).
    Empty list on failure so the row still gets inserted.
    """
    url = (
        f"{config.TWELVELABS_BASE_URL}/indexes/{config.TWELVELABS_INDEX_ID}"
        f"/indexed-assets/{video_id}"
    )
    headers = {"x-api-key": config.TWELVELABS_API_KEY}
    try:
        resp = httpx.get(
            url,
            params=[("embedding_option", "visual")],
            headers=headers,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        segments = (
            data.get("embedding", {})
            .get("video_embedding", {})
            .get("segments", [])
        )
        out: list = []
        for s in segments:
            vec = s.get("float") or s.get("float_")
            if not vec:
                continue
            out.append(
                {
                    "start_sec": float(s.get("start_offset_sec", 0.0)),
                    "end_sec": float(s.get("end_offset_sec", 0.0)),
                    "vec": vec,
                }
            )
        return out
    except Exception as e:
        logger.warning("TL retrieve failed for video %s: %s", video_id, e)
        return []


@pxt.udf
def analyze_video(video_id: str) -> dict:
    """Call Twelve Labs Analyze API to extract topic, style, and tone.

    Prefers the pre-computed JSON cache (backend/summaries.json) so Render
    setup doesn't have to make these calls — /analyze is the OOM trigger on
    the 512 MB Starter plan.
    """
    cached = _SUMMARIES_CACHE.get(video_id, {}).get("attributes")
    if isinstance(cached, dict):
        topic = cached.get("topic") or []
        style = str(cached.get("style") or "").lower()
        tone = str(cached.get("tone") or "").lower()
        if style not in VALID_STYLES:
            style = "interview"
        if tone not in VALID_TONES:
            tone = "serious"
        return {
            "topic": topic if isinstance(topic, list) else [],
            "style": style,
            "tone": tone,
        }

    url = f"{config.TWELVELABS_BASE_URL}/analyze"
    headers = {
        "x-api-key": config.TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"video_id": video_id, "prompt": config.ANALYZE_PROMPT}

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=120.0)
        resp.raise_for_status()

        # TL Analyze API returns streaming NDJSON — concatenate text fragments
        text_parts: list[str] = []
        for line in resp.text.strip().splitlines():
            try:
                event = json.loads(line)
                if event.get("event_type") == "text_generation":
                    text_parts.append(event.get("text", ""))
            except json.JSONDecodeError:
                continue
        full_text = "".join(text_parts)

        attrs = json.loads(full_text)

        topic = attrs.get("topic", [])
        if not isinstance(topic, list):
            topic = [str(topic)]

        style = str(attrs.get("style", "")).lower()
        if style not in VALID_STYLES:
            style = "interview"

        tone = str(attrs.get("tone", "")).lower()
        if tone not in VALID_TONES:
            tone = "serious"

        return {"topic": topic, "style": style, "tone": tone}

    except Exception as e:
        logger.warning("Analyze API failed for video %s: %s", video_id, e)
        return {"topic": [], "style": "interview", "tone": "serious"}


# ---------------------------------------------------------------------------
# Summary + chapters generation (TL /analyze — /summarize was deprecated 2026-01)
# ---------------------------------------------------------------------------


SUMMARY_PROMPT = (
    "Write a single paragraph (3-4 sentences) summarizing what this video is "
    "about — its main subject, who appears, and the central takeaway. Plain "
    "prose, no headings, no bullet points, no preamble like \"This video...\""
)

CHAPTERS_PROMPT = """Identify the natural chapters of this video. For each chapter, return:
- start: start time in seconds (float)
- end: end time in seconds (float)
- title: a short 3-7 word title that captures the chapter's focus
- summary: one concise sentence summarizing what happens in this chapter

Return ONLY a JSON array of chapter objects, no preamble. Aim for 4-8 chapters
covering the entire video without gaps. Example shape:

[
  {"start": 0, "end": 42.3, "title": "Setting the stage", "summary": "..."},
  {"start": 42.3, "end": 110.0, "title": "...", "summary": "..."}
]"""


def _analyze_text(video_id: str, prompt: str, timeout: float = 180.0) -> str:
    """Call /analyze with a prompt and return concatenated streamed text."""
    url = f"{config.TWELVELABS_BASE_URL}/analyze"
    headers = {
        "x-api-key": config.TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"video_id": video_id, "prompt": prompt}
    resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()

    text_parts: list[str] = []
    for line in resp.text.strip().splitlines():
        try:
            event = json.loads(line)
            if event.get("event_type") == "text_generation":
                text_parts.append(event.get("text", ""))
        except json.JSONDecodeError:
            continue
    return "".join(text_parts).strip()


def _extract_json(text: str) -> str | None:
    """Find the first JSON array or object in `text` (model output sometimes
    wraps the JSON in markdown fences or chatter)."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Strip ```json ... ``` fences
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    # Heuristic: find the outermost [ ] or { }
    for open_c, close_c in (("[", "]"), ("{", "}")):
        start = cleaned.find(open_c)
        end = cleaned.rfind(close_c)
        if 0 <= start < end:
            return cleaned[start : end + 1]
    return None


def _normalize_chapters(raw) -> list[dict]:
    """Coerce a list of chapter-like dicts to {start, end, title, summary}."""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for c in raw:
        if not isinstance(c, dict):
            continue
        try:
            start = float(c.get("start") or c.get("start_sec") or 0)
            end = float(c.get("end") or c.get("end_sec") or 0)
        except (TypeError, ValueError):
            continue
        title = str(c.get("title") or c.get("chapter_title") or "").strip()
        summary = str(c.get("summary") or c.get("chapter_summary") or "").strip()
        out.append({"start": start, "end": end, "title": title, "summary": summary})
    return out


@pxt.udf
def summarize_video(video_id: str) -> str:
    """Generate a short paragraph-length summary of the video.

    Prefers the pre-computed JSON cache. Falls back to /analyze for videos
    not in the cache (e.g. newly added to the index).
    """
    cached = _SUMMARIES_CACHE.get(video_id, {}).get("summary")
    if isinstance(cached, str) and cached.strip():
        return cached.strip()
    try:
        return _analyze_text(video_id, SUMMARY_PROMPT)
    except Exception as e:
        logger.warning("Summary call failed for video %s: %s", video_id, e)
        return ""


@pxt.udf
def chapters_for_video(video_id: str) -> list:
    """Generate ordered chapter timeline.

    Each chapter is `{start, end, title, summary}` in seconds. Empty list on
    failure so the UI gracefully hides the section. Prefers the pre-computed
    JSON cache; falls back to /analyze for un-cached videos.
    """
    cached = _SUMMARIES_CACHE.get(video_id, {}).get("chapters")
    if isinstance(cached, list) and cached:
        return _normalize_chapters(cached)
    try:
        text = _analyze_text(video_id, CHAPTERS_PROMPT)
        json_blob = _extract_json(text)
        if not json_blob:
            logger.warning("No JSON found in chapter response for %s", video_id)
            return []
        return _normalize_chapters(json.loads(json_blob))
    except Exception as e:
        logger.warning("Chapter call failed for video %s: %s", video_id, e)
        return []


# ---------------------------------------------------------------------------
# Recommendation reason generation
# ---------------------------------------------------------------------------


def generate_reason(
    source_video: dict,
    target_video: dict,
    rec_source: str,
    subscriptions: set[str],
    context: str = "similar",
) -> str:
    """Generate a short, human-readable reason for a recommendation.

    context: "similar" when the source is the currently-playing video (watch
    page sidebar); "for_you" when the source is drawn from watch history
    (home feed).
    """
    source_title = source_video.get("title", "")
    target_creator = target_video.get("creator_id", "")

    if source_title:
        anchor = (
            "the current video" if context == "similar" else "videos you've watched"
        )
        return (
            f"Recommended because it shares visual elements and scenes with {anchor}."
        )
    if target_creator in subscriptions:
        return "From a creator you follow."
    if rec_source == "discovery":
        return "A new creator that matches your taste."
    return "Recommended based on your watch history."
