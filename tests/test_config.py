import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ConfigTest(unittest.TestCase):
    def test_config_reads_secrets_from_environment(self):
        os.environ["INTERVALS_ICU_AUTH_PASSWORD"] = "env-password"
        os.environ["INTERVALS_ICU_ATHLETE_ID"] = "env-athlete"
        os.environ["INTERVALS_ICU_ACCOUNTS"] = ""
        os.environ["APP_TIMEZONE"] = "Asia/Shanghai"

        import config

        config = importlib.reload(config)

        self.assertEqual("API_KEY", config.AUTH_USERNAME)
        self.assertEqual("env-password", config.AUTH_PASSWORD)
        self.assertEqual("env-athlete", config.ATHLETE_ID)
        self.assertEqual("Asia/Shanghai", config.APP_TIMEZONE)

    def test_config_loads_local_env_file_when_environment_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "INTERVALS_ICU_AUTH_PASSWORD=file-password",
                        "INTERVALS_ICU_ATHLETE_ID=file-athlete",
                        "APP_TIMEZONE=Asia/Shanghai",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                import config

                config.ENV_FILE = env_path
                config = importlib.reload(config)

        self.assertEqual("file-password", config.AUTH_PASSWORD)
        self.assertEqual("file-athlete", config.ATHLETE_ID)

    def test_config_parses_multiple_athletes_and_discovery_flag(self):
        with patch.dict(
            os.environ,
            {
                "INTERVALS_ICU_AUTH_PASSWORD": "env-password",
                "INTERVALS_ICU_ATHLETE_ID": "coach",
                "INTERVALS_ICU_ACCOUNTS": "",
                "INTERVALS_ICU_ATHLETE_IDS": " i1, i2, i1 ",
                "INTERVALS_ICU_DISCOVER_ATHLETES": "true",
            },
            clear=True,
        ):
            import config

            config = importlib.reload(config)

        self.assertEqual(("i1", "i2"), config.ATHLETE_IDS)
        self.assertTrue(config.DISCOVER_ATHLETES)

    def test_config_parses_multiple_accounts_without_legacy_credentials(self):
        with patch.dict(
            os.environ,
            {
                "INTERVALS_ICU_ACCOUNTS": (
                    '[{"athlete_id":"coach","passkey":"coach-key",'
                    '"athlete_ids":["coach","student","student"]},'
                    '{"athlete_id":"other","passkey":"other-key",'
                    '"discover_athletes":true}]'
                )
            },
            clear=True,
        ):
            import config

            config = importlib.reload(config)

        self.assertEqual(2, len(config.SYNC_ACCOUNTS))
        self.assertEqual("coach", config.SYNC_ACCOUNTS[0].athlete_id)
        self.assertEqual("coach-key", config.SYNC_ACCOUNTS[0].passkey)
        self.assertEqual(
            ("coach", "student"), config.SYNC_ACCOUNTS[0].athlete_ids
        )
        self.assertFalse(config.SYNC_ACCOUNTS[0].discover_athletes)
        self.assertEqual("other-key", config.SYNC_ACCOUNTS[1].passkey)
        self.assertTrue(config.SYNC_ACCOUNTS[1].discover_athletes)

    def test_config_rejects_account_without_passkey(self):
        with patch.dict(
            os.environ,
            {"INTERVALS_ICU_ACCOUNTS": '[{"athlete_id":"athlete-1"}]'},
            clear=True,
        ):
            import config

            with self.assertRaisesRegex(RuntimeError, "athlete_id 和 passkey"):
                importlib.reload(config)

    def test_config_rejects_non_boolean_account_discovery_flag(self):
        with patch.dict(
            os.environ,
            {
                "INTERVALS_ICU_ACCOUNTS": (
                    '[{"athlete_id":"athlete-1","passkey":"key",'
                    '"discover_athletes":"true"}]'
                )
            },
            clear=True,
        ):
            import config

            with self.assertRaisesRegex(RuntimeError, "必须是 true 或 false"):
                importlib.reload(config)

    def test_config_rejects_invalid_discovery_flag(self):
        with patch.dict(
            os.environ,
            {
                "INTERVALS_ICU_AUTH_PASSWORD": "env-password",
                "INTERVALS_ICU_ATHLETE_ID": "coach",
                "INTERVALS_ICU_ACCOUNTS": "",
                "INTERVALS_ICU_DISCOVER_ATHLETES": "maybe",
            },
            clear=True,
        ):
            import config

            with self.assertRaises(RuntimeError):
                importlib.reload(config)


if __name__ == "__main__":
    unittest.main()
