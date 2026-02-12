"""Tests for edge cases and error handling.

Covers: malformed emails, empty bodies, email parsing, OpenAI failures.
"""

from unittest.mock import MagicMock, patch
from tests.conftest import make_user, make_email
from services import coaching_service, gmail_service


class TestEmailParsing:
    """Test the email parsing logic handles edge cases."""

    def test_parse_strips_quoted_replies(self, mock_openai):
        """EmailReplyParser should strip quoted content."""
        raw = "This is my reply.\n\nOn Mon, Jan 1 someone wrote:\n> Original message"
        result = coaching_service.parse_email(raw)
        assert "This is my reply." in result
        assert "Original message" not in result

    def test_parse_empty_body_falls_back_to_gpt(self, mock_openai):
        """If the deterministic parser returns empty, fall back to GPT."""
        mock_openai["parse_email_fallback"].return_value = "Extracted content"

        result = coaching_service.parse_email("")

        mock_openai["parse_email_fallback"].assert_called_once()
        assert result == "Extracted content"

    def test_parse_very_short_body_falls_back_to_gpt(self, mock_openai):
        """Body shorter than 5 chars should trigger fallback."""
        mock_openai["parse_email_fallback"].return_value = "Extracted"

        result = coaching_service.parse_email("Hi")

        mock_openai["parse_email_fallback"].assert_called_once()


class TestMalformedEmails:
    """Test handling of malformed or unusual email data."""

    def test_empty_body_handled(self, mock_db, mock_openai, mock_gmail):
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        email = make_email(from_email="alice@example.com", body="")

        # Should not crash — the parse_email_fallback will handle it
        result = coaching_service.process_email(email)
        # It should either process or return None, but not crash

    def test_none_message_id_handled(self, mock_db, mock_openai, mock_gmail):
        """Email with empty message_id should still be processed."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        email = make_email(from_email="alice@example.com", message_id="")

        # Empty message_id means the duplicate check is skipped (falsy check)
        result = coaching_service.process_email(email)
        assert len(mock_db["conversations"]) == 1


class TestGmailExtractBody:
    """Test the _extract_body helper handles different email formats."""

    def test_plain_text_email(self):
        import email as email_lib
        msg = email_lib.message_from_string("Content-Type: text/plain\n\nHello world")
        result = gmail_service._extract_body(msg)
        assert "Hello world" in result

    def test_multipart_email_prefers_plain_text(self):
        import email as email_lib
        raw = """MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

--boundary
Content-Type: text/plain

Plain text version
--boundary
Content-Type: text/html

<p>HTML version</p>
--boundary--"""
        msg = email_lib.message_from_string(raw)
        result = gmail_service._extract_body(msg)
        assert "Plain text" in result

    def test_empty_multipart_returns_empty_string(self):
        import email as email_lib
        raw = """MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

--boundary--"""
        msg = email_lib.message_from_string(raw)
        result = gmail_service._extract_body(msg)
        assert result == ""


class TestOpenAIEvaluationFailure:
    """Test that JSON parse failures from the evaluator are handled safely."""

    def test_json_parse_failure_returns_flagged_defaults(self):
        """When GPT returns invalid JSON, evaluate_response should return
        safe defaults with flag=True."""
        from services import openai_service

        # Create a mock response that returns invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON at all"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(openai_service, "get_client", return_value=mock_client):
            result = openai_service.evaluate_response(
                user_message="test",
                ai_response="test response",
                user_stage="Ideation",
                evaluation_prompt="Evaluate: {user_message} {ai_response} {user_stage}",
            )

        assert result["flag"] is True
        assert result["confidence"] == 3
        assert "Failed to parse" in result["flag_reason"]


class TestProcessEmailWorkflow:
    """Test the full process_emails workflow."""

    def test_workflow_completes_with_no_emails(self, mock_db, mock_openai, mock_gmail):
        from workflows import process_emails
        mock_gmail["fetch_unread_emails"].return_value = []

        process_emails.run()

        # Workflow should complete successfully
        assert any(r["status"] == "completed" for r in mock_db["workflow_runs"])

    def test_workflow_marks_emails_as_read(self, mock_db, mock_openai, mock_gmail):
        from workflows import process_emails

        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        emails = [make_email(from_email="alice@example.com", imap_id="42")]
        mock_gmail["fetch_unread_emails"].return_value = emails

        process_emails.run()

        mock_gmail["mark_as_read"].assert_called_once_with("42")

    def test_workflow_error_does_not_crash(self, mock_db, mock_openai, mock_gmail):
        """If one email fails to process, the workflow should continue."""
        from workflows import process_emails

        # First email will fail, second should succeed
        emails = [
            make_email(from_email="bad@example.com", imap_id="1"),
            make_email(from_email="good@example.com", imap_id="2"),
        ]
        mock_gmail["fetch_unread_emails"].return_value = emails

        # Make the first email cause an error in process_email
        original_process = coaching_service.process_email
        call_count = [0]

        def flaky_process(email_data):
            call_count[0] += 1
            if email_data["from_email"] == "bad@example.com":
                raise ValueError("Simulated processing error")
            return original_process(email_data)

        import services.coaching_service as cs
        original_fn = cs.process_email
        cs.process_email = flaky_process

        try:
            process_emails.run()
        finally:
            cs.process_email = original_fn

        # Second email should have been processed (new user created)
        assert any(u["email"] == "good@example.com" for u in mock_db["users"])
        # First email should NOT be marked as read (so cleanup can catch it)
        # Second email SHOULD be marked as read
        assert mock_gmail["mark_as_read"].call_count == 1


class TestCleanupWorkflow:
    """Test the cleanup workflow handles missed emails."""

    def test_cleanup_flags_missed_known_user_email(self, mock_db, mock_openai, mock_gmail):
        from workflows import cleanup

        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        missed_email = make_email(
            from_email="alice@example.com",
            imap_id="99",
            message_id="<missed@gmail.com>",
        )
        mock_gmail["fetch_old_unread_emails"].return_value = [missed_email]

        cleanup.run()

        flagged = [c for c in mock_db["conversations"] if c["status"] == "Flagged"]
        assert len(flagged) == 1
        assert "manual review" in flagged[0]["flag_reason"].lower()

    def test_cleanup_flags_unknown_sender(self, mock_db, mock_openai, mock_gmail):
        from workflows import cleanup

        missed_email = make_email(
            from_email="stranger@example.com",
            imap_id="100",
            message_id="<unknown@gmail.com>",
        )
        mock_gmail["fetch_old_unread_emails"].return_value = [missed_email]

        cleanup.run()

        flagged = [c for c in mock_db["conversations"] if c["status"] == "Flagged"]
        assert len(flagged) == 1
        assert "unknown sender" in flagged[0]["flag_reason"].lower()
