from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ---------------------------------------------------------------------------
# Response models (match frontend src/lib/types.ts)
# ---------------------------------------------------------------------------


class CreatorResponse(CamelModel):
    id: str
    name: str
    avatar_url: str = ""
    description: str = ""
    video_count: int = 0


class VideoAttributesResponse(CamelModel):
    topic: list[str] = Field(default_factory=list)
    style: str = ""
    tone: str = ""


class VideoResponse(CamelModel):
    id: str
    title: str
    creator: CreatorResponse
    category: Literal["interview", "commentary", "creative", "educational"]
    duration: int
    thumbnail_url: str = ""
    hls_url: str | None = None
    upload_date: str = ""
    attributes: VideoAttributesResponse | None = None


class RecommendationResponse(CamelModel):
    video: VideoResponse
    score: float | None = None
    reason: str = ""
    matched_attributes: list[str] = Field(default_factory=list)
    source: Literal["subscription", "discovery"] = "discovery"


# ---------------------------------------------------------------------------
# Paginated / list wrappers
# ---------------------------------------------------------------------------


class PaginatedVideosResponse(BaseModel):
    data: list[VideoResponse]
    page: int
    total: int
    total_pages: int


class CreatorsListResponse(BaseModel):
    data: list[CreatorResponse]


class CreatorDetailResponse(BaseModel):
    creator: CreatorResponse
    videos: list[VideoResponse]
    total_videos: int


# ---------------------------------------------------------------------------
# Recommendation request bodies
# ---------------------------------------------------------------------------


class ForYouRequest(CamelModel):
    subscriptions: list[str] = Field(default_factory=list)
    watch_history: list[str] = Field(default_factory=list)
    limit: int = 10


class SimilarRequest(CamelModel):
    video_id: str
    watch_history: list[str] = Field(default_factory=list)
    limit: int = 6


class CreatorCatalogRequest(CamelModel):
    creator_id: str
    watch_history: list[str] = Field(default_factory=list)
    limit: int = 20


class RecommendationsResponse(BaseModel):
    recommendations: list[RecommendationResponse]


class CreatorCatalogResponse(BaseModel):
    """Spec-compliant response for creator-catalog endpoint."""

    creator: CreatorResponse
    recommended: list[RecommendationResponse]
    popular: list[RecommendationResponse]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class SearchResultItem(BaseModel):
    video: VideoResponse
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
