"""PixelTable schema definition.

Run once to initialize the database schema:
    python setup_pixeltable.py

Idempotent — safe to re-run without losing data. The video segment
view and its embedding index are created automatically when video
files have been ingested.
"""
import logging

import pixeltable as pxt
from pixeltable.functions.twelvelabs import embed
from pixeltable.functions.video import video_splitter

import config
from functions import analyze_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

marengo = embed.using(model_name="marengo3.0")


def setup():
    logger.info("Initializing PixelTable schema under '%s'...", config.APP_NAMESPACE)
    pxt.create_dir(config.APP_NAMESPACE, if_exists="ignore")

    # -- Creators table -------------------------------------------------------

    pxt.create_table(
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
    logger.info("  creators table ready")

    # -- Videos table ---------------------------------------------------------

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
    logger.info("  videos table ready")

    # -- Marengo 3.0 embedding index on title ---------------------------------

    videos.add_embedding_index(
        "title", string_embed=marengo, idx_name="title_marengo", if_exists="ignore",
    )
    logger.info("  Marengo 3.0 embedding index on title ready")

    # -- Analyze API computed columns (topic, style, tone) --------------------

    videos.add_computed_column(raw_attributes=analyze_video(videos.id), if_exists="ignore")
    videos.add_computed_column(topic=videos.raw_attributes["topic"], if_exists="ignore")
    videos.add_computed_column(style=videos.raw_attributes["style"], if_exists="ignore")
    videos.add_computed_column(tone=videos.raw_attributes["tone"], if_exists="ignore")
    logger.info("  Analyze API computed columns (topic, style, tone) ready")

    # -- Video segment view + Marengo video embedding index -------------------
    #    Created when at least one video has a file path set. Re-run setup
    #    after ingesting with --with-videos to enable.

    view_name = f"{config.APP_NAMESPACE}.video_segments"
    has_video_files = False
    try:
        has_video_files = videos.where(videos.video != None).count() > 0
    except Exception:
        pass

    if has_video_files:
        try:
            pxt.get_table(view_name)
            logger.info("  video_segments view already exists")
        except Exception:
            logger.info("  Creating video_segments view (30s segments)...")
            pxt.create_view(
                view_name,
                videos.where(videos.video != None),
                iterator=video_splitter(videos.video, duration=30),
                if_exists="ignore",
            )
            logger.info("  video_segments view created")

        segments = pxt.get_table(view_name)
        segments.add_embedding_index(
            "video_segment", embedding=marengo, idx_name="segment_marengo", if_exists="ignore",
        )
        logger.info("  Marengo 3.0 video embedding index on segments ready")
    else:
        logger.info("  Skipping video_segments (no video files — run download_videos.py + ingest --with-videos)")

    logger.info("\nSchema setup complete.")


if __name__ == "__main__":
    setup()
