-- Coaching System: Full Supabase Schema
-- Run this in the Supabase SQL Editor (one time)

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ============================================================
-- Table: users
-- ============================================================
create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    first_name text,
    stage text default 'Ideation' check (stage in ('Ideation', 'Early Validation', 'Late Validation', 'Growth')),
    business_idea text,
    current_challenge text,
    summary text,
    status text default 'Active' check (status in ('Active', 'Paused', 'Silent', 'Onboarding')),
    last_response_date timestamptz,
    gmail_thread_id text,
    gmail_message_id text,
    auto_approve_threshold integer,
    created_at timestamptz default now(),
    notes text
);

create index if not exists idx_users_email on users (lower(email));
create index if not exists idx_users_status on users (status);

-- ============================================================
-- Table: conversations
-- ============================================================
create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid references users(id) on delete cascade,
    type text check (type in ('Check-in', 'Follow-up', 'Re-engagement', 'Onboarding')),
    user_message_raw text,
    user_message_parsed text,
    ai_response text,
    sent_response text,
    confidence integer,
    status text default 'Pending Review' check (status in ('Pending Review', 'Approved', 'Sent', 'Flagged', 'Rejected')),
    flag_reason text,
    gmail_thread_id text,
    gmail_message_id text unique,
    resource_referenced text,
    stage_detected text,
    stage_changed boolean default false,
    created_at timestamptz default now(),
    sent_at timestamptz,
    approved_at timestamptz,
    approved_by text
);

create index if not exists idx_conversations_user_id on conversations (user_id);
create index if not exists idx_conversations_status on conversations (status);
create index if not exists idx_conversations_gmail_message_id on conversations (gmail_message_id);

-- ============================================================
-- Table: model_responses
-- ============================================================
create table if not exists model_responses (
    id uuid primary key default uuid_generate_v4(),
    title text,
    stage text,
    scenario text,
    user_example text,
    ideal_response text,
    notes text,
    created_at timestamptz default now()
);

create index if not exists idx_model_responses_stage on model_responses (stage);

-- ============================================================
-- Table: corrected_responses
-- ============================================================
create table if not exists corrected_responses (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid references conversations(id) on delete set null,
    original_message text,
    ai_response text,
    corrected_response text,
    correction_notes text,
    correction_type text check (correction_type in ('Tone', 'Content', 'Length', 'Focus', 'Factual', 'Style')),
    created_at timestamptz default now()
);

-- ============================================================
-- Table: settings (key-value)
-- ============================================================
create table if not exists settings (
    key text primary key,
    value text not null
);

insert into settings (key, value) values
    ('global_auto_approve_threshold', '10'),
    ('check_in_days', 'tue,fri'),
    ('check_in_hour', '9'),
    ('process_interval_minutes', '60'),
    ('process_start_hour', '8'),
    ('process_end_hour', '21'),
    ('send_hours', '9,13,19'),
    ('re_engagement_days', '10'),
    ('coach_timezone', 'America/New_York'),
    ('max_response_paragraphs', '3')
on conflict (key) do nothing;

-- ============================================================
-- Table: workflow_runs (observability)
-- ============================================================
create table if not exists workflow_runs (
    id uuid primary key default uuid_generate_v4(),
    workflow_name text not null,
    started_at timestamptz default now(),
    completed_at timestamptz,
    status text default 'running' check (status in ('running', 'completed', 'failed')),
    items_processed integer default 0,
    error_message text
);

create index if not exists idx_workflow_runs_name on workflow_runs (workflow_name);
create index if not exists idx_workflow_runs_started on workflow_runs (started_at desc);

-- ============================================================
-- Row Level Security (allow full access via service key)
-- ============================================================
alter table users enable row level security;
alter table conversations enable row level security;
alter table model_responses enable row level security;
alter table corrected_responses enable row level security;
alter table settings enable row level security;
alter table workflow_runs enable row level security;

create policy "Allow all via service key" on users for all using (true) with check (true);
create policy "Allow all via service key" on conversations for all using (true) with check (true);
create policy "Allow all via service key" on model_responses for all using (true) with check (true);
create policy "Allow all via service key" on corrected_responses for all using (true) with check (true);
create policy "Allow all via service key" on settings for all using (true) with check (true);
create policy "Allow all via service key" on workflow_runs for all using (true) with check (true);
