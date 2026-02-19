"""Send approved coaching responses via Gmail."""

import logging
import random
import smtplib
import time
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service, openai_service

logger = logging.getLogger(__name__)


def run():
    """Send all approved, unsent responses.

    Each email gets a random offset of 1-N minutes (default N=100) so
    responses land at varied, human-feeling times rather than in a cluster.
    Emails are sorted by offset and sent with incremental gaps between them.
    """
    run_id = db.start_workflow_run("send_approved")
    sent = 0
    errors = []

    try:
        conversations = db.get_approved_unsent()
        logger.info(f"Found {len(conversations)} approved responses to send")

        if not conversations:
            db.complete_workflow_run(run_id, items_processed=0, items_failed=0)
            return

        # Assign each email a random offset and sort by it
        max_offset = max(1, int(db.get_setting("send_delay_max_minutes", "100")))
        for conv in conversations:
            conv["_send_offset"] = random.randint(1, max_offset)
        conversations.sort(key=lambda c: c["_send_offset"])

        logger.info(f"Send offsets: {[c['_send_offset'] for c in conversations]} minutes")

        prev_offset = 0
        for conv in conversations:
            try:
                user = conv.get("users")
                if not user:
                    logger.warning(f"No user found for conversation {conv['id']}")
                    continue

                # Use sent_response if edited, otherwise ai_response
                response_text = conv.get("sent_response") or conv.get("ai_response")
                if not response_text:
                    logger.warning(f"No response text for conversation {conv['id']}")
                    continue

                # Add sign-off
                full_response = f"{response_text}\n\nWes"

                # Sleep the incremental gap from previous email's offset
                gap_minutes = conv["_send_offset"] - prev_offset
                gap_seconds = gap_minutes * 60
                logger.info(f"Sending to {user['email']} (offset {conv['_send_offset']}m, sleeping {gap_seconds}s)")
                time.sleep(gap_seconds)
                prev_offset = conv["_send_offset"]

                # Threading with resilience: try user's gmail_message_id first,
                # fall back to finding the most recent conversation's message_id
                in_reply_to = user.get("gmail_message_id")
                references = user.get("gmail_message_id")

                if not in_reply_to:
                    # Fallback: try to find thread from recent conversations
                    recent = db.get_recent_conversations(user["id"], limit=1)
                    if recent and recent[0].get("gmail_message_id"):
                        in_reply_to = recent[0]["gmail_message_id"]
                        references = in_reply_to
                        logger.info(f"Using fallback threading for {user['email']}")

                sent_msg_id = gmail_service.send_email(
                    to_email=user["email"],
                    subject="Re: Coaching",
                    body=full_response,
                    in_reply_to=in_reply_to,
                    references=references,
                )

                # Update conversation status
                db.update_conversation(conv["id"], {
                    "status": "Sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "sent_response": response_text,
                })

                # Generate and apply summary update
                try:
                    user_message = conv.get("user_message_parsed") or conv.get("user_message_raw") or ""
                    if user_message:
                        summary_update = openai_service.generate_summary_update(
                            current_summary=user.get("summary", ""),
                            user_message=user_message,
                            coach_response=response_text,
                        )
                        current_summary = user.get("summary") or ""
                        date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        new_summary = f"{current_summary}\n\n{date_prefix}: {summary_update}".strip()
                        db.update_user(user["id"], {"summary": new_summary})
                except Exception as e:
                    logger.error(f"Failed to update summary for user {user['id']}: {e}")

                sent += 1
                logger.info(f"Response sent to {user['email']}")

            except smtplib.SMTPRecipientsRefused as e:
                # Hard bounce — recipient address is invalid
                error_msg = f"Bounce for conversation {conv['id']} to {user['email']}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

                # Track bounce on user
                current_bounces = (user.get("bounce_count") or 0) + 1
                user_updates = {"bounce_count": current_bounces}
                if current_bounces >= 3:
                    user_updates["notes"] = f"{user.get('notes') or ''}\n[AUTO] 3+ bounces detected — email may be invalid.".strip()
                db.update_user(user["id"], user_updates)

                # Reject this conversation
                db.update_conversation(conv["id"], {
                    "status": "Rejected",
                    "flag_reason": f"Email bounced ({current_bounces} total bounces)",
                })
                continue

            except Exception as e:
                error_msg = f"Error sending response for conversation {conv['id']}: {e}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

                # Track send attempt for retry logic
                attempts = (conv.get("send_attempts") or 0) + 1
                if attempts >= 3:
                    db.update_conversation(conv["id"], {
                        "status": "Flagged",
                        "flag_reason": f"Send failed 3 times: {e}",
                        "send_attempts": attempts,
                    })
                else:
                    db.update_conversation(conv["id"], {
                        "status": "Send Failed",
                        "send_attempts": attempts,
                    })
                continue

        db.complete_workflow_run(run_id, items_processed=sent, items_failed=len(errors))
        logger.info(f"send_approved completed: {sent} sent, {len(errors)} errors")

        # Send alert if there were errors
        if errors:
            _send_error_alert("send_approved", errors)

    except Exception as e:
        logger.error(f"send_approved workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        _send_error_alert("send_approved", [str(e)])
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
