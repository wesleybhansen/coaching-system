"""Tests for check-in and re-engagement workflows.

Covers: check-in timing, re-engagement nudge/silence, duplicate prevention.
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from tests.conftest import make_user, make_conversation
from workflows import check_in, re_engagement


def _get_today_day():
    """Helper to get the current day name used by check_in.run()."""
    # Use the same DAY_MAP as check_in module but with UTC to avoid pytz dependency in tests
    now = datetime.now(timezone.utc)
    return check_in.DAY_MAP[now.weekday()]


class TestCheckIn:
    """Test the check_in workflow sends to the right users.

    The rewritten check-in uses get_active_users_for_checkin_today(today) and
    sends via gmail_service.send_email (not send_checkin).
    """

    def test_sends_to_active_user_not_contacted_recently(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="alice@example.com",
            status="Active",
            checkin_days=today,  # schedule for today
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        mock_gmail["send_email"].assert_called_once()
        call_kwargs = mock_gmail["send_email"].call_args
        assert call_kwargs[1]["to_email"] == "alice@example.com"

    def test_skips_user_not_scheduled_today(self, mock_db, mock_openai, mock_gmail):
        """User whose check-in days don't include today should be skipped."""
        today = _get_today_day()
        # Pick a different day than today
        all_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        other_day = [d for d in all_days if d != today][0]

        user = make_user(
            email="alice@example.com",
            status="Active",
            checkin_days=other_day,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        mock_gmail["send_email"].assert_not_called()

    def test_skips_paused_user(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="bob@example.com",
            status="Paused",
            checkin_days=today,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        mock_gmail["send_email"].assert_not_called()

    def test_sends_to_user_never_contacted(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="new@example.com",
            status="Active",
            checkin_days=today,
            last_response_date=None,
        )
        mock_db["users"].append(user)

        check_in.run()

        mock_gmail["send_email"].assert_called_once()

    def test_creates_sent_conversation_record(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="alice@example.com",
            status="Active",
            checkin_days=today,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Check-in"
        assert conv["status"] == "Sent"


class TestReEngagement:
    """Test the re_engagement workflow."""

    def test_sends_nudge_to_user_silent_10_plus_days(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        mock_gmail["send_reengagement"].assert_called_once()

    def test_skips_if_recent_reengagement_sent(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        # Already sent a re-engagement 5 days ago
        mock_db["conversations"].append(
            make_conversation(
                user_id=user["id"],
                type="Re-engagement",
                created_at=(datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            )
        )

        re_engagement.run()

        mock_gmail["send_reengagement"].assert_not_called()

    def test_allows_reengagement_after_14_days(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        )
        mock_db["users"].append(user)

        # Last re-engagement was 15 days ago
        mock_db["conversations"].append(
            make_conversation(
                user_id=user["id"],
                type="Re-engagement",
                created_at=(datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
            )
        )

        re_engagement.run()

        mock_gmail["send_reengagement"].assert_called_once()

    def test_marks_very_silent_user_as_silent(self, mock_db, mock_openai, mock_gmail):
        """Users silent for 17+ days (10 + 7) should be marked as Silent."""
        user = make_user(
            email="gone@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        assert user["status"] == "Silent"

    def test_does_not_send_to_non_active_users(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="paused@example.com",
            status="Paused",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        mock_gmail["send_reengagement"].assert_not_called()

    def test_creates_reengagement_conversation_record(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        re_eng_convs = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng_convs) == 1
        assert re_eng_convs[0]["status"] == "Sent"
