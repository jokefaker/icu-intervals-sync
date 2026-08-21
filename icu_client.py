# icu_client.py
import logging
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry
from config import API_BASE, AUTH_PASSWORD, AUTH_USERNAME, DEFAULT_DAYS_RANGE

logger = logging.getLogger(__name__)

# 网络/SSL 一时性错误时自动重试，避免单次抖动导致整个同步失败
REQUEST_TIMEOUT = 30
_RETRY = Retry(
    total=5,
    connect=5,
    read=5,
    status=5,
    backoff_factor=1,  # 重试间隔：1s, 2s, 4s, 8s, 16s
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "PUT", "POST", "DELETE"]),
    raise_on_status=False,
)


class ICUClient:
    def __init__(self, athlete_id, auth_username=AUTH_USERNAME, auth_password=AUTH_PASSWORD):
        self.athlete_id = athlete_id
        self.auth = HTTPBasicAuth(auth_username, auth_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})
        adapter = HTTPAdapter(max_retries=_RETRY)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def for_athlete(self, athlete_id):
        """Reuse this authenticated session for another accessible athlete."""
        client = object.__new__(ICUClient)
        client.athlete_id = athlete_id
        client.auth = self.auth
        client.session = self.session
        return client

    def get_athletes(self):
        """List athletes followed or coached by the authenticated account."""
        url = f"{API_BASE}/athletes"
        logger.info("获取可访问的运动员列表")
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        athletes = response.json()
        if not isinstance(athletes, list):
            raise ValueError("运动员列表接口返回了非列表数据")
        return athletes

    def get_custom_items(self):
        """List custom fields, charts, streams, and other athlete items."""
        url = f"{API_BASE}/athlete/{self.athlete_id}/custom-item"
        logger.info("获取自定义项目：athlete_id=%s", self.athlete_id)
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        items = response.json()
        if not isinstance(items, list):
            raise ValueError("自定义项目接口返回了非列表数据")
        return items

    def create_custom_item(self, item):
        """Create a custom field, chart, stream, or other athlete item."""
        url = f"{API_BASE}/athlete/{self.athlete_id}/custom-item"
        logger.info(
            "创建自定义项目：athlete_id=%s，name=%s",
            self.athlete_id,
            item.get("name"),
        )
        response = self.session.post(url, json=item, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_sport_settings(self, activity_type):
        """Get settings for an activity type such as Ride."""
        url = (
            f"{API_BASE}/athlete/{self.athlete_id}/sport-settings/{activity_type}"
        )
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def update_sport_settings(self, settings_id, fields):
        """Update selected sport settings without recalculating HR zones."""
        url = f"{API_BASE}/athlete/{self.athlete_id}/sport-settings/{settings_id}"
        response = self.session.put(
            url,
            params={"recalcHrZones": "false"},
            json=fields,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def get_latest_activity(self, days=DEFAULT_DAYS_RANGE):
        """查询活动列表，返回最新的一条活动"""
        newest = datetime.now().strftime("%Y-%m-%d")
        oldest = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        logger.info(f"查询活动列表：{oldest} ~ {newest}")
        activities = self.get_activities(oldest=oldest, newest=newest)
        if not activities:
            raise ValueError(f"最近 {days} 天内未找到任何活动")
        activities_sorted = sorted(activities, key=lambda a: a.get("start_date_local", ""), reverse=True)
        latest = activities_sorted[0]
        logger.info(f"最新活动：id={latest.get('id')}，名称={latest.get('name')}")
        return latest

    def get_activities(self, oldest, newest):
        """查询指定日期范围内的活动列表"""
        url = f"{API_BASE}/athlete/{self.athlete_id}/activities"
        params = {"oldest": oldest, "newest": newest}
        logger.info(f"查询活动列表：{oldest} ~ {newest}")
        response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_segments(self, activity_id):
        """获取活动赛段列表"""
        url = f"{API_BASE}/activity/{activity_id}/segments"
        logger.info(f"获取赛段：activity_id={activity_id}")
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        segments = response.json()
        logger.info(f"共 {len(segments)} 个赛段")
        return segments

    def get_activity_detail(self, activity_id):
        """获取活动详情"""
        url = f"{API_BASE}/activity/{activity_id}?intervals=true"
        logger.info(f"获取活动详情：activity_id={activity_id}")
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def update_activity_fields(self, activity_id, fields):
        """Update activity fields, including custom activity field codes."""
        url = f"{API_BASE}/activity/{activity_id}"
        response = self.session.put(url, json=fields, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def clear_intervals(self, activity_id):
        """清除活动所有分段"""
        url = f"{API_BASE}/activity/{activity_id}/intervals"
        logger.info(f"清除分段：activity_id={activity_id}")
        response = self.session.put(url, params={"all": "true"}, json=[], timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info("清除分段成功")
        try:
            return response.json()
        except Exception:
            return {}

    def mark_interval(self, activity_id, segment):
        """标记单个分段"""
        segment_id = segment.get("segment_id")
        starred = segment.get("starred")
        segment_name = (segment.get("name") or "未知赛段").strip()
        start_index = segment.get("start_index")
        end_index = segment.get("end_index")
        icu_interval_id = -abs(start_index)
        url = f"{API_BASE}/activity/{activity_id}/intervals/{icu_interval_id}"
        body = {
            "id": icu_interval_id,
            "label": segment_name,
            "start_index": start_index,
            "end_index": end_index,
        }
        logger.info(f"标记分段：{segment_name}（id={segment_id}）是否收藏={starred}")
        response = self.session.put(url, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return {}
