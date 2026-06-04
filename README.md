# ICU Intervals Sync

Sync today's Intervals.icu ride segments into activity intervals.

## Docker on NAS

Most UGREEN NAS models run `linux/amd64`. Build the amd64 image:

```bash
docker buildx build --platform linux/amd64 -t icu-intervals-sync:amd64 --load .
```

Export it for NAS import:

```bash
docker save icu-intervals-sync:amd64 | gzip > icu-intervals-sync-amd64.tar.gz
```

Import `icu-intervals-sync-amd64.tar.gz` in the NAS container UI, then create a
container from `icu-intervals-sync:amd64`.

If your NAS is ARM instead of amd64, build with `--platform linux/arm64` and use
a matching tag, such as `icu-intervals-sync:arm64`.

Set these environment variables in the NAS container UI:

```text
INTERVALS_ICU_AUTH_USERNAME=API_KEY
INTERVALS_ICU_AUTH_PASSWORD=<your Intervals.icu API key>
INTERVALS_ICU_ATHLETE_ID=<your athlete id>
APP_TIMEZONE=Asia/Shanghai
SYNC_INTERVAL_SECONDS=60
```

Enable automatic restart for the container.

## Local Run

Create a local `.env` file with the same variables, then run:

```bash
python main.py
```

Run tests:

```bash
python -m unittest discover
```
