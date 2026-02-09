from datetime import datetime, timezone
from supabase import create_client
import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


# ── Users ──────────────────────────────────────────────────────

def get_user_by_email(email: str):
    resp = get_client().table("users").select("*").ilike("email", email).limit(1).execute()
    return resp.data[0] if resp.data else None


def get_user_by_id(user_id: str):
    resp = get_client().table("users").select("*").eq("id", user_id).limit(1).execute()
    return resp.data[0] if resp.data else None


def get_active_users_needing_checkin(days_since: int = 3):
    """Active users whose last response was >= days_since days ago, or who have never been contacted."""
    cutoff = datetime.now(timezone.utc).isoformat()
    resp = get_client().table("users").select("*").eq("status", "Active").execute()
    users = []
    for u in resp.data:
        last = u.get("last_response_date")
        if last is None:
            users.append(u)
        else:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            diff = (datetime.now(timezone.utc) - last_dt).days
            if diff >= days_since:
                users.append(u)
    return users


def get_silent_users(days: int = 10):
    resp = get_client().table("users").select("*").eq("status", "Active").execute()
    users = []
    for u in resp.data:
        last = u.get("last_response_date")
        if last is None:
            continue
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        diff = (datetime.now(timezone.utc) - last_dt).days
        if diff >= days:
            users.append(u)
    return users


def create_user(email: str, first_name: str = None):
    data = {"email": email.lower(), "status": "Onboarding"}
    if first_name:
        data["first_name"] = first_name
    resp = get_client().table("users").insert(data).execute()
    return resp.data[0] if resp.data else None


def update_user(user_id: str, updates: dict):
    resp = get_client().table("users").update(updates).eq("id", user_id).execute()
    return resp.data[0] if resp.data else None


def get_all_users():
    resp = get_client().table("users").select("*").order("created_at", desc=True).execute()
    return resp.data


# ── Conversations ──────────────────────────────────────────────

def create_conversation(data: dict):
    resp = get_client().table("conversations").insert(data).execute()
    return resp.data[0] if resp.data else None


def get_conversation(conversation_id: str):
    resp = get_client().table("conversations").select("*").eq("id", conversation_id).limit(1).execute()
    return resp.data[0] if resp.data else None


def update_conversation(conversation_id: str, updates: dict):
    resp = get_client().table("conversations").update(updates).eq("id", conversation_id).execute()
    return resp.data[0] if resp.data else None


def get_conversations_by_status(status: str):
    resp = (get_client().table("conversations")
            .select("*, users(id, email, first_name, stage, business_idea, summary)")
            .eq("status", status)
            .order("created_at", desc=False)
            .execute())
    return resp.data


def get_approved_unsent():
    resp = (get_client().table("conversations")
            .select("*, users(id, email, first_name, stage, summary, gmail_thread_id, gmail_message_id)")
            .eq("status", "Approved")
            .is_("sent_at", "null")
            .order("created_at", desc=False)
            .execute())
    return resp.data


def get_recent_conversations(user_id: str, limit: int = 3):
    resp = (get_client().table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "Sent")
            .order("created_at", desc=True)
            .limit(limit)
            .execute())
    return resp.data


def get_conversations_for_user(user_id: str):
    resp = (get_client().table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute())
    return resp.data


def conversation_exists_for_message(gmail_message_id: str) -> bool:
    resp = (get_client().table("conversations")
            .select("id")
            .eq("gmail_message_id", gmail_message_id)
            .limit(1)
            .execute())
    return len(resp.data) > 0


def get_all_conversations(limit: int = 100):
    resp = (get_client().table("conversations")
            .select("*, users(id, email, first_name, stage)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute())
    return resp.data


def has_recent_reengagement(user_id: str, within_days: int = 14) -> bool:
    cutoff = datetime.now(timezone.utc)
    resp = (get_client().table("conversations")
            .select("id")
            .eq("user_id", user_id)
            .eq("type", "Re-engagement")
            .order("created_at", desc=True)
            .limit(1)
            .execute())
    if not resp.data:
        return False
    last = datetime.fromisoformat(resp.data[0].get("created_at", "").replace("Z", "+00:00"))
    return (cutoff - last).days < within_days


# ── Model Responses ────────────────────────────────────────────

def get_model_responses_by_stage(stage: str):
    resp = get_client().table("model_responses").select("*").eq("stage", stage).execute()
    return resp.data


def get_all_model_responses():
    resp = get_client().table("model_responses").select("*").order("stage").execute()
    return resp.data


# ── Corrected Responses ───────────────────────────────────────

def get_recent_corrections(limit: int = 10, stage: str = None):
    q = get_client().table("corrected_responses").select("*").order("created_at", desc=True).limit(limit)
    resp = q.execute()
    return resp.data


def create_correction(data: dict):
    resp = get_client().table("corrected_responses").insert(data).execute()
    return resp.data[0] if resp.data else None


def get_all_corrections():
    resp = get_client().table("corrected_responses").select("*, conversations(id, user_id)").order("created_at", desc=True).execute()
    return resp.data


# ── Settings ───────────────────────────────────────────────────

def get_setting(key: str, default: str = None) -> str:
    resp = get_client().table("settings").select("value").eq("key", key).limit(1).execute()
    if resp.data:
        return resp.data[0]["value"]
    return default


def set_setting(key: str, value: str):
    get_client().table("settings").upsert({"key": key, "value": value}).execute()


def get_all_settings() -> dict:
    resp = get_client().table("settings").select("*").execute()
    return {row["key"]: row["value"] for row in resp.data}


# ── Workflow Runs ──────────────────────────────────────────────

def start_workflow_run(workflow_name: str) -> str:
    resp = get_client().table("workflow_runs").insert({
        "workflow_name": workflow_name,
        "status": "running",
    }).execute()
    return resp.data[0]["id"] if resp.data else None


def complete_workflow_run(run_id: str, items_processed: int = 0):
    get_client().table("workflow_runs").update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "items_processed": items_processed,
    }).eq("id", run_id).execute()


def fail_workflow_run(run_id: str, error_message: str):
    get_client().table("workflow_runs").update({
        "status": "failed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "error_message": error_message,
    }).eq("id", run_id).execute()


def get_recent_workflow_runs(hours: int = 24, limit: int = 50):
    resp = (get_client().table("workflow_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute())
    return resp.data
