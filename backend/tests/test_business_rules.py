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
