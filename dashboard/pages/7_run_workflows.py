"""Run workflows manually from the dashboard."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

st.set_page_config(page_title="Run Workflows", layout="wide")
st.title("Run Workflows")
st.markdown("Run any workflow manually. These also run automatically on schedule via GitHub Actions.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("\U0001f4e8 Process Emails", use_container_width=True, help="Fetch unread emails and generate AI responses"):
        with st.spinner("Processing emails..."):
            try:
                from workflows import process_emails
                process_emails.run()
                st.success("Emails processed!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col2:
    if st.button("\u2709\ufe0f Send Approved", use_container_width=True, help="Send all approved responses"):
        with st.spinner("Sending approved responses..."):
            try:
                from workflows import send_approved
                send_approved.run()
                st.success("Approved responses sent!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col3:
    if st.button("\U0001f44b Check In", use_container_width=True, help="Send check-in messages to quiet users"):
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
    if st.button("\U0001f504 Re-engagement", use_container_width=True, help="Nudge users silent 10+ days"):
        with st.spinner("Running re-engagement..."):
            try:
                from workflows import re_engagement
                re_engagement.run()
                st.success("Re-engagement complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

with col5:
    if st.button("\U0001f9f9 Cleanup", use_container_width=True, help="Catch any emails that slipped through"):
        with st.spinner("Running cleanup..."):
            try:
                from workflows import cleanup
                cleanup.run()
                st.success("Cleanup complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

# Show recent workflow history
st.divider()
st.subheader("Recent Workflow Runs (24h)")

from db import supabase_client as db

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
    st.info("No workflow runs in the last 24 hours.")
