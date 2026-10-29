"""Pixeltable schema for Substack TV-style video recommendations.

Hierarchy:
    creators (table)       creator profiles
    videos (table)         source videos + Twelve Labs Analyze attributes
    -> video_scenes (view) one row per scene (video_splitter), Marengo embeddings for semantic search

Create or update the schema with:
    pxt init
    pxt schema update app.py substack_rec
"""

from __future__ import annotations

import pixeltable as pxt
import pixeltable.functions as pxtf

from functions import analyze_video, embed_video_retry

marengo = pxtf.twelvelabs.embed.using(model_name="marengo3.0")
TableModel = pxt.model_base()


class Creators(TableModel, name="creators"):
    id = pxt.Column(type=pxt.String, primary_key=True)
    name: pxt.String | None
    avatar_url: pxt.String | None
    description: pxt.String | None


class Videos(TableModel, name="videos"):
    id = pxt.Column(type=pxt.String, primary_key=True)
    title: pxt.String | None
    creator_id: pxt.String | None
    category: pxt.String | None
    duration: pxt.Int | None
    thumbnail_url: pxt.String | None
    hls_url: pxt.String | None
    upload_date: pxt.String | None
    video: pxt.Video | None
    raw_attributes = analyze_video(id)
    topic = raw_attributes.topic
    style = raw_attributes.style
    tone = raw_attributes.tone
    scenes = video.scene_detect_histogram(fps=1, threshold=0.9, min_scene_len=900)
    __indexes__ = [pxt.EmbeddingIndex(title, string_embed=marengo)]


class VideoScenes(
    TableModel,
    name="video_scenes",
    base=Videos,
    iterator=pxtf.video.video_splitter(
        video=Videos.video, segment_times=Videos.scenes[1:].start_time, mode="fast"
    ),
):
    __indexes__ = [
        pxt.EmbeddingIndex(
            video_segment,
            embedding=embed_video_retry,  # type: ignore[name-defined]
            string_embed=marengo,
            image_embed=marengo,
            audio_embed=marengo,
        )
    ]
