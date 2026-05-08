"""Recommendation endpoints: for-you, similar, creator-catalog.

Recommendations are content-based, driven by Marengo scene embeddings stored
in the `scene_marengo` index. For each reference (watched) video we read its
stored scene vectors directly — no re-embedding — and run nearest-neighbor
queries against the same index. Per-target-video score = max similarity
across all (ref scene, target scene) pairs.
"""

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
    _attach_attrs,
    _build_video_response,
    _get_scenes_table,
    _load_creators_map,
    _scene_embeddings_for_video,
    _scene_vector_similarity,
    _select_videos,
    _title_similarity,
)
from functions import generate_reason

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


# For-you aggregates similarity across multiple watched videos, so each
# watched video doesn't need full scene coverage — neighbouring scenes have
# highly correlated Marengo embeddings, and information cross-pollinates
# across the 5 ref videos. Sampling here drops the cold for-you fetch from
# ~20–37 s to ~3–5 s (5 watched × 6 scenes vs 5 × ~50 scenes).
FOR_YOU_REF_SCENES_PER_VIDEO = 6


def _sample_evenly(items: list, n: int) -> list:
    """Return up to n items uniformly spaced across the input list."""
    if len(items) <= n or n <= 0:
        return list(items)
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


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
    ref: dict,
    exclude_ids: set[str],
    limit: int,
    creator_id: str | None = None,
    max_ref_scenes: int | None = None,
) -> list[dict]:
    """Find videos similar to `ref` using its stored scene embeddings.

    For each scene of the reference video, runs a nearest-neighbor query over
    the `scene_marengo` index. Results are aggregated per target video, keeping
    the row with the highest similarity score across any (ref scene, target
    scene) pair. Always excludes the reference video itself.

    `max_ref_scenes` caps the number of ref scenes queried via uniform sampling.
    The caller should pass it for hot paths where multi-video aggregation makes
    full per-scene coverage cost-prohibitive (e.g. for-you across 5 watched
    videos). Defaults to no cap.

    Falls back to title-text similarity only if the scene index or the
    reference's stored embeddings are unavailable (e.g., scene detection failed
    for that video).
    """
    scenes_t = _get_scenes_table()
    ref_id = ref.get("id")
    exclude_with_self = set(exclude_ids) | ({ref_id} if ref_id else set())

    if scenes_t is not None and ref_id:
        ref_embs = _scene_embeddings_for_video(scenes_t, ref_id)
        if ref_embs:
            sampled_embs = (
                _sample_evenly(ref_embs, max_ref_scenes)
                if max_ref_scenes
                else ref_embs
            )
            best: dict[str, dict] = {}
            for vec in sampled_embs:
                try:
                    rows = _scene_vector_similarity(
                        scenes_t, vec, exclude_with_self, limit, creator_id
                    )
                except Exception as exc:
                    logger.warning("vector similarity failed (%s)", exc)
                    continue
                for r in rows:
                    vid = r["id"]
                    score = r.get("score") or 0.0
                    prev = best.get(vid)
                    if prev is None or score > (prev.get("score") or 0.0):
                        best[vid] = r
            ranked = sorted(
                best.values(), key=lambda x: x.get("score", 0), reverse=True
            )
            if ranked:
                logger.info(
                    "  [scene index] %d/%d ref scenes → %d candidates",
                    len(sampled_embs), len(ref_embs), len(ranked),
                )
                return ranked[:limit]

    title_fallback = (ref.get("title") or "untitled").strip()
    logger.info("  [title fallback] no stored scene embeddings for ref; using title")
    try:
        return _title_similarity(
            videos_t, title_fallback, exclude_with_self, limit, creator_id
        )
    except Exception as exc:
        logger.warning("title similarity failed (%s); empty candidates", exc)
        return []


def _shared_attrs(source: dict, target: dict) -> list[str]:
    """Return ONLY topic/style/tone values genuinely shared between source and
    target. May be empty if there is no overlap."""
    matched: list[str] = []
    src_topics = set(source.get("topic") or [])
    tgt_topics = set(target.get("topic") or [])
    matched.extend(list(src_topics & tgt_topics)[:2])
    if source.get("style") and source["style"] == target.get("style"):
        matched.append(f"{target['style']} style")
    if source.get("tone") and source["tone"] == target.get("tone"):
        matched.append(f"{target['tone']} tone")
    return matched[:3]


def _target_tags(target: dict) -> list[str]:
    """Surface the target video's own topic/style/tone as a fallback display
    when no shared attributes exist."""
    tags: list[str] = []
    tags.extend((target.get("topic") or [])[:2])
    if target.get("style"):
        tags.append(f"{target['style']} style")
    if target.get("tone"):
        tags.append(f"{target['tone']} tone")
    return tags[:3]


def _to_rec(
    candidate: dict,
    creators_map: dict,
    source_video: dict,
    rec_source: str,
    subscriptions: set[str],
    context: str = "similar",
) -> RecommendationResponse:
    shared = _shared_attrs(source_video, candidate)
    # Only surface target's own tags as a fallback when there is no real overlap
    fallback_tags = _target_tags(candidate) if not shared else []

    target_creator = candidate.get("creator_id", "")
    context_tag: str | None = None
    if target_creator in subscriptions:
        context_tag = "From your subscriptions"
    elif rec_source == "discovery":
        creator_name = creators_map.get(target_creator, {}).get("name", "")
        if creator_name:
            context_tag = f"New creator: {creator_name}"

    return RecommendationResponse(
        video=_build_video_response(candidate, creators_map),
        score=round(candidate["score"], 4) if candidate.get("score") else None,
        reason=generate_reason(
            source_video, candidate, rec_source, subscriptions, context
        ),
        matched_attributes=shared,
        video_tags=fallback_tags,
        context_tag=context_tag,
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

        # Cold start has no signal to explain — leave reason and tags blank
        # so the frontend hides the rec-block entirely instead of stamping
        # every card with an identical "Discover / New to you" box.
        recs = [
            RecommendationResponse(
                video=_build_video_response(v, creators_map),
                score=None,
                reason="",
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

    # Recency-weighted aggregation across the last 5 watched videos.
    # The most recent watch dominates (weight 0.5) but earlier watches still
    # contribute, so a candidate that's broadly relevant to recent history
    # outranks a one-hit anchor from the very first thing the user watched.
    # Without weighting, a candidate that scored 0.9 against the first watch
    # would lock in the top slot forever (max-aggregation), which made the
    # For You row look static across navigations.
    RECENCY_WEIGHTS = [0.5, 0.25, 0.125, 0.0625, 0.0625]
    recent_watches = list(reversed(body.watch_history[-5:]))
    total_weight = sum(RECENCY_WEIGHTS[: len(recent_watches)]) or 1.0

    candidate_scores: dict[str, dict] = {}
    for idx, wid in enumerate(recent_watches):
        weight = RECENCY_WEIGHTS[idx] if idx < len(RECENCY_WEIGHTS) else 0.0
        if weight <= 0:
            continue
        w_vid = by_id.get(wid)
        if not w_vid:
            continue
        for c in _similarity_candidates(
            videos_t,
            w_vid,
            exclude,
            body.limit * 3,
            max_ref_scenes=FOR_YOU_REF_SCENES_PER_VIDEO,
        ):
            contribution = (c.get("score") or 0.0) * weight
            existing = candidate_scores.get(c["id"])
            if existing is None:
                new_row = dict(c)
                new_row["score"] = contribution
                # Iterating most-recent-first means the first contributor we
                # see for a candidate is the most recent watch that produced it
                new_row["_source_video"] = w_vid
                candidate_scores[c["id"]] = new_row
            else:
                existing["score"] = (existing.get("score") or 0.0) + contribution

    # Normalize summed weighted scores back to the underlying 0..1 similarity
    # range so the displayed "Video Match: NN" stays interpretable.
    for c in candidate_scores.values():
        c["score"] = (c.get("score") or 0.0) / total_weight

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
            c,
            creators_map,
            c.get("_source_video", {}),
            "subscription",
            subscriptions,
            context="for_you",
        )
        for c in final_sub
    ] + [
        _to_rec(
            c,
            creators_map,
            c.get("_source_video", {}),
            "discovery",
            subscriptions,
            context="for_you",
        )
        for c in final_disc
    ]
    final = recs[: body.limit]
    sub_count = sum(1 for r in final if r.source == "subscription")
    disc_count = len(final) - sub_count
    if final:
        top = final[0]
        logger.info(
            "  → %d recs (%d sub + %d disc) | [%.3f] %s",
            len(final), sub_count, disc_count,
            top.score or 0, top.video.title[:50],
        )
    else:
        logger.info("  → 0 recs")
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
        ref,
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
    if recs:
        top = recs[0]
        logger.info("  → %d similar | [%.3f] %s", len(recs), top.score or 0, top.video.title[:50])
    else:
        logger.info("  → 0 similar")
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
                    ref,
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
