"""Tests for AI response evaluation and routing logic.

Covers: confidence scoring, flag routing, JSON parse failures, threshold behavior.
"""

from unittest.mock import MagicMock
from tests.conftest import make_user
from services import coaching_service


class TestConfidenceRouting:
    """Test that confidence scores route conversations correctly."""

    def test_high_confidence_no_flag_pending_review_with_default_threshold(
        self, mock_db, mock_openai, mock_gmail
    ):
        """Default threshold is 10, so even confidence=9 goes to Pending Review."""
        user = make_user()
        mock_db["users"].append(user)
        mock_openai["evaluate_response"].return_value = {
            "confidence": 9,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Pending Review"

    def test_confidence_meets_threshold_approved(self, mock_db, mock_openai, mock_gmail):
        """If threshold is lowered to 7, confidence=7 should auto-approve."""
        user = make_user()
        mock_db["users"].append(user)
        mock_db["settings"]["global_auto_approve_threshold"] = "7"
        mock_openai["evaluate_response"].return_value = {
            "confidence": 7,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Approved"
        assert result["approved_by"] == "auto"

    def test_confidence_below_threshold_pending_review(self, mock_db, mock_openai, mock_gmail):
        user = make_user()
        mock_db["users"].append(user)
        mock_db["settings"]["global_auto_approve_threshold"] = "7"
        mock_openai["evaluate_response"].return_value = {
            "confidence": 5,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Pending Review"

    def test_user_threshold_overrides_global(self, mock_db, mock_openai, mock_gmail):
        """Per-user threshold takes precedence over global threshold."""
        user = make_user(auto_approve_threshold=6)
        mock_db["users"].append(user)
        mock_db["settings"]["global_auto_approve_threshold"] = "10"
        mock_openai["evaluate_response"].return_value = {
            "confidence": 6,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Approved"


class TestFlagRouting:
    """Test that flagged responses always route to Flagged, regardless of confidence."""

    def test_flag_overrides_high_confidence(self, mock_db, mock_openai, mock_gmail):
        user = make_user()
        mock_db["users"].append(user)
        mock_db["settings"]["global_auto_approve_threshold"] = "5"
        mock_openai["evaluate_response"].return_value = {
            "confidence": 9,
            "flag": True,
            "flag_reason": "User mentioned self-harm",
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Flagged"
        assert result["flag_reason"] == "User mentioned self-harm"

    def test_flag_with_low_confidence(self, mock_db, mock_openai, mock_gmail):
        user = make_user()
        mock_db["users"].append(user)
        mock_openai["evaluate_response"].return_value = {
            "confidence": 2,
            "flag": True,
            "flag_reason": "Topic outside scope",
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Flagged"


class TestDefaultThreshold:
    """Default threshold of 10 means nothing auto-approves."""

    def test_max_confidence_still_pending_with_default_threshold(
        self, mock_db, mock_openai, mock_gmail
    ):
        user = make_user()
        mock_db["users"].append(user)
        # Default threshold is 10
        mock_openai["evaluate_response"].return_value = {
            "confidence": 9,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Pending Review"

    def test_confidence_10_approved_with_default_threshold(
        self, mock_db, mock_openai, mock_gmail
    ):
        user = make_user()
        mock_db["users"].append(user)
        mock_openai["evaluate_response"].return_value = {
            "confidence": 10,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "test message")

        assert result["status"] == "Approved"


class TestStageDetection:
    """Test that stage changes from evaluation are captured."""

    def test_stage_change_detected(self, mock_db, mock_openai, mock_gmail):
        user = make_user(stage="Ideation")
        mock_db["users"].append(user)
        mock_openai["evaluate_response"].return_value = {
            "confidence": 7,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Early Validation",
            "stage_changed": True,
            "resource_referenced": None,
            "summary_update": None,
        }

        result = coaching_service.generate_and_evaluate(user, "I found paying customers")

        assert result["detected_stage"] == "Early Validation"
        assert result["stage_changed"] is True
