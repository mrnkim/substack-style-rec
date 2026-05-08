"""Pixeltable schema + data setup.

Pulls metadata + precomputed visual scene embeddings from the Twelve Labs
indexed assets API and stores them in Pixeltable. No local mp4 files,
no scene detection, no re-embedding — TL did all of that at upload time.

Pixeltable's role here:
  - Multimodal table + Array index (precomputed embeddings, 1st-class feature)
  - Declarative computed columns: analyze_video, fetch_tl_segments
  - Embedding indexes maintained automatically as rows arrive
  - Cross-modal text→video query via string_embed=marengo at query time

Run once — everything is idempotent.

Usage:
    uv run setup_pixeltable.py         # 3 quick-start videos
    uv run setup_pixeltable.py --full  # all 25 videos
"""

import argparse
import logging

import httpx
import numpy as np
import pixeltable as pxt
from pixeltable.functions.twelvelabs import embed

import config
from functions import analyze_video, fetch_tl_segments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUICK_YOUTUBE_IDS = {"sO4te2QNsHY", "ntPGl8UyIq4", "QpKypvDjiPM"}

marengo = embed.using(model_name="marengo3.0")

# Marengo 3.0 visual embeddings are 512-dim.
EMBEDDING_DIM = 512


def setup(full: bool = False):
    mode = "all 25 videos" if full else f"{len(QUICK_YOUTUBE_IDS)} quick-start videos"
    logger.info("Setting up Pixeltable — %s", mode)
    pxt.create_dir(config.APP_NAMESPACE, if_exists="ignore")

    # -- Schema ---------------------------------------------------------------

    creators = pxt.create_table(
        f"{config.APP_NAMESPACE}.creators",
        {
            "id": pxt.Required[pxt.String],
            "name": pxt.String,
            "avatar_url": pxt.String,
            "description": pxt.String,
        },
        primary_key=["id"],
        if_exists="ignore",
    )

    videos = pxt.create_table(
        f"{config.APP_NAMESPACE}.videos",
        {
            "id": pxt.Required[pxt.String],
            "title": pxt.String,
            "creator_id": pxt.String,
            "category": pxt.String,
            "duration": pxt.Int,
            "thumbnail_url": pxt.String,
            "hls_url": pxt.String,
            "upload_date": pxt.String,
        },
        primary_key=["id"],
        if_exists="ignore",
    )

    # Title text embedding (text → video search fallback)
    videos.add_embedding_index(
        "title", string_embed=marengo, idx_name="title_marengo", if_exists="ignore"
    )

    # Attribute extraction via Twelve Labs Analyze API
    videos.add_computed_column(
        raw_attributes=analyze_video(videos.id), if_exists="ignore"
    )
    videos.add_computed_column(topic=videos.raw_attributes["topic"], if_exists="ignore")
    videos.add_computed_column(style=videos.raw_attributes["style"], if_exists="ignore")
    videos.add_computed_column(tone=videos.raw_attributes["tone"], if_exists="ignore")

    # TL retrieve: precomputed visual segment embeddings
    videos.add_computed_column(
        tl_segments=fetch_tl_segments(videos.id), if_exists="ignore"
    )

    # Scenes table: one row per Marengo visual segment from TL retrieve.
    # Stored visual_embedding is a precomputed Array — Pixeltable indexes the
    # vectors directly, no embed function called on insert. string_embed=marengo
    # is only used at query time to embed text queries into the same space.
    scenes = pxt.create_table(
        f"{config.APP_NAMESPACE}.scenes",
        {
            "video_id": pxt.Required[pxt.String],
            "segment_idx": pxt.Required[pxt.Int],
            "start_sec": pxt.Float,
            "end_sec": pxt.Float,
            "visual_embedding": pxt.Required[pxt.Array[(EMBEDDING_DIM,), pxt.Float]],
        },
        primary_key=["video_id", "segment_idx"],
        if_exists="ignore",
    )
    scenes.add_embedding_index(
        "visual_embedding",
        string_embed=marengo,
        metric="cosine",
        idx_name="scene_marengo",
        if_exists="ignore",
    )
    logger.info("  Schema ready")

    # -- Data from Twelve Labs index ------------------------------------------

    logger.info("  Fetching from Twelve Labs index %s ...", config.TWELVELABS_INDEX_ID)
    tl_videos = _fetch_tl_videos()
    logger.info("  Found %d videos in index", len(tl_videos))

    if not full:
        tl_videos = [
            v for v in tl_videos
            if (v.get("user_metadata") or {}).get("youtubeId") in QUICK_YOUTUBE_IDS
        ]
        logger.info("  Quick-start: using %d videos (pass --full for all)", len(tl_videos))

    # Creators
    seen: set[str] = set()
    creator_rows = []
    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        cid, cname = meta.get("creatorId"), meta.get("creatorName")
        if cid and cname and cid not in seen:
            seen.add(cid)
            creator_rows.append(
                {
                    "id": cid,
                    "name": cname,
                    "avatar_url": "",
                    "description": config.CREATOR_DESCRIPTIONS.get(cid, ""),
                }
            )
    if creator_rows:
        status = creators.insert(creator_rows, on_error="ignore")
        logger.info("  Creators: %d inserted", status.num_rows)

    # Videos — metadata only, no local file path
    video_rows = []
    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        sys_meta = tlv.get("system_metadata", {})
        hls = tlv.get("hls") or {}
        if not meta.get("creatorId") or not meta.get("creatorName"):
            continue

        title = (sys_meta.get("filename") or "").rsplit(".", 1)[0]
        video_rows.append(
            {
                "id": tlv["_id"],
                "title": title,
                "creator_id": meta["creatorId"],
                "category": meta.get("category", "interview"),
                "duration": round(sys_meta.get("duration", 0)),
                "thumbnail_url": (hls.get("thumbnail_urls") or [""])[0],
                "hls_url": hls.get("video_url", ""),
                "upload_date": meta.get("uploadDate", ""),
            }
        )

    if video_rows:
        # Smaller batches keep TL Analyze + retrieve calls easy to retry on failure.
        batch_size = 3
        total_inserted, total_errors = 0, 0
        for i in range(0, len(video_rows), batch_size):
            batch = video_rows[i : i + batch_size]
            logger.info(
                "  Inserting videos %d–%d of %d...",
                i + 1,
                min(i + batch_size, len(video_rows)),
                len(video_rows),
            )
            status = videos.insert(batch, on_error="ignore")
            total_inserted += status.num_rows
            total_errors += status.num_excs
        logger.info(
            "  Videos: %d inserted, %d errors", total_inserted, total_errors
        )

    # -- Populate scenes table from videos.tl_segments -------------------------
    # tl_segments was just filled by the computed column. Read it back and
    # explode each segment list into scene rows.

    logger.info("  Populating scenes table from tl_segments ...")
    inserted_videos = list(
        videos.select(videos.id, videos.tl_segments).collect()
    )
    total_scenes = 0
    failed_videos = 0
    for vrow in inserted_videos:
        vid = vrow["id"]
        segs = vrow.get("tl_segments") or []
        if not segs:
            failed_videos += 1
            continue
        scene_rows = []
        for i, s in enumerate(segs):
            vec = s.get("vec")
            if not vec or len(vec) != EMBEDDING_DIM:
                continue
            scene_rows.append(
                {
                    "video_id": vid,
                    "segment_idx": i,
                    "start_sec": s.get("start_sec"),
                    "end_sec": s.get("end_sec"),
                    "visual_embedding": np.asarray(vec, dtype=np.float32),
                }
            )
        if scene_rows:
            scenes.insert(scene_rows, on_error="ignore")
            total_scenes += len(scene_rows)

    logger.info(
        "  scenes: %d rows inserted across %d videos (%d videos had no segments)",
        total_scenes,
        len(inserted_videos) - failed_videos,
        failed_videos,
    )
    logger.info("\nSetup complete.")


def _fetch_tl_videos() -> list[dict]:
    result: list[dict] = []
    page = 1
    while True:
        resp = httpx.get(
            f"{config.TWELVELABS_BASE_URL}/indexes/{config.TWELVELABS_INDEX_ID}/videos",
            params={"page": page, "page_limit": 50},
            headers={"x-api-key": config.TWELVELABS_API_KEY},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        result.extend(data.get("data", []))
        if page >= data.get("page_info", {}).get("total_page", 1):
            break
        page += 1
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Load all 25 videos")
    args = parser.parse_args()
    setup(full=args.full)
