"""Video listing and detail endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import pixeltable as pxt

import config
from models import (
    CreatorResponse,
    PaginatedVideosResponse,
    VideoAttributesResponse,
    VideoResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["videos"])


def _build_video_response(row: dict, creators_map: dict[str, dict]) -> VideoResponse:
    """Convert a PixelTable row dict into a VideoResponse with nested creator."""
    creator_id = row.get("creator_id", "")
    creator_data = creators_map.get(creator_id, {})

    creator = CreatorResponse(
        id=creator_id,
        name=creator_data.get("name", ""),
        avatar_url=creator_data.get("avatar_url", ""),
        description=creator_data.get("description", ""),
        video_count=creator_data.get("video_count", 0),
    )

    attributes = None
    topic = row.get("topic")
    style = row.get("style")
    tone = row.get("tone")
    if topic or style or tone:
        attributes = VideoAttributesResponse(
            topic=topic if isinstance(topic, list) else [],
            style=style or "",
            tone=tone or "",
        )

    return VideoResponse(
        id=row["id"],
        title=row.get("title", ""),
        creator=creator,
        category=row.get("category", "interview"),
        duration=row.get("duration", 0),
        thumbnail_url=row.get("thumbnail_url", ""),
        hls_url=row.get("hls_url"),
        upload_date=row.get("upload_date", ""),
        attributes=attributes,
    )


def _load_creators_map() -> dict[str, dict]:
    """Load all creators into a dict keyed by id, with video_count computed."""
    creators_t = pxt.get_table(f"{config.APP_NAMESPACE}.creators")
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    creators_rows = list(
        creators_t.select(
            creators_t.id, creators_t.name,
            creators_t.avatar_url, creators_t.description,
        ).collect()
    )

    video_rows = list(videos_t.select(videos_t.creator_id).collect())
    counts: dict[str, int] = {}
    for r in video_rows:
        cid = r.get("creator_id", "")
        counts[cid] = counts.get(cid, 0) + 1

    result: dict[str, dict] = {}
    for c in creators_rows:
        cid = c["id"]
        result[cid] = {
            "name": c.get("name", ""),
            "avatar_url": c.get("avatar_url", ""),
            "description": c.get("description", ""),
            "video_count": counts.get(cid, 0),
        }
    return result


def _select_video_fields(videos_t, query=None):
    """Build a select expression for all base + attribute columns."""
    q = query if query is not None else videos_t
    base = q.select(
        videos_t.id, videos_t.title, videos_t.creator_id,
        videos_t.category, videos_t.duration, videos_t.thumbnail_url,
        videos_t.hls_url, videos_t.upload_date,
    )
    return base


def _attach_attrs(rows: list[dict], videos_t) -> None:
    """Attach topic/style/tone from computed columns to row dicts in-place."""
    if not rows:
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


@router.get("/videos", response_model=PaginatedVideosResponse)
def list_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    creator_id: Optional[str] = None,
):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    query = videos_t
    if category:
        query = query.where(videos_t.category == category)
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)

    page_rows = list(
        _select_video_fields(videos_t, query)
        .limit(limit)
        .collect()
    )

    _attach_attrs(page_rows, videos_t)

    data = [_build_video_response(r, creators_map) for r in page_rows]
    return PaginatedVideosResponse(data=data, page=page, total=total, total_pages=total_pages)


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: str):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    rows = list(
        videos_t.where(videos_t.id == video_id)
        .select(
            videos_t.id, videos_t.title, videos_t.creator_id,
            videos_t.category, videos_t.duration, videos_t.thumbnail_url,
            videos_t.hls_url, videos_t.upload_date,
        )
        .collect()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Video not found")

    _attach_attrs(rows, videos_t)
    return _build_video_response(rows[0], creators_map)
