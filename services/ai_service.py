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


def _extract_user_message(user_context: str) -> str:
    """Extract the user's current message from the assembled context string."""
    marker = "## Their Current Message\n"
    if marker in user_context:
        after = user_context.split(marker, 1)[1]
        # The message ends at the next section header or end of string
        next_section = after.find("\n## ")
        if next_section != -1:
            return after[:next_section].strip()
        return after.strip()
    return ""


def generate_response(user_context: str, user: dict = None) -> str:
    """Generate a coaching response using the configured AI provider.

    Args:
        user_context: The assembled coaching context string
        user: Optional user dict — used to build retrieval query for Anthropic's RAG
    """
    provider, model = get_ai_config()

    if provider == "anthropic":
        from services import anthropic_service

        knowledge_context = ""
        if user:
            try:
                from services import knowledge_service
                parsed_message = _extract_user_message(user_context)
                if parsed_message:
                    query = knowledge_service.build_retrieval_query(user, parsed_message)
                    chunks = knowledge_service.retrieve_relevant_chunks(
                        query, match_count=5, stage_filter=user.get("stage")
                    )
                    knowledge_context = knowledge_service.format_chunks_for_prompt(chunks)
            except Exception as e:
                logger.warning(f"Knowledge retrieval failed, continuing without RAG: {e}")

        return anthropic_service.generate_response(user_context, model=model, knowledge_context=knowledge_context)
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
