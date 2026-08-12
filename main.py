# main.py
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from config import APP_TIMEZONE, ATHLETE_ID, ATHLETE_IDS, DISCOVER_ATHLETES
from icu_client import ICUClient
from segment_selector import is_starred, select_segments

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _athlete_id_from_record(athlete):
    athlete_id = athlete.get("id") or athlete.get("athlete_id")
    return str(athlete_id).strip() if athlete_id is not None else ""


def _comparable_athlete_id(athlete_id):
    athlete_id = str(athlete_id).strip()
    if athlete_id.startswith("i") and athlete_id[1:].isdigit():
        return athlete_id[1:]
    return athlete_id


def get_target_athlete_ids(client):
    """Resolve explicit targets or discover athletes visible to a coach."""
    if ATHLETE_IDS:
        return list(ATHLETE_IDS)
    if not DISCOVER_ATHLETES:
        return [ATHLETE_ID]

    athletes = client.get_athletes()
    athlete_ids = [ATHLETE_ID]
    seen_ids = {_comparable_athlete_id(ATHLETE_ID)}
    for athlete in athletes:
        athlete_id = _athlete_id_from_record(athlete)
        comparable_id = _comparable_athlete_id(athlete_id)
        if not athlete_id or comparable_id in seen_ids:
            continue
        athlete_ids.append(athlete_id)
        seen_ids.add(comparable_id)
    return athlete_ids


def has_labeled_intervals(detail):
    # 只要 intervals 里出现任意带 label 的分段，就认为用户已手动操作过，不再重复标记
    return any(
        (interval.get("label") or "").strip()
        for interval in detail.get("icu_intervals", [])
    )


def sync_today_activities(client, today=None):
    today = today or datetime.now(ZoneInfo(APP_TIMEZONE)).strftime("%Y-%m-%d")
    logger.info(f"查询当天活动：{today}")
    try:
        activities = client.get_activities(oldest=today, newest=today)
    except Exception as e:
        logger.error(f"查询当天活动失败：{e}")
        return

    if not activities:
        logger.warning("当天没有活动，流程结束")
        return

    logger.info(f"当天共 {len(activities)} 个活动")
    for activity in activities:
        activity_id = activity.get("id")
        activity_name = activity.get("name", "未知活动")
        activity_type = activity.get("type")
        if not activity_id:
            logger.warning(f"活动缺少 ID，跳过：{activity_name}")
            continue
        if activity_type != "Ride":
            logger.warning(f"活动不是真实骑行，跳过：id={activity_id}，名称={activity_name}，类型={activity_type}")
            continue
        logger.info("=" * 60)
        logger.info(f"开始同步活动：id={activity_id}，名称={activity_name}")
        relabel_activity_segments(client, activity_id)


def relabel_activity_segments(client, activity_id):
    # 步骤 1：获取活动详情
    logger.info("【步骤 1】获取活动详情")
    try:
        detail = client.get_activity_detail(activity_id)
        logger.info(f"活动 ID：{activity_id}，名称：{detail.get('name', '未知活动')}")
    except Exception as e:
        logger.error(f"获取活动详情失败：{e}")
        return
    if detail.get("type") != "Ride":
        logger.warning("该活动不是真实骑行，忽略")
        return

    # 步骤 2：获取赛段列表
    logger.info("【步骤 2】获取赛段列表")
    try:
        segments = client.get_segments(activity_id)
    except Exception as e:
        logger.error(f"获取赛段失败：{e}")
        return

    if not segments:
        logger.warning("该活动没有赛段，流程结束")
        return

    if has_labeled_intervals(detail):
        logger.info("该活动已存在带 label 的分段，判定为用户已手动操作，跳过同步")
        return

    selected_segments = select_segments(segments)
    if not selected_segments:
        logger.warning("该活动没有名称和索引均有效的赛段，保留现有分段")
        return
    starred_count = sum(is_starred(segment) for segment in selected_segments)
    logger.info(
        "赛段择优完成：原始=%s，保留=%s，其中收藏=%s",
        len(segments),
        len(selected_segments),
        starred_count,
    )

    # 步骤 3：清除所有分段
    logger.info("【步骤 3】清除所有分段")
    try:
        client.clear_intervals(activity_id)
    except Exception as e:
        logger.error(f"清除分段失败：{e}")
        return

    # 步骤 4：逐个标记赛段
    logger.info("【步骤 4】逐个标记赛段")
    success, skip, fail = 0, 0, 0
    for i, segment in enumerate(selected_segments, 1):
        seg_name = (segment.get("name") or "").strip()
        if not seg_name:
            skip += 1
            continue
        try:
            client.mark_interval(activity_id, segment)
            success += 1
        except Exception as e:
            logger.error(f"[{i}] 标记失败：{seg_name} - {e}")
            fail += 1

    logger.info("=" * 60)
    logger.info(f"完成！成功={success}，跳过={skip}，失败={fail}")
    logger.info("=" * 60)


def main():
    logger.info("=" * 60)
    logger.info("开始执行赛段重新标记流程")
    logger.info("=" * 60)

    client = ICUClient(athlete_id=ATHLETE_ID)
    try:
        athlete_ids = get_target_athlete_ids(client)
    except Exception as e:
        logger.error(f"获取同步运动员列表失败：{e}")
        return

    if not athlete_ids:
        logger.warning("没有找到需要同步的运动员")
        return

    logger.info("本轮将同步 %s 名运动员", len(athlete_ids))
    for athlete_id in athlete_ids:
        logger.info("开始同步运动员：athlete_id=%s", athlete_id)
        try:
            sync_today_activities(client.for_athlete(athlete_id))
        except Exception:
            logger.exception("同步运动员失败：athlete_id=%s", athlete_id)


if __name__ == "__main__":
    main()
