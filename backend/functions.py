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
# Recommendation reason generation
# ---------------------------------------------------------------------------


def generate_reason(
    source_video: dict,
    target_video: dict,
    rec_source: str,
    subscriptions: set[str],
) -> str:
    """Generate a short, human-readable reason for a recommendation."""
    source_title = source_video.get("title", "")
    target_creator = target_video.get("creator_id", "")

    if source_title:
        reason = f"Because you watched '{source_title}'"
    elif target_creator in subscriptions:
        reason = "From a creator you follow"
    elif rec_source == "discovery":
        reason = "Discover something new"
    else:
        reason = "Recommended for you"

    return reason
