-- Migration V2: Feature enhancements
-- Run this in the Supabase SQL Editor after setup.sql

-- ============================================================
-- Users table: new columns for personalized check-ins & satisfaction
-- ============================================================

-- Personalized check-in cadence (user-configurable days, max 3/week)
ALTER TABLE users ADD COLUMN IF NOT EXISTS checkin_days text DEFAULT NULL;
-- Stores comma-separated days like "mon,wed,fri". NULL means use system default.

-- Onboarding step tracking for multi-step onboarding flow
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_step integer DEFAULT 0;
-- 0 = not in onboarding, 1 = welcome sent (awaiting stage/idea), 2 = got context (awaiting challenge), 3 = onboarding complete

-- Member satisfaction signal (rolling average sentiment)
ALTER TABLE users ADD COLUMN IF NOT EXISTS satisfaction_score numeric(3,1) DEFAULT NULL;
-- 1-10 scale, updated with each reply

-- ============================================================
-- Conversations table: new columns for threading, satisfaction, timing
-- ============================================================

-- Thread reply count for enforcing the 4-reply cap per thread
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS thread_reply_count integer DEFAULT 0;

-- Member satisfaction score for individual messages
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS satisfaction_score numeric(3,1) DEFAULT NULL;

-- ============================================================
-- New table: resources (for text-based resource referencing)
-- ============================================================
CREATE TABLE IF NOT EXISTS resources (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name text NOT NULL,            -- e.g. "Lecture 7", "Chapter 3 of The Launch System"
    description text,              -- brief description of what it covers
    topics text[],                 -- array of topic keywords for matching
    stage text,                    -- which stage it's most relevant for (NULL = all)
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resources_stage ON resources (stage);

-- RLS for resources table
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all via service key" ON resources FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- Seed initial resources from program content
-- ============================================================
INSERT INTO resources (name, description, topics, stage) VALUES
    ('Lecture 1', 'Introduction to entrepreneurship and the launch framework', ARRAY['getting started', 'framework', 'overview', 'mindset'], NULL),
    ('Lecture 2', 'Finding problems worth solving', ARRAY['problem discovery', 'ideation', 'customer problems', 'pain points'], 'Ideation'),
    ('Lecture 3', 'Customer conversations and discovery interviews', ARRAY['customer discovery', 'interviews', 'conversations', 'talking to customers', 'problem interviews'], 'Ideation'),
    ('Lecture 4', 'Validating demand before building', ARRAY['validation', 'demand', 'willingness to pay', 'pre-selling'], 'Early Validation'),
    ('Lecture 5', 'Building a minimum viable offer', ARRAY['MVP', 'minimum viable', 'first version', 'manual delivery', 'prototype'], 'Early Validation'),
    ('Lecture 6', 'Pricing and monetization', ARRAY['pricing', 'monetization', 'revenue', 'charging', 'willingness to pay', 'pricing strategy'], 'Early Validation'),
    ('Lecture 7', 'Validation through real sales', ARRAY['validation', 'sales', 'first customers', 'selling', 'closing deals'], 'Early Validation'),
    ('Lecture 8', 'Iteration and product-market fit', ARRAY['iteration', 'product-market fit', 'PMF', 'pivoting', 'feedback loops'], 'Late Validation'),
    ('Lecture 9', 'Growth channels and traction', ARRAY['growth', 'traction', 'marketing channels', 'acquisition', 'customer acquisition'], 'Late Validation'),
    ('Lecture 10', 'Systematizing and scaling operations', ARRAY['systems', 'scaling', 'operations', 'processes', 'hiring', 'delegation'], 'Growth'),
    ('Lecture 11', 'Team building and leadership', ARRAY['hiring', 'team', 'leadership', 'management', 'delegation', 'culture'], 'Growth'),
    ('Lecture 12', 'Long-term sustainability and next stages', ARRAY['sustainability', 'fundraising', 'scaling', 'long-term', 'strategy'], 'Growth'),
    ('The Launch System - Chapter 1', 'Why most business ideas fail and the launch framework', ARRAY['framework', 'failure', 'getting started', 'launch system'], NULL),
    ('The Launch System - Chapter 2', 'Finding ideas through conversations, not brainstorming', ARRAY['ideation', 'ideas', 'conversations', 'brainstorming'], 'Ideation'),
    ('The Launch System - Chapter 3', 'The customer conversation framework', ARRAY['customer discovery', 'interviews', 'frameworks', 'conversations', 'problem interviews'], 'Ideation'),
    ('The Launch System - Chapter 4', 'Testing willingness to pay', ARRAY['pricing', 'willingness to pay', 'validation', 'pre-selling', 'testing demand'], 'Early Validation'),
    ('The Launch System - Chapter 5', 'Building and delivering manually first', ARRAY['MVP', 'manual delivery', 'first customers', 'prototype', 'lean'], 'Early Validation'),
    ('The Launch System - Chapter 6', 'Getting from manual to scalable', ARRAY['scaling', 'automation', 'systems', 'growth', 'operations'], 'Late Validation'),
    ('Ideas That Spread - Chapter 1', 'Why some ideas spread and others dont', ARRAY['marketing', 'virality', 'word of mouth', 'growth'], NULL),
    ('Ideas That Spread - Chapter 2', 'Understanding your audience deeply', ARRAY['audience', 'customer understanding', 'segmentation', 'target market'], NULL),
    ('Ideas That Spread - Chapter 3', 'Creating remarkable products people talk about', ARRAY['product', 'remarkable', 'differentiation', 'word of mouth'], 'Late Validation'),
    ('Ideas That Spread - Chapter 4', 'Building distribution into your product', ARRAY['distribution', 'channels', 'growth', 'marketing', 'referrals'], 'Growth')
ON CONFLICT DO NOTHING;

-- ============================================================
-- Add new default settings
-- ============================================================
INSERT INTO settings (key, value) VALUES
    ('max_thread_replies', '4'),
    ('default_checkin_days', 'tue,fri'),
    ('max_checkin_days_per_week', '3'),
    ('notification_email', 'coachwes@thelaunchpadincubator.com')
ON CONFLICT (key) DO NOTHING;
