import importlib
import os
import unittest


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


if __name__ == "__main__":
    unittest.main()
