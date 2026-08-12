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
                "INTERVALS_ICU_ATHLETE_IDS": " i1, i2, i1 ",
                "INTERVALS_ICU_DISCOVER_ATHLETES": "true",
            },
            clear=True,
        ):
            import config

            config = importlib.reload(config)

        self.assertEqual(("i1", "i2"), config.ATHLETE_IDS)
        self.assertTrue(config.DISCOVER_ATHLETES)

    def test_config_rejects_invalid_discovery_flag(self):
        with patch.dict(
            os.environ,
            {
                "INTERVALS_ICU_AUTH_PASSWORD": "env-password",
                "INTERVALS_ICU_ATHLETE_ID": "coach",
                "INTERVALS_ICU_DISCOVER_ATHLETES": "maybe",
            },
            clear=True,
        ):
            import config

            with self.assertRaises(RuntimeError):
                importlib.reload(config)


if __name__ == "__main__":
    unittest.main()
