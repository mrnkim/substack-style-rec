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
from routers.videos import (
    VIDEO_FIELDS,
    _attach_attrs,
    _build_video_response,
    _load_creators_map,
    _select_videos,
)
from functions import generate_reason

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _apply_diversity(candidates: list[dict], max_per_creator: int = 2) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    result: list[dict] = []
    for c in candidates:
        cid = c.get("creator_id", "")
        if counts[cid] < max_per_creator:
            result.append(c)
            counts[cid] += 1
    return result


def _similarity_candidates(
    videos_t,
    reference_title: str,
    exclude_ids: set[str],
    limit: int,
    creator_id: str | None = None,
) -> list[dict]:
    """Query Marengo .similarity() on title, optionally filtered by creator."""
    sim = videos_t.title.similarity(string=reference_title)
    query = videos_t
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    rows = list(
        query.order_by(sim, asc=False)
        .limit(limit + len(exclude_ids))
        .select(*cols, score=sim)
        .collect()
    )
    return [r for r in rows if r["id"] not in exclude_ids]


def _matched_attrs(source: dict, target: dict) -> list[str]:
    matched = []
    if source.get("style") and source["style"] == target.get("style"):
        matched.append(f"{target['style']} format")
    if source.get("tone") and source["tone"] == target.get("tone"):
        matched.append(f"{target['tone']} tone")
    for t in list((set(source.get("topic") or []) & set(target.get("topic") or [])))[
        :2
    ]:
        matched.append(t)
    return matched


def _to_rec(
    candidate: dict,
    creators_map: dict,
    source_video: dict,
    rec_source: str,
    subscriptions: set[str],
) -> RecommendationResponse:
    return RecommendationResponse(
        video=_build_video_response(candidate, creators_map),
        score=round(candidate["score"], 4) if candidate.get("score") else None,
        reason=generate_reason(source_video, candidate, rec_source, subscriptions),
        matched_attributes=_matched_attrs(source_video, candidate),
        source=rec_source,
    )


# ---------------------------------------------------------------------------
# POST /api/recommendations/for-you
# ---------------------------------------------------------------------------


@router.post("/for-you", response_model=RecommendationsResponse)
def for_you(body: ForYouRequest):
    logger.info(
        "for-you: %d subscriptions, %d watched, limit=%d",
        len(body.subscriptions),
        len(body.watch_history),
        body.limit,
    )
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()
    subscriptions = set(body.subscriptions)
    watched = set(body.watch_history)

    # Cold start: no watch history
    if not body.watch_history:
        all_rows = list(_select_videos(videos_t).collect())
        _attach_attrs(all_rows, videos_t)
        unwatched = [v for v in all_rows if v["id"] not in watched]

        if subscriptions:
            sub_vids = sorted(
                [v for v in unwatched if v.get("creator_id") in subscriptions],
                key=lambda v: v.get("upload_date", ""),
                reverse=True,
            )
            other = sorted(
                [v for v in unwatched if v.get("creator_id") not in subscriptions],
                key=lambda v: v.get("upload_date", ""),
                reverse=True,
            )
            combined = sub_vids + other
        else:
            combined = sorted(
                unwatched, key=lambda v: v.get("upload_date", ""), reverse=True
            )

        recs = [
            RecommendationResponse(
                video=_build_video_response(v, creators_map),
                score=None,
                reason="New to you",
                matched_attributes=[],
                source="subscription"
                if v.get("creator_id") in subscriptions
                else "discovery",
            )
            for v in _apply_diversity(combined)[: body.limit]
        ]
        logger.info("  cold start → %d recs", len(recs))
        return RecommendationsResponse(recommendations=recs)

    # Standard flow: Marengo similarity from watch history
    all_rows = list(_select_videos(videos_t).collect())
    _attach_attrs(all_rows, videos_t)
    by_id = {v["id"]: v for v in all_rows}

    # If user has watched (almost) everything, don't exclude — just deprioritize
    exclude = watched if len(watched) < len(all_rows) - 2 else set()

    candidate_scores: dict[str, dict] = {}
    for wid in body.watch_history[-5:]:
        w_vid = by_id.get(wid)
        if not w_vid:
            continue
        for c in _similarity_candidates(
            videos_t, w_vid["title"], exclude, body.limit * 3
        ):
            score = c.get("score") or 0.0
            best = candidate_scores.get(c["id"], {}).get("score") or 0.0
            if c["id"] not in candidate_scores or score > best:
                c["_source_video"] = w_vid
                candidate_scores[c["id"]] = c

    ranked = sorted(
        candidate_scores.values(), key=lambda x: x.get("score", 0), reverse=True
    )
    for c in ranked:
        vid = by_id.get(c["id"], {})
        c["topic"] = vid.get("topic")
        c["style"] = vid.get("style")
        c["tone"] = vid.get("tone")

    # 70/30 subscription vs discovery
    sub = _apply_diversity([c for c in ranked if c.get("creator_id") in subscriptions])
    disc = _apply_diversity(
        [c for c in ranked if c.get("creator_id") not in subscriptions]
    )

    n_sub = max(1, int(body.limit * 0.7))
    n_disc = body.limit - n_sub
    final_sub, final_disc = sub[:n_sub], disc[:n_disc]
    if len(final_sub) < n_sub:
        final_disc = disc[: n_disc + (n_sub - len(final_sub))]
    elif len(final_disc) < n_disc:
        final_sub = sub[: n_sub + (n_disc - len(final_disc))]

    recs = [
        _to_rec(
            c, creators_map, c.get("_source_video", {}), "subscription", subscriptions
        )
        for c in final_sub
    ] + [
        _to_rec(c, creators_map, c.get("_source_video", {}), "discovery", subscriptions)
        for c in final_disc
    ]
    final = recs[: body.limit]
    sub_count = sum(1 for r in final if r.source == "subscription")
    disc_count = len(final) - sub_count
    logger.info(
        "  → %d recs (%d sub + %d disc), top: %s",
        len(final),
        sub_count,
        disc_count,
        final[0].video.title[:50] if final else "none",
    )
    return RecommendationsResponse(recommendations=final)


# ---------------------------------------------------------------------------
# POST /api/recommendations/similar
# ---------------------------------------------------------------------------


@router.post("/similar", response_model=RecommendationsResponse)
def similar(body: SimilarRequest):
    logger.info("similar: video_id=%s", body.video_id)
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    ref_rows = list(
        _select_videos(videos_t, videos_t.where(videos_t.id == body.video_id)).collect()
    )
    if not ref_rows:
        raise HTTPException(status_code=404, detail="Video not found")

    _attach_attrs(ref_rows, videos_t)
    ref = ref_rows[0]
    total_videos = videos_t.count()
    watched_plus_current = set(body.watch_history) | {body.video_id}
    exclude = (
        watched_plus_current
        if len(watched_plus_current) < total_videos - 2
        else {body.video_id}
    )
    candidates = _similarity_candidates(
        videos_t,
        ref["title"],
        exclude,
        body.limit * 3,
    )
    _attach_attrs(candidates, videos_t)
    candidates = _apply_diversity(candidates)

    recs = [
        _to_rec(
            c,
            creators_map,
            ref,
            "subscription"
            if c.get("creator_id") == ref.get("creator_id")
            else "discovery",
            set(),
        )
        for c in candidates[: body.limit]
    ]
    logger.info(
        "  → %d similar to '%s'",
        len(recs),
        ref.get("title", "")[:40],
    )
    for r in recs[:3]:
        logger.info("    [%.3f] %s", r.score or 0, r.video.title[:50])
    return RecommendationsResponse(recommendations=recs)


# ---------------------------------------------------------------------------
# POST /api/recommendations/creator-catalog
# ---------------------------------------------------------------------------


@router.post("/creator-catalog", response_model=CreatorCatalogResponse)
def creator_catalog(body: CreatorCatalogRequest):
    logger.info(
        "creator-catalog: %s, %d watched", body.creator_id[:15], len(body.watch_history)
    )
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    if body.creator_id not in creators_map:
        raise HTTPException(status_code=404, detail="Creator not found")

    info = creators_map[body.creator_id]
    creator_resp = CreatorResponse(
        id=body.creator_id,
        name=info["name"],
        avatar_url=info["avatar_url"],
        description=info["description"],
        video_count=info["video_count"],
    )

    # Popular: this creator's videos sorted by recency
    popular_rows = list(
        _select_videos(
            videos_t, videos_t.where(videos_t.creator_id == body.creator_id)
        ).collect()
    )
    _attach_attrs(popular_rows, videos_t)
    popular_rows.sort(key=lambda r: r.get("upload_date", ""), reverse=True)

    popular = [
        RecommendationResponse(
            video=_build_video_response(r, creators_map),
            score=None,
            reason="Popular from this creator",
            matched_attributes=[],
            source="subscription",
        )
        for r in popular_rows[: body.limit]
    ]

    # Recommended: relevance-sorted via Marengo similarity to watch history
    recommended: list[RecommendationResponse] = []
    if body.watch_history:
        all_rows = list(_select_videos(videos_t).collect())
        _attach_attrs(all_rows, videos_t)
        watched_by_id = {
            v["id"]: v for v in all_rows if v["id"] in set(body.watch_history)
        }

        if watched_by_id:
            best: dict[str, dict] = {}
            for ref in list(watched_by_id.values())[-3:]:
                for c in _similarity_candidates(
                    videos_t,
                    ref["title"],
                    set(),
                    body.limit,
                    creator_id=body.creator_id,
                ):
                    if c["id"] not in best or c.get("score", 0) > best[c["id"]].get(
                        "score", 0
                    ):
                        best[c["id"]] = c

            ranked = sorted(
                best.values(), key=lambda x: x.get("score", 0), reverse=True
            )
            _attach_attrs(ranked, videos_t)
            recommended = [
                RecommendationResponse(
                    video=_build_video_response(r, creators_map),
                    score=round(r.get("score", 0), 4) if r.get("score") else None,
                    reason="Recommended based on your interests",
                    matched_attributes=[],
                    source="subscription",
                )
                for r in ranked[: body.limit]
            ]

    logger.info("  → %d recommended, %d popular", len(recommended), len(popular))
    return CreatorCatalogResponse(
        creator=creator_resp, recommended=recommended, popular=popular
    )
