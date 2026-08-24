import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("INTERVALS_ICU_AUTH_PASSWORD", "test-password")
os.environ.setdefault("INTERVALS_ICU_ATHLETE_ID", "test-athlete")
os.environ.setdefault("INTERVALS_ICU_ACCOUNTS", "")

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

    def test_get_custom_items_lists_athlete_items(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = [{"id": 10, "type": "ACTIVITY_FIELD"}]
        client.session.get = Mock(return_value=response)

        items = client.get_custom_items()

        client.session.get.assert_called_once_with(
            "https://intervals.icu/api/v1/athlete/athlete-1/custom-item",
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual([{"id": 10, "type": "ACTIVITY_FIELD"}], items)

    def test_create_custom_item_posts_definition(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = {"id": 10}
        client.session.post = Mock(return_value=response)
        definition = {"name": "Chart", "type": "ACTIVITY_CHART"}

        created = client.create_custom_item(definition)

        client.session.post.assert_called_once_with(
            "https://intervals.icu/api/v1/athlete/athlete-1/custom-item",
            json=definition,
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual({"id": 10}, created)

    def test_update_custom_item_puts_definition(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = {"id": 10}
        client.session.put = Mock(return_value=response)
        definition = {"name": "Chart", "type": "ACTIVITY_CHART"}

        updated = client.update_custom_item(10, definition)

        client.session.put.assert_called_once_with(
            "https://intervals.icu/api/v1/athlete/athlete-1/custom-item/10",
            json=definition,
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual({"id": 10}, updated)

    def test_update_sport_settings_uses_partial_update(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = {"id": 30}
        client.session.put = Mock(return_value=response)
        fields = {"activity_charts": {"home": [{"id": "20"}]}}

        updated = client.update_sport_settings(30, fields)

        client.session.put.assert_called_once_with(
            "https://intervals.icu/api/v1/athlete/athlete-1/sport-settings/30",
            params={"recalcHrZones": "false"},
            json=fields,
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual({"id": 30}, updated)

    def test_update_activity_fields_puts_custom_field_code(self):
        client = ICUClient(athlete_id="athlete-1", auth_username="user", auth_password="pass")
        response = Mock()
        response.json.return_value = {"id": "activity-1"}
        client.session.put = Mock(return_value=response)
        fields = {"StravaSegmentsJson": "{}"}

        updated = client.update_activity_fields("activity-1", fields)

        client.session.put.assert_called_once_with(
            "https://intervals.icu/api/v1/activity/activity-1",
            json=fields,
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual({"id": "activity-1"}, updated)


if __name__ == "__main__":
    unittest.main()
