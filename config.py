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


def parse_bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"环境变量 {name} 必须是 true 或 false")


def parse_csv_env(name):
    values = []
    for value in (os.environ.get(name) or "").split(","):
        value = value.strip()
        if value and value not in values:
            values.append(value)
    return tuple(values)


AUTH_USERNAME = (os.environ.get("INTERVALS_ICU_AUTH_USERNAME") or "API_KEY").strip()
AUTH_PASSWORD = require_env("INTERVALS_ICU_AUTH_PASSWORD")
ATHLETE_ID = require_env("INTERVALS_ICU_ATHLETE_ID")
ATHLETE_IDS = parse_csv_env("INTERVALS_ICU_ATHLETE_IDS")
DISCOVER_ATHLETES = parse_bool_env("INTERVALS_ICU_DISCOVER_ATHLETES")
API_BASE = "https://intervals.icu/api/v1"
DEFAULT_DAYS_RANGE = 7
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
