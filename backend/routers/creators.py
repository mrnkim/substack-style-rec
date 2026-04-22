"""Creator listing and detail endpoints."""

import logging

from fastapi import APIRouter, HTTPException
import pixeltable as pxt

import config
from models import CreatorDetailResponse, CreatorResponse, CreatorsListResponse
from routers.videos import (
    _attach_attrs,
    _build_video_response,
    _load_creators_map,
    _select_videos,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["creators"])


@router.get("/creators", response_model=CreatorsListResponse)
def list_creators():
    creators_map = _load_creators_map()
    data = [
        CreatorResponse(
            id=cid,
            name=info["name"],
            avatar_url=info["avatar_url"],
            description=info["description"],
            video_count=info["video_count"],
        )
        for cid, info in creators_map.items()
    ]
    return CreatorsListResponse(data=data)


@router.get("/creators/{creator_id}", response_model=CreatorDetailResponse)
def get_creator(creator_id: str):
    creators_map = _load_creators_map()
    if creator_id not in creators_map:
        raise HTTPException(status_code=404, detail="Creator not found")

    info = creators_map[creator_id]
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    rows = list(
        _select_videos(
            videos_t, videos_t.where(videos_t.creator_id == creator_id)
        ).collect()
    )
    _attach_attrs(rows, videos_t)

    return CreatorDetailResponse(
        creator=CreatorResponse(
            id=creator_id,
            name=info["name"],
            avatar_url=info["avatar_url"],
            description=info["description"],
            video_count=info["video_count"],
        ),
        videos=[_build_video_response(r, creators_map) for r in rows],
        total_videos=len(rows),
    )
