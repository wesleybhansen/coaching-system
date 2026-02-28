-- Migration v6: Enable RLS on knowledge_chunks table
-- Run this in the Supabase SQL Editor

ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all via service key" ON knowledge_chunks
    FOR ALL USING (true) WITH CHECK (true);
