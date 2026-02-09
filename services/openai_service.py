import json
import logging
import os
from openai import OpenAI

import config

logger = logging.getLogger(__name__)

_client = None
_instructions = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
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


def generate_response(user_context: str) -> str:
    """Generate a coaching response using the Responses API with file_search.

    Args:
        user_context: Formatted string with user info, history, model responses,
                      corrections, and the current message.

    Returns:
        The assistant's text response (natural language, not JSON).
    """
    client = get_client()

    response = client.responses.create(
        model="gpt-4o",
        instructions=_get_instructions(),
        input=user_context,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [config.VECTOR_STORE_ID],
        }],
        temperature=0.7,
    )

    return response.output_text


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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()


def parse_email_fallback(raw_email: str) -> str:
    """Fallback email parser using GPT-4o-mini when the deterministic parser returns empty."""
    client = get_client()

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
