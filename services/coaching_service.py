import logging
import os
from datetime import datetime, timezone

from email_reply_parser import EmailReplyParser

from db import supabase_client as db
from services import openai_service, gmail_service

logger = logging.getLogger(__name__)

# Load evaluation prompt once
_evaluation_prompt = None


def _get_evaluation_prompt() -> str:
    global _evaluation_prompt
    if _evaluation_prompt is None:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "evaluation_prompt.md")
        with open(prompt_path) as f:
            _evaluation_prompt = f.read()
    return _evaluation_prompt


# ── Email Parsing ──────────────────────────────────────────────

def parse_email(raw_body: str) -> str:
    """Parse email to extract only the user's new content.

    Uses email-reply-parser (deterministic, no API call) first.
    Falls back to GPT-4o-mini only if parser returns empty.
    """
    reply = EmailReplyParser.parse_reply(raw_body)
    parsed = reply.strip()

    if not parsed or len(parsed) < 5:
        logger.info("Deterministic parser returned empty, falling back to GPT")
        parsed = openai_service.parse_email_fallback(raw_body)

    return parsed


# ── Pause / Resume Detection ──────────────────────────────────

PAUSE_KEYWORDS = ["pause", "break", "stop", "unsubscribe", "take a break", "stepping back"]
RESUME_KEYWORDS = ["resume", "i'm back", "start again", "ready"]


def detect_intent(message: str) -> str:
    """Detect if the message is a pause, resume, or normal message."""
    lower = message.lower().strip()

    is_pause = any(kw in lower for kw in PAUSE_KEYWORDS)
    is_resume = any(kw in lower for kw in RESUME_KEYWORDS)

    if is_resume:
        return "resume"
    if is_pause:
        return "pause"
    return "normal"


# ── Context Building ───────────────────────────────────────────

def build_assistant_context(user: dict, parsed_message: str, message_type: str = "check-in response") -> str:
    """Build the full context string to send to the OpenAI Assistant."""
    # Recent conversations
    recent = db.get_recent_conversations(user["id"], limit=3)
    history_lines = []
    for conv in reversed(recent):
        user_msg = conv.get("user_message_parsed") or conv.get("user_message_raw") or ""
        coach_msg = conv.get("sent_response") or conv.get("ai_response") or ""
        history_lines.append(f"User: {user_msg}\nCoach: {coach_msg}")
    conversation_history = "\n\n---\n\n".join(history_lines) if history_lines else "No previous conversations"

    # Model responses for their stage
    model_responses = db.get_model_responses_by_stage(user.get("stage", "Ideation"))
    model_text = "\n\n---\n\n".join(
        f"Scenario: {m['scenario']}\nUser Example: {m['user_example']}\nIdeal Response: {m['ideal_response']}"
        for m in model_responses
    ) if model_responses else "No model responses available"

    # Recent corrections
    corrections = db.get_recent_corrections(limit=10)
    corrected_text = "\n\n---\n\n".join(
        f"AI originally wrote: {c['ai_response']}\nWes corrected it to: {c['corrected_response']}\nBecause: {c.get('correction_notes', 'N/A')}"
        for c in corrections
    ) if corrections else "No corrections to learn from yet"

    context = f"""## Context About This User
Name: {user.get('first_name', 'Unknown')}
Stage: {user.get('stage', 'Ideation')}
Business Idea: {user.get('business_idea') or 'Not specified yet'}
Summary of their journey: {user.get('summary') or 'New user, no history yet'}

## Recent Conversation History
{conversation_history}

## Message Type
{message_type}

## Their Current Message
{parsed_message}

## Model Responses (examples of your ideal coaching style)
{model_text}

## Corrected Responses (learn from these)
{corrected_text}

## Instructions
Write a short coaching response (1-3 paragraphs). Focus on 1-2 key points maximum. If relevant, point them to a specific resource. Keep it conversational and human. Do NOT include a sign-off like "Wes" - that will be added automatically. Do NOT wrap your response in JSON or code blocks - just write the natural language coaching response."""

    return context


# ── Response Generation Pipeline ───────────────────────────────

def generate_and_evaluate(user: dict, parsed_message: str, message_type: str = "check-in response") -> dict:
    """Full pipeline: generate response, evaluate it, determine routing.

    Returns dict with: ai_response, confidence, flag, flag_reason,
    detected_stage, stage_changed, resource_referenced, summary_update, status
    """
    # Build context and generate response
    context = build_assistant_context(user, parsed_message, message_type)
    ai_response = openai_service.generate_response(context)

    # Evaluate the response
    evaluation = openai_service.evaluate_response(
        user_message=parsed_message,
        ai_response=ai_response,
        user_stage=user.get("stage", "Ideation"),
        evaluation_prompt=_get_evaluation_prompt(),
    )

    confidence = evaluation.get("confidence", 5)
    flag = evaluation.get("flag", False)

    # Determine status using auto-approve logic
    user_threshold = user.get("auto_approve_threshold")
    global_threshold = int(db.get_setting("global_auto_approve_threshold", "10"))
    threshold = user_threshold if user_threshold is not None else global_threshold

    if flag:
        status = "Flagged"
    elif confidence >= threshold:
        status = "Approved"
    else:
        status = "Pending Review"

    return {
        "ai_response": ai_response,
        "confidence": confidence,
        "flag": flag,
        "flag_reason": evaluation.get("flag_reason"),
        "detected_stage": evaluation.get("detected_stage", user.get("stage")),
        "stage_changed": evaluation.get("stage_changed", False),
        "resource_referenced": evaluation.get("resource_referenced"),
        "summary_update": evaluation.get("summary_update"),
        "status": status,
        "approved_by": "auto" if status == "Approved" else None,
    }


# ── Process a Single Email ─────────────────────────────────────

def process_email(email_data: dict) -> dict | None:
    """Process a single incoming email through the full pipeline.

    Returns the created conversation record, or None if skipped.
    """
    from_email = email_data["from_email"]
    raw_body = email_data["body"]
    message_id = email_data["message_id"]

    # Skip if we already processed this message
    if message_id and db.conversation_exists_for_message(message_id):
        logger.info(f"Already processed message {message_id}, skipping")
        return None

    # Find or create user
    user = db.get_user_by_email(from_email)
    if not user:
        # Auto-create user and draft onboarding for review
        first_name = email_data.get("from_name", "").split()[0] if email_data.get("from_name") else "there"
        user = db.create_user(from_email, first_name)
        logger.info(f"New user created: {from_email}")

        onboarding_body = gmail_service.get_onboarding_body(first_name)

        # Create conversation as Pending Review so Wes can approve it first
        db.create_conversation({
            "user_id": user["id"],
            "type": "Onboarding",
            "user_message_raw": raw_body,
            "user_message_parsed": raw_body,
            "ai_response": onboarding_body,
            "confidence": 8,
            "gmail_message_id": message_id or None,
            "status": "Pending Review",
        })
        logger.info(f"Onboarding draft created for {from_email} — awaiting review")
        return None

    # Parse email content
    parsed = parse_email(raw_body)

    # Check for pause/resume
    intent = detect_intent(parsed)

    if intent == "pause":
        db.update_user(user["id"], {"status": "Paused"})
        pause_body = "No problem - I'll pause check-ins for now. Just reply 'resume' whenever you're ready to pick back up.\n\nWes"
        db.create_conversation({
            "user_id": user["id"],
            "type": "Follow-up",
            "user_message_raw": raw_body,
            "user_message_parsed": parsed,
            "ai_response": pause_body,
            "confidence": 9,
            "gmail_message_id": message_id or None,
            "status": "Pending Review",
        })
        logger.info(f"User {from_email} requested pause — awaiting review")
        return None

    if intent == "resume":
        db.update_user(user["id"], {"status": "Active"})
        resume_body = "Welcome back! I'll resume the regular check-ins. You'll hear from me soon.\n\nWes"
        db.create_conversation({
            "user_id": user["id"],
            "type": "Follow-up",
            "user_message_raw": raw_body,
            "user_message_parsed": parsed,
            "ai_response": resume_body,
            "confidence": 9,
            "gmail_message_id": message_id or None,
            "status": "Pending Review",
        })
        logger.info(f"User {from_email} requested resume — awaiting review")
        return None

    # Determine message type
    recent = db.get_recent_conversations(user["id"], limit=1)
    message_type = "follow-up question" if recent else "check-in response"

    # Generate and evaluate response
    result = generate_and_evaluate(user, parsed, message_type)

    # Store conversation
    conversation = db.create_conversation({
        "user_id": user["id"],
        "type": "Check-in" if message_type == "check-in response" else "Follow-up",
        "user_message_raw": raw_body,
        "user_message_parsed": parsed,
        "ai_response": result["ai_response"],
        "confidence": result["confidence"],
        "status": result["status"],
        "flag_reason": result.get("flag_reason"),
        "gmail_message_id": message_id or None,
        "gmail_thread_id": email_data.get("in_reply_to"),
        "resource_referenced": result.get("resource_referenced"),
        "stage_detected": result.get("detected_stage"),
        "stage_changed": result.get("stage_changed", False),
        "approved_by": result.get("approved_by"),
        "approved_at": datetime.now(timezone.utc).isoformat() if result["status"] == "Approved" else None,
    })

    # Update user metadata
    updates = {
        "last_response_date": datetime.now(timezone.utc).isoformat(),
        "gmail_message_id": email_data.get("message_id"),
    }
    if email_data.get("in_reply_to"):
        updates["gmail_thread_id"] = email_data["in_reply_to"]

    # Stage change
    if result.get("stage_changed") and result.get("detected_stage"):
        updates["stage"] = result["detected_stage"]

    db.update_user(user["id"], updates)

    logger.info(f"Processed email from {from_email}: status={result['status']}, confidence={result['confidence']}")
    return conversation
