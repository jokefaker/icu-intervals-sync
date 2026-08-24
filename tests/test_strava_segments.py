import json
import unittest
from unittest.mock import Mock, call

from strava_segments import (
    CHART_NAME,
    FIELD_CODE,
    build_segments_json,
    chart_definition,
    ensure_assets,
    field_definition,
)


class StravaSegmentsTest(unittest.TestCase):
    def test_build_segments_json_serializes_valid_segments_compactly(self):
        activity = {"strava_id": "123456"}
        segments = [
            {
                "id": 9001,
                "segment_id": 101,
                "name": " 收藏赛段 ",
                "start_index": 10,
                "end_index": 20,
                "starred": True,
            },
            {
                "id": 9002,
                "segment_id": 102,
                "name": "普通赛段",
                "start_index": 30,
                "end_index": 50,
                "starred": False,
            },
            {"name": "缺少索引"},
        ]

        value = build_segments_json(activity, segments)

        self.assertEqual(
            {
                "v": 1,
                "aid": "123456",
                "segments": [
                    {
                        "n": "收藏赛段",
                        "s": "101",
                        "e": "9001",
                        "a": 10,
                        "b": 20,
                        "f": True,
                    },
                    {
                        "n": "普通赛段",
                        "s": "102",
                        "e": "9002",
                        "a": 30,
                        "b": 50,
                        "f": False,
                    },
                ],
            },
            json.loads(value),
        )
        self.assertNotIn(" ", value)

    def test_ensure_assets_creates_only_missing_items_and_enables_chart(self):
        client = Mock()
        client.get_custom_items.return_value = []
        client.create_custom_item.side_effect = [{"id": 10}, {"id": 20}]
        client.get_sport_settings.return_value = {
            "id": 30,
            "activity_charts": {"home": [], "power": None},
        }

        result = ensure_assets(client)

        self.assertEqual(
            [call(field_definition()), call(chart_definition())],
            client.create_custom_item.call_args_list,
        )
        client.update_sport_settings.assert_called_once_with(
            30,
            {
                "activity_charts": {
                    "home": [{"id": "20", "width": None, "height": None}],
                    "power": None,
                }
            },
        )
        self.assertEqual(
            {
                "field_created": True,
                "chart_created": True,
                "chart_updated": False,
                "chart_enabled": True,
                "chart_id": 20,
            },
            result,
        )

    def test_ensure_assets_reuses_existing_items_without_duplicate_enable(self):
        client = Mock()
        client.get_custom_items.return_value = [
            {
                "id": 10,
                "type": "ACTIVITY_FIELD",
                "content": {"code": FIELD_CODE},
            },
            {"id": 20, **chart_definition()},
        ]
        client.get_sport_settings.return_value = {
            "id": 30,
            "activity_charts": {
                "home": [{"id": "20", "width": None, "height": None}]
            },
        }

        result = ensure_assets(client)

        client.create_custom_item.assert_not_called()
        client.update_custom_item.assert_not_called()
        client.update_sport_settings.assert_not_called()
        self.assertFalse(result["field_created"])
        self.assertFalse(result["chart_created"])
        self.assertFalse(result["chart_updated"])
        self.assertFalse(result["chart_enabled"])

    def test_ensure_assets_accepts_bare_chart_id_in_home_list(self):
        client = Mock()
        client.get_custom_items.return_value = [
            {
                "id": 10,
                "type": "ACTIVITY_FIELD",
                "content": {"code": FIELD_CODE},
            },
            {"id": 20, **chart_definition()},
        ]
        client.get_sport_settings.return_value = {
            "id": 30,
            "activity_charts": {"home": ["20"]},
        }

        result = ensure_assets(client)

        self.assertFalse(result["chart_enabled"])
        client.update_sport_settings.assert_not_called()

    def test_ensure_assets_updates_stale_chart_script(self):
        stale_chart = chart_definition()
        stale_chart["id"] = 20
        stale_chart["content"] = dict(stale_chart["content"])
        stale_chart["content"]["script"] = "chart = null"
        client = Mock()
        client.get_custom_items.return_value = [
            {
                "id": 10,
                "type": "ACTIVITY_FIELD",
                "content": {"code": FIELD_CODE},
            },
            stale_chart,
        ]
        client.get_sport_settings.return_value = {
            "id": 30,
            "activity_charts": {"home": ["20"]},
        }
        client.update_custom_item.return_value = {"id": 20}

        result = ensure_assets(client)

        client.update_custom_item.assert_called_once_with(20, chart_definition())
        self.assertTrue(result["chart_updated"])
        self.assertFalse(result["chart_created"])

    def test_chart_definition_contains_current_grid_features(self):
        definition = chart_definition()
        script = definition["content"]["script"]

        self.assertEqual("ACTIVITY_CHART", definition["type"])
        self.assertIn("StravaSegmentsJson", script)
        self.assertIn('"历时"', script)
        self.assertIn("`${hourText}${minuteText}${seconds}s`", script)
        self.assertIn("https://www.strava.com/segments/", script)
        self.assertIn("chart = rows.length ? {", script)
        self.assertIn('type: "heatmap"', script)
        self.assertEqual(2, script.count('type: "scatter"'))
        self.assertIn("icu.streams.watts", script)
        self.assertNotIn("icu.streams.get", script)
        self.assertNotIn("values.slice", script)
        self.assertNotIn("watts.slice", script)
        self.assertNotIn("rows.filter", script)
        self.assertNotIn('type: "table"', script)
        self.assertNotIn("annotations:", script)
        self.assertNotIn("shapes:", script)
        self.assertTrue(script.rstrip().endswith("} : null\n}"))


if __name__ == "__main__":
    unittest.main()
