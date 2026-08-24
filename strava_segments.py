import json
from functools import lru_cache
from pathlib import Path

from segment_selector import is_starred

FIELD_CODE = "StravaSegmentsJson"
FIELD_NAME = "Strava Segments Data"
CHART_NAME = "Strava 路段"


@lru_cache(maxsize=1)
def chart_script():
    return Path(__file__).with_name("strava_segments_chart.js").read_text(
        encoding="utf-8"
    )


def field_definition():
    return {
        "type": "ACTIVITY_FIELD",
        "visibility": "PRIVATE",
        "name": FIELD_NAME,
        "description": "All Strava segments for the activity, managed by icu-intervals-sync.",
        "content": {
            "max": None,
            "min": None,
            "name": FIELD_NAME,
            "code": FIELD_CODE,
            "icon": None,
            "link": None,
            "type": "text",
            "color": "#333333",
            "gauge": None,
            "total": None,
            "units": None,
            "inline": False,
            "prefix": None,
            "script": None,
            "suffix": None,
            "average": None,
            "convert": None,
            "example": None,
            "options": None,
            "aggregate": "SUM",
            "text_wrap": "false",
            "pace_units": None,
            "text_align": None,
            "number_format": None,
            "fit_session_field": None,
            "processes_fit_messages": False,
        },
    }


def chart_definition():
    return {
        "type": "ACTIVITY_CHART",
        "visibility": "PRIVATE",
        "name": CHART_NAME,
        "description": "全部 Strava 路段及训练指标，链接与表格同步滚动。",
        "content": {
            "name": CHART_NAME,
            "link": None,
            "width": "100%",
            "height": "650px",
            "script": chart_script(),
        },
    }


def find_field(items):
    for item in items:
        if item.get("type") != "ACTIVITY_FIELD":
            continue
        if (item.get("content") or {}).get("code") == FIELD_CODE:
            return item
    return None


def find_chart(items):
    for item in items:
        if item.get("type") == "ACTIVITY_CHART" and item.get("name") == CHART_NAME:
            return item
    return None


def custom_item_id(item):
    if not isinstance(item, dict):
        return None
    item_id = item.get("id")
    if item_id is not None:
        return item_id
    nested = item.get("item") or item.get("custom_item")
    return nested.get("id") if isinstance(nested, dict) else None


def chart_needs_update(chart, desired):
    chart_content = chart.get("content") or {}
    desired_content = desired["content"]
    return any(
        (
            chart.get("description") != desired["description"],
            chart_content.get("width") != desired_content["width"],
            chart_content.get("height") != desired_content["height"],
            chart_content.get("script") != desired_content["script"],
        )
    )


def build_segments_json(activity, segments):
    serialized_segments = []
    for segment in segments:
        name = (segment.get("name") or "").strip()
        start = segment.get("start_index")
        end = segment.get("end_index")
        if (
            not name
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or end <= start
        ):
            continue
        serialized_segments.append(
            {
                "n": name,
                "s": str(segment.get("segment_id") or ""),
                "e": str(segment.get("id") or ""),
                "a": start,
                "b": end,
                "f": is_starred(segment),
            }
        )

    payload = {
        "v": 1,
        "aid": str(activity.get("strava_id") or ""),
        "segments": serialized_segments,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def enable_chart_on_ride(client, chart_id):
    settings = client.get_sport_settings("Ride")
    activity_charts = dict(settings.get("activity_charts") or {})
    home = list(activity_charts.get("home") or [])
    if any(
        str(entry.get("id") if isinstance(entry, dict) else entry) == str(chart_id)
        for entry in home
    ):
        return False

    home.append({"id": str(chart_id), "width": None, "height": None})
    activity_charts["home"] = home
    client.update_sport_settings(
        settings.get("id") or "Ride", {"activity_charts": activity_charts}
    )
    return True


def ensure_assets(client):
    items = client.get_custom_items()

    field = find_field(items)
    if field is None:
        field = client.create_custom_item(field_definition())

    desired_chart = chart_definition()
    chart = find_chart(items)
    if chart is None:
        chart = client.create_custom_item(desired_chart)

    chart_id = custom_item_id(chart)
    if chart_id is None:
        chart = find_chart(client.get_custom_items())
        chart_id = custom_item_id(chart)
    if chart_id is None:
        raise ValueError("创建 Strava 路段图表后未返回图表 ID")

    chart_updated = False
    if find_chart(items) is not None and chart_needs_update(chart, desired_chart):
        chart = client.update_custom_item(chart_id, desired_chart)
        chart_updated = True

    enabled = enable_chart_on_ride(client, chart_id)
    return {
        "field_created": find_field(items) is None,
        "chart_created": find_chart(items) is None,
        "chart_updated": chart_updated,
        "chart_enabled": enabled,
        "chart_id": chart_id,
    }
