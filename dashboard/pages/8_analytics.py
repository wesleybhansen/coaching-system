"""Analytics dashboard for coaching system performance metrics."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd

from db import supabase_client as db

st.set_page_config(page_title="Analytics", layout="wide")
st.title("Analytics")

# ── 1. User Overview Metrics ──────────────────────────────────

st.subheader("User Overview")

users = db.get_all_users()

if users:
    total_users = len(users)
    status_counts = {}
    for u in users:
        s = u.get("status", "Unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Users", total_users)
    col2.metric("Active", status_counts.get("Active", 0))
    col3.metric("Paused", status_counts.get("Paused", 0))
    col4.metric("Silent", status_counts.get("Silent", 0))
    col5.metric("Onboarding", status_counts.get("Onboarding", 0))
else:
    st.info("No users yet.")

st.divider()

# ── 2. Confidence Calibration ─────────────────────────────────

st.subheader("Confidence Calibration")

calibration_data = db.get_confidence_calibration_data()

if calibration_data:
    df_cal = pd.DataFrame(calibration_data)

    # Filter to rows with a confidence score
    df_cal = df_cal[df_cal["confidence"].notna()].copy()

    if not df_cal.empty:
        # Overall edit rate
        total_responses = len(df_cal)
        total_edited = df_cal["was_edited"].sum()
        overall_edit_rate = (total_edited / total_responses * 100) if total_responses > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Reviewed Responses", total_responses)
        col2.metric("Responses Edited", int(total_edited))
        col3.metric("Overall Edit Rate", f"{overall_edit_rate:.1f}%")

        # Group by confidence score
        df_cal["confidence"] = df_cal["confidence"].astype(int)
        grouped = df_cal.groupby("confidence").agg(
            count=("was_edited", "size"),
            edited=("was_edited", "sum"),
            avg_response_time=("response_time_hours", "mean"),
        ).reset_index()
        grouped["edit_rate_%"] = (grouped["edited"] / grouped["count"] * 100).round(1)
        grouped["avg_response_time"] = grouped["avg_response_time"].round(2)
        grouped = grouped.rename(columns={
            "confidence": "Confidence",
            "count": "Responses",
            "edited": "Edited",
            "avg_response_time": "Avg Response Time (hrs)",
        })

        st.dataframe(grouped, use_container_width=True, hide_index=True)

        # Bar chart of edit rate by confidence
        try:
            chart_df = grouped.set_index("Confidence")[["edit_rate_%"]]
            chart_df = chart_df.reindex(range(1, 11), fill_value=0)
            st.bar_chart(chart_df, y="edit_rate_%", y_label="Edit Rate (%)", x_label="Confidence Score")
        except Exception:
            st.caption("Could not render confidence chart.")
    else:
        st.info("No responses with confidence scores yet.")
else:
    st.info("No calibration data yet.")

st.divider()

# ── 3. Response Time Tracking ─────────────────────────────────

st.subheader("Response Time Tracking")

if calibration_data:
    df_rt = pd.DataFrame(calibration_data)
    df_rt = df_rt[df_rt["response_time_hours"].notna()].copy()

    if not df_rt.empty:
        avg_time = df_rt["response_time_hours"].mean()
        median_time = df_rt["response_time_hours"].median()
        min_time = df_rt["response_time_hours"].min()
        max_time = df_rt["response_time_hours"].max()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Response Time", f"{avg_time:.1f} hrs")
        col2.metric("Median Response Time", f"{median_time:.1f} hrs")
        col3.metric("Fastest", f"{min_time:.1f} hrs")
        col4.metric("Slowest", f"{max_time:.1f} hrs")

        # Distribution as histogram-like bar chart
        try:
            bins = [0, 1, 2, 4, 8, 12, 24, 48, float("inf")]
            labels = ["<1h", "1-2h", "2-4h", "4-8h", "8-12h", "12-24h", "24-48h", "48h+"]
            df_rt["bucket"] = pd.cut(df_rt["response_time_hours"], bins=bins, labels=labels, right=False)
            bucket_counts = df_rt["bucket"].value_counts().reindex(labels, fill_value=0)
            chart_df = pd.DataFrame({"Responses": bucket_counts.values}, index=bucket_counts.index)
            chart_df.index.name = "Response Time"
            st.bar_chart(chart_df, y="Responses", x_label="Response Time", y_label="Count")
        except Exception:
            st.caption("Could not render response time distribution.")
    else:
        st.info("No response time data yet.")
else:
    st.info("No data available for response time tracking.")

st.divider()

# ── 4. Correction Analytics ───────────────────────────────────

st.subheader("Correction Analytics")

correction_stats = db.get_correction_stats()

if correction_stats:
    total_corrections = sum(correction_stats.values())
    st.metric("Total Corrections", total_corrections)

    try:
        df_corr = pd.DataFrame(
            list(correction_stats.items()),
            columns=["Correction Type", "Count"],
        ).sort_values("Count", ascending=False)

        st.bar_chart(df_corr.set_index("Correction Type"), y="Count", x_label="Correction Type", y_label="Count")
    except Exception:
        st.caption("Could not render correction chart.")

    st.dataframe(
        pd.DataFrame(list(correction_stats.items()), columns=["Type", "Count"]).sort_values("Count", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No corrections recorded yet.")

st.divider()

# ── 5. Satisfaction Trends ────────────────────────────────────

st.subheader("Satisfaction Trends")

satisfaction_data = db.get_satisfaction_trend()

if satisfaction_data:
    df_sat = pd.DataFrame(satisfaction_data)
    df_sat = df_sat[df_sat["satisfaction_score"].notna()].copy()

    if not df_sat.empty:
        avg_satisfaction = df_sat["satisfaction_score"].mean()
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Satisfaction", f"{avg_satisfaction:.1f} / 10")
        col2.metric("Responses with Scores", len(df_sat))
        col3.metric("Unique Users", df_sat["user_id"].nunique())

        # Line chart over time
        try:
            df_sat["created_at"] = pd.to_datetime(df_sat["created_at"])
            df_sat = df_sat.sort_values("created_at")
            chart_df = df_sat.set_index("created_at")[["satisfaction_score"]]
            chart_df = chart_df.rename(columns={"satisfaction_score": "Satisfaction Score"})
            st.line_chart(chart_df, y="Satisfaction Score", x_label="Date", y_label="Score")
        except Exception:
            st.caption("Could not render satisfaction trend chart.")
    else:
        st.info("No satisfaction scores recorded yet.")
else:
    st.info("No satisfaction data yet.")
