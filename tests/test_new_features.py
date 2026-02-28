"""Tests for new features: onboarding flow, thread reply cap, satisfaction scoring,
stage change milestones, and personalized check-in schedules.

Covers: multi-step onboarding, 4-reply cap, satisfaction rolling average,
stage change detection, and per-user check-in day configuration.
"""

from datetime import datetime, timezone, timedelta
from tests.conftest import make_user, make_email, make_conversation
from services import coaching_service
from db import supabase_client as db


class TestOnboardingFlow:
    """Test the multi-step onboarding in coaching_service.process_email."""

    def test_new_user_creates_onboarding_conversation(self, mock_db, mock_openai, mock_gmail):
        """New user email creates Onboarding conversation with status Pending Review."""
        email = make_email(from_email="newbie@example.com", from_name="Newbie Jones")

        coaching_service.process_email(email)

        # User was created
        assert len(mock_db["users"]) == 1
        assert mock_db["users"][0]["email"] == "newbie@example.com"

        # Onboarding conversation created in Pending Review
        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Onboarding"
        assert conv["status"] == "Pending Review"

    def test_onboarding_step1_reply_asks_for_challenge(self, mock_db, mock_openai, mock_gmail):
        """User with onboarding_step=1 gets step 2 response asking for their challenge."""
        user = make_user(
            email="onboard@example.com",
            first_name="Onboard",
            status="Onboarding",
            onboarding_step=1,
        )
        mock_db["users"].append(user)

        email = make_email(
            from_email="onboard@example.com",
            body="I'm working on a marketplace for freelancers. I'm in the ideation stage.",
        )

        coaching_service.process_email(email)

        # Should create a conversation asking for their challenge
        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Onboarding"
        assert conv["status"] == "Pending Review"
        assert "challenge" in conv["ai_response"].lower() or "question" in conv["ai_response"].lower()

        # User onboarding_step should advance to 2
        assert user["onboarding_step"] == 2

    def test_onboarding_step2_reply_activates_user(self, mock_db, mock_openai, mock_gmail):
        """User with onboarding_step=2 gets activated (status=Active, onboarding_step=3)."""
        user = make_user(
            email="almost@example.com",
            first_name="Almost",
            status="Onboarding",
            onboarding_step=2,
        )
        mock_db["users"].append(user)

        email = make_email(
            from_email="almost@example.com",
            body="My biggest challenge is finding my first paying customer.",
        )

        coaching_service.process_email(email)

        # User should now be active with step 3
        assert user["status"] == "Active"
        assert user["onboarding_step"] == 3

        # Should create an onboarding conversation
        assert len(mock_db["conversations"]) == 1
        conv = mock_db["conversations"][0]
        assert conv["type"] == "Onboarding"
        assert conv["status"] == "Pending Review"


class TestThreadReplyCap:
    """Test the 4-reply cap on follow-up threads."""

    def test_reply_within_cap_generates_response(self, mock_db, mock_openai, mock_gmail):
        """With 2 sent follow-ups, process_email still generates a response."""
        user = make_user(email="chatty@example.com")
        mock_db["users"].append(user)

        # Add 2 sent follow-ups
        for _ in range(2):
            mock_db["conversations"].append(
                make_conversation(
                    user_id=user["id"],
                    type="Follow-up",
                    status="Sent",
                )
            )

        email = make_email(
            from_email="chatty@example.com",
            body="Here is another update on my progress.",
        )

        result = coaching_service.process_email(email)

        # Should create a new conversation (response was generated)
        followups = [c for c in mock_db["conversations"] if c.get("user_id") == user["id"]]
        # 2 existing + 1 new = 3
        assert len(followups) == 3

    def test_reply_at_cap_skips_response(self, mock_db, mock_openai, mock_gmail):
        """With 4 sent follow-ups, process_email returns None but updates last_response_date."""
        user = make_user(email="chatty@example.com")
        mock_db["users"].append(user)
        old_date = user.get("last_response_date")

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
            body="Yet another message.",
        )

        result = coaching_service.process_email(email)

        # Should return None (skipped)
        assert result is None

        # last_response_date should still be updated
        assert user["last_response_date"] is not None


class TestSatisfactionScoring:
    """Test satisfaction score storage and rolling average."""

    def test_satisfaction_score_stored_on_conversation(self, mock_db, mock_openai, mock_gmail):
        """After processing, conversation has satisfaction_score."""
        user = make_user(email="happy@example.com")
        mock_db["users"].append(user)

        email = make_email(
            from_email="happy@example.com",
            body="Great progress! I talked to 5 customers and they loved the idea!",
        )

        coaching_service.process_email(email)

        # Find the new conversation (not any pre-existing ones)
        new_convs = [c for c in mock_db["conversations"]
                     if c.get("user_id") == user["id"]
                     and c.get("type") in ("Check-in", "Follow-up")]
        assert len(new_convs) == 1
        assert new_convs[0].get("satisfaction_score") == 7.0

    def test_satisfaction_rolling_average(self, mock_db, mock_openai, mock_gmail):
        """User with existing satisfaction_score gets a rolling average (70/30 blend)."""
        user = make_user(
            email="tracked@example.com",
            satisfaction_score=8.0,
        )
        mock_db["users"].append(user)

        # mock analyze_satisfaction returns 7.0 (from mock_openai fixture)
        email = make_email(
            from_email="tracked@example.com",
            body="Making some progress, but it's slow.",
        )

        coaching_service.process_email(email)

        # Rolling average: (8.0 * 0.7) + (7.0 * 0.3) = 5.6 + 2.1 = 7.7
        expected = round((8.0 * 0.7) + (7.0 * 0.3), 1)
        assert user["satisfaction_score"] == expected


class TestStageChangeAndMilestones:
    """Test stage change detection and milestone logging."""

    def test_stage_change_updates_user_stage(self, mock_db, mock_openai, mock_gmail):
        """When evaluation returns stage_changed=True, user's stage is updated."""
        user = make_user(
            email="evolving@example.com",
            stage="Ideation",
        )
        mock_db["users"].append(user)

        # Override evaluate_response to report a stage change
        mock_openai["evaluate_response"].return_value = {
            "confidence": 7,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Early Validation",
            "stage_changed": True,
            "resource_referenced": None,
            "summary_update": "User has started validating with customers.",
        }

        email = make_email(
            from_email="evolving@example.com",
            body="I just got my first 3 paying customers!",
        )

        coaching_service.process_email(email)

        # User stage should be updated
        assert user["stage"] == "Early Validation"

    def test_stage_change_adds_milestone_to_summary(self, mock_db, mock_openai, mock_gmail):
        """Summary includes 'MILESTONE: Progressed from X to Y'."""
        user = make_user(
            email="milestone@example.com",
            stage="Ideation",
            summary="Started exploring ideas.",
        )
        mock_db["users"].append(user)

        # Override evaluate_response to report a stage change
        mock_openai["evaluate_response"].return_value = {
            "confidence": 8,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Early Validation",
            "stage_changed": True,
            "resource_referenced": None,
            "summary_update": "User validated with first customers.",
        }

        email = make_email(
            from_email="milestone@example.com",
            body="Got my first paying customer this week!",
        )

        coaching_service.process_email(email)

        # Summary should contain the milestone note
        assert "MILESTONE: Progressed from Ideation to Early Validation" in user["summary"]


class TestPersonalizedCheckin:
    """Test personalized check-in scheduling via get_active_users_for_checkin_today."""

    def test_checkin_uses_user_schedule(self, mock_db, mock_openai, mock_gmail):
        """User with checkin_days='mon,wed' gets check-in on 'mon'."""
        user = make_user(
            email="scheduled@example.com",
            status="Active",
            checkin_days="mon,wed",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        users = db.get_active_users_for_checkin_today("mon")
        assert len(users) == 1
        assert users[0]["email"] == "scheduled@example.com"

    def test_checkin_skips_wrong_day(self, mock_db, mock_openai, mock_gmail):
        """User with checkin_days='mon,wed' does NOT get check-in on 'tue'."""
        user = make_user(
            email="scheduled@example.com",
            status="Active",
            checkin_days="mon,wed",
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        users = db.get_active_users_for_checkin_today("tue")
        assert len(users) == 0

    def test_checkin_uses_default_when_none(self, mock_db, mock_openai, mock_gmail):
        """User with checkin_days=None uses system default (tue,fri)."""
        user = make_user(
            email="defaultsched@example.com",
            status="Active",
            checkin_days=None,
            last_response_date=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        )
        mock_db["users"].append(user)

        # System default is "tue,fri"
        users_tue = db.get_active_users_for_checkin_today("tue")
        assert len(users_tue) == 1
        assert users_tue[0]["email"] == "defaultsched@example.com"

        # Should NOT appear on a non-default day
        users_mon = db.get_active_users_for_checkin_today("mon")
        assert len(users_mon) == 0
