import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("INTERVALS_ICU_AUTH_PASSWORD", "test-password")
os.environ.setdefault("INTERVALS_ICU_ATHLETE_ID", "test-athlete")

import main


class MainTest(unittest.TestCase):
    def test_sync_today_activities_relabels_each_activity(self):
        client = Mock()
        client.get_activities.return_value = [
            {"id": "activity-1", "type": "Ride"},
            {"id": "activity-2", "type": "Ride"},
            {"id": "activity-3", "type": "Run"},
            {"id": None},
        ]

        with patch.object(main, "relabel_activity_segments") as relabel:
            main.sync_today_activities(client, today="2026-06-03")

        client.get_activities.assert_called_once_with(
            oldest="2026-06-03", newest="2026-06-03"
        )
        relabel.assert_any_call(client, "activity-1")
        relabel.assert_any_call(client, "activity-2")
        self.assertEqual(2, relabel.call_count)

    def test_relabel_activity_segments_skips_when_all_segments_are_already_labeled(self):
        client = Mock()
        client.get_activity_detail.return_value = {
            "type": "Ride",
            "name": "测试骑行",
            "icu_intervals": [
                {"label": "赛段 A"},
                {"label": "赛段 B"},
            ],
        }
        client.get_segments.return_value = [
            {"name": "赛段 A"},
            {"name": "赛段 B"},
        ]

        main.relabel_activity_segments(client, "activity-1")

        client.get_activity_detail.assert_called_once_with("activity-1")
        client.get_segments.assert_called_once_with("activity-1")
        client.clear_intervals.assert_not_called()
        client.mark_interval.assert_not_called()


if __name__ == "__main__":
    unittest.main()
