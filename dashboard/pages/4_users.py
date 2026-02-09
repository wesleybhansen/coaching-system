"""User management page."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db

st.set_page_config(page_title="Users", layout="wide")
st.title("Users")

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
        submitted = st.form_submit_button("Add User")

        if submitted and new_email:
            existing = db.get_user_by_email(new_email)
            if existing:
                st.error("User with this email already exists.")
            else:
                db.create_user(new_email, new_name)
                user = db.get_user_by_email(new_email)
                if user:
                    db.update_user(user["id"], {
                        "stage": new_stage,
                        "business_idea": new_idea if new_idea else None,
                        "status": "Active",
                    })
                st.success(f"User {new_email} added!")
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

            if st.form_submit_button("Save Changes"):
                db.update_user(user["id"], {
                    "first_name": edit_name,
                    "stage": edit_stage,
                    "status": edit_status,
                    "business_idea": edit_idea or None,
                    "current_challenge": edit_challenge or None,
                    "notes": edit_notes or None,
                })
                st.success("User updated!")
                st.rerun()

        # Summary (read-only)
        if user.get("summary"):
            st.markdown("**Journey Summary:**")
            st.text(user["summary"])

        st.write(f"**Last response:** {(user.get('last_response_date') or 'Never')[:19]}")
        st.write(f"**Joined:** {(user.get('created_at') or '')[:10]}")
