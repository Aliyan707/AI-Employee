"""
workers/report_worker.py — APScheduler daily report generation job.

Runs daily at DAILY_REPORT_HOUR UTC.
Aggregates ticket data and upserts into daily_reports table.
"""

import asyncio
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import get_settings
from database.repositories.metrics_repo import get_daily_summary, upsert_daily_report
from database.session import get_db_context

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_daily_report(report_date: date = None) -> None:
    """
    Generate daily report for the given date (defaults to yesterday).

    Aggregates:
    - Total tickets by channel
    - Mean customer sentiment
    - Escalation count and rate
    - Top topics (from ticket subjects)
    """
    if report_date is None:
        report_date = date.today() - timedelta(days=1)

    logger.info("Generating daily report for %s", report_date)

    try:
        async with get_db_context() as db:
            summary = await get_daily_summary(db, report_date)
            report = await upsert_daily_report(db, report_date, summary)

        logger.info(
            "Daily report generated for %s: total_tickets=%d, escalation_rate=%.2f%%",
            report_date,
            summary["total_tickets"],
            summary["escalation_rate"],
        )
    except Exception as e:
        logger.error("Failed to generate daily report for %s: %s", report_date, e)
        raise


async def run_report_worker() -> None:
    """
    Start the APScheduler report worker.
    Runs daily at DAILY_REPORT_HOUR UTC.
    """
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        generate_daily_report,
        trigger=CronTrigger(
            hour=settings.daily_report_hour,
            minute=0,
            timezone="UTC",
        ),
        id="daily_report",
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5min late
    )

    scheduler.start()
    logger.info(
        "Report worker started — will generate daily report at %02d:00 UTC",
        settings.daily_report_hour,
    )

    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        scheduler.shutdown()
        logger.info("Report worker stopped")


def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_report_worker())


if __name__ == "__main__":
    main()
