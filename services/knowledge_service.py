"""Knowledge base retrieval service for RAG (Retrieval-Augmented Generation).

Retrieves relevant chunks from the knowledge base and formats them
for injection into Claude's system prompt.
"""

import logging

from db import supabase_client as db
from services import embedding_service

logger = logging.getLogger(__name__)


def build_retrieval_query(user: dict, parsed_message: str) -> str:
    """Build a rich query string for semantic search.

    Combines the user's message with their stage and business idea
    so the embedding captures more context for better matches.
    """
    parts = [parsed_message]

    stage = user.get("stage")
    if stage:
        parts.append(f"Stage: {stage}")

    idea = user.get("business_idea")
    if idea:
        parts.append(f"Business: {idea}")

    return " | ".join(parts)


def retrieve_relevant_chunks(query: str, match_count: int = 5, stage_filter: str = None) -> list:
    """Embed query and search the knowledge base for relevant chunks.

    Args:
        query: The search query (typically from build_retrieval_query)
        match_count: Number of chunks to return
        stage_filter: Optional stage to filter by (e.g. "Ideation")

    Returns:
        List of chunk dicts with content, source info, and similarity score
    """
    try:
        query_embedding = embedding_service.embed_text(query)
        chunks = db.match_knowledge_chunks(query_embedding, match_count, stage_filter)
        return chunks
    except Exception as e:
        logger.error(f"Knowledge retrieval failed: {e}")
        return []


def format_chunks_for_prompt(chunks: list) -> str:
    """Format retrieved chunks as readable text for the AI prompt.

    Returns a string that can be injected into the system prompt
    so the AI has relevant context from Wes's books and lectures.
    """
    if not chunks:
        return ""

    sections = []
    for chunk in chunks:
        source = chunk.get("source_name", "Unknown")
        chapter = chunk.get("chapter")
        title = chunk.get("title", "")
        content = chunk.get("content", "")

        header = source
        if chapter:
            header += f" — {chapter}"
        if title:
            header += f": {title}"

        sections.append(f"### {header}\n{content}")

    return "\n\n---\n\n".join(sections)
