"""Shared test fixtures and mocks.

All tests use fake versions of Supabase, OpenAI, and Gmail so nothing
touches real services, sends real emails, or costs API credits.
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Set required env vars BEFORE importing any project code
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "fake-key")
os.environ.setdefault("OPENAI_API_KEY", "fake-key")
os.environ.setdefault("GMAIL_ADDRESS", "coach@test.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "fake-password")

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Helper factories ────────────────────────────────────────────

def make_user(**overrides):
    """Create a fake user dict with sensible defaults."""
    defaults = {
        "id": str(uuid.uuid4()),
        "email": "alice@example.com",
        "first_name": "Alice",
        "status": "Active",
        "stage": "Ideation",
        "business_idea": "A dog-walking app",
        "summary": "New user exploring ideas.",
        "auto_approve_threshold": None,
        "gmail_message_id": "<msg-123@gmail.com>",
        "gmail_thread_id": "<thread-123@gmail.com>",
        "last_response_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checkin_days": None,        # None means use system default
        "onboarding_step": 0,
        "satisfaction_score": None,
        "current_challenge": None,
        "notes": None,
        "bounce_count": 0,
    }
    defaults.update(overrides)
    return defaults


def make_email(**overrides):
    """Create a fake incoming email dict."""
    defaults = {
        "imap_id": "1",
        "message_id": f"<{uuid.uuid4()}@gmail.com>",
        "from_email": "alice@example.com",
        "from_name": "Alice Smith",
        "subject": "Re: Coaching",
        "body": "I made progress on my business plan this week.",
        "in_reply_to": "<prev-msg@gmail.com>",
        "references": "<prev-msg@gmail.com>",
        "date": "Mon, 1 Jan 2025 10:00:00 +0000",
    }
    defaults.update(overrides)
    return defaults


def make_conversation(**overrides):
    """Create a fake conversation dict."""
    defaults = {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "type": "Follow-up",
        "user_message_raw": "I made progress.",
        "user_message_parsed": "I made progress.",
        "ai_response": "Great work! Keep going.",
        "sent_response": None,
        "confidence": 7,
        "status": "Pending Review",
        "flag_reason": None,
        "gmail_message_id": f"<{uuid.uuid4()}@gmail.com>",
        "gmail_thread_id": None,
        "sent_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "satisfaction_score": None,
        "thread_reply_count": 0,
        "resource_referenced": None,
        "stage_detected": None,
        "stage_changed": False,
        "approved_by": None,
        "approved_at": None,
        "evaluation_details": None,
        "send_attempts": 0,
    }
    defaults.update(overrides)
    return defaults


# ── Fake Supabase ───────────────────────────────────────────────

class FakeQueryBuilder:
    """Mimics the Supabase query builder chain: .select().eq().limit().execute()"""

    def __init__(self, data=None):
        self._data = data if data is not None else []

    def select(self, *a, **kw):
        return self

    def eq(self, *a, **kw):
        return self

    def ilike(self, *a, **kw):
        return self

    def is_(self, *a, **kw):
        return self

    def order(self, *a, **kw):
        return self

    def limit(self, *a, **kw):
        return self

    def insert(self, data):
        # Auto-assign an id if missing
        if isinstance(data, dict) and "id" not in data:
            data["id"] = str(uuid.uuid4())
            data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self._data = [data]
        return self

    def update(self, data):
        return self

    def upsert(self, data):
        return self

    def execute(self):
        return MagicMock(data=self._data)


@pytest.fixture
def mock_db(monkeypatch):
    """Provides a dict-based fake database. Patches db.supabase_client functions.

    Returns a storage dict so tests can set up data and inspect calls.
    """
    storage = {
        "users": [],
        "conversations": [],
        "settings": {
            "global_auto_approve_threshold": "10",
            "max_thread_replies": "4",
            "default_checkin_days": "tue,fri",
            "max_checkin_days_per_week": "3",
            "notification_email": "coachwes@thelaunchpadincubator.com",
            "send_window_minutes": "120",
        },
        "model_responses": [],
        "corrections": [],
        "workflow_runs": [],
    }

    def get_user_by_email(email):
        for u in storage["users"]:
            if u["email"].lower() == email.lower():
                return u
        return None

    def get_user_by_id(user_id):
        for u in storage["users"]:
            if u["id"] == user_id:
                return u
        return None

    def create_user(email, first_name=None):
        user = make_user(email=email.lower(), first_name=first_name or "there")
        storage["users"].append(user)
        return user

    def update_user(user_id, updates):
        for u in storage["users"]:
            if u["id"] == user_id:
                u.update(updates)
                return u
        return None

    def create_conversation(data):
        data.setdefault("id", str(uuid.uuid4()))
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        storage["conversations"].append(data)
        return data

    def update_conversation(conv_id, updates):
        for c in storage["conversations"]:
            if c["id"] == conv_id:
                c.update(updates)
                return c
        return None

    def conversation_exists_for_message(gmail_message_id):
        return any(
            c.get("gmail_message_id") == gmail_message_id
            for c in storage["conversations"]
        )

    def get_recent_conversations(user_id, limit=3):
        user_convs = [c for c in storage["conversations"]
                      if c.get("user_id") == user_id and c.get("status") == "Sent"]
        return user_convs[-limit:]

    def get_conversations_for_user(user_id):
        return [c for c in storage["conversations"] if c.get("user_id") == user_id]

    def get_approved_unsent():
        results = []
        for c in storage["conversations"]:
            # Approved and unsent
            if c.get("status") == "Approved" and c.get("sent_at") is None:
                user = get_user_by_id(c.get("user_id"))
                c_copy = dict(c)
                c_copy["users"] = user
                results.append(c_copy)
            # Send Failed with < 3 attempts (retryable)
            elif c.get("status") == "Send Failed" and (c.get("send_attempts") or 0) < 3:
                user = get_user_by_id(c.get("user_id"))
                c_copy = dict(c)
                c_copy["users"] = user
                results.append(c_copy)
        return results

    def get_conversations_by_status(status):
        return [c for c in storage["conversations"] if c.get("status") == status]

    def get_model_responses_by_stage(stage):
        return [m for m in storage["model_responses"] if m.get("stage") == stage]

    def get_recent_corrections(limit=10, stage=None):
        return storage["corrections"][:limit]

    def get_setting(key, default=None):
        return storage["settings"].get(key, default)

    def set_setting(key, value):
        storage["settings"][key] = value

    def start_workflow_run(name):
        run_id = str(uuid.uuid4())
        storage["workflow_runs"].append({"id": run_id, "workflow_name": name, "status": "running"})
        return run_id

    def complete_workflow_run(run_id, items_processed=0, items_failed=0, items_skipped=0):
        for r in storage["workflow_runs"]:
            if r["id"] == run_id:
                r["status"] = "completed_with_errors" if items_failed > 0 else "completed"
                r["items_processed"] = items_processed
                r["items_failed"] = items_failed
                r["items_skipped"] = items_skipped

    def fail_workflow_run(run_id, error_message):
        for r in storage["workflow_runs"]:
            if r["id"] == run_id:
                r["status"] = "failed"
                r["error_message"] = error_message

    def get_active_users_needing_checkin(days_since=3):
        users = []
        for u in storage["users"]:
            if u.get("status") != "Active":
                continue
            last = u.get("last_response_date")
            if last is None:
                users.append(u)
            else:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - last_dt).days >= days_since:
                    users.append(u)
        return users

    def get_active_users_for_checkin_today(day_of_week):
        default_days_str = storage["settings"].get("default_checkin_days", "tue,fri")
        default_days = [d.strip().lower() for d in default_days_str.split(",")]

        users = []
        for u in storage["users"]:
            if u.get("status") != "Active":
                continue

            user_days_str = u.get("checkin_days")
            if user_days_str:
                user_days = [d.strip().lower() for d in user_days_str.split(",")]
            else:
                user_days = default_days

            if day_of_week in user_days:
                # Also check at least 1 day since last_response_date
                last = u.get("last_response_date")
                if last is None:
                    users.append(u)
                else:
                    last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                    if (datetime.now(timezone.utc) - last_dt).days >= 1:
                        users.append(u)
        return users

    def get_silent_users(days=10):
        users = []
        for u in storage["users"]:
            if u.get("status") != "Active":
                continue
            last = u.get("last_response_date")
            if last is None:
                continue
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - last_dt).days >= days:
                users.append(u)
        return users

    def has_pending_outreach(user_id):
        return any(
            c.get("user_id") == user_id and c.get("status") in ("Pending Review", "Approved")
            for c in storage["conversations"]
        )

    def get_onboarding_users():
        return [u for u in storage["users"] if u.get("status") == "Onboarding"]

    def has_recent_reengagement(user_id, within_days=14):
        for c in reversed(storage["conversations"]):
            if c.get("user_id") == user_id and c.get("type") == "Re-engagement":
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                return (datetime.now(timezone.utc) - created).days < within_days
        return False

    def count_thread_replies(user_id):
        return sum(
            1 for c in storage["conversations"]
            if c.get("user_id") == user_id
            and c.get("type") == "Follow-up"
            and c.get("status") == "Sent"
        )

    def get_resource_list_for_prompt(stage=None):
        return "- Lecture 1: Intro to entrepreneurship (Topics: getting started)"

    def get_correction_stats():
        return {}

    def get_all_resources():
        return []

    def get_confidence_calibration_data():
        return []

    def get_satisfaction_trend(user_id=None, limit=50):
        return []

    # Patch all db functions
    import db.supabase_client as db_mod
    monkeypatch.setattr(db_mod, "get_user_by_email", get_user_by_email)
    monkeypatch.setattr(db_mod, "get_user_by_id", get_user_by_id)
    monkeypatch.setattr(db_mod, "create_user", create_user)
    monkeypatch.setattr(db_mod, "update_user", update_user)
    monkeypatch.setattr(db_mod, "create_conversation", create_conversation)
    monkeypatch.setattr(db_mod, "update_conversation", update_conversation)
    monkeypatch.setattr(db_mod, "conversation_exists_for_message", conversation_exists_for_message)
    monkeypatch.setattr(db_mod, "get_recent_conversations", get_recent_conversations)
    monkeypatch.setattr(db_mod, "get_conversations_for_user", get_conversations_for_user)
    monkeypatch.setattr(db_mod, "get_approved_unsent", get_approved_unsent)
    monkeypatch.setattr(db_mod, "get_conversations_by_status", get_conversations_by_status)
    monkeypatch.setattr(db_mod, "get_model_responses_by_stage", get_model_responses_by_stage)
    monkeypatch.setattr(db_mod, "get_recent_corrections", get_recent_corrections)
    monkeypatch.setattr(db_mod, "get_setting", get_setting)
    monkeypatch.setattr(db_mod, "set_setting", set_setting)
    monkeypatch.setattr(db_mod, "start_workflow_run", start_workflow_run)
    monkeypatch.setattr(db_mod, "complete_workflow_run", complete_workflow_run)
    monkeypatch.setattr(db_mod, "fail_workflow_run", fail_workflow_run)
    monkeypatch.setattr(db_mod, "get_active_users_needing_checkin", get_active_users_needing_checkin)
    monkeypatch.setattr(db_mod, "get_active_users_for_checkin_today", get_active_users_for_checkin_today)
    monkeypatch.setattr(db_mod, "get_silent_users", get_silent_users)
    monkeypatch.setattr(db_mod, "has_pending_outreach", has_pending_outreach)
    monkeypatch.setattr(db_mod, "get_onboarding_users", get_onboarding_users)
    monkeypatch.setattr(db_mod, "has_recent_reengagement", has_recent_reengagement)
    monkeypatch.setattr(db_mod, "count_thread_replies", count_thread_replies)
    monkeypatch.setattr(db_mod, "get_resource_list_for_prompt", get_resource_list_for_prompt)
    monkeypatch.setattr(db_mod, "get_correction_stats", get_correction_stats)
    monkeypatch.setattr(db_mod, "get_all_resources", get_all_resources)
    monkeypatch.setattr(db_mod, "get_confidence_calibration_data", get_confidence_calibration_data)
    monkeypatch.setattr(db_mod, "get_satisfaction_trend", get_satisfaction_trend)

    return storage


@pytest.fixture
def mock_openai(monkeypatch):
    """Patches OpenAI service functions with controllable fakes.

    Returns a dict of MagicMock objects so tests can inspect calls
    and override return values.
    """
    import services.openai_service as oai

    mocks = {
        "generate_response": MagicMock(return_value="Great progress! Keep focusing on customer discovery."),
        "evaluate_response": MagicMock(return_value={
            "confidence": 7,
            "flag": False,
            "flag_reason": None,
            "detected_stage": "Ideation",
            "stage_changed": False,
            "resource_referenced": None,
            "summary_update": "User making progress on ideation.",
            "sub_scores": {
                "relevance": 7,
                "tone": 8,
                "actionability": 7,
                "length": 7,
                "closing_question": 7,
            },
        }),
        "generate_summary_update": MagicMock(return_value="User continued working on their business plan."),
        "parse_email_fallback": MagicMock(return_value="Parsed email content."),
        "generate_checkin_question": MagicMock(return_value="Hey! How's the customer discovery going? Made any progress this week?"),
        "analyze_satisfaction": MagicMock(return_value=7.0),
        "confirm_intent": MagicMock(return_value=True),
    }

    for name, mock in mocks.items():
        monkeypatch.setattr(oai, name, mock)

    return mocks


@pytest.fixture
def mock_gmail(monkeypatch):
    """Patches Gmail service functions with no-op fakes.

    Returns a dict of MagicMock objects so tests can inspect calls.
    """
    import services.gmail_service as gmail

    mocks = {
        "fetch_unread_emails": MagicMock(return_value=[]),
        "mark_as_read": MagicMock(),
        "mark_multiple_as_read": MagicMock(),
        "send_email": MagicMock(return_value="<sent-msg-id@gmail.com>"),
        "send_coaching_response": MagicMock(return_value="<sent-msg-id@gmail.com>"),
        "send_checkin": MagicMock(return_value="<sent-checkin-id@gmail.com>"),
        "send_reengagement": MagicMock(return_value="<sent-reengage-id@gmail.com>"),
        "send_onboarding": MagicMock(return_value="<sent-onboard-id@gmail.com>"),
        "get_onboarding_body": MagicMock(return_value="Welcome to coaching!"),
        "fetch_old_unread_emails": MagicMock(return_value=[]),
    }

    for name, mock in mocks.items():
        monkeypatch.setattr(gmail, name, mock)

    return mocks


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Prevent any real sleeping during tests."""
    import time
    import workflows.send_approved as sa
    monkeypatch.setattr(time, "sleep", lambda x: None)
    monkeypatch.setattr(sa.random, "randint", lambda a, b: 0)
    monkeypatch.setattr(sa.time, "sleep", lambda x: None)
