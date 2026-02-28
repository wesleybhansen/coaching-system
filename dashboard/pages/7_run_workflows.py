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
        st.write("✅ **Database** — Connected")
    except Exception:
        st.write("❌ **Database** — Error")

with status_cols[1]:
    try:
        from services import gmail_service
        gmail_service._imap_connect().logout()
        st.write("✅ **Gmail** — Connected")
    except Exception:
        st.write("❌ **Gmail** — Error")

with status_cols[2]:
    import platform
    py_ver = platform.python_version()
    ok = tuple(int(x) for x in py_ver.split(".")[:2]) >= (3, 9)
    st.write(f"{'✅' if ok else '⚠️'} **Python** — {py_ver}")

with status_cols[3]:
    # Check if migration has been applied by looking for a new column
    try:
        users = db.get_client().table("users").select("checkin_days").limit(1).execute()
        st.write("✅ **Migration v2** — Applied")
    except Exception:
        st.write("❌ **Migration v2** — Not applied")

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

st.info(
    "**How sending works:**\n\n"
    "- **Send Approved** runs automatically at scheduled times (9am, 1pm, 7pm ET). "
    "Clicking the button below sends immediately without waiting.\n"
    "- **Check In** generates check-in messages that go to **Pending Review** first — "
    "they are NOT sent directly to users.\n"
    "- After approving check-ins on the Pending Review page, they wait for the next "
    "Send Approved run, or click Send Approved to send them right away."
)

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
                import importlib
                from workflows import send_approved
                importlib.reload(send_approved)
                send_approved.run(immediate=True)
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

# ── Fine-Tuning Export ───────────────────────────────────────
st.divider()
st.subheader("Fine-Tuning Export")
st.markdown(
    "Export your corrected coaching responses as an OpenAI fine-tuning dataset. "
    "The more corrections you've made, the better the fine-tuned model will be."
)

# Show current correction count
try:
    corrections = db.get_all_corrections()
    total_corrections = len(corrections)
    usable = sum(1 for c in corrections if (c.get("corrected_response") or "").strip())
except Exception:
    total_corrections = 0
    usable = 0

ft_cols = st.columns(3)
ft_cols[0].metric("Total Corrections", total_corrections)
ft_cols[1].metric("Usable for Training", usable)
ft_cols[2].metric("Recommended Minimum", "50+", help="OpenAI recommends at least 50 examples for fine-tuning, though 10+ can work")

if usable < 10:
    st.warning(
        f"You have **{usable}** usable corrections. Keep reviewing and correcting AI responses "
        "to build up your training dataset. OpenAI recommends at least 50 examples."
    )

with st.expander("📖 How to use the fine-tuning file after export"):
    st.markdown("""
**What is fine-tuning?**

Fine-tuning takes a base model (like GPT-4o-mini) and trains it on your corrected coaching
responses so it learns *your* voice, style, and approach. The result is a custom model that
gives better responses out of the box — fewer corrections needed over time.

---

**Step-by-step guide:**

**1. Build your dataset (you're here!)**
- Review AI responses on the **Pending Review** and **Flagged** pages
- When a response needs changes, edit it and save — that creates a correction
- Aim for **50+ corrections** minimum (more is better — 100+ is ideal)
- Make sure corrections cover a variety of topics, stages, and response types

**2. Export and download**
- Set your filename and click **Export Fine-Tuning Data** below
- Click **Download JSONL File** to save it to your computer

**3. Upload to OpenAI**
- Go to [platform.openai.com/finetune](https://platform.openai.com/finetune)
- Click **Create** in the top right
- Select **gpt-4o-mini-2024-07-18** as the base model (best cost/quality balance)
- Upload your `.jsonl` file
- Click **Create** to start the fine-tuning job

*Alternatively, use the CLI:*
```bash
pip install openai
openai api fine_tuning.jobs.create -t finetune_data.jsonl -m gpt-4o-mini-2024-07-18
```

**4. Wait for training**
- Fine-tuning typically takes **15–45 minutes** depending on dataset size
- You'll get an email from OpenAI when it's done
- The new model will appear at [platform.openai.com/finetune](https://platform.openai.com/finetune)

**5. Switch to your fine-tuned model**
- Copy your fine-tuned model ID (looks like `ft:gpt-4o-mini-2024-07-18:your-org::abc123`)
- Go to the **Settings** page in this dashboard
- Update the **Model** setting to your fine-tuned model ID
- The system will now use your custom model for all new responses

---

**Tips:**
- **Quality over quantity** — 50 great corrections beat 200 sloppy ones
- **Re-fine-tune periodically** — as you make more corrections, export and fine-tune again
- **Cost** — fine-tuning GPT-4o-mini is very affordable (~$0.80 per 100 examples)
- **Keep the base model as fallback** — save the original model ID in case you want to switch back
""")

# Export controls
ft_control_cols = st.columns([2, 1])
with ft_control_cols[0]:
    output_filename = st.text_input(
        "Output filename",
        value="finetune_data.jsonl",
        help="File will be saved in your project root directory",
    )
with ft_control_cols[1]:
    min_corrections = st.number_input(
        "Minimum corrections required",
        min_value=0,
        max_value=500,
        value=50,
        help="Export will skip if fewer corrections exist than this threshold",
    )

if st.button("🧠 Export Fine-Tuning Data", use_container_width=True, help="Generate JSONL file for OpenAI fine-tuning"):
    if usable == 0:
        st.error("No usable corrections found. Make some corrections on the Pending Review or Flagged pages first.")
    else:
        with st.spinner("Exporting fine-tuning data..."):
            try:
                from scripts.export_finetune_data import export_finetune_data
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                output_path = os.path.join(project_root, output_filename)
                stats = export_finetune_data(output_path, min_corrections=min_corrections)

                if stats["exported"] > 0:
                    st.success(
                        f"Exported **{stats['exported']}** training examples to `{output_filename}`  \n"
                        f"({stats['skipped']} skipped — missing corrected response)"
                    )

                    # Offer download
                    with open(output_path, "r") as f:
                        file_contents = f.read()
                    st.download_button(
                        label="📥 Download JSONL File",
                        data=file_contents,
                        file_name=output_filename,
                        mime="application/jsonl",
                    )
                    st.info("👆 Download the file, then follow the instructions above to upload it to OpenAI and start fine-tuning.")
                elif stats["total"] < min_corrections:
                    st.warning(
                        f"Only {stats['total']} corrections found, but minimum is set to {min_corrections}. "
                        "Lower the threshold or make more corrections."
                    )
                else:
                    st.warning("No examples could be exported. Check that corrections have a corrected_response field.")
            except Exception as e:
                st.error(f"Export failed: {e}")

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
