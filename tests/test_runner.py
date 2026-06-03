import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("INTERVALS_ICU_AUTH_PASSWORD", "test-password")
os.environ.setdefault("INTERVALS_ICU_ATHLETE_ID", "test-athlete")

import runner


class RunnerTest(unittest.TestCase):
    def test_sync_interval_seconds_defaults_to_sixty(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(60, runner.get_sync_interval_seconds())

    def test_sync_interval_seconds_reads_environment(self):
        with patch.dict(os.environ, {"SYNC_INTERVAL_SECONDS": "15"}, clear=True):
            self.assertEqual(15, runner.get_sync_interval_seconds())

    def test_sync_interval_seconds_rejects_values_below_one(self):
        with patch.dict(os.environ, {"SYNC_INTERVAL_SECONDS": "0"}, clear=True):
            with self.assertRaises(ValueError):
                runner.get_sync_interval_seconds()

    def test_run_forever_runs_sync_then_sleeps_between_iterations(self):
        sync_once = Mock()
        sleep = Mock(side_effect=KeyboardInterrupt)

        runner.run_forever(interval_seconds=5, sync_once=sync_once, sleep=sleep)

        sync_once.assert_called_once_with()
        sleep.assert_called_once_with(5)

    def test_run_forever_sleeps_after_failed_sync(self):
        sync_once = Mock(side_effect=RuntimeError("boom"))
        sleep = Mock(side_effect=KeyboardInterrupt)

        with patch.object(runner.logger, "exception") as log_exception:
            runner.run_forever(interval_seconds=5, sync_once=sync_once, sleep=sleep)

        sync_once.assert_called_once_with()
        log_exception.assert_called_once_with("Sync run failed")
        sleep.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
