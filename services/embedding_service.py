"""OpenAI embedding service for knowledge base vector search."""

import logging
import time

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"  # 1536 dimensions, very cheap
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=60.0,
            max_retries=0,
        )
    return _client


def _retry_with_backoff(func, *args, **kwargs):
    """Retry an API call with exponential backoff."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Embedding API call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Embedding API call failed after {MAX_RETRIES} attempts: {e}")
    raise last_error


def embed_text(text: str) -> list:
    """Embed a single text string. Returns a list of 1536 floats."""
    client = get_client()

    def _call():
        response = client.embeddings.create(
            model=MODEL,
            input=text,
        )
        return response.data[0].embedding

    return _retry_with_backoff(_call)


def embed_batch(texts: list, batch_size: int = 20) -> list:
    """Embed a list of texts in batches. Returns a list of embedding vectors."""
    client = get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Embedding batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size} ({len(batch)} texts)")

        def _call(b=batch):
            response = client.embeddings.create(
                model=MODEL,
                input=b,
            )
            return [item.embedding for item in response.data]

        embeddings = _retry_with_backoff(_call)
        all_embeddings.extend(embeddings)

    return all_embeddings
