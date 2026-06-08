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

def require_env(name):
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"缺少必填环境变量：{name}，请在容器参数中填写")
    return value


AUTH_USERNAME = (os.environ.get("INTERVALS_ICU_AUTH_USERNAME") or "API_KEY").strip()
AUTH_PASSWORD = require_env("INTERVALS_ICU_AUTH_PASSWORD")
ATHLETE_ID = require_env("INTERVALS_ICU_ATHLETE_ID")
API_BASE = "https://intervals.icu/api/v1"
DEFAULT_DAYS_RANGE = 7
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
