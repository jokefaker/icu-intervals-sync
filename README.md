# ICU Intervals Sync

Sync today's Intervals.icu ride segments into activity intervals.

## Docker on NAS

Build the image:

```bash
docker build -t icu-intervals-sync:latest .
```

Export it for NAS import:

```bash
docker save icu-intervals-sync:latest | gzip > icu-intervals-sync.tar.gz
```

Import `icu-intervals-sync.tar.gz` in the NAS container UI, then create a
container from `icu-intervals-sync:latest`.

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
