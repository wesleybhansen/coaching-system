"""Send re-engagement nudges to silent users, mark very silent users, and flag stalled onboarding."""

import logging
from datetime import datetime, timezone

from db import supabase_client as db

logger = logging.getLogger(__name__)


def run():
    """
    Two-part workflow:
    1. Send re-engagement emails to users silent for 10+ days (if not already sent in last 14 days)
    2. Mark users silent for 17+ days as "Silent" status
    """
    run_id = db.start_workflow_run("re_engagement")
    processed = 0

    try:
        re_engagement_days = int(db.get_setting("re_engagement_days", "10"))

        # Part 1: Send re-engagement emails
        silent_users = db.get_silent_users(days=re_engagement_days)
        logger.info(f"Found {len(silent_users)} users silent for {re_engagement_days}+ days")

        for user in silent_users:
            try:
                # Skip if there's already pending outreach (Pending Review or Approved)
                if db.has_pending_outreach(user["id"]):
                    logger.info(f"Pending outreach exists for {user['email']}, skipping re-engagement")
                    continue

                # Skip if we already sent a re-engagement in the last 14 days
                if db.has_recent_reengagement(user["id"], within_days=14):
                    logger.info(f"Already sent re-engagement to {user['email']} recently, skipping")
                    continue

                first_name = user.get("first_name") or "there"

                body = f"""Hey {first_name},

Haven't heard from you in a bit. Everything okay?

When you're ready, just reply with a quick update on what you're working on."""

                # Route through Pending Review instead of sending directly
                db.create_conversation({
                    "user_id": user["id"],
                    "type": "Re-engagement",
                    "status": "Pending Review",
                    "ai_response": body,
                })

                processed += 1
                logger.info(f"Re-engagement queued for review: {user['email']}")

            except Exception as e:
                logger.error(f"Error sending re-engagement to {user['email']}: {e}", exc_info=True)
                continue

        # Part 2: Mark very silent users (17+ days = 10 days + 7 days after re-engagement)
        very_silent_users = db.get_silent_users(days=re_engagement_days + 7)
        for user in very_silent_users:
            try:
                db.update_user(user["id"], {"status": "Silent"})
                logger.info(f"Marked {user['email']} as Silent")
                processed += 1
            except Exception as e:
                logger.error(f"Error marking {user['email']} as Silent: {e}", exc_info=True)

        # Part 3: Flag stalled onboarding users (no conversation in 7+ days)
        onboarding_users = db.get_onboarding_users()
        for user in onboarding_users:
            try:
                created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
                days_since = (datetime.now(timezone.utc) - created).days
                if days_since < 7:
                    continue

                # Check if there's already a flagged conversation for this stall
                existing = db.get_conversations_for_user(user["id"])
                already_flagged = any(
                    c.get("status") == "Flagged" and "stalled" in (c.get("flag_reason") or "").lower()
                    for c in existing
                )
                if already_flagged:
                    continue

                first_name = user.get("first_name") or user.get("email", "Unknown")
                db.create_conversation({
                    "user_id": user["id"],
                    "type": "Onboarding",
                    "status": "Flagged",
                    "flag_reason": f"Onboarding stalled — {first_name} hasn't responded in {days_since} days",
                    "ai_response": None,
                })
                processed += 1
                logger.info(f"Flagged stalled onboarding for {user['email']} ({days_since} days)")

            except Exception as e:
                logger.error(f"Error checking onboarding stall for {user.get('email')}: {e}", exc_info=True)

        db.complete_workflow_run(run_id, items_processed=processed)
        logger.info(f"re_engagement completed: {processed} items processed")

    except Exception as e:
        logger.error(f"re_engagement workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
