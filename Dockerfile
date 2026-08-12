FROM docker.m.daocloud.io/library/python:3.12-slim

# 镜像自我声明所需参数，方便在 NAS 创建容器界面里查看与填写
LABEL org.opencontainers.image.title="icu-intervals-sync" \
      org.opencontainers.image.description="同步 Intervals.icu 当天骑行赛段到活动分段" \
      env.INTERVALS_ICU_AUTH_PASSWORD="必填：你的 Intervals.icu API Key" \
      env.INTERVALS_ICU_ATHLETE_ID="必填：你的 athlete id" \
      env.INTERVALS_ICU_ATHLETE_IDS="可选：要同步的 athlete id 白名单，逗号分隔" \
      env.INTERVALS_ICU_DISCOVER_ATHLETES="可选：自动同步教练本人及可访问的其他运动员，默认 false" \
      env.INTERVALS_ICU_AUTH_USERNAME="可选，默认 API_KEY（基本认证固定用户名）" \
      env.APP_TIMEZONE="可选，默认 Asia/Shanghai" \
      env.SYNC_INTERVAL_SECONDS="可选，默认 60，循环同步间隔秒数（最小 1）"

# 用 ENV 预声明所有变量，NAS 创建容器时会自动列出，必填项留空待用户填写
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    INTERVALS_ICU_AUTH_USERNAME=API_KEY \
    INTERVALS_ICU_AUTH_PASSWORD="" \
    INTERVALS_ICU_ATHLETE_ID="" \
    INTERVALS_ICU_ATHLETE_IDS="" \
    INTERVALS_ICU_DISCOVER_ATHLETES=false \
    SYNC_INTERVAL_SECONDS=60 \
    APP_TIMEZONE=Asia/Shanghai

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py icu_client.py main.py runner.py segment_selector.py ./

CMD ["python", "runner.py"]
