"""Review flagged responses that need special attention."""

import streamlit as st
from datetime import datetime, timezone

from db import supabase_client as db

st.set_page_config(page_title="Flagged", layout="wide")
st.title("Flagged Responses")

conversations = db.get_conversations_by_status("Flagged")

if not conversations:
    st.success("No flagged responses!")
    st.stop()

st.warning(f"{len(conversations)} flagged response(s) need attention")

for conv in conversations:
    user = conv.get("users") or {}
    user_name = user.get("first_name") or user.get("email", "Unknown")
    confidence = conv.get("confidence", "?")

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        col1.subheader(f"{user_name}")
        col2.metric("Confidence", f"{confidence}/10")

        # Flag reason prominently displayed
        st.error(f"**Flag Reason:** {conv.get('flag_reason', 'Not specified')}")

        # User's message
        st.markdown("**Their message:**")
        st.text_area(
            "User message",
            value=conv.get("user_message_parsed") or conv.get("user_message_raw", ""),
            height=100,
            disabled=True,
            key=f"flagged_user_msg_{conv['id']}",
            label_visibility="collapsed",
        )

        # AI response (editable) — may be empty for cleanup-caught items
        st.markdown("**AI Response (editable):**")
        ai_resp = conv.get("ai_response") or ""
        edited_response = st.text_area(
            "AI response",
            value=ai_resp,
            height=150,
            key=f"flagged_ai_resp_{conv['id']}",
            label_visibility="collapsed",
            placeholder="Write a response here..." if not ai_resp else None,
        )

        # Context
        with st.expander("View user context"):
            st.write(f"**Stage:** {user.get('stage', '?')}")
            st.write(f"**Business Idea:** {user.get('business_idea', 'Not specified')}")
            st.write(f"**Summary:** {user.get('summary', 'No summary yet')}")

        # Actions
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("Approve", key=f"flagged_approve_{conv['id']}", type="primary"):
                response_to_save = edited_response.strip()
                if not response_to_save:
                    st.error("Please write a response before approving.")
                else:
                    updates = {
                        "status": "Approved",
                        "approved_at": datetime.now(timezone.utc).isoformat(),
                        "approved_by": "manual",
                    }
                    if response_to_save != ai_resp.strip():
                        updates["sent_response"] = response_to_save
                        if ai_resp:
                            db.create_correction({
                                "conversation_id": conv["id"],
                                "original_message": conv.get("user_message_parsed", ""),
                                "ai_response": ai_resp,
                                "corrected_response": response_to_save,
                                "correction_notes": "Corrected from flagged review",
                                "correction_type": "Content",
                            })
                    db.update_conversation(conv["id"], updates)
                    st.success("Approved!")
                    st.rerun()

        with btn_col2:
            if st.button("Reject", key=f"flagged_reject_{conv['id']}"):
                db.update_conversation(conv["id"], {"status": "Rejected"})
                st.info("Rejected")
                st.rerun()

        with btn_col3:
            if st.button("Move to Pending", key=f"flagged_pending_{conv['id']}"):
                db.update_conversation(conv["id"], {
                    "status": "Pending Review",
                    "flag_reason": None,
                })
                st.info("Moved to Pending Review")
                st.rerun()
