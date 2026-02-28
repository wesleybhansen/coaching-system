from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone

from email_reply_parser import EmailReplyParser

from db import supabase_client as db
from services import openai_service, gmail_service, ai_service

logger = logging.getLogger(__name__)


def _generate_dedup_key(email_data: dict) -> str:
    """Generate a synthetic dedup key from email content when Message-ID is missing.

    Creates a hash from (from_email, subject, first 500 chars of body) to prevent
    the same email from being processed multiple times.
    """
    raw = f"{email_data.get('from_email', '')}|{email_data.get('subject', '')}|{email_data.get('body', '')[:500]}"
    return f"synthetic-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"

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
    """Detect if the message is a pause, resume, or normal message.

    Short messages (<= 20 words) use keyword matching only.
    Longer messages with keywords get AI confirmation to avoid false positives
    (e.g. "I need to stop overthinking and just start" isn't a pause request).
    """
    lower = message.lower().strip()

    is_pause = any(kw in lower for kw in PAUSE_KEYWORDS)
    is_resume = any(kw in lower for kw in RESUME_KEYWORDS)

    if is_resume:
        keyword_intent = "resume"
    elif is_pause:
        keyword_intent = "pause"
    else:
        return "normal"

    # Short messages: trust keyword detection directly
    word_count = len(message.split())
    if word_count <= 20:
        return keyword_intent

    # Longer messages: confirm with AI to avoid false positives
    if openai_service.confirm_intent(message, keyword_intent):
        return keyword_intent
    return "normal"


# ── Stage-Specific Coaching Prompts ───────────────────────────

STAGE_PROMPTS = {
    "Ideation": """## Stage-Specific Guidance (Ideation)
This user is in the Ideation stage. They need help with:
- Finding problems worth solving through conversations (not brainstorming)
- Getting out of their head and talking to real people
- Picking ONE idea to explore rather than juggling many
- Having their first customer discovery conversations
Key challenge: They may be stuck in analysis paralysis or avoiding real conversations.""",

    "Early Validation": """## Stage-Specific Guidance (Early Validation)
This user is in Early Validation. They need help with:
- Conducting structured problem interviews (not just casual chats)
- Testing willingness to pay before building
- Creating a minimum viable offer (manual before automated)
- Getting their first paying customer
Key challenge: They may want to skip ahead to building or get distracted by marketing too early.""",

    "Late Validation": """## Stage-Specific Guidance (Late Validation)
This user is in Late Validation. They need help with:
- Reducing churn and increasing customer value
- Systematizing what's working before scaling
- Understanding their unit economics
- Focusing on ONE growth channel before expanding
Key challenge: They may be doing too many things at once or avoiding hard conversations about churn.""",

    "Growth": """## Stage-Specific Guidance (Growth)
This user is in the Growth stage. They need help with:
- Hiring and delegation decisions
- Building repeatable sales processes
- Managing team and operations at scale
- Knowing when and how to raise capital
Key challenge: They may be building features instead of selling, or spreading too thin across initiatives.""",
}


# ── Context Building ───────────────────────────────────────────

def build_assistant_context(user: dict, parsed_message: str, message_type: str = "check-in response") -> str:
    """Build the full context string to send to the OpenAI Assistant."""
    # Recent conversations
    recent = db.get_recent_conversations(user["id"], limit=5)
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

    # Recent corrections (scoped to user's stage)
    corrections = db.get_recent_corrections(limit=10, stage=user.get("stage"))
    corrected_text = "\n\n---\n\n".join(
        f"AI originally wrote: {c['ai_response']}\nWes corrected it to: {c['corrected_response']}\nBecause: {c.get('correction_notes', 'N/A')}"
        for c in corrections
    ) if corrections else "No corrections to learn from yet"

    # Available resources for their stage
    resource_list = db.get_resource_list_for_prompt(user.get("stage"))

    stage_prompt = STAGE_PROMPTS.get(user.get("stage", "Ideation"), "")

    context = f"""{stage_prompt}

## Context About This User
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

## Available Resources (reference by name only — do NOT include links or URLs)
{resource_list}

## Model Responses (examples of your ideal coaching style)
{model_text}

## Corrected Responses (learn from these)
{corrected_text}

## Instructions
Write a short coaching response (1-3 paragraphs). Focus on 1-2 key points maximum. If relevant, point them to a specific resource BY NAME (e.g. "Lecture 7 walks through this" or "Chapter 3 of the Launch System covers this well"). NEVER include links, URLs, or attachments. Keep it conversational and human. Do NOT include a sign-off like "Wes" - that will be added automatically. Do NOT wrap your response in JSON or code blocks - just write the natural language coaching response."""

    return context


# ── Response Generation Pipeline ───────────────────────────────

def generate_and_evaluate(user: dict, parsed_message: str, message_type: str = "check-in response") -> dict:
    """Full pipeline: generate response, evaluate it, determine routing.

    Returns dict with: ai_response, confidence, flag, flag_reason,
    detected_stage, stage_changed, resource_referenced, summary_update, status
    """
    # Build context and generate response
    context = build_assistant_context(user, parsed_message, message_type)
    ai_response = ai_service.generate_response(context, user=user)

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
        "evaluation_details": evaluation.get("sub_scores"),
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

    # If Message-ID header is missing, generate a synthetic one for dedup
    if not message_id:
        message_id = _generate_dedup_key(email_data)
        email_data["message_id"] = message_id
        logger.info(f"No Message-ID header, using synthetic key: {message_id}")

    # Skip if we already processed this message
    if db.conversation_exists_for_message(message_id):
        logger.info(f"Already processed message {message_id}, skipping")
        return None

    # Block system/support addresses from becoming users
    email_prefix = from_email.split("@")[0].lower()
    if email_prefix in ("noreply", "no-reply", "no_reply", "support"):
        logger.info(f"Ignoring system address: {from_email}")
        return None

    # Find user — invite-only model, no auto-creation
    user = db.get_user_by_email(from_email)
    if not user:
        # Ignore emails from unknown senders.
        # The cleanup workflow will flag these after 24h as a safety net.
        logger.info(f"Ignoring email from unknown sender: {from_email}")
        return None

    # Handle multi-step onboarding
    if user.get("status") == "Onboarding":
        onboarding_step = user.get("onboarding_step", 1)
        parsed = parse_email(raw_body)

        if onboarding_step <= 1:
            # They replied with their stage/idea — process it and ask for challenge
            followup_body = f"Thanks {user.get('first_name', 'there')}! That helps a lot.\n\nOne more thing before we get started: What's the single biggest challenge or question you're facing right now with your business?\n\nOnce I know that, I'll start sending you focused check-ins."
            db.create_conversation({
                "user_id": user["id"],
                "type": "Onboarding",
                "user_message_raw": raw_body,
                "user_message_parsed": parsed,
                "ai_response": followup_body,
                "confidence": 8,
                "gmail_message_id": message_id or None,
                "status": "Pending Review",
            })
            db.update_user(user["id"], {"onboarding_step": 2})
            logger.info(f"Onboarding step 2 for {from_email} — awaiting review")
            return None
        else:
            # They replied with their challenge — activate them
            db.update_user(user["id"], {
                "status": "Active",
                "onboarding_step": 3,
                "current_challenge": parsed[:500],
                "last_response_date": datetime.now(timezone.utc).isoformat(),
                "gmail_message_id": email_data.get("message_id"),
            })

            welcome_body = f"You're all set, {user.get('first_name', 'there')}. I'll start checking in regularly.\n\nIn the meantime, here's your first nudge: based on what you told me, what's the ONE thing you could do this week to make progress on that challenge?\n\nKeep it small and specific."
            db.create_conversation({
                "user_id": user["id"],
                "type": "Onboarding",
                "user_message_raw": raw_body,
                "user_message_parsed": parsed,
                "ai_response": welcome_body,
                "confidence": 8,
                "gmail_message_id": message_id or None,
                "status": "Pending Review",
            })
            logger.info(f"Onboarding complete for {from_email} — activated, awaiting review")
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

    # Check thread reply cap (max 4 follow-up replies per check-in cycle)
    try:
        max_thread_replies = int(db.get_setting("max_thread_replies", "4"))
    except (ValueError, TypeError):
        max_thread_replies = 4
    current_replies = db.count_thread_replies(user["id"])
    if current_replies >= max_thread_replies:
        logger.info(f"Thread reply cap ({max_thread_replies}) reached for {from_email}, creating wrap-up")
        first_name = user.get("first_name", "there")
        wrap_up_body = f"Great conversation so far, {first_name}! I'll pick this up in your next check-in. Keep the momentum going in the meantime."
        db.create_conversation({
            "user_id": user["id"],
            "type": "Follow-up",
            "user_message_raw": raw_body,
            "user_message_parsed": parsed,
            "status": "Pending Review",
            "ai_response": wrap_up_body,
            "confidence": 8,
            "flag_reason": f"Thread reply cap ({max_thread_replies}) reached",
            "gmail_message_id": message_id or None,
        })
        # Still update the user's last_response_date so we know they're active
        db.update_user(user["id"], {
            "last_response_date": datetime.now(timezone.utc).isoformat(),
            "gmail_message_id": email_data.get("message_id"),
        })
        return None

    # Determine message type
    recent = db.get_recent_conversations(user["id"], limit=1)
    message_type = "follow-up question" if recent else "check-in response"

    # Generate and evaluate response
    result = generate_and_evaluate(user, parsed, message_type)

    # Analyze member satisfaction/engagement
    try:
        satisfaction = openai_service.analyze_satisfaction(parsed)
    except Exception as e:
        logger.warning(f"Failed to analyze satisfaction for {from_email}: {e}")
        satisfaction = None

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
        "satisfaction_score": satisfaction,
        "evaluation_details": result.get("evaluation_details"),
    })

    # Update user metadata
    updates = {
        "last_response_date": datetime.now(timezone.utc).isoformat(),
        "gmail_message_id": email_data.get("message_id"),
    }
    if email_data.get("in_reply_to"):
        updates["gmail_thread_id"] = email_data["in_reply_to"]

    # Check for stage change milestone
    if result.get("stage_changed") and result.get("detected_stage"):
        updates["stage"] = result["detected_stage"]
        # Log milestone for celebration in next interaction
        milestone_note = f"MILESTONE: Progressed from {user.get('stage')} to {result['detected_stage']}"
        current_summary = user.get("summary") or ""
        date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        updates["summary"] = f"{current_summary}\n\n{date_prefix}: {milestone_note}".strip()

    # Update user satisfaction score (rolling average)
    if satisfaction is not None:
        current_satisfaction = user.get("satisfaction_score")
        if current_satisfaction is not None:
            try:
                new_satisfaction = round((float(current_satisfaction) * 0.7) + (satisfaction * 0.3), 1)
            except (ValueError, TypeError):
                new_satisfaction = satisfaction
        else:
            new_satisfaction = satisfaction
        updates["satisfaction_score"] = new_satisfaction

    db.update_user(user["id"], updates)

    logger.info(f"Processed email from {from_email}: status={result['status']}, confidence={result['confidence']}")
    return conversation
