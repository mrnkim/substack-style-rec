"""Recommendation endpoints: for-you, similar, creator-catalog."""
import logging
from collections import defaultdict

from fastapi import APIRouter, HTTPException
import pixeltable as pxt

import config
from models import (
    CreatorCatalogRequest,
    CreatorCatalogResponse,
    CreatorResponse,
    ForYouRequest,
    RecommendationResponse,
    RecommendationsResponse,
    SimilarRequest,
)
from routers.videos import _attach_attrs, _build_video_response, _load_creators_map
from functions import generate_reason

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _apply_creator_diversity(
    candidates: list[dict], max_per_creator: int = 2
) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    result: list[dict] = []
    for c in candidates:
        cid = c.get("creator_id", "")
        if counts[cid] < max_per_creator:
            result.append(c)
            counts[cid] += 1
    return result


def _load_all_videos(videos_t) -> list[dict]:
    """Load all video rows once. Attributes are attached lazily."""
    rows = list(
        videos_t.select(
            videos_t.id, videos_t.title, videos_t.creator_id,
            videos_t.category, videos_t.duration, videos_t.thumbnail_url,
            videos_t.hls_url, videos_t.upload_date,
        ).collect()
    )
    _attach_attrs(rows, videos_t)
    return rows


def _similarity_candidates(
    videos_t, reference_title: str, exclude_ids: set[str], limit: int
) -> list[dict]:
    sim = videos_t.title.similarity(string=reference_title)
    rows = list(
        videos_t.order_by(sim, asc=False)
        .limit(limit + len(exclude_ids))
        .select(
            videos_t.id, videos_t.title, videos_t.creator_id,
            videos_t.category, videos_t.duration, videos_t.thumbnail_url,
            videos_t.hls_url, videos_t.upload_date,
            score=sim,
        )
        .collect()
    )
    return [r for r in rows if r["id"] not in exclude_ids]


def _extract_matched_attrs(source: dict, target: dict) -> list[str]:
    matched = []
    src_style = source.get("style")
    tgt_style = target.get("style")
    if src_style and tgt_style and src_style == tgt_style:
        matched.append(f"{tgt_style} format")

    src_tone = source.get("tone")
    tgt_tone = target.get("tone")
    if src_tone and tgt_tone and src_tone == tgt_tone:
        matched.append(f"{tgt_tone} tone")

    src_topics = set(source.get("topic") or [])
    tgt_topics = set(target.get("topic") or [])
    for t in list(src_topics & tgt_topics)[:2]:
        matched.append(t)

    return matched


# ---------------------------------------------------------------------------
# POST /api/recommendations/for-you
# ---------------------------------------------------------------------------

@router.post("/for-you", response_model=RecommendationsResponse)
def for_you(body: ForYouRequest):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()
    subscriptions = set(body.subscriptions)
    watched = set(body.watch_history)

    # --- Cold start (empty watch history) ---
    if not body.watch_history:
        all_videos = _load_all_videos(videos_t)
        unwatched = [v for v in all_videos if v["id"] not in watched]

        if subscriptions:
            sub_vids = sorted(
                [v for v in unwatched if v.get("creator_id") in subscriptions],
                key=lambda v: v.get("upload_date", ""),
                reverse=True,
            )
            other_vids = sorted(
                [v for v in unwatched if v.get("creator_id") not in subscriptions],
                key=lambda v: v.get("upload_date", ""),
                reverse=True,
            )
            combined = sub_vids + other_vids
        else:
            combined = sorted(unwatched, key=lambda v: v.get("upload_date", ""), reverse=True)

        combined = _apply_creator_diversity(combined)
        recs = []
        for v in combined[: body.limit]:
            video_resp = _build_video_response(v, creators_map)
            source = "subscription" if v.get("creator_id") in subscriptions else "discovery"
            recs.append(RecommendationResponse(
                video=video_resp, score=None,
                reason="New to you", matched_attributes=[], source=source,
            ))
        return RecommendationsResponse(recommendations=recs)

    # --- Standard flow: embedding similarity ---
    all_videos = _load_all_videos(videos_t)
    watched_vids = {v["id"]: v for v in all_videos if v["id"] in watched}
    attrs_by_id = {v["id"]: v for v in all_videos}

    recent_watched = body.watch_history[-5:]
    candidate_scores: dict[str, dict] = {}

    for wid in recent_watched:
        w_vid = watched_vids.get(wid)
        if not w_vid:
            continue
        candidates = _similarity_candidates(videos_t, w_vid["title"], watched, body.limit * 3)
        for c in candidates:
            vid = c["id"]
            score = c.get("score", 0.0)
            if vid not in candidate_scores or score > candidate_scores[vid].get("score", 0):
                c["_source_video"] = w_vid
                candidate_scores[vid] = c

    ranked = sorted(candidate_scores.values(), key=lambda x: x.get("score", 0), reverse=True)

    for c in ranked:
        vid_data = attrs_by_id.get(c["id"], {})
        c["topic"] = vid_data.get("topic")
        c["style"] = vid_data.get("style")
        c["tone"] = vid_data.get("tone")

    # 70/30 split with diversity applied per bucket
    sub_candidates = _apply_creator_diversity(
        [c for c in ranked if c.get("creator_id") in subscriptions]
    )
    disc_candidates = _apply_creator_diversity(
        [c for c in ranked if c.get("creator_id") not in subscriptions]
    )

    n_sub = max(1, int(body.limit * 0.7))
    n_disc = body.limit - n_sub

    final_sub = sub_candidates[:n_sub]
    final_disc = disc_candidates[:n_disc]

    # Backfill if either bucket is short
    if len(final_sub) < n_sub:
        extra = n_sub - len(final_sub)
        final_disc = disc_candidates[: n_disc + extra]
    elif len(final_disc) < n_disc:
        extra = n_disc - len(final_disc)
        final_sub = sub_candidates[: n_sub + extra]

    # Interleave: subscription first, then discovery (preserves quota)
    merged: list[dict] = []
    for c in final_sub:
        c["_source"] = "subscription"
        merged.append(c)
    for c in final_disc:
        c["_source"] = "discovery"
        merged.append(c)

    recs = []
    for c in merged[: body.limit]:
        video_resp = _build_video_response(c, creators_map)
        source_vid = c.get("_source_video", {})
        reason = generate_reason(source_vid, c, c.get("_source", "discovery"), subscriptions)
        recs.append(RecommendationResponse(
            video=video_resp,
            score=round(c.get("score", 0), 4) if c.get("score") else None,
            reason=reason,
            matched_attributes=_extract_matched_attrs(source_vid, c),
            source=c.get("_source", "discovery"),
        ))

    return RecommendationsResponse(recommendations=recs)


# ---------------------------------------------------------------------------
# POST /api/recommendations/similar
# ---------------------------------------------------------------------------

@router.post("/similar", response_model=RecommendationsResponse)
def similar(body: SimilarRequest):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    ref_rows = list(
        videos_t.where(videos_t.id == body.video_id)
        .select(videos_t.id, videos_t.title, videos_t.creator_id, videos_t.category)
        .collect()
    )
    if not ref_rows:
        raise HTTPException(status_code=404, detail="Video not found")

    ref = ref_rows[0]
    watched = set(body.watch_history)
    candidates = _similarity_candidates(videos_t, ref["title"], watched | {body.video_id}, body.limit * 3)
    _attach_attrs(candidates, videos_t)
    candidates = _apply_creator_diversity(candidates)

    subscriptions: set[str] = set()
    recs = []
    for c in candidates[: body.limit]:
        video_resp = _build_video_response(c, creators_map)
        source = "subscription" if c.get("creator_id") == ref.get("creator_id") else "discovery"
        reason = generate_reason(ref, c, source, subscriptions)
        recs.append(RecommendationResponse(
            video=video_resp,
            score=round(c.get("score", 0), 4) if c.get("score") else None,
            reason=reason,
            matched_attributes=_extract_matched_attrs(ref, c),
            source=source,
        ))

    return RecommendationsResponse(recommendations=recs)


# ---------------------------------------------------------------------------
# POST /api/recommendations/creator-catalog
# ---------------------------------------------------------------------------

@router.post("/creator-catalog", response_model=CreatorCatalogResponse)
def creator_catalog(body: CreatorCatalogRequest):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    if body.creator_id not in creators_map:
        raise HTTPException(status_code=404, detail="Creator not found")

    info = creators_map[body.creator_id]
    creator_resp = CreatorResponse(
        id=body.creator_id, name=info["name"],
        avatar_url=info["avatar_url"], description=info["description"],
        video_count=info["video_count"],
    )

    watched = set(body.watch_history)

    # Popular: all creator videos sorted by recency
    popular_rows = list(
        videos_t.where(videos_t.creator_id == body.creator_id)
        .select(
            videos_t.id, videos_t.title, videos_t.creator_id,
            videos_t.category, videos_t.duration, videos_t.thumbnail_url,
            videos_t.hls_url, videos_t.upload_date,
        )
        .collect()
    )
    _attach_attrs(popular_rows, videos_t)
    popular_rows.sort(key=lambda r: r.get("upload_date", ""), reverse=True)

    popular = [
        RecommendationResponse(
            video=_build_video_response(r, creators_map),
            score=None, reason="Popular from this creator",
            matched_attributes=[], source="subscription",
        )
        for r in popular_rows[: body.limit]
    ]

    # Recommended: relevance-sorted if watch history exists
    recommended: list[RecommendationResponse] = []
    if body.watch_history:
        all_videos = _load_all_videos(videos_t)
        watched_vids = [v for v in all_videos if v["id"] in watched]

        if watched_vids:
            # Aggregate similarity across recent watch history
            recent = watched_vids[-3:]
            candidate_scores: dict[str, dict] = {}
            for ref in recent:
                sim = videos_t.title.similarity(string=ref["title"])
                rows = list(
                    videos_t.where(videos_t.creator_id == body.creator_id)
                    .order_by(sim, asc=False)
                    .limit(body.limit)
                    .select(
                        videos_t.id, videos_t.title, videos_t.creator_id,
                        videos_t.category, videos_t.duration, videos_t.thumbnail_url,
                        videos_t.hls_url, videos_t.upload_date,
                        score=sim,
                    )
                    .collect()
                )
                for r in rows:
                    vid = r["id"]
                    score = r.get("score", 0.0)
                    if vid not in candidate_scores or score > candidate_scores[vid].get("score", 0):
                        candidate_scores[vid] = r

            ranked = sorted(candidate_scores.values(), key=lambda x: x.get("score", 0), reverse=True)
            _attach_attrs(ranked, videos_t)

            for r in ranked[: body.limit]:
                recommended.append(RecommendationResponse(
                    video=_build_video_response(r, creators_map),
                    score=round(r.get("score", 0), 4) if r.get("score") else None,
                    reason="Recommended based on your interests",
                    matched_attributes=[],
                    source="subscription",
                ))

    return CreatorCatalogResponse(
        creator=creator_resp,
        recommended=recommended,
        popular=popular,
    )
