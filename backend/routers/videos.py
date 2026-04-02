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

VIDEO_FIELDS = ("id", "title", "creator_id", "category", "duration", "thumbnail_url", "hls_url", "upload_date")


def _select_videos(videos_t, query=None):
    """Select base video fields from the table or a filtered query."""
    q = query if query is not None else videos_t
    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    return q.select(*cols)


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


def _build_video_response(row: dict, creators_map: dict[str, dict]) -> VideoResponse:
    """Convert a PixelTable row dict into a VideoResponse with nested creator."""
    cid = row.get("creator_id", "")
    cdata = creators_map.get(cid, {})

    attributes = None
    if row.get("topic") or row.get("style") or row.get("tone"):
        attributes = VideoAttributesResponse(
            topic=row["topic"] if isinstance(row.get("topic"), list) else [],
            style=row.get("style") or "",
            tone=row.get("tone") or "",
        )

    return VideoResponse(
        id=row["id"],
        title=row.get("title", ""),
        creator=CreatorResponse(
            id=cid, name=cdata.get("name", ""),
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
    )


def _load_creators_map() -> dict[str, dict]:
    """Load all creators keyed by id, with video_count."""
    creators_t = pxt.get_table(f"{config.APP_NAMESPACE}.creators")
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    creators = {
        c["id"]: {"name": c["name"], "avatar_url": c["avatar_url"], "description": c["description"], "video_count": 0}
        for c in creators_t.select(creators_t.id, creators_t.name, creators_t.avatar_url, creators_t.description).collect()
    }
    for r in videos_t.select(videos_t.creator_id).collect():
        cid = r.get("creator_id", "")
        if cid in creators:
            creators[cid]["video_count"] += 1
    return creators


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
    rows = list(_select_videos(videos_t, query).limit(limit).collect())
    _attach_attrs(rows, videos_t)

    return PaginatedVideosResponse(
        data=[_build_video_response(r, creators_map) for r in rows],
        page=page, total=total, total_pages=total_pages,
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
