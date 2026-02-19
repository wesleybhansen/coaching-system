"""Review and approve pending AI-generated coaching responses."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

# ── Bulk approve section ───────────────────────────────────────
eligible = [c for c in conversations if (c.get("confidence") or 0) >= 7]

if eligible:
    st.markdown("---")
    bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 2, 2])

    with bulk_col1:
        if st.button("Select all eligible", key="select_all"):
            for c in eligible:
                st.session_state[f"bulk_{c['id']}"] = True
            st.rerun()
    with bulk_col2:
        if st.button("Deselect all", key="deselect_all"):
            for c in conversations:
                st.session_state[f"bulk_{c['id']}"] = False
            st.rerun()

    selected_ids = [c["id"] for c in eligible if st.session_state.get(f"bulk_{c['id']}")]

    with bulk_col3:
        if selected_ids:
            if st.button(f"Bulk Approve {len(selected_ids)} Selected", type="primary", key="bulk_approve"):
                for cid in selected_ids:
                    db.update_conversation(cid, {
                        "status": "Approved",
                        "approved_at": datetime.now(timezone.utc).isoformat(),
                        "approved_by": "manual_bulk",
                    })
                st.success(f"Bulk approved {len(selected_ids)} conversation(s)")
                st.rerun()

    st.markdown("---")

# ── Individual conversation cards ──────────────────────────────
for conv in conversations:
    user = conv.get("users") or {}
    user_name = user.get("first_name") or user.get("email", "Unknown")
    confidence = conv.get("confidence", "?")
    is_eligible = isinstance(confidence, (int, float)) and confidence >= 7

    with st.container(border=True):
        # Header with optional bulk checkbox
        header_cols = st.columns([0.5, 3, 1, 1]) if eligible else st.columns([3, 1, 1])

        if eligible:
            with header_cols[0]:
                if is_eligible:
                    st.checkbox(
                        "Select",
                        key=f"bulk_{conv['id']}",
                        label_visibility="collapsed",
                    )
            header_cols[1].subheader(f"{user_name}")
            header_cols[2].metric("Confidence", f"{confidence}/10")
            header_cols[3].write(f"**Stage:** {user.get('stage', '?')}")
        else:
            header_cols[0].subheader(f"{user_name}")
            header_cols[1].metric("Confidence", f"{confidence}/10")
            header_cols[2].write(f"**Stage:** {user.get('stage', '?')}")

        # Confidence breakdown (sub-scores from evaluation)
        eval_details = conv.get("evaluation_details")
        if isinstance(eval_details, dict):
            with st.expander("Confidence breakdown"):
                s1, s2, s3, s4, s5 = st.columns(5)
                s1.metric("Relevance", f"{eval_details.get('relevance', '?')}/10")
                s2.metric("Tone", f"{eval_details.get('tone', '?')}/10")
                s3.metric("Actionability", f"{eval_details.get('actionability', '?')}/10")
                s4.metric("Length", f"{eval_details.get('length', '?')}/10")
                s5.metric("Closing Q", f"{eval_details.get('closing_question', '?')}/10")

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
