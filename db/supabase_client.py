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


def get_active_users_for_checkin_today(day_of_week: str):
    """Get active users who should receive a check-in today based on their personalized schedule.

    Args:
        day_of_week: Three-letter lowercase day, e.g. 'mon', 'tue', 'wed'

    Returns users whose checkin_days includes today, or who use the system default
    and today is in the system default.
    """
    default_days_str = get_setting("default_checkin_days", "tue,fri")
    default_days = [d.strip().lower() for d in default_days_str.split(",")]

    resp = get_client().table("users").select("*").eq("status", "Active").execute()
    users = []
    for u in resp.data:
        user_days_str = u.get("checkin_days")
        if user_days_str:
            user_days = [d.strip().lower() for d in user_days_str.split(",")]
        else:
            user_days = default_days

        if day_of_week in user_days:
            # Also check they haven't been contacted too recently (at least 1 day gap)
            last = u.get("last_response_date")
            if last is None:
                users.append(u)
            else:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                diff = (datetime.now(timezone.utc) - last_dt).days
                if diff >= 1:
                    users.append(u)
    return users


def get_onboarding_users() -> list:
    """Get users with status 'Onboarding'."""
    resp = get_client().table("users").select("*").eq("status", "Onboarding").execute()
    return resp.data


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
    """Fetch conversations ready to send: Approved (unsent) + Send Failed (< 3 attempts)."""
    # Approved, never sent
    approved_resp = (get_client().table("conversations")
                     .select("*, users(id, email, first_name, stage, summary, gmail_thread_id, gmail_message_id, bounce_count)")
                     .eq("status", "Approved")
                     .is_("sent_at", "null")
                     .order("created_at", desc=False)
                     .execute())
    # Send Failed, retryable (< 3 attempts)
    retry_resp = (get_client().table("conversations")
                  .select("*, users(id, email, first_name, stage, summary, gmail_thread_id, gmail_message_id, bounce_count)")
                  .eq("status", "Send Failed")
                  .lt("send_attempts", 3)
                  .order("created_at", desc=False)
                  .execute())
    return approved_resp.data + retry_resp.data


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


def has_pending_outreach(user_id: str) -> bool:
    """Check if a user has any conversations in Pending Review or Approved (unsent)."""
    for status in ("Pending Review", "Approved"):
        resp = (get_client().table("conversations")
                .select("id")
                .eq("user_id", user_id)
                .eq("status", status)
                .limit(1)
                .execute())
        if resp.data:
            return True
    return False


def has_recent_reengagement(user_id: str, within_days: int = 14) -> bool:
    cutoff = datetime.now(timezone.utc)
    resp = (get_client().table("conversations")
            .select("id, created_at")
            .eq("user_id", user_id)
            .eq("type", "Re-engagement")
            .order("created_at", desc=True)
            .limit(1)
            .execute())
    if not resp.data:
        return False
    last = datetime.fromisoformat(resp.data[0].get("created_at", "").replace("Z", "+00:00"))
    return (cutoff - last).days < within_days


def count_thread_replies(user_id: str) -> int:
    """Count the number of Follow-up replies sent since the last Check-in for a user.

    This effectively counts replies within the current 'thread' / check-in cycle,
    used to enforce the 4-reply cap per thread.
    """
    # Get the most recent check-in
    checkin_resp = (get_client().table("conversations")
                    .select("created_at")
                    .eq("user_id", user_id)
                    .eq("type", "Check-in")
                    .eq("status", "Sent")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute())

    if checkin_resp.data:
        last_checkin_time = checkin_resp.data[0]["created_at"]
        # Count follow-ups since that check-in
        followup_resp = (get_client().table("conversations")
                         .select("id")
                         .eq("user_id", user_id)
                         .eq("type", "Follow-up")
                         .eq("status", "Sent")
                         .gt("created_at", last_checkin_time)
                         .execute())
        return len(followup_resp.data)
    else:
        # No check-in found, count all follow-ups
        followup_resp = (get_client().table("conversations")
                         .select("id")
                         .eq("user_id", user_id)
                         .eq("type", "Follow-up")
                         .eq("status", "Sent")
                         .execute())
        return len(followup_resp.data)


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


def get_correction_stats() -> dict:
    """Get correction statistics grouped by type for analytics."""
    resp = get_client().table("corrected_responses").select("correction_type, created_at").execute()
    stats = {}
    for row in resp.data:
        ctype = row.get("correction_type", "Unknown")
        stats[ctype] = stats.get(ctype, 0) + 1
    return stats


# ── Resources ─────────────────────────────────────────────────

def get_all_resources():
    resp = get_client().table("resources").select("*").order("name").execute()
    return resp.data


def get_resources_by_stage(stage: str = None):
    """Get resources, optionally filtered by stage (includes stage=NULL for all-stage resources)."""
    if stage:
        resp = (get_client().table("resources")
                .select("*")
                .or_(f"stage.eq.{stage},stage.is.null")
                .order("name")
                .execute())
    else:
        resp = get_client().table("resources").select("*").order("name").execute()
    return resp.data


def get_resource_list_for_prompt(stage: str = None) -> str:
    """Get a formatted string of resources for inclusion in AI prompts."""
    resources = get_resources_by_stage(stage)
    if not resources:
        return "No resources available"
    lines = []
    for r in resources:
        topics = ", ".join(r.get("topics", [])) if r.get("topics") else ""
        lines.append(f"- {r['name']}: {r.get('description', '')} (Topics: {topics})")
    return "\n".join(lines)


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


def complete_workflow_run(run_id: str, items_processed: int = 0,
                          items_failed: int = 0, items_skipped: int = 0):
    status = "completed_with_errors" if items_failed > 0 else "completed"
    update_data = {
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "items_processed": items_processed,
    }
    # Store failure/skip info in error_message field if any failures occurred
    if items_failed > 0 or items_skipped > 0:
        update_data["error_message"] = f"{items_failed} failed, {items_skipped} skipped"
    get_client().table("workflow_runs").update(update_data).eq("id", run_id).execute()


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


# ── Analytics ──────────────────────────────────────────────────

def get_confidence_calibration_data() -> list[dict]:
    """Get data for confidence calibration: confidence score vs was_edited.

    Returns list of dicts with confidence, was_edited, approved_by,
    response_time_hours for conversations that were reviewed.
    """
    resp = (get_client().table("conversations")
            .select("confidence, ai_response, sent_response, status, approved_by, created_at, approved_at")
            .in_("status", ["Sent", "Approved"])
            .order("created_at", desc=True)
            .limit(500)
            .execute())

    results = []
    for c in resp.data:
        was_edited = (c.get("sent_response") is not None
                      and c.get("sent_response", "").strip() != (c.get("ai_response") or "").strip())
        # Calculate response time (time from creation to approval)
        response_time_hours = None
        if c.get("created_at") and c.get("approved_at"):
            try:
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                approved = datetime.fromisoformat(c["approved_at"].replace("Z", "+00:00"))
                response_time_hours = (approved - created).total_seconds() / 3600
            except (ValueError, TypeError):
                pass

        results.append({
            "confidence": c.get("confidence"),
            "was_edited": was_edited,
            "approved_by": c.get("approved_by"),
            "response_time_hours": response_time_hours,
        })
    return results


def get_satisfaction_trend(user_id: str = None, limit: int = 50) -> list[dict]:
    """Get satisfaction scores over time for trend analysis."""
    q = (get_client().table("conversations")
         .select("satisfaction_score, created_at, user_id")
         .not_.is_("satisfaction_score", "null")
         .order("created_at", desc=True)
         .limit(limit))
    if user_id:
        q = q.eq("user_id", user_id)
    resp = q.execute()
    return resp.data
