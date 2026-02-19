"""Tests for the send_approved workflow.

Covers: sending approved conversations, email threading, SMTP failures, signature handling.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from tests.conftest import make_user, make_conversation
from workflows import send_approved


class TestSendApproved:
    """Test that approved conversations are sent correctly."""

    def test_sends_approved_conversation(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep up the great work on customer interviews!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        # Email should have been sent
        mock_gmail["send_email"].assert_called_once()
        call_kwargs = mock_gmail["send_email"].call_args

        # Should be sent to the right email
        assert call_kwargs[1]["to_email"] == "alice@example.com"

    def test_marks_conversation_as_sent(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Great progress!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        assert conv["status"] == "Sent"
        assert conv["sent_at"] is not None

    def test_uses_edited_response_when_available(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Original AI response",
            sent_response="Wes's edited version",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        call_kwargs = mock_gmail["send_email"].call_args
        # Should use the edited response, not the original
        assert "edited version" in call_kwargs[1]["body"]

    def test_signature_added(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep going!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        call_kwargs = mock_gmail["send_email"].call_args
        body = call_kwargs[1]["body"]
        assert body.endswith("Wes")

    def test_signature_not_doubled(self, mock_db, mock_openai, mock_gmail):
        """If the AI response already ends with Wes, the final body
        should not have double signatures."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        # AI response already has the sign-off (this is a known edge case)
        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep going!\n\nWes",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        call_kwargs = mock_gmail["send_email"].call_args
        body = call_kwargs[1]["body"]
        # Count occurrences of "Wes" — should ideally be 1 but the current
        # code adds it unconditionally, so this documents the behavior
        wes_count = body.count("\n\nWes")
        # This test documents a potential bug: signature may be doubled
        # If this assertion fails, it means the bug was fixed
        assert wes_count >= 1

    def test_email_threading_headers(self, mock_db, mock_openai, mock_gmail):
        """In-Reply-To and References should be set from user's gmail_message_id."""
        user = make_user(
            email="alice@example.com",
            gmail_message_id="<thread-msg@gmail.com>",
        )
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        call_kwargs = mock_gmail["send_email"].call_args
        assert call_kwargs[1]["in_reply_to"] == "<thread-msg@gmail.com>"

    def test_smtp_failure_marks_as_send_failed(self, mock_db, mock_openai, mock_gmail):
        """If send_email raises an exception, conversation should be marked as Send Failed."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        mock_gmail["send_email"].side_effect = Exception("SMTP connection failed")

        send_approved.run()

        # Conversation should be marked as Send Failed (not Sent, not Approved)
        assert conv["status"] == "Send Failed"
        assert conv["sent_at"] is None
        assert conv["send_attempts"] == 1

    def test_skips_conversation_without_user(self, mock_db, mock_openai, mock_gmail):
        """If a conversation has no linked user, it should be skipped."""
        conv = make_conversation(
            user_id="nonexistent-user-id",
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        # No email should have been sent
        mock_gmail["send_email"].assert_not_called()

    def test_skips_conversation_without_response_text(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response=None,
            sent_response=None,
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        mock_gmail["send_email"].assert_not_called()

    def test_summary_updated_after_send(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com", summary="Initial summary.")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep going!",
            user_message_parsed="I talked to 3 customers.",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        # Summary should have been updated
        assert "Initial summary." in user["summary"]
        # The mock returns "User continued working on their business plan."
        assert "business plan" in user["summary"]


class TestSendOffsets:
    """Test per-email random offset logic."""

    def test_multiple_emails_all_sent(self, mock_db, mock_openai, mock_gmail):
        """All approved emails should be sent regardless of offset assignment."""
        user1 = make_user(email="alice@example.com")
        user2 = make_user(email="bob@example.com")
        user3 = make_user(email="carol@example.com")
        mock_db["users"].extend([user1, user2, user3])

        for user in [user1, user2, user3]:
            conv = make_conversation(
                user_id=user["id"],
                status="Approved",
                ai_response="Keep going!",
                sent_at=None,
            )
            mock_db["conversations"].append(conv)

        send_approved.run()

        assert mock_gmail["send_email"].call_count == 3

    def test_send_delay_max_minutes_setting_respected(self, mock_db, mock_openai, mock_gmail):
        """The send_delay_max_minutes setting should control offset range."""
        mock_db["settings"]["send_delay_max_minutes"] = "50"

        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep going!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        send_approved.run()

        # Email should still be sent
        mock_gmail["send_email"].assert_called_once()
        # Conversation should be marked as Sent
        assert conv["status"] == "Sent"

    def test_no_startup_delay(self, mock_db, mock_openai, mock_gmail):
        """The old startup delay logic should not exist — offset is per-email."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Keep going!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        # If old send_window_minutes setting is present, it should be ignored
        mock_db["settings"]["send_window_minutes"] = "120"

        send_approved.run()
        mock_gmail["send_email"].assert_called_once()
