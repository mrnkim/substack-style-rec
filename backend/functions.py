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
