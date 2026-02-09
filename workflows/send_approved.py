"""Send approved coaching responses via Gmail."""

import logging
import random
import time
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service, openai_service

logger = logging.getLogger(__name__)


def run():
    """Send all approved, unsent responses."""
    run_id = db.start_workflow_run("send_approved")
    sent = 0

    try:
        conversations = db.get_approved_unsent()
        logger.info(f"Found {len(conversations)} approved responses to send")

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

                # Random delay (0-30 minutes) to feel human
                delay = random.randint(0, 60)
                logger.info(f"Sending to {user['email']} with {delay}s delay")
                time.sleep(delay)

                # Send email
                in_reply_to = user.get("gmail_message_id")
                references = user.get("gmail_message_id")

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

            except Exception as e:
                logger.error(f"Error sending response for conversation {conv['id']}: {e}", exc_info=True)
                continue

        db.complete_workflow_run(run_id, items_processed=sent)
        logger.info(f"send_approved completed: {sent} responses sent")

    except Exception as e:
        logger.error(f"send_approved workflow failed: {e}", exc_info=True)
        db.fail_workflow_run(run_id, str(e))
        raise
