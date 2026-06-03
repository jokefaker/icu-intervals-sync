# icu_client.py
import logging
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
from config import API_BASE, AUTH_PASSWORD, AUTH_USERNAME, DEFAULT_DAYS_RANGE

logger = logging.getLogger(__name__)


class ICUClient:
    def __init__(self, athlete_id, auth_username=AUTH_USERNAME, auth_password=AUTH_PASSWORD):
        self.athlete_id = athlete_id
        self.auth = HTTPBasicAuth(auth_username, auth_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

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
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_segments(self, activity_id):
        """获取活动赛段列表"""
        url = f"{API_BASE}/activity/{activity_id}/segments"
        logger.info(f"获取赛段：activity_id={activity_id}")
        response = self.session.get(url)
        response.raise_for_status()
        segments = response.json()
        logger.info(f"共 {len(segments)} 个赛段")
        return segments

    def get_activity_detail(self, activity_id):
        """获取活动详情"""
        url = f"{API_BASE}/activity/{activity_id}?intervals=true"
        logger.info(f"获取活动详情：activity_id={activity_id}")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def clear_intervals(self, activity_id):
        """清除活动所有分段"""
        url = f"{API_BASE}/activity/{activity_id}/intervals"
        logger.info(f"清除分段：activity_id={activity_id}")
        response = self.session.put(url, params={"all": "true"}, json=[])
        response.raise_for_status()
        logger.info("清除分段成功")
        try:
            return response.json()
        except Exception:
            return {}

    def mark_interval(self, activity_id, segment):
        """标记单个分段"""
        segment_effort_id = segment.get("id")
        segment_id = segment.get("segment_id")
        starred  = segment.get("starred")
        segment_name = segment.get("name", "未知赛段").strip()
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
        response = self.session.put(url, json=body)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return {}
