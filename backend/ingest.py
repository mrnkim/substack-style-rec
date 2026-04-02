"""Ingest video and creator data from Twelve Labs index into PixelTable.

Fetches all videos from the TL index, extracts user_metadata, and inserts
into the creators and videos tables. The embedding index and Analyze API
computed columns trigger automatically on insert.

If video files exist in data/videos/ (from download_videos.py), they are
included in the insert so segment embeddings can be generated.

Usage:
    python ingest.py                # metadata only (fast)
    python ingest.py --with-videos  # include video file paths for segment embeddings
"""
import argparse
import csv
import re
import logging
from pathlib import Path

import httpx
import pixeltable as pxt

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = config.TWELVELABS_BASE_URL
INDEX_ID = config.TWELVELABS_INDEX_ID
HEADERS = {"x-api-key": config.TWELVELABS_API_KEY}
VIDEOS_DIR = Path(__file__).resolve().parent / "data" / "videos"
CSV_PATH = Path(__file__).resolve().parent.parent / "scripts" / "videos_metadata.csv"


def strip_extension(filename: str) -> str:
    return re.sub(r"\.(mp4|webm|mkv|mov)$", "", filename, flags=re.IGNORECASE).strip()


def fetch_all_tl_videos() -> list[dict]:
    """Paginate through TL index and return raw video dicts."""
    videos: list[dict] = []
    page = 1
    while True:
        resp = httpx.get(
            f"{BASE_URL}/indexes/{INDEX_ID}/videos",
            params={"page": page, "page_limit": 50},
            headers=HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        videos.extend(data.get("data", []))
        page_info = data.get("page_info", {})
        if page >= page_info.get("total_page", 1):
            break
        page += 1
    return videos


def build_video_file_map() -> dict[str, str]:
    """Build a YouTube ID -> local file path mapping from CSV + disk."""
    if not CSV_PATH.exists():
        return {}
    result: dict[str, str] = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yt_id = row.get("video_id", "").strip()
            if yt_id:
                fp = VIDEOS_DIR / f"{yt_id}.mp4"
                if fp.exists():
                    result[yt_id] = str(fp)
    return result


def run(with_videos: bool = False):
    logger.info("Fetching videos from Twelve Labs index %s ...", INDEX_ID)
    tl_videos = fetch_all_tl_videos()
    logger.info("Found %d videos in TL index", len(tl_videos))

    creators_t = pxt.get_table(f"{config.APP_NAMESPACE}.creators")
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    # -- Build video file mapping (YouTube ID -> local path) -------------------
    yt_file_map: dict[str, str] = {}
    if with_videos:
        yt_file_map = build_video_file_map()
        logger.info("Found %d video files on disk", len(yt_file_map))

    # -- Insert creators -------------------------------------------------------
    seen_creators: set[str] = set()
    creator_rows: list[dict] = []

    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        cid = meta.get("creatorId")
        cname = meta.get("creatorName")
        if not cid or not cname or cid in seen_creators:
            continue
        seen_creators.add(cid)
        creator_rows.append({
            "id": cid,
            "name": cname,
            "avatar_url": "",
            "description": config.CREATOR_DESCRIPTIONS.get(cid, ""),
        })

    if creator_rows:
        logger.info("Inserting %d creators ...", len(creator_rows))
        status = creators_t.insert(creator_rows, on_error="ignore")
        logger.info("Creators: inserted=%d, errors=%d", status.num_rows, status.num_excs)

    # -- Insert videos ---------------------------------------------------------
    video_rows: list[dict] = []

    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        sys_meta = tlv.get("system_metadata", {})
        hls = tlv.get("hls") or {}
        cid = meta.get("creatorId")
        cname = meta.get("creatorName")
        if not cid or not cname:
            logger.warning("Skipping video %s — missing creator metadata", tlv.get("_id"))
            continue

        row = {
            "id": tlv["_id"],
            "title": strip_extension(sys_meta.get("filename", "")),
            "creator_id": cid,
            "category": meta.get("category", "interview"),
            "duration": round(sys_meta.get("duration", 0)),
            "thumbnail_url": (hls.get("thumbnail_urls") or [""])[0],
            "hls_url": hls.get("video_url", ""),
            "upload_date": meta.get("uploadDate", ""),
        }

        # Attach video file path if available
        yt_id = meta.get("youtubeId")
        if with_videos and yt_id and yt_id in yt_file_map:
            row["video"] = yt_file_map[yt_id]

        video_rows.append(row)

    if video_rows:
        videos_with_files = sum(1 for r in video_rows if "video" in r)
        logger.info(
            "Inserting %d videos (%d with video files)...",
            len(video_rows), videos_with_files,
        )
        status = videos_t.insert(video_rows, on_error="ignore")
        logger.info("Videos: inserted=%d, errors=%d", status.num_rows, status.num_excs)

    # -- Backfill video paths for existing rows (if re-running with --with-videos)
    if with_videos and yt_file_map:
        existing_rows = list(videos_t.select(videos_t.id).collect())
        tl_to_yt = {tlv["_id"]: (tlv.get("user_metadata") or {}).get("youtubeId") for tlv in tl_videos}
        backfilled = 0
        for row in existing_rows:
            yt_id = tl_to_yt.get(row["id"])
            if yt_id and yt_id in yt_file_map:
                videos_t.update({"video": yt_file_map[yt_id]}, where=(videos_t.id == row["id"]))
                backfilled += 1
        if backfilled:
            logger.info("Backfilled video paths for %d existing rows", backfilled)

    logger.info("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest data from Twelve Labs index")
    parser.add_argument(
        "--with-videos", action="store_true",
        help="Include local video file paths for segment embeddings (run download_videos.py first)",
    )
    args = parser.parse_args()
    run(with_videos=args.with_videos)
