"""Custom UDFs and helper functions for the recommendation engine."""

import json
import logging

import httpx
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


@pxt.udf
def analyze_video(video_id: str) -> dict:
    """Call Twelve Labs Analyze API to extract topic, style, and tone."""
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
# Summary + chapters generation (TL Generate API — /summarize)
# ---------------------------------------------------------------------------


def _summarize(video_id: str, summary_type: str, timeout: float = 180.0) -> dict:
    """Single internal call to TL /summarize with the given type."""
    url = f"{config.TWELVELABS_BASE_URL}/summarize"
    headers = {
        "x-api-key": config.TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"video_id": video_id, "type": summary_type}
    resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


@pxt.udf
def summarize_video(video_id: str) -> str:
    """Generate a short paragraph-length summary of the video."""
    try:
        data = _summarize(video_id, "summary")
        return str(data.get("summary", "")).strip()
    except Exception as e:
        logger.warning("Summary API failed for video %s: %s", video_id, e)
        return ""


@pxt.udf
def chapters_for_video(video_id: str) -> list:
    """Generate ordered chapter timeline.

    Each chapter is `{start, end, title, summary}` in seconds. Empty list on
    failure so the UI gracefully hides the section.
    """
    try:
        data = _summarize(video_id, "chapter")
        raw = data.get("chapters") or []
        chapters: list[dict] = []
        for c in raw:
            try:
                start = float(c.get("start") or c.get("start_sec") or 0)
                end = float(c.get("end") or c.get("end_sec") or 0)
            except (TypeError, ValueError):
                continue
            title = str(
                c.get("chapter_title") or c.get("title") or ""
            ).strip()
            summary = str(
                c.get("chapter_summary") or c.get("summary") or ""
            ).strip()
            chapters.append(
                {"start": start, "end": end, "title": title, "summary": summary}
            )
        return chapters
    except Exception as e:
        logger.warning("Chapter API failed for video %s: %s", video_id, e)
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
