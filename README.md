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

### Coach / multiple-athlete mode

`INTERVALS_ICU_ATHLETE_ID` identifies the coach account that owns the API key.
Choose one target mode:

```text
# Recommended for a controlled production rollout: explicit allowlist
INTERVALS_ICU_ATHLETE_IDS=i123456,i234567

# Or sync the coach plus every accessible athlete returned by GET /api/v1/athletes
INTERVALS_ICU_DISCOVER_ATHLETES=true
```

The discovery endpoint returns athletes the account follows or coaches, plus the
account itself. This service always includes `INTERVALS_ICU_ATHLETE_ID` and then
adds the discovered athletes. It cannot infer which entries are active students,
so use the allowlist when that distinction matters (and include the coach ID in
the allowlist when the coach should also be synced).

Intervals.icu may not expose activities imported from Strava through its API due
to Strava data-forwarding restrictions. Activities from other supported sources
can still be processed when the coach account has access.

Before intervals are written, every valid starred segment is retained, including
overlapping starred segments. Regular segments overlapping any starred segment
are discarded. When the remaining regular segments overlap each other, the
longer segment wins. The result is written in activity order. Invalid or unnamed
segments are ignored.

For each target athlete, the service also provisions the private
`StravaSegmentsJson` activity field and `Strava 路段` activity chart when they do
not already exist. The chart is added to the athlete's Ride home charts. This
check runs once per athlete per container process and is idempotent across
restarts. Every Ride stores all valid raw Strava segments in the custom field so
the chart can display them even when interval relabeling is skipped because the
athlete has manually labeled intervals.

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
