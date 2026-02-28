"""User management page."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db
from services import gmail_service

st.set_page_config(page_title="Users", layout="wide")
st.title("Users")

# Day options for checkin_days multiselect
DAY_OPTIONS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_OPTIONS_LOWER = [d.lower() for d in DAY_OPTIONS]

# Filter
status_filter = st.selectbox("Filter by status", ["All", "Active", "Paused", "Silent", "Onboarding"])

users = db.get_all_users()
if status_filter != "All":
    users = [u for u in users if u.get("status") == status_filter]

st.write(f"Showing {len(users)} user(s)")

# Add new user
with st.expander("Add new user"):
    with st.form("add_user"):
        new_email = st.text_input("Email")
        new_name = st.text_input("First name")
        new_stage = st.selectbox("Stage", ["Ideation", "Early Validation", "Late Validation", "Growth"])
        new_idea = st.text_area("Business idea", height=80)
        new_checkin_days = st.multiselect(
            "Check-in days (max 3, leave empty for system default)",
            options=DAY_OPTIONS,
            default=[],
            max_selections=3,
            key="new_user_checkin_days",
        )
        submitted = st.form_submit_button("Add User")

        if submitted and new_email:
            existing = db.get_user_by_email(new_email)
            if existing:
                st.error("User with this email already exists.")
            else:
                db.create_user(new_email, new_name)
                user = db.get_user_by_email(new_email)
                if user:
                    checkin_days_value = ",".join(d.lower() for d in new_checkin_days) if new_checkin_days else None
                    db.update_user(user["id"], {
                        "stage": new_stage,
                        "business_idea": new_idea if new_idea else None,
                        "status": "Onboarding",
                        "onboarding_step": 1,
                        "checkin_days": checkin_days_value,
                    })
                    # Create onboarding email in Pending Review
                    first = new_name or "there"
                    onboarding_body = gmail_service.get_onboarding_body(first)
                    db.create_conversation({
                        "user_id": user["id"],
                        "type": "Onboarding",
                        "status": "Pending Review",
                        "ai_response": onboarding_body,
                    })
                st.success(f"User {new_email} added! Onboarding email is in Pending Review.")
                st.rerun()

# User list
for user in users:
    status_icon = {"Active": "\U0001f7e2", "Paused": "\U0001f7e1", "Silent": "\U0001f534", "Onboarding": "\U0001f535"}.get(
        user.get("status", ""), "\u26aa")

    with st.expander(f"{status_icon} {user.get('first_name', '')} — {user['email']} ({user.get('status', '?')})"):
        with st.form(f"edit_user_{user['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                edit_name = st.text_input("First name", value=user.get("first_name", ""), key=f"name_{user['id']}")
                edit_stage = st.selectbox(
                    "Stage",
                    ["Ideation", "Early Validation", "Late Validation", "Growth"],
                    index=["Ideation", "Early Validation", "Late Validation", "Growth"].index(
                        user.get("stage", "Ideation")
                    ),
                    key=f"stage_{user['id']}",
                )
                edit_status = st.selectbox(
                    "Status",
                    ["Active", "Paused", "Silent", "Onboarding"],
                    index=["Active", "Paused", "Silent", "Onboarding"].index(
                        user.get("status", "Active")
                    ),
                    key=f"status_{user['id']}",
                )

            with col2:
                edit_idea = st.text_area("Business idea", value=user.get("business_idea", "") or "", height=80, key=f"idea_{user['id']}")
                edit_challenge = st.text_area("Current challenge", value=user.get("current_challenge", "") or "", height=80, key=f"challenge_{user['id']}")
                edit_notes = st.text_area("Notes", value=user.get("notes", "") or "", height=80, key=f"notes_{user['id']}")

                # Parse current checkin_days from comma-separated string
                user_checkin_str = user.get("checkin_days") or ""
                current_checkin = [d.strip().capitalize() for d in user_checkin_str.split(",") if d.strip()] if user_checkin_str else []
                # Filter to valid options only
                current_checkin = [d for d in current_checkin if d in DAY_OPTIONS]

                edit_checkin_days = st.multiselect(
                    "Check-in days (max 3, leave empty for system default)",
                    options=DAY_OPTIONS,
                    default=current_checkin,
                    max_selections=3,
                    key=f"checkin_days_{user['id']}",
                )

            if st.form_submit_button("Save Changes"):
                checkin_days_value = ",".join(d.lower() for d in edit_checkin_days) if edit_checkin_days else None
                db.update_user(user["id"], {
                    "first_name": edit_name,
                    "stage": edit_stage,
                    "status": edit_status,
                    "business_idea": edit_idea or None,
                    "current_challenge": edit_challenge or None,
                    "notes": edit_notes or None,
                    "checkin_days": checkin_days_value,
                })
                st.success("User updated!")
                st.rerun()

        # Summary (read-only)
        if user.get("summary"):
            st.markdown("**Journey Summary:**")
            st.text(user["summary"])

        st.write(f"**Satisfaction score:** {user.get('satisfaction_score') if user.get('satisfaction_score') is not None else 'N/A'}")
        st.write(f"**Onboarding step:** {user.get('onboarding_step') if user.get('onboarding_step') is not None else 'N/A'}")
        st.write(f"**Last response:** {(user.get('last_response_date') or 'Never')[:19]}")
        st.write(f"**Joined:** {(user.get('created_at') or '')[:10]}")

        # Delete user
        st.divider()
        delete_confirm_key = f"delete_user_confirm_{user['id']}"
        if delete_confirm_key not in st.session_state:
            st.session_state[delete_confirm_key] = False

        if not st.session_state[delete_confirm_key]:
            if st.button("Delete User", key=f"delete_user_{user['id']}"):
                st.session_state[delete_confirm_key] = True
                st.rerun()
        else:
            user_label = f"{user.get('first_name', '')} ({user['email']})"
            st.error(f"Delete **{user_label}** and ALL their conversations? This cannot be undone.")
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("Yes, delete", key=f"delete_user_yes_{user['id']}", type="primary"):
                    db.get_client().table("users").delete().eq("id", user["id"]).execute()
                    st.session_state[delete_confirm_key] = False
                    st.success("User deleted")
                    st.rerun()
            with no_col:
                if st.button("Cancel", key=f"delete_user_cancel_{user['id']}"):
                    st.session_state[delete_confirm_key] = False
                    st.rerun()
