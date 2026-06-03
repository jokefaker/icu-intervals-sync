import os

AUTH_USERNAME = os.environ.get("INTERVALS_ICU_AUTH_USERNAME", "API_KEY")
AUTH_PASSWORD = os.environ["INTERVALS_ICU_AUTH_PASSWORD"]
ATHLETE_ID = os.environ["INTERVALS_ICU_ATHLETE_ID"]
API_BASE = "https://intervals.icu/api/v1"
DEFAULT_DAYS_RANGE = 7
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
