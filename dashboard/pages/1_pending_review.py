"""Review and approve pending AI-generated coaching responses."""

import streamlit as st
from datetime import datetime, timezone

from db import supabase_client as db

st.set_page_config(page_title="Pending Review", layout="wide")
st.title("Pending Review")

conversations = db.get_conversations_by_status("Pending Review")

if not conversations:
    st.success("No pending responses to review!")
    st.stop()

st.info(f"{len(conversations)} response(s) awaiting review")

for conv in conversations:
    user = conv.get("users") or {}
    user_name = user.get("first_name") or user.get("email", "Unknown")
    confidence = conv.get("confidence", "?")

    with st.container(border=True):
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.subheader(f"{user_name}")
        col2.metric("Confidence", f"{confidence}/10")
        col3.write(f"**Stage:** {user.get('stage', '?')}")

        if conv.get("flag_reason"):
            st.warning(f"Flag: {conv['flag_reason']}")

        # User's message
        st.markdown("**Their message:**")
        st.text_area(
            "User message",
            value=conv.get("user_message_parsed") or conv.get("user_message_raw", ""),
            height=100,
            disabled=True,
            key=f"user_msg_{conv['id']}",
            label_visibility="collapsed",
        )

        # AI response (editable)
        st.markdown("**AI Response (editable):**")
        edited_response = st.text_area(
            "AI response",
            value=conv.get("ai_response", ""),
            height=150,
            key=f"ai_resp_{conv['id']}",
            label_visibility="collapsed",
        )

        # Context expander
        with st.expander("View user context"):
            st.write(f"**Business Idea:** {user.get('business_idea', 'Not specified')}")
            st.write(f"**Summary:** {user.get('summary', 'No summary yet')}")

            recent = db.get_recent_conversations(user.get("id", ""), limit=3)
            if recent:
                st.markdown("**Recent exchanges:**")
                for r in recent:
                    st.markdown(f"- **User:** {(r.get('user_message_parsed') or '')[:100]}...")
                    st.markdown(f"  **Coach:** {(r.get('sent_response') or r.get('ai_response') or '')[:100]}...")

        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("Approve", key=f"approve_{conv['id']}", type="primary"):
                original = conv.get("ai_response", "")
                was_edited = edited_response.strip() != original.strip()

                updates = {
                    "status": "Approved",
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "approved_by": "manual",
                }

                if was_edited:
                    updates["sent_response"] = edited_response
                    # Create correction record for learning
                    db.create_correction({
                        "conversation_id": conv["id"],
                        "original_message": conv.get("user_message_parsed", ""),
                        "ai_response": original,
                        "corrected_response": edited_response,
                        "correction_notes": "Edited during review",
                        "correction_type": "Content",
                    })

                db.update_conversation(conv["id"], updates)
                st.success("Approved!" + (" (correction saved)" if was_edited else ""))
                st.rerun()

        with btn_col2:
            if st.button("Reject", key=f"reject_{conv['id']}"):
                db.update_conversation(conv["id"], {"status": "Rejected"})
                st.info("Rejected")
                st.rerun()

        with btn_col3:
            if st.button("Flag", key=f"flag_{conv['id']}"):
                db.update_conversation(conv["id"], {
                    "status": "Flagged",
                    "flag_reason": "Manually flagged during review",
                })
                st.warning("Flagged for attention")
                st.rerun()
