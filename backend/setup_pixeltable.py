"""Pixeltable schema + data setup.

Creates tables, indexes, computed columns, and loads video data from
the Twelve Labs index. Run once — everything is idempotent.

Usage:
    uv run setup_pixeltable.py
"""

import logging
import re

import httpx
import pixeltable as pxt
from pixeltable.functions.twelvelabs import embed

import config
from functions import analyze_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

marengo = embed.using(model_name="marengo3.0")


def strip_extension(filename: str) -> str:
    return re.sub(r"\.(mp4|webm|mkv|mov)$", "", filename, flags=re.IGNORECASE).strip()


def setup():
    logger.info("Setting up Pixeltable under '%s'...", config.APP_NAMESPACE)
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

    videos.add_embedding_index(
        "title", string_embed=marengo, idx_name="title_marengo", if_exists="ignore"
    )
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
    logger.info("  Found %d videos", len(tl_videos))

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

    # Videos
    video_rows = []
    for tlv in tl_videos:
        meta = tlv.get("user_metadata") or {}
        sys_meta = tlv.get("system_metadata", {})
        hls = tlv.get("hls") or {}
        if not meta.get("creatorId") or not meta.get("creatorName"):
            continue
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
            }
        )
    if video_rows:
        logger.info("  Inserting %d videos...", len(video_rows))
        status = videos.insert(video_rows, on_error="ignore")
        logger.info(
            "  Videos: %d inserted, %d errors", status.num_rows, status.num_excs
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
    setup()
