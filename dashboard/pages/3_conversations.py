"""Browse all conversations by user, status, and date."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db

st.set_page_config(page_title="Conversations", layout="wide")
st.title("Conversations")

# Filters
col1, col2 = st.columns(2)

with col1:
    users = db.get_all_users()
    user_options = {"All Users": None}
    for u in users:
        label = f"{u.get('first_name', '')} ({u['email']})"
        user_options[label] = u["id"]
    selected_user_label = st.selectbox("Filter by user", options=list(user_options.keys()))
    selected_user_id = user_options[selected_user_label]

with col2:
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Pending Review", "Approved", "Sent", "Flagged", "Rejected"],
    )

# Fetch conversations
if selected_user_id:
    conversations = db.get_conversations_for_user(selected_user_id)
else:
    conversations = db.get_all_conversations(limit=200)

# Apply status filter
if status_filter != "All":
    conversations = [c for c in conversations if c.get("status") == status_filter]

st.write(f"Showing {len(conversations)} conversation(s)")

for conv in conversations:
    user = conv.get("users") or {}
    user_name = user.get("first_name") or user.get("email", "")
    status = conv.get("status", "?")
    created = (conv.get("created_at") or "")[:19].replace("T", " ")

    status_colors = {
        "Sent": "green",
        "Approved": "blue",
        "Pending Review": "orange",
        "Flagged": "red",
        "Rejected": "gray",
    }
    color = status_colors.get(status, "gray")

    with st.expander(f":{color}[{status}] {user_name} — {created}"):
        col1, col2, col3 = st.columns(3)
        col1.write(f"**Type:** {conv.get('type', '?')}")
        col2.write(f"**Confidence:** {conv.get('confidence', '?')}/10")
        col3.write(f"**Stage:** {conv.get('stage_detected', '?')}")

        if conv.get("flag_reason"):
            st.warning(f"Flag: {conv['flag_reason']}")

        if conv.get("user_message_parsed") or conv.get("user_message_raw"):
            st.markdown("**User message:**")
            st.text(conv.get("user_message_parsed") or conv.get("user_message_raw", ""))

        if conv.get("ai_response"):
            st.markdown("**AI response:**")
            st.text(conv["ai_response"])

        if conv.get("sent_response") and conv["sent_response"] != conv.get("ai_response"):
            st.markdown("**Sent response (edited):**")
            st.text(conv["sent_response"])

        if conv.get("sent_at"):
            st.write(f"**Sent at:** {conv['sent_at'][:19].replace('T', ' ')}")
        if conv.get("resource_referenced"):
            st.write(f"**Resource referenced:** {conv['resource_referenced']}")
