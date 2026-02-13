import json
import logging
import os
import time
from openai import OpenAI

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds, doubles each retry

_client = None
_instructions = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=120.0,       # 120s total request timeout
            max_retries=0,       # We handle retries ourselves via _retry_with_backoff
        )
    return _client


def _get_instructions() -> str:
    """Load and cache the assistant instructions from the prompts file."""
    global _instructions
    if _instructions is None:
        instructions_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "assistant_instructions.md"
        )
        with open(instructions_path) as f:
            _instructions = f.read()
    return _instructions


def _retry_with_backoff(func, *args, **kwargs):
    """Retry an OpenAI API call with exponential backoff."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"OpenAI API call failed after {MAX_RETRIES} attempts: {e}")
    raise last_error


def generate_response(user_context: str) -> str:
    """Generate a coaching response using the Responses API with file_search."""
    client = get_client()

    def _call():
        response = client.responses.create(
            model="gpt-4o",
            instructions=_get_instructions(),
            input=user_context,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [config.VECTOR_STORE_ID],
            }],
            temperature=0.7,
            max_output_tokens=1500,  # ~3 paragraphs of coaching response
        )
        return response.output_text

    return _retry_with_backoff(_call)


def evaluate_response(user_message: str, ai_response: str, user_stage: str,
                      evaluation_prompt: str) -> dict:
    """Evaluate a coaching response using GPT-4o-mini (cheap, fast).

    Returns structured evaluation:
        confidence (1-10), flag (bool), flag_reason, detected_stage,
        stage_changed (bool), resource_referenced, summary_update
    """
    client = get_client()

    full_prompt = evaluation_prompt.format(
        user_message=user_message,
        ai_response=ai_response,
        user_stage=user_stage,
    )

    def _call():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    text = _retry_with_backoff(_call)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse evaluation JSON: {text}")
        return {
            "confidence": 3,
            "flag": True,
            "flag_reason": "Failed to parse evaluation response",
            "detected_stage": user_stage,
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }


def generate_summary_update(current_summary: str, user_message: str,
                            coach_response: str) -> str:
    """Generate a brief summary update to append to the user's journey summary."""
    client = get_client()

    prompt = f"""You are helping update a user's coaching summary. Based on the recent exchange below, provide a brief 1-2 sentence update to add to their ongoing summary.

Current Summary:
{current_summary or 'No previous summary'}

User's Message:
{user_message}

Coach's Response:
{coach_response}

Provide only the new summary text to append (1-2 sentences). Focus on key progress, challenges, or direction changes."""

    def _call():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def parse_email_fallback(raw_email: str) -> str:
    """Fallback email parser using GPT-4o-mini when the deterministic parser returns empty."""
    client = get_client()

    def _call():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Extract only the user's actual message from this email. Remove:
- Email signatures
- Previous quoted messages (lines starting with >)
- "On [date], [person] wrote:" headers
- Confidentiality disclaimers
- "Sent from my iPhone" footers
- Any other boilerplate

Return only the user's new content, preserving their formatting.

Email:
{raw_email}"""
            }],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def generate_checkin_question(user_context: str) -> str:
    """Generate a personalized check-in question based on user context."""
    client = get_client()

    prompt = f"""You are Wes, an entrepreneurship coach. Generate a personalized check-in message for this member.
Keep it short (2-4 sentences). Reference what they've been working on recently. Ask a specific question that moves them forward.
Do NOT use bullet points or numbered lists. Write in a natural, conversational tone.
Do NOT include a sign-off like "Wes" - that will be added automatically.

{user_context}"""

    def _call():
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def analyze_satisfaction(user_message: str) -> float:
    """Analyze the satisfaction/engagement level of a user's reply.

    Returns a score from 1-10:
    - 1-3: Disengaged (short, dismissive, frustrated)
    - 4-6: Neutral (going through the motions)
    - 7-10: Engaged (detailed, enthusiastic, taking action)
    """
    client = get_client()

    prompt = f"""Analyze this coaching program member's email reply for engagement and satisfaction level.

Reply: {user_message}

Score from 1-10 where:
- 1-3: Disengaged, frustrated, or dismissive (e.g., "ok", "thanks", "not really")
- 4-6: Neutral, going through the motions (e.g., brief answers without enthusiasm)
- 7-10: Engaged, taking action, detailed responses, showing progress

Return ONLY a number (1-10), nothing else."""

    def _call():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=5,
        )
        text = response.choices[0].message.content.strip()
        try:
            score = float(text)
            return max(1.0, min(10.0, score))
        except ValueError:
            return 5.0

    return _retry_with_backoff(_call)
