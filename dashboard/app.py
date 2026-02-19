"""Streamlit dashboard for the Coach Wes Coaching System."""

import os
import sys

# Ensure the project root is on the Python path so imports like `db`, `services` work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Coach Wes Dashboard",
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Password protection ---
def check_password():
    """Return True if the user entered the correct password."""
    password = st.secrets.get("DASHBOARD_PASSWORD", "")
    if not password:
        return True  # No password configured, skip gate

    if st.session_state.get("authenticated"):
        return True

    st.title("Coach Wes Dashboard")
    entered = st.text_input("Password", type="password")
    if st.button("Log in"):
        if entered == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

st.title("Coach Wes Coaching System")

st.markdown("""
### Welcome to the coaching dashboard

Use the sidebar to navigate between pages:

- **Pending Review** — Review and approve AI-generated coaching responses
- **Flagged** — Responses that need special attention
- **Conversations** — Browse all conversation history
- **Users** — Manage coaching program members
- **Corrections** — View and add corrected responses for AI learning
- **Settings** — Configure auto-approve thresholds, schedules, and system status
""")

# Quick stats
try:
    from db import supabase_client as db

    col1, col2, col3, col4 = st.columns(4)

    pending = db.get_conversations_by_status("Pending Review")
    flagged = db.get_conversations_by_status("Flagged")
    users = db.get_all_users()
    active_users = [u for u in users if u.get("status") == "Active"]

    col1.metric("Pending Review", len(pending))
    col2.metric("Flagged", len(flagged))
    col3.metric("Active Users", len(active_users))
    col4.metric("Total Users", len(users))

    # Error banner: failed workflows and send failures
    try:
        send_failed = db.get_conversations_by_status("Send Failed")
        recent_runs = db.get_recent_workflow_runs(hours=24, limit=50)
        failed_runs = [r for r in recent_runs if r.get("status") in ("failed", "completed_with_errors")]

        alerts = []
        if send_failed:
            alerts.append(f"{len(send_failed)} conversation(s) failed to send")
        if failed_runs:
            alerts.append(f"{len(failed_runs)} workflow(s) had errors in the last 24h")

        if alerts:
            st.error("**Attention needed:** " + " | ".join(alerts))
            with st.expander("Error details"):
                if send_failed:
                    st.markdown("**Send failures:**")
                    for sf in send_failed[:10]:
                        attempts = sf.get("send_attempts", 0)
                        st.write(f"- Conversation {sf['id'][:8]}... ({attempts} attempt(s))")
                if failed_runs:
                    st.markdown("**Failed workflows:**")
                    for fr in failed_runs[:10]:
                        started = (fr.get("started_at") or "")[:19].replace("T", " ")
                        st.write(f"- {fr['workflow_name']} at {started}: {fr.get('error_message', 'Unknown error')}")
    except Exception:
        pass  # Don't let the error banner crash the dashboard

    # Recent workflow runs
    st.subheader("Recent Workflow Runs")
    runs = db.get_recent_workflow_runs(hours=24, limit=10)
    if runs:
        for run in runs:
            status_icon = {"completed": "\u2705", "failed": "\u274c", "running": "\u23f3"}.get(
                run.get("status", ""), "\u2753")
            started = run.get("started_at", "")[:19].replace("T", " ")
            st.write(
                f"{status_icon} **{run['workflow_name']}** — {started} — "
                f"{run.get('items_processed', 0)} items — {run['status']}"
            )
            if run.get("error_message"):
                st.error(run["error_message"])
    else:
        st.info("No workflow runs in the last 24 hours.")

except Exception as e:
    st.warning(f"Could not connect to Supabase. Check your environment variables.\n\n{e}")
