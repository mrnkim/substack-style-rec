"""Video listing and detail endpoints.

Also exports shared helpers used by other routers:
    VIDEO_FIELDS, _select_videos, _attach_attrs, _build_video_response,
    _load_creators_map, _get_scenes_table, _scene_similarity, _title_similarity,
    _scene_embeddings_for_video, _scene_vector_similarity
"""

import logging
import time

from fastapi import APIRouter, HTTPException, Query
import pixeltable as pxt

import config
from models import (
    ChapterResponse,
    CreatorResponse,
    PaginatedVideosResponse,
    VideoAttributesResponse,
    VideoResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["videos"])

VIDEO_FIELDS = (
    "id",
    "title",
    "creator_id",
    "category",
    "duration",
    "thumbnail_url",
    "hls_url",
    "upload_date",
)

SCENE_INDEX_NAME = "scene_marengo"


def _get_scenes_table():
    """Return the video_scenes view, or None if unavailable."""
    try:
        return pxt.get_table(f"{config.APP_NAMESPACE}.video_scenes")
    except Exception:
        return None


ATTR_FIELDS = ("topic", "style", "tone")
GENERATED_FIELDS = ("summary", "chapters")
ALL_FIELDS = VIDEO_FIELDS + ATTR_FIELDS + GENERATED_FIELDS


def _select_videos(videos_t, query=None, include_attrs: bool = True):
    """Select video fields, including computed attrs when available."""
    q = query if query is not None else videos_t
    if include_attrs:
        try:
            cols = [getattr(videos_t, f) for f in ALL_FIELDS]
            return q.select(*cols)
        except Exception:
            pass
    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    return q.select(*cols)


def _scene_similarity(
    scenes_t,
    exclude_ids: set[str] | None = None,
    limit: int = 10,
    creator_id: str | None = None,
    **sim_kwargs,
) -> list[dict]:
    """Query video_segment embeddings on scenes view, deduplicate to unique videos.

    Accepts any similarity kwargs: string="text", image="/path", video="/path", audio="/path".
    """
    sim = scenes_t.video_segment.similarity(**sim_kwargs)
    query = scenes_t
    if creator_id:
        query = query.where(scenes_t.creator_id == creator_id)

    exclude = exclude_ids or set()
    cols = [getattr(scenes_t, f) for f in VIDEO_FIELDS]
    # Include scene timestamps when available
    try:
        cols.extend([scenes_t.segment_start, scenes_t.segment_end])
        has_timestamps = True
    except AttributeError:
        has_timestamps = False
    # Fetch extra scenes before deduping to unique videos; a small multiplier
    # under-fills when a few titles dominate the top-N scenes (hurts recall).
    fetch_mult = 12
    scene_rows = list(
        query.order_by(sim, asc=False)
        .limit((limit + len(exclude)) * fetch_mult)
        .select(*cols, score=sim)
        .collect()
    )

    seen: set[str] = set()
    deduped: list[dict] = []
    for row in scene_rows:
        vid = row["id"]
        if vid not in seen and vid not in exclude:
            seen.add(vid)
            deduped.append(row)
            if len(deduped) >= limit:
                break
    return deduped


def _title_similarity(
    videos_t,
    query_string: str,
    exclude_ids: set[str] | None = None,
    limit: int = 10,
    creator_id: str | None = None,
) -> list[dict]:
    """Title-embedding similarity on the videos table (fallback)."""
    sim = videos_t.title.similarity(string=query_string)
    query = videos_t
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    exclude = exclude_ids or set()
    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    rows = list(
        query.order_by(sim, asc=False)
        .limit(limit + len(exclude))
        .select(*cols, score=sim)
        .collect()
    )
    return [r for r in rows if r["id"] not in exclude]


def _scene_embeddings_for_video(scenes_t, video_id: str) -> list:
    """Return the stored Marengo scene embeddings for one video (no re-embedding).

    Reads them via ColumnRef.embedding(idx=...) — the index values themselves —
    so this is a direct lookup, not an API call.
    """
    try:
        emb_col = scenes_t.video_segment.embedding(idx=SCENE_INDEX_NAME)
        rows = list(
            scenes_t.where(scenes_t.id == video_id)
            .select(emb=emb_col)
            .collect()
        )
        return [r["emb"] for r in rows if r.get("emb") is not None]
    except Exception as exc:
        logger.warning("Could not read stored scene embeddings for %s: %s", video_id, exc)
        return []


def _scene_vector_similarity(
    scenes_t,
    query_vec,
    exclude_ids: set[str] | None = None,
    limit: int = 10,
    creator_id: str | None = None,
) -> list[dict]:
    """Nearest-neighbor over the scene index using a raw vector. Dedupes scenes → videos."""
    sim = scenes_t.video_segment.similarity(vector=query_vec)
    query = scenes_t
    if creator_id:
        query = query.where(scenes_t.creator_id == creator_id)

    exclude = exclude_ids or set()
    cols = [getattr(scenes_t, f) for f in VIDEO_FIELDS]
    try:
        cols.extend([scenes_t.segment_start, scenes_t.segment_end])
    except AttributeError:
        pass
    fetch_mult = 12
    scene_rows = list(
        query.order_by(sim, asc=False)
        .limit((limit + len(exclude)) * fetch_mult)
        .select(*cols, score=sim)
        .collect()
    )

    seen: set[str] = set()
    deduped: list[dict] = []
    for row in scene_rows:
        vid = row["id"]
        if vid not in seen and vid not in exclude:
            seen.add(vid)
            deduped.append(row)
            if len(deduped) >= limit:
                break
    return deduped


def _attach_attrs(rows: list[dict], videos_t) -> None:
    """Attach topic/style/tone to rows missing them (e.g. from chunk queries)."""
    if not rows or rows[0].get("topic") is not None:
        return
    try:
        row_ids = [r["id"] for r in rows]
        attr_rows = list(
            videos_t.where(videos_t.id.isin(row_ids))
            .select(videos_t.id, videos_t.topic, videos_t.style, videos_t.tone)
            .collect()
        )
        attr_map = {r["id"]: r for r in attr_rows}
        for row in rows:
            attrs = attr_map.get(row["id"], {})
            row["topic"] = attrs.get("topic")
            row["style"] = attrs.get("style")
            row["tone"] = attrs.get("tone")
    except Exception as e:
        logger.debug("Could not load attributes: %s", e)


def _build_video_response(row: dict, creators_map: dict[str, dict]) -> VideoResponse:
    """Convert a Pixeltable row dict into a VideoResponse with nested creator."""
    cid = row.get("creator_id", "")
    cdata = creators_map.get(cid, {})

    attributes = None
    if row.get("topic") or row.get("style") or row.get("tone"):
        attributes = VideoAttributesResponse(
            topic=row["topic"] if isinstance(row.get("topic"), list) else [],
            style=row.get("style") or "",
            tone=row.get("tone") or "",
        )

    chapters_raw = row.get("chapters")
    chapters = (
        [
            ChapterResponse(
                start=float(c.get("start", 0) or 0),
                end=float(c.get("end", 0) or 0),
                title=str(c.get("title", "") or ""),
                summary=str(c.get("summary", "") or ""),
            )
            for c in chapters_raw
            if isinstance(c, dict)
        ]
        if isinstance(chapters_raw, list) and chapters_raw
        else None
    )

    summary_raw = row.get("summary")
    summary = summary_raw.strip() if isinstance(summary_raw, str) and summary_raw.strip() else None

    return VideoResponse(
        id=row["id"],
        title=row.get("title", ""),
        creator=CreatorResponse(
            id=cid,
            name=cdata.get("name", ""),
            avatar_url=cdata.get("avatar_url", ""),
            description=cdata.get("description", ""),
            video_count=cdata.get("video_count", 0),
        ),
        category=row.get("category", "interview"),
        duration=row.get("duration", 0),
        thumbnail_url=row.get("thumbnail_url", ""),
        hls_url=row.get("hls_url"),
        upload_date=row.get("upload_date", ""),
        attributes=attributes,
        summary=summary,
        chapters=chapters,
    )


_creators_cache: dict[str, dict] | None = None
_creators_cache_ts: float = 0.0
_CREATORS_CACHE_TTL = 300.0  # 5 minutes


def _load_creators_map() -> dict[str, dict]:
    """Load all creators keyed by id, with video_count. Cached for 5 min."""
    global _creators_cache, _creators_cache_ts
    now = time.monotonic()
    if _creators_cache is not None and (now - _creators_cache_ts) < _CREATORS_CACHE_TTL:
        return _creators_cache

    creators_t = pxt.get_table(f"{config.APP_NAMESPACE}.creators")
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    creators = {
        c["id"]: {
            "name": c["name"],
            "avatar_url": c["avatar_url"],
            "description": c["description"],
            "video_count": 0,
        }
        for c in creators_t.select(
            creators_t.id,
            creators_t.name,
            creators_t.avatar_url,
            creators_t.description,
        ).collect()
    }
    for r in videos_t.select(videos_t.creator_id).collect():
        cid = r.get("creator_id", "")
        if cid in creators:
            creators[cid]["video_count"] += 1

    _creators_cache = creators
    _creators_cache_ts = now
    return creators


@router.get("/videos", response_model=PaginatedVideosResponse)
def list_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    creator_id: str | None = None,
):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    query = videos_t
    if category:
        query = query.where(videos_t.category == category)
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    raw_rows = list(_select_videos(videos_t, query).collect())
    # Incremental setup runs (no --drop-dir) can leave duplicate-id rows;
    # collapse to first occurrence so the listing is clean.
    seen: set[str] = set()
    all_rows: list[dict] = []
    for r in raw_rows:
        rid = r.get("id")
        if rid and rid not in seen:
            seen.add(rid)
            all_rows.append(r)
    total = len(all_rows)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    rows = all_rows[start : start + limit]
    _attach_attrs(rows, videos_t)

    return PaginatedVideosResponse(
        data=[_build_video_response(r, creators_map) for r in rows],
        page=page,
        total=total,
        total_pages=total_pages,
    )


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: str):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    rows = list(
        _select_videos(videos_t, videos_t.where(videos_t.id == video_id)).collect()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Video not found")

    _attach_attrs(rows, videos_t)
    return _build_video_response(rows[0], _load_creators_map())
