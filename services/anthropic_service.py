"""Anthropic (Claude) service for coaching response generation."""

import logging
import os
import time

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

_client = None
_instructions = None


def get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            timeout=120.0,
            max_retries=0,
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
    """Retry an API call with exponential backoff."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Anthropic API call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Anthropic API call failed after {MAX_RETRIES} attempts: {e}")
    raise last_error


def generate_response(user_context: str, model: str = "claude-sonnet-4-6", knowledge_context: str = "") -> str:
    """Generate a coaching response using Claude.

    Args:
        user_context: The assembled coaching context (user info, history, message)
        model: Claude model to use
        knowledge_context: Optional formatted excerpts from Wes's books/lectures
    """
    client = get_client()

    system_prompt = _get_instructions()
    if knowledge_context:
        system_prompt += f"\n\n## Reference Material from Your Books and Lectures\nUse these excerpts to ground your response in your actual teaching. Reference sources naturally (e.g. 'I talk about this in Lecture 7' or 'Chapter 3 of The Launch System covers this'). Do NOT quote them verbatim — paraphrase in your own voice.\n\n{knowledge_context}"

    def _call():
        message = client.messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_context}],
            temperature=0.7,
            max_tokens=1500,
        )
        return message.content[0].text

    return _retry_with_backoff(_call)


def generate_checkin_question(user_context: str, model: str = "claude-sonnet-4-6") -> str:
    """Generate a personalized check-in question using Claude."""
    client = get_client()

    prompt = f"""You are Wes, an entrepreneurship coach. Generate a personalized check-in message for this member.
Keep it short (2-4 sentences). Reference what they've been working on recently. Ask a specific question that moves them forward.
Do NOT use bullet points or numbered lists. Write in a natural, conversational tone.
Do NOT include a sign-off like "Wes" - that will be added automatically.

{user_context}"""

    def _call():
        message = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return message.content[0].text

    return _retry_with_backoff(_call)
