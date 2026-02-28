"""View and add corrected responses for AI learning."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db

st.set_page_config(page_title="Corrections", layout="wide")
st.title("Corrected Responses")

st.markdown("Corrections help the AI learn from your edits. When you edit a response during review, "
            "a correction is automatically saved. You can also add corrections manually here.")

# Add manual correction
with st.expander("Add manual correction"):
    with st.form("add_correction"):
        orig_message = st.text_area("Original user message", height=80)
        ai_resp = st.text_area("What the AI generated (or would have generated)", height=100)
        corrected = st.text_area("What you would write instead", height=100)
        notes = st.text_area("Why this correction matters", height=60)
        correction_type = st.selectbox("Type", ["Tone", "Content", "Length", "Focus", "Factual", "Style"])
        submitted = st.form_submit_button("Save Correction")

        if submitted and corrected:
            db.create_correction({
                "original_message": orig_message,
                "ai_response": ai_resp,
                "corrected_response": corrected,
                "correction_notes": notes,
                "correction_type": correction_type,
            })
            st.success("Correction saved!")
            st.rerun()

# List existing corrections
corrections = db.get_all_corrections()

st.write(f"{len(corrections)} correction(s) total")

for corr in corrections:
    created = (corr.get("created_at") or "")[:10]
    corr_type = corr.get("correction_type", "?")

    with st.expander(f"[{corr_type}] {created} — {(corr.get('original_message') or 'No message')[:60]}..."):
        if corr.get("original_message"):
            st.markdown("**User said:**")
            st.text(corr["original_message"])

        if corr.get("ai_response"):
            st.markdown("**AI generated:**")
            st.text(corr["ai_response"])

        st.markdown("**Corrected to:**")
        st.text(corr.get("corrected_response", ""))

        if corr.get("correction_notes"):
            st.info(f"**Why:** {corr['correction_notes']}")
