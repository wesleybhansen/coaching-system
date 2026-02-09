"""Send re-engagement nudges to silent users and mark very silent users."""

import logging
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service

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
                # Skip if we already sent a re-engagement in the last 14 days
                if db.has_recent_reengagement(user["id"], within_days=14):
                    logger.info(f"Already sent re-engagement to {user['email']} recently, skipping")
                    continue

                first_name = user.get("first_name") or "there"
                in_reply_to = user.get("gmail_message_id")
                references = user.get("gmail_message_id")

                sent_msg_id = gmail_service.send_reengagement(
                    to_email=user["email"],
                    first_name=first_name,
                    in_reply_to=in_reply_to,
                    references=references,
                )

                # Log the re-engagement
                db.create_conversation({
                    "user_id": user["id"],
                    "type": "Re-engagement",
                    "status": "Sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "gmail_message_id": sent_msg_id,
                })

                processed += 1
                logger.info(f"Re-engagement sent to {user['email']}")

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

        db.complete_workflow_run(run_id, items_processed=processed)
        logger.info(f"re_engagement completed: {processed} items processed")

    except Exception as e:
        logger.error(f"re_engagement workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
