"""Class schema for the existing (migrated 0.6.x) database, with Marengo 3.5 indexes.

This is app_existing.py with one change: the two named embedding indexes,
title_marengo and scene_marengo, use Marengo 3.5 instead of Marengo 3.0.
Everything else is the same, so applying it keeps every row, the Analyze tags,
the scene cuts, and the scene clips. Only the two indexes are rebuilt.

Apply it with upgrade_existing_marengo35.py, after migrate_existing.py. Once a
database is on Marengo 3.5, use this file, not app_existing.py, for later schema
updates on it. app_existing.py would rebuild the indexes with Marengo 3.0 again.
"""

from __future__ import annotations

import pixeltable as pxt
import pixeltable.functions as pxtf

from functions import analyze_video

# embed() is the synchronous call, used for text and image queries and for titles.
# async_embed_asset() runs an async embedding task and returns one fused vector for a
# whole clip of any length. Scene clips average about 88 seconds, over the 30 second
# limit of the synchronous call.
marengo = pxtf.twelvelabs.embed.using(model_name="marengo3.5")
marengo_async = pxtf.twelvelabs.async_embed_asset.using(model_name="marengo3.5")
TableModel = pxt.model_base()


class Creators(TableModel, name="creators", has_default_idxs=True):
    id = pxt.Column(type=pxt.String, primary_key=True)
    name: pxt.String | None
    avatar_url: pxt.String | None
    description: pxt.String | None


class Videos(TableModel, name="videos", has_default_idxs=True):
    id = pxt.Column(type=pxt.String, primary_key=True)
    title: pxt.String | None
    creator_id: pxt.String | None
    category: pxt.String | None
    duration: pxt.Int | None
    thumbnail_url: pxt.String | None
    hls_url: pxt.String | None
    upload_date: pxt.String | None
    video: pxt.Video | None
    raw_attributes = analyze_video(id).astype(pxt.Json)
    topic = raw_attributes.topic
    style = raw_attributes.style
    tone = raw_attributes.tone
    scenes = video.scene_detect_histogram(
        fps=1, threshold=0.9, min_scene_len=900
    ).astype(pxt.Json[(pxt.Json, ...)] | None)
    __indexes__ = [pxt.EmbeddingIndex(title, string_embed=marengo, name="title_marengo")]


class VideoScenes(
    TableModel,
    name="video_scenes",
    base=Videos,
    has_default_idxs=True,
    iterator=pxtf.video.video_splitter(
        video=Videos.video, segment_times=Videos.scenes[1:].start_time, mode="fast"
    ),
):
    __indexes__ = [
        pxt.EmbeddingIndex(
            video_segment,  # type: ignore[name-defined]
            video_embed=marengo_async,
            audio_embed=marengo_async,
            string_embed=marengo,
            image_embed=marengo,
            name="scene_marengo",
        )
    ]
