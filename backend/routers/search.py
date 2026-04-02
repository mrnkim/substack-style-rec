"""Semantic video search via PixelTable .similarity()."""
import logging
from typing import Optional

from fastapi import APIRouter, Query
import pixeltable as pxt

import config
from models import SearchResponse, SearchResultItem
from routers.videos import _attach_attrs, _build_video_response, _load_creators_map

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search_videos(
    q: str = Query(..., min_length=1),
    creator_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    sim = videos_t.title.similarity(string=q)

    query = videos_t
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    rows = list(
        query.order_by(sim, asc=False)
        .limit(limit)
        .select(
            videos_t.id, videos_t.title, videos_t.creator_id,
            videos_t.category, videos_t.duration, videos_t.thumbnail_url,
            videos_t.hls_url, videos_t.upload_date,
            score=sim,
        )
        .collect()
    )

    _attach_attrs(rows, videos_t)

    results = [
        SearchResultItem(
            video=_build_video_response(row, creators_map),
            score=round(row.get("score", 0.0), 4),
        )
        for row in rows
    ]

    return SearchResponse(query=q, results=results)
