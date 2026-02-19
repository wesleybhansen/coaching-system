"""AI service router — delegates to the correct provider based on settings."""

import logging

from db import supabase_client as db

logger = logging.getLogger(__name__)

PROVIDERS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-5.2"],
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-opus-4-5-20250918"],
}


def get_ai_config() -> tuple:
    """Read ai_provider and ai_model from settings. Validate and return (provider, model)."""
    provider = db.get_setting("ai_provider", "openai")
    model = db.get_setting("ai_model", "gpt-4o")

    # Validate provider
    if provider not in PROVIDERS:
        logger.warning(f"Unknown AI provider '{provider}', falling back to openai")
        provider = "openai"

    # Validate model belongs to provider
    if model not in PROVIDERS[provider]:
        logger.warning(f"Model '{model}' not valid for {provider}, using default")
        model = PROVIDERS[provider][0]

    return provider, model


def generate_response(user_context: str) -> str:
    """Generate a coaching response using the configured AI provider."""
    provider, model = get_ai_config()

    if provider == "anthropic":
        from services import anthropic_service
        return anthropic_service.generate_response(user_context, model=model)
    else:
        from services import openai_service
        return openai_service.generate_response(user_context, model=model)


def generate_checkin_question(user_context: str) -> str:
    """Generate a personalized check-in question using the configured AI provider."""
    provider, model = get_ai_config()

    if provider == "anthropic":
        from services import anthropic_service
        return anthropic_service.generate_checkin_question(user_context, model=model)
    else:
        from services import openai_service
        return openai_service.generate_checkin_question(user_context, model=model)
