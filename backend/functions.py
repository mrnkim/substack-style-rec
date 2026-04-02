"""Custom UDFs and helper functions for the recommendation engine."""
import json
import logging
import re

import httpx
import pixeltable as pxt

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Analyze API UDF — extracts topic/style/tone from TL-indexed videos
# ---------------------------------------------------------------------------

VALID_STYLES = frozenset({
    "interview", "documentary", "essay", "tutorial",
    "conversation", "analysis", "performance", "explainer",
})

VALID_TONES = frozenset({
    "serious", "casual", "playful", "contemplative",
    "energetic", "analytical",
})


@pxt.udf
def analyze_video(video_id: str) -> dict:
    """
    Call Twelve Labs Analyze API to extract topic, style, and tone attributes.

    The video must already be indexed in the TL index. Returns a dict with keys:
    topic (list[str]), style (str), tone (str).
    """
    url = f"{config.TWELVELABS_BASE_URL}/analyze"
    headers = {
        "x-api-key": config.TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "video_id": video_id,
        "prompt": config.ANALYZE_PROMPT,
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("data", "")

        # Extract JSON from the response text (handles nested objects)
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            attrs = json.loads(json_match.group())
        else:
            attrs = json.loads(text)

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
# Recommendation reason generation (spec: BACKEND_SPEC.md §Recommendation
# Explanation Generation)
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
        topics_str = ", ".join(list(overlap)[:2])
        parts.append(f"Also covers {topics_str}")

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
