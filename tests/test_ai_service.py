"""Tests for the AI service router.

Covers: provider routing, fallback behavior, model validation.
"""

from unittest.mock import MagicMock, patch

from tests.conftest import make_user
from services import ai_service


class TestAIServiceRouting:
    """Test that ai_service routes to the correct provider."""

    def test_default_routes_to_openai(self, mock_db, mock_openai):
        """Default settings (openai / gpt-4o) should call openai_service."""
        result = ai_service.generate_response("test context")
        mock_openai["generate_response"].assert_called_once()
        assert result == "Great progress! Keep focusing on customer discovery."

    def test_anthropic_routes_to_anthropic(self, mock_db, mock_anthropic):
        """When provider is anthropic, should call anthropic_service."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        result = ai_service.generate_response("test context")
        mock_anthropic["generate_response"].assert_called_once()
        assert result == "Great progress! Keep focusing on customer discovery."

    def test_checkin_routes_to_openai_by_default(self, mock_db, mock_openai):
        """Check-in generation defaults to OpenAI."""
        result = ai_service.generate_checkin_question("test context")
        mock_openai["generate_checkin_question"].assert_called_once()

    def test_checkin_routes_to_anthropic(self, mock_db, mock_anthropic):
        """Check-in generation routes to Anthropic when configured."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        result = ai_service.generate_checkin_question("test context")
        mock_anthropic["generate_checkin_question"].assert_called_once()

    def test_invalid_provider_falls_back_to_openai(self, mock_db, mock_openai):
        """Unknown provider should fall back to openai."""
        mock_db["settings"]["ai_provider"] = "deepseek"
        mock_db["settings"]["ai_model"] = "gpt-4o"

        result = ai_service.generate_response("test context")
        mock_openai["generate_response"].assert_called_once()

    def test_invalid_model_falls_back_to_provider_default(self, mock_db, mock_openai):
        """Unknown model for a provider should fall back to provider's first model."""
        mock_db["settings"]["ai_provider"] = "openai"
        mock_db["settings"]["ai_model"] = "nonexistent-model"

        result = ai_service.generate_response("test context")
        # Should still work — falls back to gpt-4o
        call_kwargs = mock_openai["generate_response"].call_args
        assert call_kwargs[1]["model"] == "gpt-4o"

    def test_model_passed_to_openai(self, mock_db, mock_openai):
        """The model setting should be passed through to openai_service."""
        mock_db["settings"]["ai_model"] = "gpt-4o-mini"

        ai_service.generate_response("test context")
        call_kwargs = mock_openai["generate_response"].call_args
        assert call_kwargs[1]["model"] == "gpt-4o-mini"

    def test_model_passed_to_anthropic(self, mock_db, mock_anthropic):
        """The model setting should be passed through to anthropic_service."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-opus-4-6"

        ai_service.generate_response("test context")
        call_kwargs = mock_anthropic["generate_response"].call_args
        assert call_kwargs[1]["model"] == "claude-opus-4-6"


class TestGetAIConfig:
    """Test the config validation logic."""

    def test_returns_defaults(self, mock_db):
        provider, model = ai_service.get_ai_config()
        assert provider == "openai"
        assert model == "gpt-4o"

    def test_returns_anthropic_config(self, mock_db):
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        provider, model = ai_service.get_ai_config()
        assert provider == "anthropic"
        assert model == "claude-sonnet-4-6"

    def test_invalid_provider_returns_openai(self, mock_db):
        mock_db["settings"]["ai_provider"] = "banana"

        provider, model = ai_service.get_ai_config()
        assert provider == "openai"

    def test_mismatched_model_returns_provider_default(self, mock_db):
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "gpt-4o"  # OpenAI model with Anthropic provider

        provider, model = ai_service.get_ai_config()
        assert provider == "anthropic"
        assert model == "claude-sonnet-4-6"  # Falls back to first Anthropic model
