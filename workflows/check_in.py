"""Send check-in emails to active users who haven't been contacted recently."""

import logging
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service

logger = logging.getLogger(__name__)


def run():
    """Send check-in emails to active users with 3+ days since last contact."""
    run_id = db.start_workflow_run("check_in")
    sent = 0

    try:
        users = db.get_active_users_needing_checkin(days_since=3)
        logger.info(f"Found {len(users)} users needing check-in")

        for user in users:
            try:
                first_name = user.get("first_name") or "there"
                email_addr = user["email"]

                # Send as reply if thread exists, otherwise new email
                in_reply_to = user.get("gmail_message_id")
                references = user.get("gmail_message_id")

                sent_msg_id = gmail_service.send_checkin(
                    to_email=email_addr,
                    first_name=first_name,
                    in_reply_to=in_reply_to,
                    references=references,
                )

                # Log the check-in conversation
                db.create_conversation({
                    "user_id": user["id"],
                    "type": "Check-in",
                    "status": "Sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "gmail_message_id": sent_msg_id,
                })

                # Update user's gmail tracking
                updates = {"gmail_message_id": sent_msg_id}
                if not in_reply_to:
                    updates["gmail_thread_id"] = sent_msg_id
                db.update_user(user["id"], updates)

                sent += 1
                logger.info(f"Check-in sent to {email_addr}")

            except Exception as e:
                logger.error(f"Error sending check-in to {user['email']}: {e}", exc_info=True)
                continue

        db.complete_workflow_run(run_id, items_processed=sent)
        logger.info(f"check_in completed: {sent} check-ins sent")

    except Exception as e:
        logger.error(f"check_in workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
