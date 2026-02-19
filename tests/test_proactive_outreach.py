"""Tests for check-in and re-engagement workflows.

Covers: check-in timing, re-engagement nudge/silence, duplicate prevention.
Both workflows now route through Pending Review instead of sending directly.
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
    """Test the check_in workflow queues check-ins for review.

    Check-ins are routed through Pending Review so the coach can
    approve/edit before they are sent.
    """

    def test_queues_checkin_for_active_user(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="alice@example.com",
            status="Active",
            checkin_days=today,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Check-in"
        assert conv["status"] == "Pending Review"
        assert conv["ai_response"]  # has generated content

    def test_does_not_send_email_directly(self, mock_db, mock_openai, mock_gmail):
        """Check-ins should never call send_email directly."""
        today = _get_today_day()
        user = make_user(
            email="alice@example.com",
            status="Active",
            checkin_days=today,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        check_in.run()

        mock_gmail["send_email"].assert_not_called()

    def test_skips_user_not_scheduled_today(self, mock_db, mock_openai, mock_gmail):
        """User whose check-in days don't include today should be skipped."""
        today = _get_today_day()
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

        assert len(mock_db["conversations"]) == 0

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

        assert len(mock_db["conversations"]) == 0

    def test_queues_checkin_for_user_never_contacted(self, mock_db, mock_openai, mock_gmail):
        today = _get_today_day()
        user = make_user(
            email="new@example.com",
            status="Active",
            checkin_days=today,
            last_response_date=None,
        )
        mock_db["users"].append(user)

        check_in.run()

        assert len(mock_db["conversations"]) == 1
        assert mock_db["conversations"][0]["status"] == "Pending Review"


class TestReEngagement:
    """Test the re_engagement workflow queues nudges for review."""

    def test_queues_nudge_for_silent_user(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        re_eng_convs = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng_convs) == 1
        assert re_eng_convs[0]["status"] == "Pending Review"
        assert re_eng_convs[0]["ai_response"]  # has body text

    def test_does_not_send_email_directly(self, mock_db, mock_openai, mock_gmail):
        """Re-engagement should never call send_reengagement directly."""
        user = make_user(
            email="silent@example.com",
            status="Active",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        mock_gmail["send_reengagement"].assert_not_called()
        mock_gmail["send_email"].assert_not_called()

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

        # Should still be just the 1 pre-existing re-engagement (no new one created)
        re_eng_convs = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng_convs) == 1

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

        # Should now have 2 re-engagements: the old one + the new Pending Review one
        re_eng_convs = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng_convs) == 2
        new_conv = re_eng_convs[-1]
        assert new_conv["status"] == "Pending Review"

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

    def test_does_not_queue_for_non_active_users(self, mock_db, mock_openai, mock_gmail):
        user = make_user(
            email="paused@example.com",
            status="Paused",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
        )
        mock_db["users"].append(user)

        re_engagement.run()

        re_eng_convs = [c for c in mock_db["conversations"] if c["type"] == "Re-engagement"]
        assert len(re_eng_convs) == 0
