import logging
import os
import sys
import time

import main

logger = logging.getLogger(__name__)


def get_sync_interval_seconds():
    raw_value = os.environ.get("SYNC_INTERVAL_SECONDS", "60")
    interval_seconds = int(raw_value)
    if interval_seconds < 1:
        raise ValueError("SYNC_INTERVAL_SECONDS must be at least 1")
    return interval_seconds


def run_forever(interval_seconds=None, sync_once=main.main, sleep=time.sleep):
    if interval_seconds is None:
        interval_seconds = get_sync_interval_seconds()
    logger.info("Starting sync runner with interval=%s seconds", interval_seconds)

    while True:
        try:
            sync_once()
        except KeyboardInterrupt:
            raise
        except Exception:
            logger.exception("Sync run failed")

        try:
            sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Sync runner stopped")
            return


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_forever()
