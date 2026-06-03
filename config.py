import os
from pathlib import Path

ENV_FILE = globals().get("ENV_FILE", Path(__file__).with_name(".env"))


def load_env_file(path=ENV_FILE):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_file()

AUTH_USERNAME = os.environ.get("INTERVALS_ICU_AUTH_USERNAME", "API_KEY")
AUTH_PASSWORD = os.environ["INTERVALS_ICU_AUTH_PASSWORD"]
ATHLETE_ID = os.environ["INTERVALS_ICU_ATHLETE_ID"]
API_BASE = "https://intervals.icu/api/v1"
DEFAULT_DAYS_RANGE = 7
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
