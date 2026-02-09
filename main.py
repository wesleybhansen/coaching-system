"""Scheduler entry point for the coaching system worker."""

import logging
import sys

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from db import supabase_client as db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _run_workflow(name: str):
    """Import and run a workflow by name, catching errors."""
    try:
        if name == "process_emails":
            from workflows.process_emails import run
        elif name == "check_in":
            from workflows.check_in import run
        elif name == "send_approved":
            from workflows.send_approved import run
        elif name == "re_engagement":
            from workflows.re_engagement import run
        elif name == "cleanup":
            from workflows.cleanup import run
        else:
            logger.error(f"Unknown workflow: {name}")
            return
        run()
    except Exception as e:
        logger.error(f"Workflow {name} failed: {e}", exc_info=True)


def main():
    logger.info("Starting coaching system scheduler...")

    # Load schedule settings from Supabase
    try:
        settings = db.get_all_settings()
    except Exception as e:
        logger.warning(f"Could not load settings from Supabase, using defaults: {e}")
        settings = {}

    tz_name = settings.get("coach_timezone", "America/New_York")
    tz = pytz.timezone(tz_name)

    process_interval = int(settings.get("process_interval_minutes", "60"))
    process_start = int(settings.get("process_start_hour", "8"))
    process_end = int(settings.get("process_end_hour", "21"))
    check_in_days = settings.get("check_in_days", "tue,fri")
    check_in_hour = int(settings.get("check_in_hour", "9"))
    send_hours = settings.get("send_hours", "9,13,19")

    scheduler = BlockingScheduler(timezone=tz)

    # Process emails: every N minutes during operating hours
    scheduler.add_job(
        _run_workflow,
        CronTrigger(minute=f"*/{process_interval}", hour=f"{process_start}-{process_end}", timezone=tz),
        args=["process_emails"],
        id="process_emails",
        name="Process incoming emails",
    )

    # Check-ins: specific days at check_in_hour
    day_map = {"mon": "0", "tue": "1", "wed": "2", "thu": "3", "fri": "4", "sat": "5", "sun": "6"}
    cron_days = ",".join(day_map.get(d.strip().lower(), d.strip()) for d in check_in_days.split(","))
    scheduler.add_job(
        _run_workflow,
        CronTrigger(day_of_week=cron_days, hour=check_in_hour, timezone=tz),
        args=["check_in"],
        id="check_in",
        name="Send check-in emails",
    )

    # Send approved responses: at configured hours
    scheduler.add_job(
        _run_workflow,
        CronTrigger(hour=send_hours, timezone=tz),
        args=["send_approved"],
        id="send_approved",
        name="Send approved responses",
    )

    # Re-engagement: daily at 10am
    scheduler.add_job(
        _run_workflow,
        CronTrigger(hour=10, timezone=tz),
        args=["re_engagement"],
        id="re_engagement",
        name="Re-engagement nudges",
    )

    # Cleanup: daily at 11pm
    scheduler.add_job(
        _run_workflow,
        CronTrigger(hour=23, timezone=tz),
        args=["cleanup"],
        id="cleanup",
        name="Cleanup missed emails",
    )

    logger.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name}: {job.trigger}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down...")


if __name__ == "__main__":
    main()
