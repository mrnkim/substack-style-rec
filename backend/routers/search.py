"""Semantic video search.

Prefers Twelve Labs Search API (returns scene-level timestamps).
Falls back to Pixeltable scene similarity or title embeddings.
"""

import logging
import shutil
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, Query, UploadFile
import pixeltable as pxt

import config
from models import SearchResponse, SearchResultItem
from routers.videos import (
    _attach_attrs,
    _build_video_response,
    _get_scenes_table,
    _load_creators_map,
    _scene_similarity,
    _title_similarity,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

MIME_TO_MODALITY = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/gif": "image",
    "video/mp4": "video",
    "video/webm": "video",
    "video/quicktime": "video",
    "audio/mpeg": "audio",
    "audio/mp4": "audio",
    "audio/m4a": "audio",
    "audio/x-m4a": "audio",
    "audio/wav": "audio",
    "audio/webm": "audio",
}


def _tl_search(query: str, limit: int = 10) -> list[SearchResultItem] | None:
    """Call Twelve Labs Search API directly — returns results with scene timestamps."""
    if not config.TWELVELABS_API_KEY or not config.TWELVELABS_INDEX_ID:
        return None

    url = f"{config.TWELVELABS_BASE_URL}/search"
    headers = {"x-api-key": config.TWELVELABS_API_KEY}

    try:
        resp = httpx.post(
            url,
            headers=headers,
            files={
                "query_text": (None, query),
                "index_id": (None, config.TWELVELABS_INDEX_ID),
                "search_options": (None, "visual"),
                "page_limit": (None, str(limit)),
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("TL Search API failed: %s", exc)
        return None

    creators_map = _load_creators_map()
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    all_rows = list(
        videos_t.select(
            videos_t.id, videos_t.title, videos_t.creator_id, videos_t.category,
            videos_t.duration, videos_t.thumbnail_url, videos_t.hls_url, videos_t.upload_date,
        ).collect()
    )
    by_tl_id = {r["id"]: r for r in all_rows}

    results: list[SearchResultItem] = []
    seen: set[str] = set()
    total_clips = len(data.get("data", []))
    for i, clip in enumerate(data.get("data", [])):
        vid_id = clip.get("video_id", "")
        if vid_id in seen:
            continue
        seen.add(vid_id)

        row = by_tl_id.get(vid_id)
        if not row:
            continue

        # Rank-based score: top result = 1.0, decreasing
        score = round(1.0 - (i / max(total_clips, 1)) * 0.5, 4)

        results.append(SearchResultItem(
            video=_build_video_response(row, creators_map),
            score=score,
            scene_start=round(clip.get("start", 0.0), 2),
            scene_end=round(clip.get("end", 0.0), 2),
            scene_thumbnail_url=clip.get("thumbnail_url"),
        ))

    logger.info("  [TL Search API] %d results with timestamps", len(results))
    return results if results else None


def _format_results(rows, query_label, modality="text"):
    """Convert raw rows into a SearchResponse."""
    creators_map = _load_creators_map()
    results = [
        SearchResultItem(
            video=_build_video_response(row, creators_map),
            score=round(row.get("score") or 0.0, 4),
            scene_start=round(row["segment_start"], 2) if row.get("segment_start") is not None else None,
            scene_end=round(row["segment_end"], 2) if row.get("segment_end") is not None else None,
        )
        for row in rows
    ]

    if results:
        top = results[0]
        logger.info(
            "  → %d results | [%.3f] %s", len(results), top.score, top.video.title[:50]
        )
    else:
        logger.info("  → 0 results")

    return SearchResponse(query=query_label, modality=modality, results=results)


def _search(videos_t, scenes_t, q, creator_id, limit, **file_kwargs):
    """Unified search: prefer scenes (content-based), fall back to title."""
    is_file_query = bool(file_kwargs)

    if scenes_t is not None:
        kwargs = file_kwargs if file_kwargs else {"string": q}
        try:
            rows = _scene_similarity(scenes_t, None, limit, creator_id, **kwargs)
            if rows:
                logger.info("  [scene index] multimodal video content search")
                _attach_attrs(rows, videos_t)
                return rows
        except Exception as exc:
            logger.warning("scene search failed (%s), falling back to title", exc)

    if is_file_query:
        if scenes_t is None:
            logger.warning(
                "  File search requires video_scenes view (not created yet). "
                "Run 'uv run download_videos.py && uv run setup_pixeltable.py' to enable."
            )
        else:
            logger.warning(
                "  File multimodal search failed (embed limits or similarity error). "
                "Twelve Labs caps images at ~5 MB and video query files at ~36 MB; "
                "try a smaller file or add a text query for title fallback."
            )
        return None

    if q:
        logger.info("  [title fallback] text-only title similarity")
        rows = _title_similarity(videos_t, q, None, limit, creator_id)
        _attach_attrs(rows, videos_t)
        return rows

    return []


# ── Text-only search (backward-compatible GET) ──────────────────────────────


@router.get("/search", response_model=SearchResponse)
def search_videos(
    q: str = Query(..., min_length=1),
    creator_id: str | None = None,
    limit: int = Query(10, ge=1, le=50),
):
    logger.info("search: text q=%r, limit=%d", q, limit)

    # Try TL Search API first (returns scene-level timestamps)
    if not creator_id:
        tl_results = _tl_search(q, limit)
        if tl_results:
            return SearchResponse(query=q, modality="text", results=tl_results)

    # Fall back to Pixeltable similarity
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    scenes_t = _get_scenes_table()
    rows = _search(videos_t, scenes_t, q, creator_id, limit)
    return _format_results(rows, q)


# ── Multimodal search (POST with file upload) ──────────────────────────────


@router.post("/search", response_model=SearchResponse)
async def search_multimodal(
    q: str | None = Form(None),
    file: UploadFile | None = File(None),
    creator_id: str | None = Form(None),
    limit: int = Form(10),
):
    """Cross-modal search: text, image, video, or audio -> video results.

    All modalities search against video_segment embeddings on the
    video_scenes view for content-based similarity.
    """
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    scenes_t = _get_scenes_table()
    tmp_path: Path | None = None

    try:
        if file and file.filename:
            content_type = file.content_type or ""
            modality = MIME_TO_MODALITY.get(content_type)

            if not modality:
                ext = Path(file.filename).suffix.lower()
                if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                    modality = "image"
                elif ext in {".mp4", ".webm", ".mov"}:
                    modality = "video"
                elif ext in {".mp3", ".m4a", ".wav", ".webm"}:
                    modality = "audio"

            if not modality:
                logger.warning("Unknown file type: %s (%s)", file.filename, content_type)
                if q:
                    rows = _search(videos_t, scenes_t, q, creator_id, limit)
                    return _format_results(rows, q)
                return SearchResponse(query="unknown file type", results=[])

            suffix = Path(file.filename).suffix or f".{modality}"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_path = Path(tmp.name)
            shutil.copyfileobj(file.file, tmp)
            tmp.close()

            label = f"[{modality}] {file.filename}"
            logger.info("search: %s file=%r, limit=%d", modality, file.filename, limit)

            file_kwargs = {modality: str(tmp_path)}
            rows = _search(videos_t, scenes_t, q, creator_id, limit, **file_kwargs)
            if rows is None:
                return SearchResponse(
                    query=f"[{modality}] {file.filename}",
                    modality=modality,
                    results=[],
                    message="File search failed (e.g. file over embed size limit). Use a smaller image/video or add text.",
                )
            return _format_results(rows, label, modality=modality)

        elif q:
            logger.info("search: text q=%r, limit=%d", q, limit)
            rows = _search(videos_t, scenes_t, q, creator_id, limit)
            return _format_results(rows, q)

        else:
            return SearchResponse(query="", results=[])

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
