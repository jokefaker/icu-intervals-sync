import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("INTERVALS_ICU_AUTH_PASSWORD", "test-password")
os.environ.setdefault("INTERVALS_ICU_ATHLETE_ID", "test-athlete")

from icu_client import ICUClient


class ICUClientTest(unittest.TestCase):
    def test_get_athletes_lists_accessible_athletes(self):
        client = ICUClient(athlete_id="coach", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = [{"id": "coach"}, {"id": "athlete-1"}]
        client.session.get = Mock(return_value=response)

        athletes = client.get_athletes()

        client.session.get.assert_called_once_with(
            "https://intervals.icu/api/v1/athletes",
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual([{"id": "coach"}, {"id": "athlete-1"}], athletes)

    def test_for_athlete_reuses_authenticated_session(self):
        client = ICUClient(athlete_id="coach", auth_username="user", auth_password="pass")

        athlete_client = client.for_athlete("athlete-1")

        self.assertEqual("athlete-1", athlete_client.athlete_id)
        self.assertIs(client.session, athlete_client.session)

    def test_get_activity_detail_fetches_activity_by_id(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = {"id": "i152273673", "name": "测试活动"}
        client.session.get = Mock(return_value=response)

        activity = client.get_activity_detail("i152273673")

        client.session.get.assert_called_once_with(
            "https://intervals.icu/api/v1/activity/i152273673?intervals=true",
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual({"id": "i152273673", "name": "测试活动"}, activity)

    def test_get_activities_fetches_activities_for_date_range(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = [{"id": "activity-1"}]
        client.session.get = Mock(return_value=response)

        activities = client.get_activities(oldest="2026-06-03", newest="2026-06-03")

        client.session.get.assert_called_once_with(
            "https://intervals.icu/api/v1/athlete/athlete-1/activities",
            params={"oldest": "2026-06-03", "newest": "2026-06-03"},
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual([{"id": "activity-1"}], activities)


if __name__ == "__main__":
    unittest.main()
