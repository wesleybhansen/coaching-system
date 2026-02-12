"""Send check-in emails to active users based on their personalized schedule."""

import logging
from datetime import datetime, timezone

from db import supabase_client as db
from services import gmail_service, openai_service

logger = logging.getLogger(__name__)

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def run():
    """Send personalized check-in emails based on each user's configured schedule."""
    run_id = db.start_workflow_run("check_in")
    sent = 0

    try:
        # Determine today's day of week
        tz_name = db.get_setting("coach_timezone", "America/New_York")
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(tz_name)
        except (ImportError, KeyError):
            try:
                import pytz
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = timezone.utc

        now = datetime.now(tz)
        today = DAY_MAP[now.weekday()]

        users = db.get_active_users_for_checkin_today(today)
        logger.info(f"Found {len(users)} users scheduled for check-in on {today}")

        for user in users:
            try:
                first_name = user.get("first_name") or "there"
                email_addr = user["email"]

                # Generate personalized check-in question based on user context
                checkin_body = _generate_checkin_body(user, first_name)

                # Send as reply if thread exists, otherwise new email
                in_reply_to = user.get("gmail_message_id")
                references = user.get("gmail_message_id")

                subject = "Re: Coaching" if in_reply_to else "Quick check-in"

                sent_msg_id = gmail_service.send_email(
                    to_email=email_addr,
                    subject=subject,
                    body=checkin_body,
                    in_reply_to=in_reply_to,
                    references=references,
                )

                # Log the check-in conversation
                db.create_conversation({
                    "user_id": user["id"],
                    "type": "Check-in",
                    "status": "Sent",
                    "ai_response": checkin_body,
                    "sent_response": checkin_body,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "gmail_message_id": sent_msg_id,
                })

                # Update user's gmail tracking
                updates = {
                    "gmail_message_id": sent_msg_id,
                    "last_response_date": datetime.now(timezone.utc).isoformat(),
                }
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


def _generate_checkin_body(user: dict, first_name: str) -> str:
    """Generate a personalized check-in message or fall back to the standard template."""
    try:
        # Build minimal context for check-in generation
        summary = user.get("summary") or "No history yet"
        stage = user.get("stage", "Ideation")
        business_idea = user.get("business_idea") or "Not specified"
        challenge = user.get("current_challenge") or "Not specified"

        # Get recent conversations for context
        recent = db.get_recent_conversations(user["id"], limit=2)
        recent_text = ""
        if recent:
            for conv in reversed(recent):
                user_msg = conv.get("user_message_parsed") or ""
                coach_msg = conv.get("sent_response") or conv.get("ai_response") or ""
                if user_msg:
                    recent_text += f"\nUser: {user_msg[:200]}\nCoach: {coach_msg[:200]}\n"

        context = f"""Name: {first_name}
Stage: {stage}
Business Idea: {business_idea}
Current Challenge: {challenge}
Journey Summary: {summary[-500:] if len(summary) > 500 else summary}
Recent Exchanges: {recent_text if recent_text else 'None yet'}"""

        checkin_msg = openai_service.generate_checkin_question(context)
        # Add sign-off
        return f"{checkin_msg}\n\nWes"

    except Exception as e:
        logger.warning(f"Failed to generate personalized check-in for {first_name}: {e}. Using standard template.")
        return _standard_checkin_body(first_name)


def _standard_checkin_body(first_name: str) -> str:
    """Fallback standard check-in template."""
    return f"""Hey {first_name},

Quick check-in. Reply with:

1. Accomplished - What did you get done since we last talked?
2. Current Focus - What are you working on now?
3. Next Step - What's the single most important thing you need to do next?
4. Approach - How are you going about it?

Keep it brief - a sentence or two for each.

Wes"""
