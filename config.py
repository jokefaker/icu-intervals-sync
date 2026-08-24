import json
import os
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class SyncAccount:
    athlete_id: str
    passkey: str = field(repr=False)
    athlete_ids: tuple = ()
    discover_athletes: bool = False


def parse_accounts_env(name="INTERVALS_ICU_ACCOUNTS"):
    raw_value = (os.environ.get(name) or "").strip()
    if not raw_value:
        return ()

    try:
        raw_accounts = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"环境变量 {name} 必须是合法的 JSON 数组") from exc

    if not isinstance(raw_accounts, list) or not raw_accounts:
        raise RuntimeError(f"环境变量 {name} 必须是非空 JSON 数组")

    accounts = []
    seen_account_ids = set()
    for index, raw_account in enumerate(raw_accounts, 1):
        if not isinstance(raw_account, dict):
            raise RuntimeError(f"环境变量 {name} 的第 {index} 项必须是 JSON 对象")

        athlete_id = str(raw_account.get("athlete_id") or "").strip()
        passkey = str(raw_account.get("passkey") or "").strip()
        if not athlete_id or not passkey:
            raise RuntimeError(
                f"环境变量 {name} 的第 {index} 项必须包含 athlete_id 和 passkey"
            )
        if athlete_id in seen_account_ids:
            raise RuntimeError(f"环境变量 {name} 中 athlete_id 重复：{athlete_id}")

        raw_athlete_ids = raw_account.get("athlete_ids", [])
        if not isinstance(raw_athlete_ids, list):
            raise RuntimeError(
                f"环境变量 {name} 的第 {index} 项 athlete_ids 必须是 JSON 数组"
            )
        athlete_ids = []
        for raw_athlete_id in raw_athlete_ids:
            target_id = str(raw_athlete_id or "").strip()
            if target_id and target_id not in athlete_ids:
                athlete_ids.append(target_id)

        discover_athletes = raw_account.get("discover_athletes", False)
        if not isinstance(discover_athletes, bool):
            raise RuntimeError(
                f"环境变量 {name} 的第 {index} 项 discover_athletes 必须是 true 或 false"
            )

        accounts.append(
            SyncAccount(
                athlete_id=athlete_id,
                passkey=passkey,
                athlete_ids=tuple(athlete_ids),
                discover_athletes=discover_athletes,
            )
        )
        seen_account_ids.add(athlete_id)
    return tuple(accounts)


AUTH_USERNAME = (os.environ.get("INTERVALS_ICU_AUTH_USERNAME") or "API_KEY").strip()
SYNC_ACCOUNTS = parse_accounts_env()
if SYNC_ACCOUNTS:
    primary_account = SYNC_ACCOUNTS[0]
    AUTH_PASSWORD = primary_account.passkey
    ATHLETE_ID = primary_account.athlete_id
    ATHLETE_IDS = primary_account.athlete_ids
    DISCOVER_ATHLETES = primary_account.discover_athletes
else:
    AUTH_PASSWORD = require_env("INTERVALS_ICU_AUTH_PASSWORD")
    ATHLETE_ID = require_env("INTERVALS_ICU_ATHLETE_ID")
    ATHLETE_IDS = parse_csv_env("INTERVALS_ICU_ATHLETE_IDS")
    DISCOVER_ATHLETES = parse_bool_env("INTERVALS_ICU_DISCOVER_ATHLETES")
    SYNC_ACCOUNTS = (
        SyncAccount(
            athlete_id=ATHLETE_ID,
            passkey=AUTH_PASSWORD,
            athlete_ids=ATHLETE_IDS,
            discover_athletes=DISCOVER_ATHLETES,
        ),
    )
API_BASE = "https://intervals.icu/api/v1"
DEFAULT_DAYS_RANGE = 7
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
