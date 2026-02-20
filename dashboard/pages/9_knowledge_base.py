"""Knowledge Base management page — view, browse, and manage knowledge chunks."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from db import supabase_client as db

st.set_page_config(page_title="Knowledge Base", layout="wide")
st.title("Knowledge Base")

# ── Stats ──────────────────────────────────────────────────────

stats = db.get_knowledge_stats()

col1, col2, col3 = st.columns(3)
col1.metric("Sources", stats.get("source_count", 0))
col2.metric("Total Chunks", stats.get("chunk_count", 0))
col3.metric("Total Words", f"{stats.get('total_words', 0):,}")

st.divider()

# ── Browse by Source ───────────────────────────────────────────

st.subheader("Browse by Source")

sources = db.get_all_knowledge_sources()

if not sources:
    st.info("No knowledge base content yet. Run the ingestion script to populate it.")
    st.code("python scripts/ingest_knowledge_base.py --dry-run  # preview\npython scripts/ingest_knowledge_base.py           # ingest", language="bash")
else:
    source_names = [s["source_name"] for s in sources]
    selected_source = st.selectbox("Select source", source_names)

    if selected_source:
        # Show source info
        source_info = next((s for s in sources if s["source_name"] == selected_source), None)
        if source_info:
            st.caption(f"Type: {source_info.get('source_type', 'unknown')} · "
                       f"Chunks: {source_info.get('chunk_count', 0)} · "
                       f"Words: {source_info.get('total_words', 0):,}")

        # List chunks for this source
        chunks = db.get_chunks_by_source(selected_source)

        for chunk in chunks:
            title = chunk.get("title") or "Untitled"
            summary = chunk.get("summary") or ""
            word_count = chunk.get("word_count", 0)
            stages = ", ".join(chunk.get("stage") or [])
            topics = ", ".join(chunk.get("topics") or [])
            chapter = chunk.get("chapter") or ""

            with st.expander(f"{title} ({word_count} words)"):
                if chapter:
                    st.caption(f"Chapter: {chapter}")
                if summary:
                    st.markdown(f"**Summary:** {summary}")
                if stages:
                    st.caption(f"Stages: {stages}")
                if topics:
                    st.caption(f"Topics: {topics}")

                st.text_area(
                    "Content",
                    value=chunk.get("content", ""),
                    height=200,
                    key=f"chunk_{chunk['id']}",
                    disabled=True,
                )

        # Delete source
        st.divider()
        if st.button(f"Delete all chunks from '{selected_source}'", type="secondary"):
            db.delete_chunks_by_source(selected_source)
            st.success(f"Deleted all chunks from '{selected_source}'")
            st.rerun()

# ── Upload New Document ────────────────────────────────────────

st.divider()
st.subheader("Upload New Document")
st.markdown("Upload a PDF or TXT file to add to the knowledge base. "
            "It will be automatically chunked, tagged, and embedded.")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt"])

if uploaded_file is not None:
    if st.button("Process and Upload"):
        with st.spinner("Processing..."):
            try:
                import tempfile
                from scripts.ingest_knowledge_base import process_file, tag_all_chunks, embed_all_chunks

                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                # Rename temp file to preserve original name for source detection
                named_path = os.path.join(os.path.dirname(tmp_path), uploaded_file.name)
                os.rename(tmp_path, named_path)

                # Process
                chunks = process_file(named_path)
                if not chunks:
                    st.error("No content could be extracted from this file.")
                else:
                    st.info(f"Extracted {len(chunks)} chunks. Tagging with AI...")
                    tag_all_chunks(chunks)

                    st.info("Generating embeddings...")
                    embed_all_chunks(chunks)

                    st.info("Inserting into database...")
                    for chunk in chunks:
                        db.insert_knowledge_chunk({
                            "source_name": chunk["source_name"],
                            "source_type": chunk["source_type"],
                            "chapter": chunk.get("chapter"),
                            "title": chunk.get("title", ""),
                            "content": chunk["content"],
                            "summary": chunk.get("summary", ""),
                            "stage": chunk.get("stage", []),
                            "topics": chunk.get("topics", []),
                            "word_count": chunk["word_count"],
                            "embedding": chunk["embedding"],
                        })

                    st.success(f"Uploaded {len(chunks)} chunks from '{uploaded_file.name}'")
                    st.rerun()

                # Clean up temp file
                try:
                    os.unlink(named_path)
                except OSError:
                    pass

            except Exception as e:
                st.error(f"Upload failed: {e}")
