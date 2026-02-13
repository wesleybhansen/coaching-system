-- Migration V3: Reliability improvements
-- Run this in the Supabase SQL Editor after migration_v2.sql

-- ============================================================
-- Workflow runs: support 'completed_with_errors' status
-- ============================================================

-- Drop the old check constraint and add an updated one
ALTER TABLE workflow_runs DROP CONSTRAINT IF EXISTS workflow_runs_status_check;
ALTER TABLE workflow_runs ADD CONSTRAINT workflow_runs_status_check
    CHECK (status IN ('running', 'completed', 'completed_with_errors', 'failed'));

-- ============================================================
-- Performance indexes for common query patterns
-- ============================================================

-- Conversations: frequently queried by (user_id, status) together
CREATE INDEX IF NOT EXISTS idx_conversations_user_status ON conversations (user_id, status);

-- Conversations: ordered by created_at for recent lookups
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations (created_at DESC);

-- Conversations: type filtering
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations (type);

-- Users: last_response_date for re-engagement queries
CREATE INDEX IF NOT EXISTS idx_users_last_response ON users (last_response_date);

-- Users: stage for stage-based filtering
CREATE INDEX IF NOT EXISTS idx_users_stage ON users (stage);

-- Corrected responses: for stage-scoped correction lookups
CREATE INDEX IF NOT EXISTS idx_corrected_responses_created ON corrected_responses (created_at DESC);

-- ============================================================
-- Add updated_at timestamps to key tables
-- ============================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- Auto-update updated_at on row changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to conversations table
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Add onboarding_step validation
-- ============================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_onboarding_step_check;
ALTER TABLE users ADD CONSTRAINT users_onboarding_step_check
    CHECK (onboarding_step >= 0 AND onboarding_step <= 3);

-- ============================================================
-- Add satisfaction_score validation
-- ============================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_satisfaction_check;
ALTER TABLE users ADD CONSTRAINT users_satisfaction_check
    CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 1 AND satisfaction_score <= 10));

ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_satisfaction_check;
ALTER TABLE conversations ADD CONSTRAINT conversations_satisfaction_check
    CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 1 AND satisfaction_score <= 10));
