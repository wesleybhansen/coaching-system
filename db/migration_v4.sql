-- Migration v4: Evaluation details, send retry tracking, bounce detection
-- Run in Supabase SQL Editor before deploying code changes.

-- Store evaluation sub-scores (relevance, tone, actionability, length, closing_question)
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS evaluation_details jsonb DEFAULT NULL;

-- Track send retry attempts for failed sends
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS send_attempts integer DEFAULT 0;

-- Track email bounces per user
ALTER TABLE users ADD COLUMN IF NOT EXISTS bounce_count integer DEFAULT 0;
