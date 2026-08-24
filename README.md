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

### Multiple passkeys / unrelated athletes

Use `INTERVALS_ICU_ACCOUNTS` when the targets are not all accessible with the
same coach API key. Its value is a JSON array. Each entry creates an independent
authenticated session, so a passkey is only used for the athletes in that entry:

```text
INTERVALS_ICU_ACCOUNTS=[{"athlete_id":"iCOACH","passkey":"coach-api-key","athlete_ids":["iCOACH","iSTUDENT1","iSTUDENT2"]},{"athlete_id":"iOTHER1","passkey":"other-api-key-1"},{"athlete_id":"iOTHER2","passkey":"other-api-key-2"}]
```

Each entry supports these fields:

- `athlete_id` and `passkey` are required. `athlete_id` identifies the account
  that owns that passkey.
- `athlete_ids` is an optional explicit target list accessible by that account.
  When omitted, only the entry's `athlete_id` is synced.
- `discover_athletes` can be set to `true` instead of `athlete_ids` to sync the
  account plus every athlete returned by its `/athletes` endpoint.

When `INTERVALS_ICU_ACCOUNTS` is non-empty, it replaces
`INTERVALS_ICU_AUTH_PASSWORD`, `INTERVALS_ICU_ATHLETE_ID`,
`INTERVALS_ICU_ATHLETE_IDS`, and `INTERVALS_ICU_DISCOVER_ATHLETES`. The legacy
single-passkey configuration remains supported when the new variable is empty.
Store this JSON as a container secret or private environment variable because it
contains every configured API key.

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
