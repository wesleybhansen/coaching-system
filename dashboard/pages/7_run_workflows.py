"""Run workflows manually and monitor system status."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from datetime import datetime, timezone

from db import supabase_client as db

st.set_page_config(page_title="Run Workflows", layout="wide")
st.title("Run Workflows")

# ── System Status ────────────────────────────────────────────
st.subheader("System Status")

# Quick health checks
status_cols = st.columns(4)

with status_cols[0]:
    try:
        db.get_setting("global_auto_approve_threshold")
        st.metric("Database", "✅ Connected")
    except Exception:
        st.metric("Database", "❌ Error")

with status_cols[1]:
    try:
        from services import gmail_service
        gmail_service._imap_connect().logout()
        st.metric("Gmail", "✅ Connected")
    except Exception:
        st.metric("Gmail", "❌ Error")

with status_cols[2]:
    import platform
    py_ver = platform.python_version()
    ok = tuple(int(x) for x in py_ver.split(".")[:2]) >= (3, 9)
    st.metric("Python", f"{'✅' if ok else '⚠️'} {py_ver}")

with status_cols[3]:
    # Check if migration has been applied by looking for a new column
    try:
        users = db.get_client().table("users").select("checkin_days").limit(1).execute()
        st.metric("Migration v2", "✅ Applied")
    except Exception:
        st.metric("Migration v2", "❌ Not applied")

# ── Automated Schedule ───────────────────────────────────────
st.divider()
st.subheader("Automated Schedule (GitHub Actions)")
st.caption("All workflows run automatically via GitHub Actions. Times shown in Eastern.")

schedule_data = [
    {"Workflow": "📨 Process Emails", "Schedule": "Every hour, 8am–9pm ET", "Cron (UTC)": "0 13-23,0-2 * * *"},
    {"Workflow": "✉️ Send Approved", "Schedule": "9am, 1pm, 7pm ET", "Cron (UTC)": "0 14,18,0 * * *"},
    {"Workflow": "👋 Check In", "Schedule": "Daily at 9am ET", "Cron (UTC)": "0 14 * * *"},
    {"Workflow": "🔄 Re-engagement", "Schedule": "Daily at 10am ET", "Cron (UTC)": "0 15 * * *"},
    {"Workflow": "🧹 Cleanup", "Schedule": "Daily at 11pm ET", "Cron (UTC)": "0 4 * * *"},
]
st.table(schedule_data)

st.info(
    "💡 **Check-ins run daily** but the code checks each user's personal schedule "
    "(set on the Users page). Only users scheduled for today will get a check-in."
)

# ── Manual Triggers ──────────────────────────────────────────
st.divider()
st.subheader("Manual Triggers")
st.markdown("Run any workflow on-demand. Results appear in the run history below.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📨 Process Emails", use_container_width=True, help="Fetch unread emails and generate AI responses"):
        with st.spinner("Processing emails..."):
            try:
                from workflows import process_emails
                process_emails.run()
                st.success("Emails processed!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col2:
    if st.button("✉️ Send Approved", use_container_width=True, help="Send all approved responses"):
        with st.spinner("Sending approved responses..."):
            try:
                from workflows import send_approved
                send_approved.run()
                st.success("Approved responses sent!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col3:
    if st.button("👋 Check In", use_container_width=True, help="Send check-in messages to users scheduled for today"):
        with st.spinner("Sending check-ins..."):
            try:
                from workflows import check_in
                check_in.run()
                st.success("Check-ins sent!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

col4, col5, _ = st.columns(3)

with col4:
    if st.button("🔄 Re-engagement", use_container_width=True, help="Nudge users silent 10+ days"):
        with st.spinner("Running re-engagement..."):
            try:
                from workflows import re_engagement
                re_engagement.run()
                st.success("Re-engagement complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col5:
    if st.button("🧹 Cleanup", use_container_width=True, help="Catch any emails that slipped through"):
        with st.spinner("Running cleanup..."):
            try:
                from workflows import cleanup
                cleanup.run()
                st.success("Cleanup complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

# ── Workflow Run History ─────────────────────────────────────
st.divider()
st.subheader("Workflow Run History")

history_hours = st.selectbox("Show runs from last", [24, 48, 72, 168], format_func=lambda x: f"{x} hours" if x < 168 else "7 days")
runs = db.get_recent_workflow_runs(hours=history_hours)

if runs:
    # Summary stats
    completed = sum(1 for r in runs if r.get("status") == "completed")
    failed = sum(1 for r in runs if r.get("status") == "failed")
    running = sum(1 for r in runs if r.get("status") == "running")

    stat_cols = st.columns(4)
    stat_cols[0].metric("Total Runs", len(runs))
    stat_cols[1].metric("Completed", completed)
    stat_cols[2].metric("Failed", failed)
    stat_cols[3].metric("Running", running)

    # Group by workflow for quick overview
    workflow_names = sorted(set(r.get("workflow_name", "unknown") for r in runs))
    for wf_name in workflow_names:
        wf_runs = [r for r in runs if r.get("workflow_name") == wf_name]
        last_run = wf_runs[0] if wf_runs else None
        last_status = last_run.get("status", "unknown") if last_run else "never"
        status_icon = {"completed": "✅", "failed": "❌", "running": "⏳"}.get(last_status, "❓")
        last_time = (last_run.get("started_at") or "")[:19].replace("T", " ") if last_run else "Never"
        items = last_run.get("items_processed", 0) if last_run else 0

        with st.expander(f"{status_icon} **{wf_name}** — Last: {last_time} — {items} items — ({len(wf_runs)} runs)"):
            for run in wf_runs:
                run_icon = {"completed": "✅", "failed": "❌", "running": "⏳"}.get(run.get("status", ""), "❓")
                started = (run.get("started_at") or "")[:19].replace("T", " ")
                st.write(
                    f"{run_icon} {started} — "
                    f"{run.get('items_processed', 0)} items processed"
                )
                if run.get("error_message"):
                    st.error(run["error_message"])
else:
    st.info(f"No workflow runs in the last {history_hours} hours.")
