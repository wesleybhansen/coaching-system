"""Tests for v4 improvements: sub-scores, AI intent confirmation, bounce detection,
thread cap wrap-up, pending outreach skip, onboarding stall, send retry.
"""

import smtplib
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from tests.conftest import make_user, make_email, make_conversation
from services import coaching_service
from workflows import send_approved, re_engagement


# ── Phase 1: Context uses 5 conversations ────────────────────

class TestContextHistory:
    def test_context_uses_5_conversations(self, mock_db, mock_openai, mock_gmail):
        """build_assistant_context should request 5 recent conversations."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        # Add 6 sent conversations
        for i in range(6):
            mock_db["conversations"].append(
                make_conversation(
                    user_id=user["id"],
                    status="Sent",
                    user_message_parsed=f"Message {i}",
                    sent_response=f"Response {i}",
                )
            )

        context = coaching_service.build_assistant_context(user, "New message")

        # Should include 5 most recent, not the 6th
        assert "Message 1" in context  # 2nd oldest of 6 = included in last 5
        assert "Message 5" in context  # newest
        # Message 0 is the oldest and should be excluded (only 5 kept)
        # (The mock returns last `limit` items, so Message 0 is excluded)


# ── Phase 2: Sub-scores stored on conversation ───────────────

class TestSubScores:
    def test_sub_scores_stored_on_conversation(self, mock_db, mock_openai, mock_gmail):
        """Evaluation sub-scores should be stored as evaluation_details on the conversation."""
        user = make_user(email="alice@example.com")
        mock_db["users"].append(user)

        email = make_email(
            from_email="alice@example.com",
            body="I talked to 3 potential customers this week.",
        )

        coaching_service.process_email(email)

        # Find the new conversation
        new_convs = [c for c in mock_db["conversations"]
                     if c.get("user_id") == user["id"]
                     and c.get("type") in ("Check-in", "Follow-up")]
        assert len(new_convs) == 1
        details = new_convs[0].get("evaluation_details")
        assert isinstance(details, dict)
        assert "relevance" in details
        assert "closing_question" in details


# ── Phase 3.1: AI intent confirmation ─────────────────────────

class TestAIIntentConfirmation:
    def test_short_pause_keyword_no_ai_call(self, mock_db, mock_openai, mock_gmail):
        """Short messages (<= 20 words) should not call confirm_intent."""
        result = coaching_service.detect_intent("I want to pause")
        assert result == "pause"
        mock_openai["confirm_intent"].assert_not_called()

    def test_long_message_with_keyword_calls_ai(self, mock_db, mock_openai, mock_gmail):
        """Messages > 20 words with a keyword should call confirm_intent."""
        long_msg = "I need to stop overthinking everything and just focus on talking to customers because I have been spending too much time in my head and not enough time doing the work"
        mock_openai["confirm_intent"].return_value = False  # AI says it's not a real pause

        result = coaching_service.detect_intent(long_msg)

        assert result == "normal"
        mock_openai["confirm_intent"].assert_called_once()

    def test_long_message_confirmed_pause(self, mock_db, mock_openai, mock_gmail):
        """When AI confirms the long message is a real pause, return 'pause'."""
        long_msg = "Hey Wes, I need to take a break from coaching for a while because things have gotten really busy at work and I just cannot keep up with everything right now"
        mock_openai["confirm_intent"].return_value = True

        result = coaching_service.detect_intent(long_msg)

        assert result == "pause"
        mock_openai["confirm_intent"].assert_called_once()


# ── Phase 3.2: Bounce detection ──────────────────────────────

class TestBounceDetection:
    def test_bounce_increments_count_and_rejects(self, mock_db, mock_openai, mock_gmail):
        """SMTPRecipientsRefused should increment bounce_count and reject the conversation."""
        user = make_user(email="bad@example.com", bounce_count=0)
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        mock_gmail["send_email"].side_effect = smtplib.SMTPRecipientsRefused(
            {"bad@example.com": (550, b"User unknown")}
        )

        send_approved.run()

        assert user["bounce_count"] == 1
        assert conv["status"] == "Rejected"

    def test_three_bounces_adds_note(self, mock_db, mock_openai, mock_gmail):
        """After 3 bounces, a note should be added to the user record."""
        user = make_user(email="bouncy@example.com", bounce_count=2)
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
        )
        mock_db["conversations"].append(conv)

        mock_gmail["send_email"].side_effect = smtplib.SMTPRecipientsRefused(
            {"bouncy@example.com": (550, b"User unknown")}
        )

        send_approved.run()

        assert user["bounce_count"] == 3
        assert "bounces detected" in (user.get("notes") or "").lower()


# ── Phase 3.3: Thread cap wrap-up ────────────────────────────

class TestThreadCapWrapUp:
    def test_thread_cap_creates_pending_review_wrap_up(self, mock_db, mock_openai, mock_gmail):
        """When thread cap is hit, create a friendly wrap-up in Pending Review."""
        user = make_user(email="chatty@example.com")
        mock_db["users"].append(user)

        # Add 4 sent follow-ups to hit the cap
        for _ in range(4):
            mock_db["conversations"].append(
                make_conversation(
                    user_id=user["id"],
                    type="Follow-up",
                    status="Sent",
                )
            )

        email = make_email(
            from_email="chatty@example.com",
            body="Another message",
        )

        coaching_service.process_email(email)

        # The new conversation should be Pending Review with a wrap-up message
        new_convs = [c for c in mock_db["conversations"]
                     if c.get("status") == "Pending Review"]
        assert len(new_convs) == 1
        assert "next check-in" in new_convs[0]["ai_response"].lower()


# ── Phase 3.4: Skip re-engagement if pending outreach ────────

class TestPendingOutreachSkip:
    def test_skips_reengagement_if_pending_outreach(self, mock_db, mock_openai, mock_gmail):
        """User with a Pending Review conversation should not get re-engagement."""
        user = make_user(
            email="has_pending@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        # Existing pending conversation
        mock_db["conversations"].append(
            make_conversation(
                user_id=user["id"],
                status="Pending Review",
                type="Check-in",
            )
        )

        re_engagement.run()

        # Should NOT have created a new re-engagement
        re_eng = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng) == 0


# ── Phase 3.5: Onboarding stall timeout ──────────────────────

class TestOnboardingStall:
    def test_flags_stalled_onboarding(self, mock_db, mock_openai, mock_gmail):
        """Onboarding user with no response in 7+ days should be flagged."""
        user = make_user(
            email="stalled@example.com",
            first_name="Stalled",
            status="Onboarding",
            created_at=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        flagged = [c for c in mock_db["conversations"]
                   if c.get("status") == "Flagged" and "stalled" in (c.get("flag_reason") or "").lower()]
        assert len(flagged) == 1
        assert "Stalled" in flagged[0]["flag_reason"]


# ── Phase 4.1: Send failure retry ─────────────────────────────

class TestSendRetry:
    def test_first_failure_marks_send_failed(self, mock_db, mock_openai, mock_gmail):
        """First send failure should mark as 'Send Failed' with 1 attempt."""
        user = make_user(email="retry@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Approved",
            ai_response="Good work!",
            sent_at=None,
            send_attempts=0,
        )
        mock_db["conversations"].append(conv)

        mock_gmail["send_email"].side_effect = Exception("Temporary failure")

        send_approved.run()

        assert conv["status"] == "Send Failed"
        assert conv["send_attempts"] == 1

    def test_third_failure_flags_permanently(self, mock_db, mock_openai, mock_gmail):
        """Third send failure should move to 'Flagged' permanently."""
        user = make_user(email="retry@example.com")
        mock_db["users"].append(user)

        conv = make_conversation(
            user_id=user["id"],
            status="Send Failed",
            ai_response="Good work!",
            sent_at=None,
            send_attempts=2,  # Already failed twice
        )
        mock_db["conversations"].append(conv)

        mock_gmail["send_email"].side_effect = Exception("Persistent failure")

        send_approved.run()

        assert conv["status"] == "Flagged"
        assert conv["send_attempts"] == 3
        assert "Send failed 3 times" in conv["flag_reason"]
