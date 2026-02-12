"""Tests for email processing logic (coaching_service.process_email).

Covers: new users, known users, pause/resume, duplicates, junk filtering, self-emails.
"""

from tests.conftest import make_user, make_email, make_conversation
from services import coaching_service


class TestNewUserOnboarding:
    """When an email arrives from an unknown address, system should create
    a new user and draft an onboarding message in Pending Review."""

    def test_creates_user_and_onboarding_conversation(self, mock_db, mock_openai, mock_gmail):
        email = make_email(from_email="newperson@example.com", from_name="New Person")

        coaching_service.process_email(email)

        # User was created
        assert len(mock_db["users"]) == 1
        assert mock_db["users"][0]["email"] == "newperson@example.com"

        # Onboarding conversation created in Pending Review
        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Onboarding"
        assert conv["status"] == "Pending Review"

    def test_new_user_first_name_extracted(self, mock_db, mock_openai, mock_gmail):
        email = make_email(from_email="jane@example.com", from_name="Jane Doe")

        coaching_service.process_email(email)

        assert mock_db["users"][0]["first_name"] == "Jane"

    def test_new_user_no_name_defaults_to_there(self, mock_db, mock_openai, mock_gmail):
        email = make_email(from_email="anon@example.com", from_name="")

        coaching_service.process_email(email)

        assert mock_db["users"][0]["first_name"] == "there"


class TestKnownUserNormalMessage:
    """When a known active user sends a normal message, system should parse it,
    generate an AI response, evaluate it, and create a conversation."""

    def test_creates_conversation_with_ai_response(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        email = make_email(from_email="alice@example.com",
                           body="I validated my idea with 5 customers this week.")

        coaching_service.process_email(email)

        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["user_id"] == user["id"]
        assert conv["ai_response"] is not None
        assert conv["status"] in ("Pending Review", "Approved", "Flagged")

    def test_updates_user_last_response_date(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com", last_response_date=None)
        mock_db["users"].append(user)

        email = make_email(from_email="alice@example.com")
        coaching_service.process_email(email)

        assert user["last_response_date"] is not None


class TestPauseResume:
    """Pause/resume keywords should change user status and create
    appropriate conversations in Pending Review."""

    def test_pause_keyword_sets_user_to_paused(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="bob@example.com", status="Active")
        mock_db["users"].append(user)

        email = make_email(from_email="bob@example.com", body="I need to take a break")

        coaching_service.process_email(email)

        assert user["status"] == "Paused"

    def test_pause_creates_pending_review_conversation(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="bob@example.com", status="Active")
        mock_db["users"].append(user)

        email = make_email(from_email="bob@example.com", body="pause")

        coaching_service.process_email(email)

        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["status"] == "Pending Review"
        assert "pause" in conv["ai_response"].lower()

    def test_resume_keyword_sets_user_to_active(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="bob@example.com", status="Paused")
        mock_db["users"].append(user)

        email = make_email(from_email="bob@example.com", body="I'm back")

        coaching_service.process_email(email)

        assert user["status"] == "Active"

    def test_resume_creates_pending_review_conversation(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="bob@example.com", status="Paused")
        mock_db["users"].append(user)

        email = make_email(from_email="bob@example.com", body="resume")

        coaching_service.process_email(email)

        conv = mock_db["conversations"][0]
        assert conv["status"] == "Pending Review"
        assert "resume" in conv["ai_response"].lower() or "welcome back" in conv["ai_response"].lower()

    def test_resume_takes_priority_over_pause(self, mock_db, mock_openai, mock_gmail):
        """If message contains both pause and resume keywords, resume wins."""
        user = make_user(email="bob@example.com", status="Paused")
        mock_db["users"].append(user)

        email = make_email(from_email="bob@example.com",
                           body="I took a break but I'm back and ready to resume")

        coaching_service.process_email(email)

        assert user["status"] == "Active"


class TestDuplicateEmails:
    """If we already processed a Gmail message ID, skip it."""

    def test_duplicate_message_id_is_skipped(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        msg_id = "<duplicate-123@gmail.com>"
        mock_db["conversations"].append(
            make_conversation(gmail_message_id=msg_id, user_id=user["id"])
        )

        email = make_email(from_email="alice@example.com", message_id=msg_id)

        result = coaching_service.process_email(email)

        assert result is None
        # Should still only have the original conversation
        assert len(mock_db["conversations"]) == 1


class TestJunkEmailFiltering:
    """Gmail service should filter out system/no-reply emails.
    These tests verify the _is_ignored_sender logic."""

    def test_noreply_is_ignored(self):
        from services.gmail_service import _is_ignored_sender
        assert _is_ignored_sender("noreply@google.com") is True

    def test_no_reply_hyphen_is_ignored(self):
        from services.gmail_service import _is_ignored_sender
        assert _is_ignored_sender("no-reply@workspace.com") is True

    def test_mailer_daemon_is_ignored(self):
        from services.gmail_service import _is_ignored_sender
        assert _is_ignored_sender("mailer-daemon@gmail.com") is True

    def test_normal_email_not_ignored(self):
        from services.gmail_service import _is_ignored_sender
        assert _is_ignored_sender("alice@example.com") is False

    def test_notifications_is_ignored(self):
        from services.gmail_service import _is_ignored_sender
        assert _is_ignored_sender("notifications@github.com") is True


class TestIntentDetection:
    """Test the pause/resume keyword detection logic."""

    def test_normal_message(self):
        assert coaching_service.detect_intent("I worked on my business plan") == "normal"

    def test_pause_keyword(self):
        assert coaching_service.detect_intent("I want to pause") == "pause"

    def test_stop_keyword(self):
        assert coaching_service.detect_intent("Please stop sending emails") == "pause"

    def test_resume_keyword(self):
        assert coaching_service.detect_intent("resume") == "resume"

    def test_im_back_keyword(self):
        assert coaching_service.detect_intent("Hey, I'm back!") == "resume"

    def test_case_insensitive(self):
        assert coaching_service.detect_intent("PAUSE") == "pause"
        assert coaching_service.detect_intent("RESUME") == "resume"
