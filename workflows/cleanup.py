"""Catch unprocessed emails and flag them for review."""

import logging
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service

logger = logging.getLogger(__name__)


def run():
    """Find unread emails older than 24h and log them as flagged."""
    run_id = db.start_workflow_run("cleanup")
    processed = 0
    missed_summary = []

    try:
        emails = gmail_service.fetch_old_unread_emails(max_results=100)
        logger.info(f"Found {len(emails)} old unread emails")

        for email_data in emails:
            try:
                from_email = email_data["from_email"]
                message_id = email_data["message_id"]

                # Skip if already processed
                if message_id and db.conversation_exists_for_message(message_id):
                    gmail_service.mark_as_read(email_data["imap_id"])
                    continue

                # Find user
                user = db.get_user_by_email(from_email)

                if user:
                    # Known user — log as flagged follow-up
                    db.create_conversation({
                        "user_id": user["id"],
                        "type": "Follow-up",
                        "user_message_raw": email_data["body"],
                        "status": "Flagged",
                        "flag_reason": "Missed by regular processing - manual review needed",
                        "gmail_message_id": message_id or None,
                        "gmail_thread_id": email_data.get("in_reply_to"),
                    })
                    missed_summary.append(f"- {from_email}: Known user")
                else:
                    # Unknown sender — log for potential onboarding
                    db.create_conversation({
                        "type": "Onboarding",
                        "user_message_raw": f"From: {from_email}\n\n{email_data['body']}",
                        "status": "Flagged",
                        "flag_reason": "Unknown sender - potential new user to onboard",
                        "gmail_message_id": message_id or None,
                    })
                    missed_summary.append(f"- {from_email}: Unknown sender")

                # Mark as read
                gmail_service.mark_as_read(email_data["imap_id"])
                processed += 1

            except Exception as e:
                logger.error(f"Error processing missed email from {email_data['from_email']}: {e}", exc_info=True)
                continue

        # Send notification if any missed emails were found
        if missed_summary:
            summary_text = "\n".join(missed_summary)
            notification_body = f"""The cleanup workflow found {processed} email(s) that weren't processed by the regular workflow.

They've been logged as 'Flagged' for your review.

Summary:
{summary_text}

Check the Flagged page in the dashboard."""

            try:
                gmail_service.send_email(
                    to_email=db.get_setting("notification_email", "coachwes@thelaunchpadincubator.com"),
                    subject=f"Coaching System: {processed} Missed Emails Flagged",
                    body=notification_body,
                )
            except Exception as e:
                logger.error(f"Failed to send cleanup notification: {e}")

        db.complete_workflow_run(run_id, items_processed=processed)
        logger.info(f"cleanup completed: {processed} missed emails flagged")

    except Exception as e:
        logger.error(f"cleanup workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
