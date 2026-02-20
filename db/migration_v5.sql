-- Migration V5: Knowledge Base (pgvector RAG for Claude)
-- Run this in the Supabase SQL Editor.

-- 1. Enable pgvector extension (already available on Supabase)
create extension if not exists vector;

-- 2. Create the knowledge_chunks table
create table if not exists knowledge_chunks (
    id uuid primary key default gen_random_uuid(),
    source_name text not null,           -- e.g. "The Launch System", "Lecture 7"
    source_type text not null,           -- "book", "lecture", or "syllabus"
    chapter text,                        -- chapter name/number (books) or null (lectures)
    title text,                          -- AI-generated title for this chunk
    content text not null,               -- the actual text
    summary text,                        -- AI-generated 1-2 sentence summary
    stage text[],                        -- which stages this is relevant to
    topics text[],                       -- topic tags for browsing
    word_count integer not null default 0,
    embedding vector(1536),              -- OpenAI text-embedding-3-small output
    created_at timestamptz default now()
);

-- 3. Create IVFFlat index for cosine similarity search
-- Note: IVFFlat requires at least 1 row to build the index.
-- We create it after ingestion, but Supabase handles empty indexes gracefully.
create index if not exists knowledge_chunks_embedding_idx
    on knowledge_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 20);

-- 4. Create the RPC function for vector search
create or replace function match_knowledge_chunks(
    query_embedding vector(1536),
    match_count integer default 5,
    filter_stage text default null
)
returns table (
    id uuid,
    source_name text,
    source_type text,
    chapter text,
    title text,
    content text,
    summary text,
    stage text[],
    topics text[],
    word_count integer,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        kc.id,
        kc.source_name,
        kc.source_type,
        kc.chapter,
        kc.title,
        kc.content,
        kc.summary,
        kc.stage,
        kc.topics,
        kc.word_count,
        1 - (kc.embedding <=> query_embedding) as similarity
    from knowledge_chunks kc
    where
        kc.embedding is not null
        and (filter_stage is null or filter_stage = any(kc.stage))
    order by kc.embedding <=> query_embedding
    limit match_count;
end;
$$;
