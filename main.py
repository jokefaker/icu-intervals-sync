# main.py
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from config import APP_TIMEZONE, ATHLETE_ID
from icu_client import ICUClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def sync_today_activities(client, today=None):
    today = today or datetime.now(ZoneInfo(APP_TIMEZONE)).strftime("%Y-%m-%d")
    logger.info(f"查询当天活动：{today}")
    try:
        activities = client.get_activities(oldest=today, newest=today)
    except Exception as e:
        logger.error(f"查询当天活动失败：{e}")
        sys.exit(1)

    if not activities:
        logger.warning("当天没有活动，流程结束")
        return

    logger.info(f"当天共 {len(activities)} 个活动")
    for activity in activities:
        activity_id = activity.get("id")
        activity_name = activity.get("name", "未知活动")
        if not activity_id:
            logger.warning(f"活动缺少 ID，跳过：{activity_name}")
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
        sys.exit(1)
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
    for i, segment in enumerate(segments, 1):
        seg_name = segment.get("name", "").strip()
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
    sync_today_activities(client)


if __name__ == "__main__":
    main()
