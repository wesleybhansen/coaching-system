"""System settings and status page."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db

st.set_page_config(page_title="Settings", layout="wide")
st.title("Settings")

# ── Run Workflows ─────────────────────────────────────────
st.subheader("Run Workflows")
st.markdown("Run any workflow manually. These also run automatically on schedule via GitHub Actions.")

wf_col1, wf_col2, wf_col3 = st.columns(3)

with wf_col1:
    if st.button("\U0001f4e8 Process Emails", use_container_width=True, help="Fetch unread emails and generate AI responses"):
        with st.spinner("Processing emails..."):
            try:
                from workflows import process_emails
                process_emails.run()
                st.success("Emails processed!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with wf_col2:
    if st.button("\u2709\ufe0f Send Approved", use_container_width=True, help="Send all approved responses"):
        with st.spinner("Sending approved responses..."):
            try:
                from workflows import send_approved
                send_approved.run()
                st.success("Approved responses sent!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with wf_col3:
    if st.button("\U0001f44b Check In", use_container_width=True, help="Send check-in messages to quiet users"):
        with st.spinner("Sending check-ins..."):
            try:
                from workflows import check_in
                check_in.run()
                st.success("Check-ins sent!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

wf_col4, wf_col5, _ = st.columns(3)

with wf_col4:
    if st.button("\U0001f504 Re-engagement", use_container_width=True, help="Nudge users silent 10+ days"):
        with st.spinner("Running re-engagement..."):
            try:
                from workflows import re_engagement
                re_engagement.run()
                st.success("Re-engagement complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with wf_col5:
    if st.button("\U0001f9f9 Cleanup", use_container_width=True, help="Catch any emails that slipped through"):
        with st.spinner("Running cleanup..."):
            try:
                from workflows import cleanup
                cleanup.run()
                st.success("Cleanup complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

st.divider()

# Load current settings
settings = db.get_all_settings()

# ── Auto-Approve ───────────────────────────────────────────────
st.subheader("Auto-Approve Threshold")
st.markdown("Responses with confidence >= this threshold will be auto-approved. "
            "Start at 10 (nothing auto-approves) and lower gradually as trust builds.")

current_threshold = int(settings.get("global_auto_approve_threshold", "10"))
new_threshold = st.slider(
    "Global threshold",
    min_value=1,
    max_value=10,
    value=current_threshold,
    help="1 = auto-approve almost everything, 10 = manual review everything",
)
if new_threshold != current_threshold:
    db.set_setting("global_auto_approve_threshold", str(new_threshold))
    st.success(f"Threshold updated to {new_threshold}")

# ── Check-in Schedule ─────────────────────────────────────
st.subheader("Check-in Schedule")

col1, col2 = st.columns(2)
with col1:
    days_str = settings.get("check_in_days", "tue,fri")
    day_options = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    current_days = [d.strip().lower() for d in days_str.split(",")]
    selected_days = st.multiselect(
        "Check-in days",
        options=day_options,
        default=current_days,
        format_func=lambda x: x.capitalize(),
    )
    new_days = ",".join(selected_days)
    if new_days != days_str:
        db.set_setting("check_in_days", new_days)
        st.success("Check-in days updated")

with col2:
    current_hour = int(settings.get("check_in_hour", "9"))
    new_hour = st.number_input("Check-in hour (24h)", min_value=0, max_value=23, value=current_hour)
    if new_hour != current_hour:
        db.set_setting("check_in_hour", str(new_hour))
        st.success("Check-in hour updated")

# ── Processing Schedule ───────────────────────────────────
st.subheader("Email Processing")

col1, col2, col3 = st.columns(3)
with col1:
    interval = int(settings.get("process_interval_minutes", "60"))
    new_interval = st.number_input("Process interval (minutes)", min_value=15, max_value=240, value=interval)
    if new_interval != interval:
        db.set_setting("process_interval_minutes", str(new_interval))
        st.success("Interval updated")

with col2:
    start_h = int(settings.get("process_start_hour", "8"))
    new_start = st.number_input("Start hour (24h)", min_value=0, max_value=23, value=start_h)
    if new_start != start_h:
        db.set_setting("process_start_hour", str(new_start))
        st.success("Start hour updated")

with col3:
    end_h = int(settings.get("process_end_hour", "21"))
    new_end = st.number_input("End hour (24h)", min_value=0, max_value=23, value=end_h)
    if new_end != end_h:
        db.set_setting("process_end_hour", str(new_end))
        st.success("End hour updated")

# ── Send Hours ────────────────────────────────────────────
st.subheader("Send Hours")
send_hours = settings.get("send_hours", "9,13,19")
new_send = st.text_input("Hours to send approved responses (comma-separated)", value=send_hours)
if new_send != send_hours:
    db.set_setting("send_hours", new_send)
    st.success("Send hours updated")

# ── Re-engagement ─────────────────────────────────────────
st.subheader("Re-engagement")
re_days = int(settings.get("re_engagement_days", "10"))
new_re_days = st.number_input("Days of silence before nudge", min_value=3, max_value=30, value=re_days)
if new_re_days != re_days:
    db.set_setting("re_engagement_days", str(new_re_days))
    st.success("Re-engagement days updated")

# ── Response Length ────────────────────────────────────────
st.subheader("Response Settings")
max_p = int(settings.get("max_response_paragraphs", "3"))
new_max_p = st.number_input("Max response paragraphs", min_value=1, max_value=5, value=max_p)
if new_max_p != max_p:
    db.set_setting("max_response_paragraphs", str(new_max_p))
    st.success("Max paragraphs updated")

# ── Gmail Status ──────────────────────────────────────────
st.subheader("Gmail Connection")
try:
    from services import gmail_service
    gmail_service._imap_connect().logout()
    st.success("Gmail connection: OK")
except Exception as e:
    st.error(f"Gmail connection failed: {e}")

# ── Workflow History ──────────────────────────────────────
st.subheader("Recent Workflow Runs (24h)")
runs = db.get_recent_workflow_runs(hours=24)
if runs:
    for run in runs:
        status_icon = {"completed": "\u2705", "failed": "\u274c", "running": "\u23f3"}.get(
            run.get("status", ""), "\u2753")
        started = (run.get("started_at") or "")[:19].replace("T", " ")
        st.write(
            f"{status_icon} **{run['workflow_name']}** — {started} — "
            f"{run.get('items_processed', 0)} items"
        )
        if run.get("error_message"):
            st.error(run["error_message"])
else:
    st.info("No workflow runs recorded.")

st.divider()
st.caption("Workflows also run automatically on schedule via GitHub Actions.")
