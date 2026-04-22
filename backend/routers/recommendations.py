"""Recommendation endpoints: for-you, similar, creator-catalog."""

import logging
from collections import defaultdict
from pathlib import Path

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
    _scene_similarity,
    _select_videos,
    _title_similarity,
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


def _sim_kwargs_from_ref(ref: dict) -> dict:
    """Prefer full-file video query when local file exists and is under TL embed size cap; else title."""
    path = ref.get("_video_path") or ref.get("video")
    if path and str(path).strip():
        p = Path(str(path))
        try:
            if p.is_file():
                size = p.stat().st_size
                if size <= config.TWELVELABS_EMBED_VIDEO_MAX_BYTES:
                    return {"video": str(p)}
                logger.info(
                    "  skip video= query (%.1f MB > embed cap); using title",
                    size / (1024 * 1024),
                )
        except OSError:
            pass
    title = (ref.get("title") or "").strip()
    return {"string": title if title else "untitled"}


def _enrich_video_paths(rows: list[dict], videos_t) -> None:
    """Attach _video_path from the videos table for scene similarity(video=...)."""
    if not rows:
        return
    ids = [r["id"] for r in rows if r.get("id")]
    if not ids:
        return
    try:
        pmap = {
            r["id"]: r.get("video")
            for r in videos_t.where(videos_t.id.isin(ids))
            .select(videos_t.id, videos_t.video)
            .collect()
        }
    except Exception:
        return
    for r in rows:
        r["_video_path"] = pmap.get(r["id"])


def _similarity_candidates(
    videos_t,
    ref: dict,
    exclude_ids: set[str],
    limit: int,
    creator_id: str | None = None,
) -> list[dict]:
    """Query Marengo on video_scenes; use similarity(video=path) when available, else string=title."""
    scenes_t = _get_scenes_table()
    sim_kw = _sim_kwargs_from_ref(ref)
    title_fallback = (ref.get("title") or "untitled").strip()

    if scenes_t is not None:
        try:
            rows = _scene_similarity(scenes_t, exclude_ids, limit, creator_id, **sim_kw)
            if rows:
                if "video" in sim_kw:
                    logger.info("  [scene index] query=video file (content-to-content)")
                else:
                    logger.info("  [scene index] query=title text")
                return rows
        except Exception as exc:
            logger.warning("scene similarity failed (%s), falling back to title", exc)

    logger.info("  [title fallback] using title similarity")
    try:
        return _title_similarity(
            videos_t, title_fallback, exclude_ids, limit, creator_id
        )
    except Exception as exc:
        logger.warning("title similarity failed (%s); empty candidates", exc)
        return []


def _matched_attrs(source: dict, target: dict) -> list[str]:
    matched = []
    # Topic overlap first — most meaningful to users
    src_topics = set(source.get("topic") or [])
    tgt_topics = set(target.get("topic") or [])
    for t in list(src_topics & tgt_topics)[:2]:
        matched.append(t)
    # Style / tone as secondary signals
    if source.get("style") and source["style"] == target.get("style"):
        matched.append(f"{target['style']} style")
    if source.get("tone") and source["tone"] == target.get("tone"):
        matched.append(f"{target['tone']} tone")
    # If no attribute overlap, surface the target's own attributes
    if not matched:
        tgt_topic_list = target.get("topic") or []
        if tgt_topic_list:
            matched.append(tgt_topic_list[0])
        elif target.get("style"):
            matched.append(f"{target['style']} style")
        if target.get("tone") and len(matched) < 2:
            matched.append(f"{target['tone']} tone")
    return matched[:3]


def _to_rec(
    candidate: dict,
    creators_map: dict,
    source_video: dict,
    rec_source: str,
    subscriptions: set[str],
) -> RecommendationResponse:
    attrs = _matched_attrs(source_video, candidate)
    # Add contextual signal as last attribute
    target_creator = candidate.get("creator_id", "")
    if target_creator in subscriptions:
        attrs.append("From your subscriptions")
    elif rec_source == "discovery":
        creator_name = creators_map.get(target_creator, {}).get("name", "")
        if creator_name:
            attrs.append(f"New creator: {creator_name}")

    return RecommendationResponse(
        video=_build_video_response(candidate, creators_map),
        score=round(candidate["score"], 4) if candidate.get("score") else None,
        reason=generate_reason(source_video, candidate, rec_source, subscriptions),
        matched_attributes=attrs[:4],
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
    _enrich_video_paths(all_rows, videos_t)
    by_id = {v["id"]: v for v in all_rows}

    # If user has watched (almost) everything, don't exclude — just deprioritize
    exclude = watched if len(watched) < len(all_rows) - 2 else set()

    candidate_scores: dict[str, dict] = {}
    for wid in body.watch_history[-5:]:
        w_vid = by_id.get(wid)
        if not w_vid:
            continue
        for c in _similarity_candidates(
            videos_t, w_vid, exclude, body.limit * 3
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
    _enrich_video_paths(ref_rows, videos_t)
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
        _enrich_video_paths(all_rows, videos_t)
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
