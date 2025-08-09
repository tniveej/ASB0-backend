import logging
import os
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from app.routes.scraping import scrape_news


logger = logging.getLogger(__name__)
_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler() -> None:
    global _scheduler
    if os.getenv("ENABLE_SCHEDULER", "false").lower() not in {"1", "true", "yes"}:
        logger.info("Scheduler disabled; set ENABLE_SCHEDULER=true to enable.")
        return
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_run_scrape_job, "interval", minutes=30, id="rss_scrape_job")
    _scheduler.start()
    logger.info("Scheduler started with job 'rss_scrape_job' (every 30 minutes)")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Scheduler shutdown")


def _run_scrape_job() -> None:
    try:
        result = scrape_news()
        logger.info("Scheduled scrape result: %s", result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scheduled scrape failed: %s", exc)


