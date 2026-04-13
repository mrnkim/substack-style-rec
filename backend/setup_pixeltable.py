"""Pixeltable schema + data setup.

Creates tables, indexes, computed columns, and loads video data from
the Twelve Labs index. Run once — everything is idempotent.

By default loads 3 quick-start videos (fast).
Pass --full to load all 25 videos.

Scene detection (scene_detect_histogram) finds natural scene boundaries,
then video_splitter splits at those points with mode='fast' (stream copy,
no re-encoding). This produces ~10 scenes per video in seconds.

Usage:
    uv run download_videos.py          # download 3 videos
    uv run setup_pixeltable.py         # insert 3 videos + detect scenes + embed

    uv run download_videos.py --full   # download all 25 videos (13GB)
    uv run setup_pixeltable.py --full  # insert all 25 + detect scenes + embed
"""

import argparse
import logging
import re
from pathlib import Path

import httpx
import pixeltable as pxt
from pixeltable.functions.twelvelabs import embed
from pixeltable.functions.video import video_splitter

import config
from functions import analyze_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUICK_YOUTUBE_IDS = {"sO4te2QNsHY", "ntPGl8UyIq4", "QpKypvDjiPM"}

marengo = embed.using(model_name="marengo3.0")

VIDEO_FILES_DIR = Path(__file__).resolve().parent / "video_files"


def strip_extension(filename: str) -> str:
    return re.sub(r"\.(mp4|webm|mkv|mov)$", "", filename, flags=re.IGNORECASE).strip()


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
            "video": pxt.Video,
        },
        primary_key=["id"],
        if_exists="ignore",
    )

    # Text-based embedding index on title (for text → video search)
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

    # Videos — resolve local video file paths via YouTube ID
    video_rows = []
    missing_files = []
    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        sys_meta = tlv.get("system_metadata", {})
        hls = tlv.get("hls") or {}
        if not meta.get("creatorId") or not meta.get("creatorName"):
            continue

        youtube_id = meta.get("youtubeId", "")
        video_path = _resolve_video_path(youtube_id)
        if not video_path:
            missing_files.append(youtube_id or tlv["_id"])

        video_rows.append(
            {
                "id": tlv["_id"],
                "title": strip_extension(sys_meta.get("filename", "")),
                "creator_id": meta["creatorId"],
                "category": meta.get("category", "interview"),
                "duration": round(sys_meta.get("duration", 0)),
                "thumbnail_url": (hls.get("thumbnail_urls") or [""])[0],
                "hls_url": hls.get("video_url", ""),
                "upload_date": meta.get("uploadDate", ""),
                "video": video_path,
            }
        )

    if missing_files:
        logger.warning(
            "  %d videos missing local files — run 'uv run download_videos.py' first. "
            "IDs: %s",
            len(missing_files),
            ", ".join(missing_files[:5]),
        )

    if video_rows:
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

    # -- Scene detection + scene-based view (for cross-modal search) -----------
    # Uses Pixeltable's built-in scene_detect_histogram to find natural scene
    # boundaries, then video_splitter with mode='fast' (stream copy, no
    # re-encoding) to split at those points. ~10 scenes per video in seconds.

    videos.add_computed_column(
        scenes=videos.video.scene_detect_histogram(
            fps=10, threshold=0.6, min_scene_len=100,
        ),
        if_exists="ignore",
    )
    logger.info("  Scene detection column ready")

    try:
        logger.info("  Creating video_scenes view...")
        video_scenes = pxt.create_view(
            f"{config.APP_NAMESPACE}.video_scenes",
            videos,
            iterator=video_splitter(
                video=videos.video,
                segment_times=videos.scenes[1:].start_time,
                mode="fast",
            ),
            if_exists="ignore",
        )

        video_scenes.add_embedding_index(
            "video_segment",
            embedding=marengo,
            idx_name="scene_marengo",
            if_exists="ignore",
        )
        scene_count = video_scenes.count()
        logger.info("  video_scenes: %d scenes indexed", scene_count)
    except Exception as exc:
        logger.warning(
            "  video_scenes creation failed: %s\n"
            "  The app will use title-based similarity as fallback.\n"
            "  Re-run setup to retry.",
            exc,
        )

    logger.info("\nSetup complete.")


def _resolve_video_path(youtube_id: str) -> str | None:
    """Find the local .mp4 file for a given YouTube video ID."""
    if not youtube_id:
        return None
    path = VIDEO_FILES_DIR / f"{youtube_id}.mp4"
    if path.exists() and path.stat().st_size > 0:
        return str(path)
    return None


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
