#!/usr/bin/env python3
"""One-time ingestion script for the knowledge base.

Processes PDFs and lecture transcripts from knowledge-base-files/,
chunks them, auto-tags with GPT-4o-mini, embeds, and inserts into Supabase.

Usage:
    python scripts/ingest_knowledge_base.py --dry-run    # Preview chunks
    python scripts/ingest_knowledge_base.py              # Full ingestion
"""

import argparse
import json
import logging
import os
import re
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from services import embedding_service
from db import supabase_client as db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge-base-files")

# Target chunk size in words
TARGET_CHUNK_WORDS = 1000
MIN_CHUNK_WORDS = 100


# ── PDF Extraction ─────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            # Strip null bytes — PDFs sometimes contain \x00 which PostgreSQL rejects
            text = text.replace("\x00", "")
            pages.append(text.strip())
    return "\n\n".join(pages)


# ── Chunking ───────────────────────────────────────────────────

def chunk_by_chapters(text: str, source_name: str) -> list:
    """Try to split book text by chapter boundaries.

    Looks for patterns like "Chapter 1", "CHAPTER ONE", "Chapter 1:", etc.
    Falls back to paragraph-based chunking if no chapters found.
    """
    # Match chapter headings (various formats)
    chapter_pattern = re.compile(
        r'^(Chapter\s+\d+[:\.\s].*|CHAPTER\s+\d+[:\.\s].*|Chapter\s+(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)[:\.\s].*)',
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(chapter_pattern.finditer(text))

    if len(matches) < 2:
        # Not enough chapters found, fall back to paragraph chunking
        return chunk_by_paragraphs(text, source_name)

    chunks = []
    for i, match in enumerate(matches):
        chapter_title = match.group(0).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()

        # If the chapter is very long, sub-chunk by paragraphs
        word_count = len(chapter_text.split())
        if word_count > TARGET_CHUNK_WORDS * 2:
            sub_chunks = chunk_by_paragraphs(chapter_text, source_name, chapter=chapter_title)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "source_name": source_name,
                "chapter": chapter_title,
                "content": chapter_text,
                "word_count": word_count,
            })

    return chunks


def chunk_by_paragraphs(text: str, source_name: str, chapter: str = None) -> list:
    """Split text into chunks by paragraph boundaries, targeting ~1000 words.

    Groups paragraphs together until hitting the target word count,
    then starts a new chunk.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_paragraphs = []
    current_word_count = 0

    for para in paragraphs:
        para_words = len(para.split())

        if current_word_count + para_words > TARGET_CHUNK_WORDS and current_word_count >= MIN_CHUNK_WORDS:
            # Save current chunk and start a new one
            chunk_text = "\n\n".join(current_paragraphs)
            chunks.append({
                "source_name": source_name,
                "chapter": chapter,
                "content": chunk_text,
                "word_count": current_word_count,
            })
            current_paragraphs = [para]
            current_word_count = para_words
        else:
            current_paragraphs.append(para)
            current_word_count += para_words

    # Don't forget the last chunk
    if current_paragraphs and current_word_count >= MIN_CHUNK_WORDS:
        chunk_text = "\n\n".join(current_paragraphs)
        chunks.append({
            "source_name": source_name,
            "chapter": chapter,
            "content": chunk_text,
            "word_count": current_word_count,
        })
    elif current_paragraphs and chunks:
        # Too short on its own — merge with previous chunk
        prev = chunks[-1]
        prev["content"] += "\n\n" + "\n\n".join(current_paragraphs)
        prev["word_count"] += current_word_count

    return chunks


def chunk_lecture(text: str, source_name: str) -> list:
    """Chunk a lecture transcript.

    Short lectures (< 2x target) stay whole. Longer ones get paragraph-chunked.
    """
    word_count = len(text.split())

    if word_count <= TARGET_CHUNK_WORDS * 2:
        return [{
            "source_name": source_name,
            "chapter": None,
            "content": text.strip(),
            "word_count": word_count,
        }]

    return chunk_by_paragraphs(text, source_name)


# ── AI Tagging ─────────────────────────────────────────────────

def tag_chunk(chunk: dict) -> dict:
    """Use GPT-4o-mini to generate title, summary, stages, and topics for a chunk."""
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=60.0)

    # Truncate content for tagging prompt (first 2000 chars is plenty)
    content_preview = chunk["content"][:2000]

    prompt = f"""You are tagging content from an entrepreneurship coaching program for a knowledge base.

Source: {chunk['source_name']}
{f"Chapter: {chunk['chapter']}" if chunk.get('chapter') else ""}

Content (may be truncated):
{content_preview}

Return a JSON object with:
- "title": A concise title for this chunk (5-10 words)
- "summary": A 1-2 sentence summary of the key teaching point
- "stages": Array of relevant stages from ["Ideation", "Early Validation", "Late Validation", "Growth"] (can be multiple)
- "topics": Array of 2-4 topic tags (e.g. "customer discovery", "pricing", "mindset", "marketing")

Return ONLY valid JSON, no markdown formatting."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        tags = json.loads(response.choices[0].message.content)
        chunk["title"] = tags.get("title", "")
        chunk["summary"] = tags.get("summary", "")
        chunk["stage"] = tags.get("stages", [])
        chunk["topics"] = tags.get("topics", [])
    except Exception as e:
        logger.warning(f"Tagging failed for chunk from {chunk['source_name']}: {e}")
        chunk["title"] = ""
        chunk["summary"] = ""
        chunk["stage"] = []
        chunk["topics"] = []

    return chunk


# ── Source Type Detection ──────────────────────────────────────

def detect_source_type(filename: str) -> str:
    """Determine source type from filename."""
    lower = filename.lower()
    if "lecture" in lower:
        return "lecture"
    if "syllabus" in lower:
        return "syllabus"
    return "book"


def get_source_name(filename: str) -> str:
    """Clean up filename to a readable source name."""
    name = os.path.splitext(filename)[0]
    return name.strip()


# ── Main Ingestion ─────────────────────────────────────────────

def process_file(filepath: str) -> list:
    """Process a single file into tagged chunks."""
    filename = os.path.basename(filepath)
    source_name = get_source_name(filename)
    source_type = detect_source_type(filename)

    logger.info(f"Processing: {filename} (type={source_type})")

    # Extract text
    if filepath.lower().endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    elif filepath.lower().endswith(".txt"):
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
    else:
        logger.warning(f"Skipping unsupported file type: {filename}")
        return []

    if not text.strip():
        logger.warning(f"No text extracted from {filename}")
        return []

    # Chunk
    if source_type == "lecture":
        chunks = chunk_lecture(text, source_name)
    elif source_type == "book":
        chunks = chunk_by_chapters(text, source_name)
    else:
        # Syllabus or other — use paragraph chunking
        chunks = chunk_by_paragraphs(text, source_name)

    # Set source_type on each chunk
    for chunk in chunks:
        chunk["source_type"] = source_type

    logger.info(f"  → {len(chunks)} chunks from {filename}")
    return chunks


def tag_all_chunks(chunks: list) -> list:
    """Tag all chunks with AI-generated metadata. Includes rate limiting."""
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        logger.info(f"Tagging chunk {i + 1}/{total}: {chunk['source_name']}")
        tag_chunk(chunk)
        # Small delay to avoid rate limits
        if (i + 1) % 10 == 0:
            time.sleep(1)
    return chunks


def embed_all_chunks(chunks: list) -> list:
    """Generate embeddings for all chunks."""
    texts = [chunk["content"] for chunk in chunks]
    logger.info(f"Embedding {len(texts)} chunks...")
    embeddings = embedding_service.embed_batch(texts, batch_size=20)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    logger.info("Embedding complete")
    return chunks


def insert_chunks(chunks: list):
    """Insert all chunks into Supabase."""
    total = len(chunks)
    for i, chunk in enumerate(chunks):
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
        if (i + 1) % 10 == 0:
            logger.info(f"Inserted {i + 1}/{total} chunks")

    logger.info(f"All {total} chunks inserted into Supabase")


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base files into Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Preview chunks without inserting")
    args = parser.parse_args()

    if not os.path.isdir(SOURCE_DIR):
        logger.error(f"Source directory not found: {SOURCE_DIR}")
        sys.exit(1)

    # Gather all files
    files = sorted([
        os.path.join(SOURCE_DIR, f)
        for f in os.listdir(SOURCE_DIR)
        if f.endswith((".pdf", ".txt")) and not f.startswith(".")
    ])

    if not files:
        logger.error("No PDF or TXT files found in knowledge-base-files/")
        sys.exit(1)

    logger.info(f"Found {len(files)} files to process")

    # Process all files into chunks
    all_chunks = []
    for filepath in files:
        chunks = process_file(filepath)
        all_chunks.extend(chunks)

    logger.info(f"Total chunks: {len(all_chunks)}")
    total_words = sum(c["word_count"] for c in all_chunks)
    logger.info(f"Total words: {total_words:,}")

    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN — {len(all_chunks)} chunks from {len(files)} files")
        print(f"Total words: {total_words:,}")
        print(f"{'='*60}\n")

        for i, chunk in enumerate(all_chunks):
            source = chunk["source_name"]
            chapter = chunk.get("chapter", "")
            wc = chunk["word_count"]
            preview = chunk["content"][:150].replace("\n", " ")
            print(f"[{i + 1}] {source} | {chapter or 'no chapter'} | {wc} words")
            print(f"    {preview}...")
            print()

        print(f"Run without --dry-run to tag, embed, and insert all chunks.")
        return

    # Tag all chunks with AI
    logger.info("Starting AI tagging...")
    tag_all_chunks(all_chunks)

    # Embed all chunks
    logger.info("Starting embedding...")
    embed_all_chunks(all_chunks)

    # Insert into Supabase
    logger.info("Inserting into Supabase...")
    insert_chunks(all_chunks)

    logger.info("Ingestion complete!")


if __name__ == "__main__":
    main()
