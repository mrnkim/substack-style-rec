import json
import unittest
from collections import Counter
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import functions
import httpx
from models import ForYouRequest
from routers import recommendations
from routers.videos import _build_video_response


def video(video_id: str, creator_id: str, score: float = 0.8) -> dict[str, Any]:
    return {
        "id": video_id,
        "title": video_id,
        "creator_id": creator_id,
        "category": "creative",
        "duration": 60,
        "thumbnail_url": "",
        "hls_url": "",
        "upload_date": "2026-10-01",
        "topic": ["music"],
        "style": "explainer",
        "tone": "analytical",
        "score": score,
    }


class RecommendationRulesTest(unittest.TestCase):
    def recommendations(self, subscription_count: int, discovery_count: int) -> list:
        subscriptions = [f"sub-{i}" for i in range(4)]
        seed = video("seed", "seed-creator")
        candidates = [
            video(f"s-{i}", subscriptions[i // 2], 0.95 - i * 0.01)
            for i in range(subscription_count)
        ] + [
            video(f"d-{i}", f"disc-{i // 2}", 0.85 - i * 0.01)
            for i in range(discovery_count)
        ]
        rows = [seed, *candidates]
        creators = {row["creator_id"]: {"name": row["creator_id"]} for row in rows}
        with (
            patch.object(recommendations.pxt, "get_table", return_value=object()),
            patch.object(recommendations, "_load_creators_map", return_value=creators),
            patch.object(
                recommendations,
                "_select_videos",
                return_value=SimpleNamespace(collect=lambda: rows),
            ),
            patch.object(recommendations, "_attach_attrs"),
            patch.object(
                recommendations, "_similarity_candidates", return_value=candidates
            ) as query,
        ):
            result = recommendations.for_you(
                ForYouRequest(
                    subscriptions=subscriptions,
                    watch_history=["seed"],
                    limit=10,
                )
            )
        self.assertEqual(query.call_args.args[2], {"seed"})
        self.assertEqual(len(result.recommendations), 10)
        self.assertLessEqual(
            max(
                Counter(
                    item.video.creator.id for item in result.recommendations
                ).values()
            ),
            2,
        )
        return result.recommendations

    def test_subscription_discovery_target(self) -> None:
        result = self.recommendations(8, 12)
        self.assertEqual(
            Counter(item.source for item in result), {"subscription": 7, "discovery": 3}
        )

    def test_subscription_shortage_is_filled_from_discovery(self) -> None:
        result = self.recommendations(1, 12)
        self.assertEqual(
            Counter(item.source for item in result), {"subscription": 1, "discovery": 9}
        )


class SceneVectorFallbackTest(unittest.TestCase):
    def query(self, vector_rows, text_rows):
        title_rows = [video("title-result", "creator", 0.7)]
        with (
            patch.object(recommendations, "_get_scenes_table", return_value=object()),
            patch.object(recommendations, "_get_ref_scene_vectors", return_value=[[0.0] * 512]),
            patch.object(recommendations, "_scene_similarity", side_effect=[vector_rows, text_rows]) as scene,
            patch.object(recommendations, "_title_similarity", return_value=title_rows) as title,
        ):
            result = recommendations._similarity_candidates(
                object(), video("seed", "seed-creator"), {"watched"}, 5
            )
        self.assertEqual(scene.call_args_list[0].args[1], {"seed", "watched"})
        self.assertIn("vector", scene.call_args_list[0].kwargs)
        return result, scene, title

    def test_zero_vector_scores_fall_back_to_text(self):
        text_rows = [video("text-result", "creator", 0.8)]
        result, scene, title = self.query([video("zero", "creator", 0.0)], text_rows)
        self.assertEqual(result, text_rows)
        self.assertEqual(scene.call_count, 2)
        self.assertIn("string", scene.call_args.kwargs)
        title.assert_not_called()

    def test_missing_and_negative_vector_scores_fall_back_to_title(self):
        rows = [video("null", "creator") | {"score": None}, video("negative", "creator", -0.1)]
        result, _, title = self.query(rows, [video("zero", "creator", 0.0)])
        self.assertEqual(result[0]["id"], "title-result")
        title.assert_called_once()

    def test_positive_vectors_keep_video_path_and_exclude_zero_scores(self):
        positive = video("positive", "creator", 0.9)
        result, scene, title = self.query([video("zero", "creator", 0.0), positive], [])
        self.assertEqual(result, [positive])
        self.assertEqual(scene.call_count, 1)
        title.assert_not_called()


class AnalyzeAttributesTest(unittest.IsolatedAsyncioTestCase):
    async def test_provider_failure_does_not_invent_attributes(self) -> None:
        with (
            patch.object(
                functions,
                "_lookup_asset_id",
                new=AsyncMock(side_effect=httpx.ReadTimeout("timeout")),
            ),
            self.assertLogs("functions", level="WARNING"),
        ):
            attrs = await functions.analyze_video.py_fn("video")
        self.assertEqual(attrs, {"topic": [], "style": "", "tone": ""})
        row = video("video", "creator") | attrs
        self.assertIsNone(_build_video_response(row, {}).attributes)
        self.assertEqual(recommendations._matched_attrs(row, row), [])

    async def test_only_supported_provider_attributes_are_used(self) -> None:
        async_client = httpx.AsyncClient
        for style, tone, expected in (
            ("explainer", "analytical", ("explainer", "analytical")),
            ("unknown-style", "unknown-tone", ("", "")),
        ):
            with self.subTest(style=style, tone=tone):
                data = json.dumps({"topic": ["music"], "style": style, "tone": tone})
                transport = httpx.MockTransport(
                    lambda _request, data=data: httpx.Response(200, json={"data": data})
                )
                with (
                    patch.object(
                        functions,
                        "_lookup_asset_id",
                        new=AsyncMock(return_value="asset"),
                    ),
                    patch.object(
                        functions.httpx,
                        "AsyncClient",
                        side_effect=lambda transport=transport: async_client(
                            transport=transport
                        ),
                    ),
                ):
                    attrs = await functions.analyze_video.py_fn("video")
                self.assertEqual((attrs["style"], attrs["tone"]), expected)
                self.assertEqual(attrs["topic"], ["music"])
