"""Fetch new emails and process them into coaching response drafts."""

import logging

from db import supabase_client as db
from services import gmail_service, coaching_service

logger = logging.getLogger(__name__)


def run():
    """Main workflow: fetch unread emails, process each one."""
    run_id = db.start_workflow_run("process_emails")
    processed = 0
    skipped = 0
    errors = []

    try:
        emails = gmail_service.fetch_unread_emails(max_results=50)
        logger.info(f"Found {len(emails)} unread emails")

        # Collect imap_ids to mark as read only after successful processing
        to_mark_read = []

        for email_data in emails:
            try:
                result = coaching_service.process_email(email_data)
                if result:
                    processed += 1
                else:
                    skipped += 1

                # Only queue for mark-as-read AFTER processing succeeded (or intentional skip)
                to_mark_read.append(email_data["imap_id"])

            except Exception as e:
                error_msg = f"Error processing email from {email_data['from_email']}: {e}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                # Don't mark as read so cleanup can catch it
                continue

        # Batch mark as read — only emails that were successfully processed
        if to_mark_read:
            try:
                gmail_service.mark_multiple_as_read(to_mark_read)
            except Exception as e:
                logger.error(f"Failed to mark {len(to_mark_read)} emails as read: {e}", exc_info=True)
                # Not fatal — cleanup workflow will handle stragglers

        db.complete_workflow_run(run_id, items_processed=processed,
                                items_failed=len(errors), items_skipped=skipped)
        logger.info(f"process_emails completed: {processed} processed, {skipped} skipped, {len(errors)} errors")

        # Send alert if there were errors
        if errors:
            _send_error_alert("process_emails", errors)

    except Exception as e:
        logger.error(f"process_emails workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        _send_error_alert("process_emails", [str(e)])
        raise


def _send_error_alert(workflow_name: str, errors: list[str]):
    """Send an email alert when a workflow encounters errors."""
    try:
        notification_email = db.get_setting("notification_email", "coachwes@thelaunchpadincubator.com")
        error_list = "\n".join(f"- {e}" for e in errors[:10])
        body = f"""The {workflow_name} workflow encountered {len(errors)} error(s).

Errors:
{error_list}

Check the dashboard for more details."""

        gmail_service.send_email(
            to_email=notification_email,
            subject=f"Coaching System Alert: {workflow_name} errors",
            body=body,
        )
    except Exception as e:
        logger.error(f"Failed to send error alert: {e}")
