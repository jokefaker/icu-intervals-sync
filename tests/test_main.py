import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

os.environ.setdefault("INTERVALS_ICU_AUTH_PASSWORD", "test-password")
os.environ.setdefault("INTERVALS_ICU_ATHLETE_ID", "test-athlete")
os.environ.setdefault("INTERVALS_ICU_ACCOUNTS", "")

import main


class MainTest(unittest.TestCase):
    @staticmethod
    def account(athlete_id, passkey, athlete_ids=(), discover_athletes=False):
        return SimpleNamespace(
            athlete_id=athlete_id,
            passkey=passkey,
            athlete_ids=athlete_ids,
            discover_athletes=discover_athletes,
        )

    def test_get_target_athlete_ids_defaults_to_current_athlete(self):
        client = Mock()

        with patch.object(main, "ATHLETE_ID", "coach"), patch.object(
            main, "ATHLETE_IDS", ()
        ), patch.object(main, "DISCOVER_ATHLETES", False):
            athlete_ids = main.get_target_athlete_ids(client)

        self.assertEqual(["coach"], athlete_ids)
        client.get_athletes.assert_not_called()

    def test_get_target_athlete_ids_prefers_explicit_allowlist(self):
        client = Mock()

        with patch.object(main, "ATHLETE_IDS", ("athlete-1", "athlete-2")), patch.object(
            main, "DISCOVER_ATHLETES", True
        ):
            athlete_ids = main.get_target_athlete_ids(client)

        self.assertEqual(["athlete-1", "athlete-2"], athlete_ids)
        client.get_athletes.assert_not_called()

    def test_get_target_athlete_ids_discovers_athletes_and_includes_coach(self):
        client = Mock()
        client.get_athletes.return_value = [
            {"id": "123"},
            {"athlete_id": "i456"},
            {"id": "i456"},
            {"id": None},
        ]

        with patch.object(main, "ATHLETE_ID", "i123"), patch.object(
            main, "ATHLETE_IDS", ()
        ), patch.object(main, "DISCOVER_ATHLETES", True):
            athlete_ids = main.get_target_athlete_ids(client)

        self.assertEqual(["i123", "i456"], athlete_ids)

    def test_get_target_athlete_ids_includes_coach_when_endpoint_omits_it(self):
        client = Mock()
        client.get_athletes.return_value = [{"id": "i456"}]

        with patch.object(main, "ATHLETE_ID", "i123"), patch.object(
            main, "ATHLETE_IDS", ()
        ), patch.object(main, "DISCOVER_ATHLETES", True):
            athlete_ids = main.get_target_athlete_ids(client)

        self.assertEqual(["i123", "i456"], athlete_ids)

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

    def test_relabel_activity_segments_skips_when_any_interval_is_labeled(self):
        client = Mock()
        client.get_activity_detail.return_value = {
            "type": "Ride",
            "name": "测试骑行",
            "icu_intervals": [
                {"label": "赛段 A"},
                {"label": None},
            ],
        }
        client.get_segments.return_value = [
            {"name": "赛段 A"},
            {"name": "赛段 B"},
        ]

        main.relabel_activity_segments(client, "activity-1")

        client.get_activity_detail.assert_called_once_with("activity-1")
        client.get_segments.assert_called_once_with("activity-1")
        client.update_activity_fields.assert_called_once()
        client.clear_intervals.assert_not_called()
        client.mark_interval.assert_not_called()

    def test_relabel_activity_segments_marks_only_selected_segments(self):
        client = Mock()
        client.get_activity_detail.return_value = {
            "type": "Ride",
            "icu_intervals": [],
        }
        regular = {
            "name": "普通短赛段",
            "start_index": 20,
            "end_index": 40,
            "starred": False,
        }
        starred = {
            "name": "收藏赛段",
            "start_index": 10,
            "end_index": 50,
            "starred": True,
        }
        client.get_segments.return_value = [regular, starred]

        main.relabel_activity_segments(client, "activity-1")

        client.clear_intervals.assert_called_once_with("activity-1")
        client.mark_interval.assert_called_once_with("activity-1", starred)

    def test_relabel_activity_segments_preserves_intervals_when_all_segments_invalid(self):
        client = Mock()
        client.get_activity_detail.return_value = {
            "type": "Ride",
            "icu_intervals": [],
        }
        client.get_segments.return_value = [
            {"name": "缺少索引"},
            {"name": "索引倒置", "start_index": 20, "end_index": 10},
        ]

        main.relabel_activity_segments(client, "activity-1")

        client.clear_intervals.assert_not_called()
        client.mark_interval.assert_not_called()

    def test_main_syncs_each_target_athlete(self):
        root_client = Mock()
        athlete_clients = [Mock(), Mock()]
        root_client.for_athlete.side_effect = athlete_clients

        with patch.object(main, "ICUClient", return_value=root_client), patch.object(
            main, "get_target_athlete_ids", return_value=["athlete-1", "athlete-2"]
        ), patch.object(main, "ensure_assets_once") as ensure, patch.object(
            main, "sync_today_activities"
        ) as sync:
            main.main()

        root_client.for_athlete.assert_any_call("athlete-1")
        root_client.for_athlete.assert_any_call("athlete-2")
        self.assertEqual(2, root_client.for_athlete.call_count)
        self.assertEqual(
            [((athlete_clients[0],), {}), ((athlete_clients[1],), {})],
            ensure.call_args_list,
        )
        self.assertEqual(
            [((athlete_clients[0],), {}), ((athlete_clients[1],), {})],
            sync.call_args_list,
        )

    def test_main_continues_when_one_athlete_fails(self):
        root_client = Mock()
        athlete_clients = [Mock(), Mock()]
        root_client.for_athlete.side_effect = athlete_clients

        with patch.object(main, "ICUClient", return_value=root_client), patch.object(
            main, "get_target_athlete_ids", return_value=["athlete-1", "athlete-2"]
        ), patch.object(main, "ensure_assets_once"), patch.object(
            main,
            "sync_today_activities",
            side_effect=[RuntimeError("bad athlete data"), None],
        ) as sync, patch.object(main.logger, "exception"):
            main.main()

        self.assertEqual(2, sync.call_count)

    def test_main_uses_separate_passkey_for_each_account(self):
        accounts = (
            self.account(
                "coach", "coach-key", athlete_ids=("coach", "student")
            ),
            self.account("unrelated", "unrelated-key"),
        )
        coach_root = Mock()
        unrelated_root = Mock()
        athlete_clients = [Mock(), Mock(), Mock()]
        coach_root.for_athlete.side_effect = athlete_clients[:2]
        unrelated_root.for_athlete.return_value = athlete_clients[2]

        with patch.object(main, "SYNC_ACCOUNTS", accounts), patch.object(
            main, "ICUClient", side_effect=[coach_root, unrelated_root]
        ) as client_class, patch.object(
            main, "ensure_assets_once"
        ) as ensure, patch.object(
            main, "sync_today_activities"
        ) as sync:
            main.main()

        self.assertEqual(
            [
                call(
                    athlete_id="coach",
                    auth_username="API_KEY",
                    auth_password="coach-key",
                ),
                call(
                    athlete_id="unrelated",
                    auth_username="API_KEY",
                    auth_password="unrelated-key",
                ),
            ],
            client_class.call_args_list,
        )
        self.assertEqual(3, ensure.call_count)
        self.assertEqual(3, sync.call_count)

    def test_main_continues_when_one_account_cannot_list_athletes(self):
        accounts = (
            self.account("bad", "bad-key", discover_athletes=True),
            self.account("working", "working-key"),
        )
        bad_root = Mock()
        bad_root.get_athletes.side_effect = RuntimeError("unauthorized")
        working_root = Mock()
        working_client = Mock()
        working_root.for_athlete.return_value = working_client

        with patch.object(main, "SYNC_ACCOUNTS", accounts), patch.object(
            main, "ICUClient", side_effect=[bad_root, working_root]
        ), patch.object(main.logger, "error") as error, patch.object(
            main, "ensure_assets_once"
        ) as ensure, patch.object(main, "sync_today_activities") as sync:
            main.main()

        error.assert_called_once()
        bad_root.for_athlete.assert_not_called()
        working_root.for_athlete.assert_called_once_with("working")
        ensure.assert_called_once_with(working_client)
        sync.assert_called_once_with(working_client)

    def test_ensure_assets_once_caches_success_per_athlete(self):
        client = Mock()
        client.athlete_id = "i123"
        main._initialized_asset_athletes.clear()

        with patch.object(main, "ensure_assets", return_value={
            "field_created": True,
            "chart_created": True,
            "chart_updated": False,
            "chart_enabled": True,
        }) as ensure:
            main.ensure_assets_once(client)
            main.ensure_assets_once(client)

        ensure.assert_called_once_with(client)

    def test_sync_strava_segments_data_skips_unchanged_value(self):
        client = Mock()
        detail = {"strava_id": "123"}
        segments = [
            {
                "id": 11,
                "segment_id": 22,
                "name": "赛段",
                "start_index": 1,
                "end_index": 2,
                "starred": False,
            }
        ]
        value = main.build_segments_json(detail, segments)
        detail[main.FIELD_CODE] = value

        changed = main.sync_strava_segments_data(
            client, "activity-1", detail, segments
        )

        self.assertFalse(changed)
        client.update_activity_fields.assert_not_called()

    def test_sync_strava_segments_data_updates_changed_value(self):
        client = Mock()
        detail = {"strava_id": "123"}
        segments = []

        changed = main.sync_strava_segments_data(
            client, "activity-1", detail, segments
        )

        self.assertTrue(changed)
        client.update_activity_fields.assert_called_once_with(
            "activity-1",
            {main.FIELD_CODE: '{"v":1,"aid":"123","segments":[]}'},
        )

    def test_has_labeled_intervals(self):
        # 出现任意带 label 的分段 -> 判定为用户已操作
        self.assertTrue(
            main.has_labeled_intervals({"icu_intervals": [{"label": "赛段 A"}]})
        )
        # label 为 null / 空白 / 缺失 -> 不算
        self.assertFalse(
            main.has_labeled_intervals(
                {"icu_intervals": [{"label": None}, {"label": "  "}, {}]}
            )
        )
        # 没有 icu_intervals 字段 -> 不算
        self.assertFalse(main.has_labeled_intervals({}))


if __name__ == "__main__":
    unittest.main()
