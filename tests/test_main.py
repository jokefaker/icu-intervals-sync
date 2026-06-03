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
            {"id": "activity-1"},
            {"id": "activity-2"},
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


if __name__ == "__main__":
    unittest.main()
