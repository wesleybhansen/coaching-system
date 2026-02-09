"""Fetch new emails and process them into coaching response drafts."""

import logging

from db import supabase_client as db
from services import gmail_service, coaching_service

logger = logging.getLogger(__name__)


def run():
    """Main workflow: fetch unread emails, process each one."""
    run_id = db.start_workflow_run("process_emails")
    processed = 0

    try:
        emails = gmail_service.fetch_unread_emails(max_results=50)
        logger.info(f"Found {len(emails)} unread emails")

        for email_data in emails:
            try:
                result = coaching_service.process_email(email_data)
                if result:
                    processed += 1

                # Mark as read regardless of processing outcome
                gmail_service.mark_as_read(email_data["imap_id"])

            except Exception as e:
                logger.error(f"Error processing email from {email_data['from_email']}: {e}", exc_info=True)
                # Don't mark as read so cleanup can catch it
                continue

        db.complete_workflow_run(run_id, items_processed=processed)
        logger.info(f"process_emails completed: {processed} emails processed")

    except Exception as e:
        logger.error(f"process_emails workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
