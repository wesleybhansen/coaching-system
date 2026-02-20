"""Tests for knowledge base: embedding, retrieval, formatting, and RAG integration."""

import uuid
from unittest.mock import MagicMock, patch

from tests.conftest import make_user


# ── Embedding Service ─────────────────────────────────────────

class TestEmbeddingService:
    """Tests for services/embedding_service.py"""

    def test_embed_text(self, mock_db):
        """embed_text returns a list of floats from OpenAI."""
        fake_embedding = [0.1] * 1536

        with patch("services.embedding_service.get_client") as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=fake_embedding)]
            mock_client.return_value.embeddings.create.return_value = mock_response

            from services.embedding_service import embed_text
            result = embed_text("test text")

            assert result == fake_embedding
            mock_client.return_value.embeddings.create.assert_called_once()

    def test_embed_batch(self, mock_db):
        """embed_batch processes texts in batches and returns all embeddings."""
        fake_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]

        with patch("services.embedding_service.get_client") as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=e) for e in fake_embeddings]
            mock_client.return_value.embeddings.create.return_value = mock_response

            from services.embedding_service import embed_batch
            result = embed_batch(["text1", "text2", "text3"], batch_size=10)

            assert len(result) == 3
            assert result[0] == fake_embeddings[0]

    def test_embed_batch_multiple_batches(self, mock_db):
        """embed_batch handles multiple batches correctly."""
        batch1 = [[0.1] * 1536, [0.2] * 1536]
        batch2 = [[0.3] * 1536]

        call_count = 0

        with patch("services.embedding_service.get_client") as mock_client:
            def side_effect(**kwargs):
                nonlocal call_count
                call_count += 1
                embeddings = batch1 if call_count == 1 else batch2
                resp = MagicMock()
                resp.data = [MagicMock(embedding=e) for e in embeddings]
                return resp

            mock_client.return_value.embeddings.create.side_effect = side_effect

            from services.embedding_service import embed_batch
            result = embed_batch(["a", "b", "c"], batch_size=2)

            assert len(result) == 3
            assert call_count == 2


# ── Knowledge Service ─────────────────────────────────────────

class TestKnowledgeService:
    """Tests for services/knowledge_service.py"""

    def test_build_retrieval_query_full(self, mock_db):
        """build_retrieval_query combines message, stage, and business idea."""
        from services.knowledge_service import build_retrieval_query

        user = make_user(stage="Early Validation", business_idea="Dog-walking app")
        query = build_retrieval_query(user, "How do I price my service?")

        assert "How do I price my service?" in query
        assert "Early Validation" in query
        assert "Dog-walking app" in query

    def test_build_retrieval_query_minimal(self, mock_db):
        """build_retrieval_query works with just a message."""
        from services.knowledge_service import build_retrieval_query

        user = make_user(stage=None, business_idea=None)
        query = build_retrieval_query(user, "Help me get started")

        assert "Help me get started" in query

    def test_retrieve_relevant_chunks(self, mock_db):
        """retrieve_relevant_chunks embeds query and calls db."""
        # Add some chunks to storage
        mock_db["knowledge_chunks"].append({
            "id": str(uuid.uuid4()),
            "source_name": "The Launch System",
            "source_type": "book",
            "chapter": "Chapter 1",
            "title": "Getting Started",
            "content": "Start by talking to people about their problems.",
            "summary": "How to begin customer discovery",
            "stage": ["Ideation"],
            "topics": ["customer discovery"],
            "word_count": 8,
        })

        with patch("services.knowledge_service.embedding_service") as mock_emb:
            mock_emb.embed_text.return_value = [0.1] * 1536

            from services.knowledge_service import retrieve_relevant_chunks
            chunks = retrieve_relevant_chunks("how to start", match_count=5)

            assert len(chunks) == 1
            assert chunks[0]["source_name"] == "The Launch System"
            mock_emb.embed_text.assert_called_once_with("how to start")

    def test_retrieve_relevant_chunks_handles_error(self, mock_db):
        """retrieve_relevant_chunks returns empty list on error."""
        with patch("services.knowledge_service.embedding_service") as mock_emb:
            mock_emb.embed_text.side_effect = Exception("API error")

            from services.knowledge_service import retrieve_relevant_chunks
            chunks = retrieve_relevant_chunks("test query")

            assert chunks == []

    def test_format_chunks_for_prompt(self, mock_db):
        """format_chunks_for_prompt formats chunks into readable text."""
        from services.knowledge_service import format_chunks_for_prompt

        chunks = [
            {
                "source_name": "The Launch System",
                "chapter": "Chapter 3",
                "title": "Customer Discovery",
                "content": "Talk to 10 people before building anything.",
            },
            {
                "source_name": "Lecture 7",
                "chapter": None,
                "title": "Pricing Strategies",
                "content": "Start with a price that feels uncomfortable.",
            },
        ]

        result = format_chunks_for_prompt(chunks)

        assert "The Launch System" in result
        assert "Chapter 3" in result
        assert "Customer Discovery" in result
        assert "Talk to 10 people" in result
        assert "Lecture 7" in result
        assert "Pricing Strategies" in result
        assert "---" in result  # separator between chunks

    def test_format_chunks_empty(self, mock_db):
        """format_chunks_for_prompt returns empty string for no chunks."""
        from services.knowledge_service import format_chunks_for_prompt

        assert format_chunks_for_prompt([]) == ""


# ── AI Service RAG Integration ─────────────────────────────────

class TestAIServiceRAG:
    """Tests for RAG integration in ai_service.py"""

    def test_extract_user_message(self, mock_db):
        """_extract_user_message pulls message from context string."""
        from services.ai_service import _extract_user_message

        context = """## Context About This User
Name: Alice

## Their Current Message
I need help pricing my dog-walking service.

## Available Resources
- Lecture 1: Intro"""

        result = _extract_user_message(context)
        assert result == "I need help pricing my dog-walking service."

    def test_extract_user_message_end_of_string(self, mock_db):
        """_extract_user_message handles message at end of context."""
        from services.ai_service import _extract_user_message

        context = "## Their Current Message\nHow do I find customers?"
        result = _extract_user_message(context)
        assert result == "How do I find customers?"

    def test_extract_user_message_missing(self, mock_db):
        """_extract_user_message returns empty string if marker not found."""
        from services.ai_service import _extract_user_message

        result = _extract_user_message("No marker here")
        assert result == ""

    def test_anthropic_uses_knowledge_retrieval(self, mock_db, mock_openai):
        """When provider is anthropic and user is provided, RAG retrieval happens."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        user = make_user(stage="Ideation", business_idea="Dog-walking app")

        with patch("services.anthropic_service.generate_response", return_value="Great coaching response!") as mock_anth, \
             patch("services.knowledge_service.retrieve_relevant_chunks", return_value=[]) as mock_retrieve, \
             patch("services.knowledge_service.build_retrieval_query", return_value="test query") as mock_query:

            from services.ai_service import generate_response
            result = generate_response("## Their Current Message\nHelp me!", user=user)

            assert result == "Great coaching response!"
            mock_query.assert_called_once()
            mock_retrieve.assert_called_once()

    def test_anthropic_without_user_skips_rag(self, mock_db):
        """When provider is anthropic but no user provided, RAG is skipped."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        with patch("services.anthropic_service.generate_response", return_value="Response") as mock_anth:
            from services.ai_service import generate_response
            result = generate_response("some context")

            assert result == "Response"
            mock_anth.assert_called_once_with("some context", model="claude-sonnet-4-6", knowledge_context="")

    def test_openai_ignores_user_param(self, mock_db, mock_openai):
        """When provider is openai, user param is ignored (file_search handles it)."""
        mock_db["settings"]["ai_provider"] = "openai"
        mock_db["settings"]["ai_model"] = "gpt-4o"

        user = make_user()

        from services.ai_service import generate_response
        result = generate_response("some context", user=user)

        # OpenAI mock is already set up in mock_openai fixture
        mock_openai["generate_response"].assert_called_once_with("some context", model="gpt-4o")

    def test_rag_failure_doesnt_break_response(self, mock_db):
        """If knowledge retrieval fails, response still generates without RAG."""
        mock_db["settings"]["ai_provider"] = "anthropic"
        mock_db["settings"]["ai_model"] = "claude-sonnet-4-6"

        user = make_user()

        with patch("services.anthropic_service.generate_response", return_value="Response") as mock_anth, \
             patch("services.knowledge_service.retrieve_relevant_chunks", side_effect=Exception("DB down")):

            from services.ai_service import generate_response
            result = generate_response("## Their Current Message\nHelp!", user=user)

            assert result == "Response"
            # Should still be called with empty knowledge_context
            mock_anth.assert_called_once()


# ── Anthropic Service Knowledge Context ────────────────────────

class TestAnthropicKnowledgeContext:
    """Tests for knowledge_context param in anthropic_service."""

    def test_knowledge_context_appended_to_system_prompt(self, mock_db):
        """When knowledge_context is provided, it's appended to system prompt."""
        with patch("services.anthropic_service.get_client") as mock_client, \
             patch("services.anthropic_service._get_instructions", return_value="Be Wes."):

            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Great coaching!")]
            mock_client.return_value.messages.create.return_value = mock_message

            from services.anthropic_service import generate_response
            result = generate_response(
                "user context here",
                model="claude-sonnet-4-6",
                knowledge_context="### Lecture 7\nPricing is about value."
            )

            assert result == "Great coaching!"
            call_args = mock_client.return_value.messages.create.call_args
            system_prompt = call_args.kwargs["system"]
            assert "Lecture 7" in system_prompt
            assert "Pricing is about value" in system_prompt
            assert "Be Wes." in system_prompt

    def test_no_knowledge_context_uses_plain_instructions(self, mock_db):
        """When knowledge_context is empty, system prompt is just instructions."""
        with patch("services.anthropic_service.get_client") as mock_client, \
             patch("services.anthropic_service._get_instructions", return_value="Be Wes."):

            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Response")]
            mock_client.return_value.messages.create.return_value = mock_message

            from services.anthropic_service import generate_response
            result = generate_response("context", knowledge_context="")

            call_args = mock_client.return_value.messages.create.call_args
            system_prompt = call_args.kwargs["system"]
            assert system_prompt == "Be Wes."


# ── Coaching Service Integration ───────────────────────────────

class TestCoachingServicePassesUser:
    """Tests that coaching_service passes user to ai_service."""

    def test_generate_and_evaluate_passes_user(self, mock_db, mock_openai):
        """generate_and_evaluate passes user dict to ai_service.generate_response."""
        user = make_user()
        mock_db["users"].append(user)

        with patch("services.ai_service.generate_response", return_value="Great!") as mock_gen:
            from services.coaching_service import generate_and_evaluate
            result = generate_and_evaluate(user, "How do I find customers?", "check-in response")

            # Verify user was passed
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args
            assert call_kwargs.kwargs.get("user") == user


# ── Database CRUD ──────────────────────────────────────────────

class TestKnowledgeDBOperations:
    """Tests for knowledge base CRUD operations in the mock db."""

    def test_insert_and_retrieve_chunk(self, mock_db):
        """Can insert a chunk and retrieve it by source."""
        import db.supabase_client as db_mod

        db_mod.insert_knowledge_chunk({
            "source_name": "Test Book",
            "source_type": "book",
            "chapter": "Chapter 1",
            "title": "Intro",
            "content": "This is test content.",
            "summary": "A test.",
            "stage": ["Ideation"],
            "topics": ["testing"],
            "word_count": 5,
            "embedding": [0.1] * 1536,
        })

        chunks = db_mod.get_chunks_by_source("Test Book")
        assert len(chunks) == 1
        assert chunks[0]["title"] == "Intro"

    def test_get_knowledge_stats(self, mock_db):
        """get_knowledge_stats returns correct counts."""
        import db.supabase_client as db_mod

        db_mod.insert_knowledge_chunk({
            "source_name": "Book A", "source_type": "book",
            "content": "Content", "word_count": 100,
        })
        db_mod.insert_knowledge_chunk({
            "source_name": "Book A", "source_type": "book",
            "content": "More content", "word_count": 200,
        })
        db_mod.insert_knowledge_chunk({
            "source_name": "Lecture 1", "source_type": "lecture",
            "content": "Lecture", "word_count": 50,
        })

        stats = db_mod.get_knowledge_stats()
        assert stats["source_count"] == 2
        assert stats["chunk_count"] == 3
        assert stats["total_words"] == 350

    def test_delete_chunks_by_source(self, mock_db):
        """delete_chunks_by_source removes only that source's chunks."""
        import db.supabase_client as db_mod

        db_mod.insert_knowledge_chunk({
            "source_name": "Book A", "source_type": "book",
            "content": "A", "word_count": 10,
        })
        db_mod.insert_knowledge_chunk({
            "source_name": "Book B", "source_type": "book",
            "content": "B", "word_count": 20,
        })

        db_mod.delete_chunks_by_source("Book A")

        assert len(db_mod.get_chunks_by_source("Book A")) == 0
        assert len(db_mod.get_chunks_by_source("Book B")) == 1

    def test_get_all_knowledge_sources(self, mock_db):
        """get_all_knowledge_sources aggregates correctly."""
        import db.supabase_client as db_mod

        db_mod.insert_knowledge_chunk({
            "source_name": "Lecture 1", "source_type": "lecture",
            "content": "Hello", "word_count": 100,
        })
        db_mod.insert_knowledge_chunk({
            "source_name": "Lecture 1", "source_type": "lecture",
            "content": "World", "word_count": 150,
        })

        sources = db_mod.get_all_knowledge_sources()
        assert len(sources) == 1
        assert sources[0]["chunk_count"] == 2
        assert sources[0]["total_words"] == 250

    def test_match_knowledge_chunks_returns_top_n(self, mock_db):
        """match_knowledge_chunks returns first N chunks from mock."""
        import db.supabase_client as db_mod

        for i in range(10):
            db_mod.insert_knowledge_chunk({
                "source_name": f"Source {i}", "source_type": "book",
                "content": f"Content {i}", "word_count": 100,
            })

        results = db_mod.match_knowledge_chunks([0.1] * 1536, match_count=3)
        assert len(results) == 3


# ── Ingestion Script Chunking ──────────────────────────────────

class TestIngestionChunking:
    """Tests for the chunking logic in the ingestion script."""

    def test_chunk_by_paragraphs_basic(self, mock_db):
        """chunk_by_paragraphs splits text at paragraph boundaries."""
        from scripts.ingest_knowledge_base import chunk_by_paragraphs

        # Create text with multiple paragraphs
        paragraphs = ["Word " * 600, "Another " * 600]  # Each ~600 words
        text = "\n\n".join(paragraphs)

        chunks = chunk_by_paragraphs(text, "Test Source")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk["source_name"] == "Test Source"
            assert chunk["word_count"] > 0

    def test_chunk_lecture_short(self, mock_db):
        """Short lectures stay as a single chunk."""
        from scripts.ingest_knowledge_base import chunk_lecture

        text = "This is a short lecture. " * 50  # ~300 words
        chunks = chunk_lecture(text, "Lecture 1")

        assert len(chunks) == 1
        assert chunks[0]["source_name"] == "Lecture 1"

    def test_chunk_lecture_long(self, mock_db):
        """Long lectures get split into multiple chunks."""
        from scripts.ingest_knowledge_base import chunk_lecture

        # Create long text with paragraph breaks
        paragraphs = [f"Paragraph {i}. " + "word " * 800 for i in range(5)]
        text = "\n\n".join(paragraphs)

        chunks = chunk_lecture(text, "Lecture 34")

        assert len(chunks) > 1

    def test_detect_source_type(self, mock_db):
        """detect_source_type correctly identifies file types."""
        from scripts.ingest_knowledge_base import detect_source_type

        assert detect_source_type("Lecture 7.txt") == "lecture"
        assert detect_source_type("The Launch System.pdf") == "book"
        assert detect_source_type("The Launch Pad Course Syllabus.pdf") == "syllabus"

    def test_get_source_name(self, mock_db):
        """get_source_name strips extension and whitespace."""
        from scripts.ingest_knowledge_base import get_source_name

        assert get_source_name("Lecture 7.txt") == "Lecture 7"
        assert get_source_name("The Launch System.pdf") == "The Launch System"
