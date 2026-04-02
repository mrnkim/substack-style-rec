"""Schema definition for the Substack Rec PixelTable backend.

Run once to initialize the database schema:
    python setup_pixeltable.py

This is idempotent — safe to re-run without losing data.
The schema includes all phases (video column, segment view, etc.)
and gracefully skips parts that depend on video files being present.
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

    # -- 1. Creators table ---------------------------------------------------

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

    # -- 2. Videos table (includes video column for segment embeddings) ------

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

    # -- 3. Marengo 3.0 text embedding index on title ------------------------

    videos.add_embedding_index("title", string_embed=marengo, if_exists="ignore")
    logger.info("  Marengo 3.0 text embedding index on title ready")

    # -- 4. Analyze API computed columns -------------------------------------

    videos.add_computed_column(
        raw_attributes=analyze_video(videos.id),
        if_exists="ignore",
    )
    videos.add_computed_column(topic=videos.raw_attributes["topic"], if_exists="ignore")
    videos.add_computed_column(style=videos.raw_attributes["style"], if_exists="ignore")
    videos.add_computed_column(tone=videos.raw_attributes["tone"], if_exists="ignore")
    logger.info("  Analyze API computed columns (topic, style, tone) ready")

    # -- 5. Video segment view + Marengo video embedding index ---------------
    #    Only created when at least one video has a file path set.
    #    If no video files exist yet, this section is skipped and can be
    #    triggered later by re-running setup after ingesting with video paths.

    view_name = f"{config.APP_NAMESPACE}.video_segments"
    has_video_files = False
    try:
        count = videos.where(videos.video != None).count()
        has_video_files = count > 0
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
            "video_segment",
            embedding=marengo,
            if_exists="ignore",
        )
        logger.info("  Marengo 3.0 video embedding index on segments ready")
    else:
        logger.info("  Skipping video_segments view (no video files yet)")
        logger.info("  To enable: run download_videos.py, then ingest with --with-videos, then re-run setup")

    logger.info("\nSchema setup complete.")


if __name__ == "__main__":
    setup()
