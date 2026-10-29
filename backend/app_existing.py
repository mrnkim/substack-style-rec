"""Class schema for existing 0.6.x databases; preserve stored types and indexes.

Run migrate_existing.py before reconciling this schema. New installations use
app.py instead. Retain the existing Marengo index to avoid re-embedding media.
"""

from __future__ import annotations

import pixeltable as pxt
import pixeltable.functions as pxtf

from functions import analyze_video

marengo = pxtf.twelvelabs.embed.using(model_name="marengo3.0")
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
        pxt.EmbeddingIndex(video_segment, embedding=marengo, name="scene_marengo")
    ]
