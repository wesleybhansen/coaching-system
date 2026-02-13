# Launchpad Incubator Coaching System: Technical Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Tech Stack Components](#tech-stack-components)
   - [OpenAI (AI Engine)](#1-openai-ai-engine)
   - [Gmail (Email Transport)](#2-gmail-email-transport)
   - [Supabase (Database)](#3-supabase-database)
   - [Streamlit (Dashboard)](#4-streamlit-dashboard)
   - [GitHub Actions (Scheduling)](#5-github-actions-scheduling)
   - [Python (Application Layer)](#6-python-application-layer)
4. [Data Flow Architecture](#data-flow-architecture)
   - [Inbound Email Processing Pipeline](#inbound-email-processing-pipeline)
   - [Outbound Email Pipeline](#outbound-email-pipeline)
   - [Check-in Pipeline](#check-in-pipeline)
   - [Review Pipeline (Human-in-the-Loop)](#review-pipeline-human-in-the-loop)
   - [Learning Loop](#learning-loop)
5. [Database Schema](#database-schema)
6. [Key Design Decisions](#key-design-decisions)
7. [Environment Variables](#environment-variables)
8. [File Structure](#file-structure)
9. [Test Suite](#test-suite)

---

## System Overview

The Launchpad Incubator Coaching System is an automated AI coaching platform purpose-built for an entrepreneurship program. It provides personalized, stage-aware coaching to program members entirely through email -- no new app install, no portal, no friction. Members simply email their coach and receive thoughtful, contextual responses grounded in the program's curriculum.

The architecture is designed around two core principles: **email-first** (meet users where they already are -- their inbox) and **human-in-the-loop** (AI generates, humans review, and the system learns from corrections over time). Every component serves one of these principles.

Under the hood, the system orchestrates six services into a cohesive pipeline:

- **Receives emails** from program members via Gmail IMAP polling on an hourly schedule.
- **Generates personalized coaching responses** using OpenAI GPT-4o with retrieval-augmented generation (RAG), pulling relevant program content from a vector store containing all lecture and book material.
- **Evaluates response quality** with a secondary AI model (GPT-4o-mini) that scores confidence, detects safety flags, identifies the member's entrepreneurship stage, and analyzes engagement satisfaction.
- **Routes responses through a review pipeline** with three outcomes: Auto-approved (high confidence, no flags), Pending Review (moderate confidence), or Flagged (legal, mental health, out-of-scope, or URL issues).
- **Sends approved responses** via Gmail SMTP with human-like threading and randomized timing delays that make the interaction feel natural.
- **Provides a web dashboard** (Streamlit) for administrative management of users, conversations, corrections, settings, and analytics.
- **Runs automated workflows** on scheduled cron jobs via GitHub Actions, covering email processing, response sending, daily check-ins, re-engagement nudges, and cleanup.

The result is a system that feels like a personal coach to each member while operating at scale with minimal operator overhead.

---

## Architecture Diagram

```
                          +-------------------+
                          |   Program Members  |
                          |   (Gmail Inbox)    |
                          +--------+----------+
                                   |
                          IMAP Fetch / SMTP Send
                                   |
                          +--------v----------+
                          |   Gmail Service    |
                          |  (IMAP + SMTP)     |
                          +--------+----------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
    +---------v--------+  +-------v---------+  +--------v--------+
    | process_emails   |  | send_approved   |  |   check_in      |
    | (hourly)         |  | (3x daily)      |  |   (daily)       |
    +--------+---------+  +-------+---------+  +--------+--------+
              |                    |                     |
              +--------------------+--------------------+
                                   |
                          +--------v----------+
                          | Coaching Service   |
                          | (Business Logic)   |
                          +--------+----------+
                                   |
                    +--------------+--------------+
                    |                              |
           +--------v----------+         +--------v----------+
           |  OpenAI Service   |         |  Supabase Client  |
           |  GPT-4o (RAG)     |         |  (PostgreSQL)     |
           |  GPT-4o-mini      |         +-------------------+
           |  Vector Store     |
           +-------------------+
                                          +-------------------+
                                          | Streamlit Dashboard|
                                          | (Admin Interface) |
                                          +-------------------+
                                                   |
                                          +--------v----------+
                                          | GitHub Actions     |
                                          | (Cron Scheduler)   |
                                          +-------------------+
```

The architecture is deliberately simple. There are no message queues, no microservices, no container orchestration. Each workflow is a single Python script that runs, does its job, and exits. GitHub Actions handles the scheduling. Supabase handles the state. This simplicity makes the system easy to understand, debug, and maintain.

---

## Tech Stack Components

### 1. OpenAI (AI Engine)

The system uses two OpenAI models in a deliberate division of labor: a powerful model for generation tasks that require nuance and creativity, and a lightweight model for evaluation tasks that require speed, consistency, and cost efficiency.

#### GPT-4o -- Primary Generation Model

GPT-4o handles all tasks where quality and contextual understanding are paramount:

- **Coaching response generation**: Invoked through the Responses API with the `file_search` tool enabled, allowing the model to retrieve relevant program content from a pre-built vector store before generating its response. This is the system's RAG implementation -- the model searches your curriculum materials and weaves relevant references into its coaching advice.
- **Personalized check-in question generation**: Creates individualized, context-aware check-in questions based on each member's stage, business idea, current challenge, and recent conversation history. No two check-ins are the same.
- **Journey summary updates**: After responses are sent, generates updated narrative summaries of each member's coaching journey. These summaries give the AI persistent memory across conversations.

The generation temperature is set to **0.7**, balancing creativity with coherence in coaching responses. Summary generation uses **0.5** for a more measured, factual tone.

#### GPT-4o-mini -- Secondary Evaluation Model

GPT-4o-mini handles high-volume, lower-stakes tasks where speed and cost efficiency matter more than generative depth:

- **Response evaluation and confidence scoring**: Assigns a 1-10 confidence score to every generated response, directly controlling the review pipeline routing. This is the gatekeeper that determines whether a response needs human review.
- **Flag detection**: Identifies four categories of concern -- legal issues, mental health indicators, out-of-scope questions, and URLs present in the response (the system is designed to never include links).
- **Stage detection**: Classifies each member's current entrepreneurship stage (Ideation, Early Validation, Late Validation, Growth) based on their message content, enabling automatic stage tracking.
- **Satisfaction analysis**: Scores member engagement on a 1-10 scale based on message tone, depth, and responsiveness. This feeds the rolling satisfaction score that tracks engagement trends.
- **Email parsing fallback**: When the deterministic `email-reply-parser` library fails to cleanly extract the user's message from an email thread, GPT-4o-mini serves as an intelligent fallback parser that understands email structure.

The evaluation temperature is set to **0.2** for maximum determinism and consistency across evaluations.

#### RAG Implementation (Responses API with file_search)

Rather than building a custom retrieval pipeline with embeddings, vector databases, and chunking logic, the system leverages OpenAI's built-in `file_search` tool through the Responses API. This approach offloads vector storage, chunking, and retrieval entirely to OpenAI's infrastructure -- reducing complexity while maintaining high retrieval quality.

- **Vector Store**: Contains the complete program curriculum -- all lectures, book chapters, frameworks, and coaching materials.
- When generating a coaching response, the API automatically searches the vector store for content relevant to the member's current situation and injects it into the model's context window alongside the conversation history and user profile.
- This means the AI can say things like "Lecture 7 walks through exactly this scenario" because it has actually retrieved and read the relevant content.

#### Retry and Resilience

All OpenAI API calls use exponential backoff retry logic to handle transient failures gracefully:

- **MAX_RETRIES**: 3
- **RETRY_DELAY_BASE**: 2 seconds
- Resulting delays: 2s, 4s, 8s before final failure
- This handles transient rate limits, API hiccups, and temporary network issues without operator intervention.

---

### 2. Gmail (Email Transport)

Gmail serves as both the inbound and outbound transport layer. The system connects using standard IMAP and SMTP protocols with App Password authentication -- no OAuth complexity, no token refresh flows, just a secure, reliable email connection.

#### Inbound (IMAP)

- **Host**: `imap.gmail.com` with SSL encryption
- Polls the inbox on a scheduled basis (hourly during business hours, 8am-9pm ET) to fetch new messages.
- **Sender filtering**: Automatically ignores known non-human senders including `no-reply`, `mailer-daemon`, Google Workspace system notifications, calendar notifications, and other automated addresses. This prevents the system from trying to "coach" automated emails.
- **Email parsing**: A two-tier approach designed for robustness. The `email-reply-parser` library handles deterministic extraction of the member's actual message from the email thread (stripping signatures, quoted replies, forwarded content, etc.). When this fails to produce a clean result -- which happens with some email clients that use non-standard formatting -- GPT-4o-mini is called as an intelligent fallback parser that understands email structure semantically.
- **Deduplication**: Every email is tracked by its Gmail message ID. Before processing any email, the system checks if that ID already exists in the database, preventing double-processing even if a workflow runs multiple times or the same email is fetched again.

#### Outbound (SMTP)

- **Host**: `smtp.gmail.com`, **Port**: 587, **Encryption**: STARTTLS
- **From address**: Displays as `"Wes" <email>` to maintain the coaching persona.
- **Email threading**: Sets `In-Reply-To` and `References` headers to ensure responses appear in the same conversation thread in the member's inbox. This is critical for the user experience -- coaching responses appear as natural replies in an ongoing conversation, not as separate disconnected emails. Includes fallback logic when original message IDs are unavailable.
- **Human-like timing**: Applies a random delay of 0-60 seconds before sending each response. This prevents responses from feeling robotic (instant replies would be suspicious) and avoids Gmail rate limiting when processing batches.

#### Authentication

- Uses Gmail App Passwords, which require two-factor authentication to be enabled on the Google account. This avoids the complexity of OAuth2 token refresh flows while maintaining security. App Passwords are 16-character passwords generated specifically for the coaching system and can be revoked independently of the account password.

---

### 3. Supabase (Database)

The persistence layer is a PostgreSQL database hosted on Supabase, accessed through the Python `supabase` client library using a singleton connection pattern. Supabase was chosen for its generous free tier, built-in SQL editor (useful for schema management), and straightforward REST API.

#### Security

- **Row Level Security (RLS)** is enabled on all tables. Access is controlled through the Supabase service key, which bypasses RLS for server-side operations while ensuring the database is protected against direct unauthorized access from other clients.

#### Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `users` | Program member profiles and coaching state | email, name, stage, business_idea, summary, status, checkin_days, onboarding_step, satisfaction_score, gmail_message_id, gmail_thread_id, auto_approve_threshold, notes, current_challenge |
| `conversations` | All email exchanges and coaching interactions | user_id, type, status, user_message_raw, user_message_parsed, ai_response, sent_response, confidence, flag_reason, gmail_message_id, gmail_thread_id, sent_at, approved_by, approved_at, satisfaction_score, thread_reply_count, resource_referenced, stage_detected, stage_changed |
| `corrected_responses` | Human corrections saved for AI learning | conversation_id, original_message, ai_response, corrected_response, correction_notes, correction_type |
| `settings` | Key-value system configuration | key, value (stores auto-approve threshold, check-in schedule, thread cap, send hours, re-engagement config, response length limits, notification preferences) |
| `resources` | Program resources with topic and stage metadata | title, description, topics (array), stage (22 seeded resources covering the full curriculum) |
| `workflow_runs` | Audit log of all automated workflow executions | workflow name, status, timestamp, details |
| `model_responses` | Example ideal responses by stage for context injection | stage, scenario, ideal response (used to ground the AI's tone and approach) |

The `users` table serves a dual purpose, tracking both coaching state (stage, business idea, current challenge, journey summary) and operational state (onboarding step, check-in days, satisfaction score, Gmail threading IDs). This single-table design keeps all user context in one queryable location, simplifying the context-building process that feeds the AI.

---

### 4. Streamlit (Dashboard)

The admin dashboard is built with Streamlit and hosted on Streamlit Community Cloud (free tier). It provides a complete management interface for the coaching system -- from reviewing individual AI responses to monitoring system-wide analytics.

#### Access Control

- Password-protected via the `DASHBOARD_PASSWORD` secret stored in Streamlit's secrets management. Admins enter the password on first visit and remain authenticated for the session.

#### Pages

The dashboard uses Streamlit's multipage app pattern, with pages auto-discovered from the `dashboard/pages/` directory. There are 9 pages in total:

1. **Home** (`app.py`) -- Quick stats overview showing active users, pending reviews, recent workflow runs, and system health at a glance. This is the operator's first stop each day.

2. **Pending Review** -- The primary operational page and where operators spend most of their time. Displays AI-generated responses awaiting human review. Shows the member's message, the AI's response (editable), confidence score, user context (stage, business idea, recent history), and action buttons to approve, reject, or flag. Editing a response before approval automatically creates a correction record that feeds the learning loop.

3. **Flagged** -- Responses that triggered one or more safety flags (legal, mental health, out-of-scope, URLs). Displays the specific flag reasons prominently to help admins understand why the response was flagged and what to look for. These conversations need human judgment rather than rubber-stamping.

4. **Conversations** -- Full conversation history browser with filters by user and status. Provides a chronological view of all coaching interactions, useful for understanding a member's journey and reviewing past exchanges.

5. **Users** -- Member management interface. Add new users, edit profiles (business idea, stage, challenge, notes), set per-user check-in days, view onboarding status, satisfaction scores, and current stage. This is where operator knowledge about each member lives.

6. **Corrections** -- View and manage the corpus of human corrections that teach the AI over time. Each correction includes the original message, the AI's response, the corrected version, notes explaining the change, and a categorized correction type (Tone, Content, Length, Focus, Factual, Style).

7. **Settings** -- System-wide configuration. Controls the auto-approve confidence threshold, default check-in schedule (days of the week), thread reply cap, allowed send hours, re-engagement timing, response length limits, notification preferences, and Gmail connectivity status.

8. **Run Workflows** -- Operational control center. Displays system health checks (database connectivity, Gmail status, Python version, migration status), the automated schedule table showing all cron jobs, manual trigger buttons to run any workflow on demand, a fine-tuning data export tool with step-by-step instructions, and a history of recent workflow runs with expandable details.

9. **Analytics** -- Data visualizations covering user overview metrics, confidence calibration analysis (showing edit rates by confidence score to validate threshold settings), response time tracking, correction analytics (distribution by type and stage), and satisfaction trend charts.

---

### 5. GitHub Actions (Scheduling)

All automated workflows run on GitHub Actions using cron triggers. This provides reliable scheduling, built-in logging, manual override capabilities, and secret management without requiring a dedicated server, cloud functions, or always-on infrastructure.

#### Workflow Schedule

| Workflow | File | Schedule (ET) | Cron (UTC) | Purpose |
|---|---|---|---|---|
| Process Emails | `process_emails.yml` | Every hour, 8am-9pm | `0 13-23,0-2 * * *` | Fetch and process new inbound emails |
| Send Approved | `send_approved.yml` | 9am, 1pm, 7pm | `0 14,18,0 * * *` | Send approved responses to members |
| Check-in | `check_in.yml` | 9am daily | `0 14 * * *` | Send personalized check-in questions |
| Re-engagement | `re_engagement.yml` | 10am daily | `0 15 * * *` | Nudge silent users, mark very silent users |
| Cleanup | `cleanup.yml` | 11pm daily | `0 4 * * *` | Catch any missed or stuck emails |

#### Runtime Configuration

- **Runtime**: Python 3.11 on `ubuntu-latest`
- **Manual triggers**: All workflows include `workflow_dispatch`, allowing admins to trigger any workflow on demand from either the GitHub Actions UI or the Streamlit dashboard's Run Workflows page.
- **Secrets**: All credentials (Supabase, OpenAI, Gmail) are stored as GitHub repository secrets and injected as environment variables at runtime. They never appear in logs.
- **Entry point**: `run_workflow.py` serves as a simple dispatcher that accepts a workflow name argument and calls the corresponding workflow module. This single entry point simplifies the GitHub Actions YAML files.

---

### 6. Python (Application Layer)

The application is written in Python 3.9+ (leveraging `zoneinfo` from the standard library for timezone handling). The codebase follows a service-oriented architecture with clear separation of concerns: services handle external integrations, workflows orchestrate business processes, and the dashboard provides the operator interface.

#### Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai` | >= 1.30.0 | OpenAI API client (Responses API, file_search) |
| `supabase` | >= 2.4.0 | Supabase/PostgreSQL client |
| `streamlit` | >= 1.35.0 | Dashboard framework |
| `email-reply-parser` | >= 0.5.12 | Deterministic email thread parsing |
| `python-dotenv` | >= 1.0.0 | Environment variable loading from `.env` files |
| `pytz` | >= 2024.1 | Timezone fallback for environments lacking `zoneinfo` data |
| `pytest` | >= 8.0.0 | Test framework |

#### Configuration Strategy

The `config.py` module loads all configuration from environment variables with a Streamlit secrets fallback. When running in GitHub Actions, environment variables are injected from repository secrets. When running on Streamlit Community Cloud, the same values are read from Streamlit's secrets management system. This dual-source approach means the same codebase works in both execution contexts without modification -- no feature flags, no conditional imports, no deployment-specific config files.

---

## Data Flow Architecture

### Inbound Email Processing Pipeline

This is the core pipeline, triggered hourly by the `process_emails` workflow. It is the most complex flow in the system and handles everything from reading raw emails to producing reviewed coaching responses.

```
Gmail Inbox (IMAP fetch)
  --> Filter ignored senders (no-reply, mailer-daemon, system notifications)
  --> Match sender to existing user by email address
      --> If no match: create new user record, initiate onboarding sequence
  --> Parse email body
      --> Primary: email-reply-parser (deterministic extraction)
      --> Fallback: GPT-4o-mini (intelligent parsing when deterministic fails)
  --> Detect intent (pause request, resume request, or normal coaching message)
  --> Check thread reply cap (default: 4 replies per thread)
  --> Build generation context:
      |-- Stage-specific system prompt (from assistant_instructions.md)
      |-- User profile (name, stage, business idea, challenge, summary)
      |-- Recent conversation history (last several exchanges)
      |-- Relevant program resources (matched by stage and topic)
      |-- Stage-scoped corrections from corrected_responses table
      |-- Model responses for the user's current stage
  --> Generate coaching response (GPT-4o via Responses API with file_search RAG)
  --> Evaluate response (GPT-4o-mini):
      |-- Confidence score (1-10)
      |-- Flag detection (legal, mental health, out-of-scope, URLs)
      |-- Stage detection (Ideation / Early Validation / Late Validation / Growth)
      |-- Resource reference detection
  --> Analyze satisfaction (GPT-4o-mini --> 1-10 engagement score)
  --> Route based on evaluation:
      |-- confidence >= threshold AND no flags --> Auto-approved
      |-- Any flags present --> Flagged
      |-- Otherwise --> Pending Review
  --> Store conversation record in database
  --> Update user metadata:
      |-- Satisfaction score (rolling average: 70% old / 30% new)
      |-- Stage changes (if detected)
      |-- Milestone tracking
```

### Outbound Email Pipeline

Triggered 3 times daily by the `send_approved` workflow:

```
Query: approved conversations where sent_at IS NULL
  --> For each approved conversation:
      --> Append sign-off ("Wes")
      --> Apply random delay (0-60 seconds) for human-like pacing
      --> Resolve email threading:
          |-- Look up user's gmail_message_id and gmail_thread_id
          |-- Set In-Reply-To and References headers
          |-- Fallback logic if original message IDs unavailable
      --> Send via Gmail SMTP (STARTTLS on port 587)
      --> Generate journey summary update (GPT-4o-mini)
      --> Update conversation: set status to "Sent", record sent_at timestamp
      --> Update user: refresh summary with latest journey narrative
```

### Check-in Pipeline

Triggered daily at 9am ET by the `check_in` workflow:

```
Determine current day of week (timezone-aware, respects COACH_TIMEZONE)
  --> Fetch users eligible for today's check-in:
      |-- Users with personalized checkin_days that include today
      |-- Users without personalized days who match the system default schedule
      |-- Only active users (not paused, not in onboarding, not silent)
  --> For each eligible user:
      --> Build context (name, stage, business idea, current challenge, recent history)
      --> Generate personalized check-in question (GPT-4o, temperature 0.7)
      --> If generation fails: fall back to a standard stage-appropriate template
      --> Send via Gmail SMTP with proper threading
      --> Log conversation record with type "check_in" and status "Sent"
```

### Review Pipeline (Human-in-the-Loop)

The review pipeline is the system's quality assurance mechanism and the heart of the human-in-the-loop design:

```
AI generates response --> GPT-4o-mini evaluates --> Confidence score assigned (1-10)

Routing logic:
  IF confidence >= auto_approve_threshold AND no flags detected:
      --> Auto-approved (proceeds to send queue)
  ELSE IF any flags detected (legal, mental_health, out_of_scope, urls):
      --> Flagged (requires admin attention, flag reasons displayed)
  ELSE:
      --> Pending Review (admin reviews before sending)

Admin review workflow (via Streamlit dashboard):
  --> View original message, AI response, confidence score, user context
  --> Options:
      --> Approve as-is
      --> Edit response text, then approve
          --> If edited: correction automatically saved to corrected_responses
      --> Reject (response discarded, user receives nothing)
      --> Move to Flagged / Move to Pending
```

The auto-approve threshold is configurable via the Settings page, providing a tunable dial for graduated trust. A typical progression: start at 10 (review everything), lower to 9 after the first few weeks, then gradually down to 7-8 as the correction corpus builds and the AI proves reliable.

### Learning Loop

The system implements a continuous improvement cycle that makes the AI smarter over time:

```
Admin edits AI response before approval
  --> Correction saved to corrected_responses table:
      |-- Original user message (what the member said)
      |-- AI's original response (what the AI drafted)
      |-- Admin's corrected version (what was actually sent)
      |-- Correction notes (admin's explanation of the change)
      |-- Correction type (Tone, Content, Length, Focus, Factual, Style)

Future response generation:
  --> Stage-scoped corrections are injected into the generation context
  --> The model sees examples of "what you generated" vs "what the human preferred"
  --> This grounds future responses closer to the admin's standards
  --> Effect is cumulative: more corrections = better responses

Long-term fine-tuning path:
  --> Export corrections as JSONL fine-tuning dataset (via Run Workflows page)
  --> Fine-tune GPT-4o-mini on the correction corpus
  --> Deploy the custom fine-tuned model for evaluation tasks
  --> Potentially fine-tune GPT-4o for generation with sufficient data (100+ corrections)
```

---

## Database Schema

### Entity Relationship Summary

```
users (1) ---< (many) conversations
users (1) ---< (many) corrected_responses (via conversations)
conversations (1) ---< (many) corrected_responses

settings: standalone key-value store
resources: standalone reference table (22 seeded records)
workflow_runs: standalone audit log
model_responses: standalone reference table (example responses by stage)
```

### Key Indexes and Query Patterns

- **Conversations** are primarily queried by `status` (pending_review, flagged, approved, sent) and `user_id`. The Pending Review and Flagged pages query by status; the Conversations page queries by user_id.
- **Users** are queried by `email` (for sender matching during email processing) and by `checkin_days` (for daily check-in targeting).
- **Corrected responses** are queried by stage (via join to conversations/users) for context injection during generation. Only corrections matching the current user's stage are included.
- **Settings** are queried by `key` for individual configuration values, loaded fresh on each workflow run.
- **Workflow runs** are queried by timestamp for recent history display on the Run Workflows page.

---

## Key Design Decisions

### Email-First Interface

The system deliberately avoids building a dedicated app or web portal for members. Members interact entirely through their existing email client. This eliminates adoption friction -- there is nothing to install, no new login to remember, and the experience integrates naturally into the member's existing workflow. The result is dramatically higher engagement compared to systems that require members to visit a separate platform.

### Human-in-the-Loop with Graduated Trust

Every AI-generated response passes through evaluation before reaching a member. The auto-approve threshold provides a tunable dial: start conservative (threshold 9-10, nearly everything reviewed) and gradually relax as the system proves reliable. This builds trust incrementally rather than requiring a binary all-or-nothing decision. The operator is always in control.

### Dual-Model Architecture

Using GPT-4o for generation and GPT-4o-mini for evaluation is a deliberate cost/quality optimization. Generation tasks benefit from the larger model's superior reasoning and creativity. Evaluation tasks are more formulaic (score this response, detect these flags) and run well on the smaller, faster, cheaper model. This keeps API costs low while maintaining high generation quality.

### Stage-Specific Coaching

The system recognizes four entrepreneurship stages (Ideation, Early Validation, Late Validation, Growth) and adapts its coaching approach for each. Stage-specific system prompts, resources, corrections, and model responses ensure that a member in Ideation receives fundamentally different coaching than one in Growth. Stage transitions are detected automatically and can be confirmed by the operator.

### Resource Referencing by Name Only

A deliberate design rule: the system never includes URLs or hyperlinks in responses. Resources are referenced by name only (e.g., "review Lecture 5 on customer discovery"). This prevents broken links, avoids the AI hallucinating URLs, and keeps responses feeling conversational rather than automated. The evaluation model flags any response that contains a URL.

### Thread Reply Cap

To prevent unbounded back-and-forth that could dilute coaching quality, conversations are capped at a configurable number of thread replies (default: 4). After the cap, the system stops generating new responses and waits for the next check-in to reset the cycle. This keeps coaching focused and prevents members from using the system as a general-purpose chatbot.

### Satisfaction Tracking with Smoothing

Member satisfaction scores use a rolling average formula: `new_score = (0.7 * old_score) + (0.3 * latest_score)`. The 70/30 weighting smooths out noise from individual message variance while still being responsive to genuine engagement shifts. This provides a more stable indicator of engagement trends than raw per-message scores.

### Personalized Check-in Scheduling

Each user can have individualized check-in days (e.g., Monday and Thursday) stored in their profile. Users without personalized settings fall back to the system-wide default schedule. This allows the coaching cadence to be tailored to each member's needs and availability while keeping configuration simple.

### Resilience Patterns

The system is designed to fail gracefully:

- **Exponential backoff** on all OpenAI API calls (3 retries: 2s, 4s, 8s).
- **Fallback email parsing** (deterministic parser to GPT-4o-mini when parsing fails).
- **Fallback check-in templates** (stage-appropriate templates when personalized generation fails).
- **Fallback threading** (graceful degradation when Gmail message IDs are unavailable).
- **Error alerting** through workflow run logging and email notifications to the operator.
- **Idempotent processing** via Gmail message ID deduplication to handle duplicate email fetches safely.
- **Cleanup workflow** as a nightly safety net that catches any emails missed during the day.

### Privacy-Conscious Architecture

No user data is sent to any external service beyond OpenAI, which is required for response generation and evaluation. The Supabase database, Gmail transport, and Streamlit dashboard form a closed loop. There are no analytics services, no third-party integrations, and no data sharing beyond what is strictly necessary for the coaching function.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL (e.g., `https://xxxx.supabase.co`) |
| `SUPABASE_KEY` | Supabase service role key (bypasses RLS for server-side operations) |
| `OPENAI_API_KEY` | OpenAI API key with access to GPT-4o, GPT-4o-mini, and the Responses API |
| `VECTOR_STORE_ID` | OpenAI Vector Store ID containing indexed program content for RAG retrieval |
| `GMAIL_ADDRESS` | Gmail address used for sending and receiving coaching emails |
| `GMAIL_APP_PASSWORD` | Gmail App Password (requires 2FA enabled on the Google account) |
| `GMAIL_IMAP_HOST` | IMAP server hostname (default: `imap.gmail.com`) |
| `GMAIL_SMTP_HOST` | SMTP server hostname (default: `smtp.gmail.com`) |
| `GMAIL_SMTP_PORT` | SMTP server port (default: `587` for STARTTLS) |
| `COACH_TIMEZONE` | Timezone for schedule calculations (default: `America/New_York`) |
| `DASHBOARD_PASSWORD` | Password required to access the Streamlit admin dashboard |

These variables are stored as GitHub repository secrets for workflow execution and as Streamlit secrets for dashboard operation. The `config.py` module abstracts over both sources, checking environment variables first and falling back to Streamlit secrets, so the same code runs in both contexts without modification.

---

## File Structure

```
coaching-system/
├── config.py                        # Centralized configuration loader
│                                    # Reads from env vars with Streamlit secrets fallback
├── run_workflow.py                   # GitHub Actions entry point / dispatcher
│                                    # Accepts workflow name, calls corresponding module
├── requirements.txt                 # Python dependency pinning
│
├── dashboard/
│   ├── app.py                       # Main dashboard entry + Home page
│   │                                # Quick stats, recent workflow runs, system health
│   └── pages/
│       ├── 1_pending_review.py      # Review/edit/approve AI responses
│       ├── 2_flagged.py             # Flagged responses needing attention
│       ├── 3_conversations.py       # Full conversation history browser
│       ├── 4_users.py               # Member management interface
│       ├── 5_corrections.py         # Human correction corpus manager
│       ├── 6_settings.py            # System-wide configuration
│       ├── 7_run_workflows.py       # Health checks, manual triggers, fine-tuning export
│       └── 8_analytics.py           # Metrics, charts, calibration analysis
│
├── db/
│   ├── supabase_client.py           # Singleton database access layer
│   │                                # All CRUD operations, query builders
│   ├── setup.sql                    # Initial schema DDL (tables, RLS, indexes)
│   ├── migration_v2.sql             # Feature enhancement migrations
│   │                                # (satisfaction, onboarding, analytics fields)
│   └── seed_model_responses.sql     # Example ideal responses by stage
│
├── services/
│   ├── coaching_service.py          # Core business logic orchestrator
│   │                                # Context building, pipeline coordination
│   ├── gmail_service.py             # Email send/receive abstraction
│   │                                # IMAP fetch, SMTP send, threading, parsing
│   └── openai_service.py            # AI model interaction layer
│                                    # Generation, evaluation, RAG, retries
│
├── workflows/
│   ├── process_emails.py            # Inbound email processing pipeline
│   ├── send_approved.py             # Outbound approved response sender
│   ├── check_in.py                  # Personalized daily check-in sender
│   ├── re_engagement.py             # Silent user re-engagement nudger
│   └── cleanup.py                   # Catch missed/stuck email cleanup
│
├── prompts/
│   ├── assistant_instructions.md    # Coach "Wes" persona definition and rules
│   │                                # Tone, boundaries, stage-specific guidance
│   ├── evaluation_prompt.md         # Response quality evaluation template
│   │                                # Confidence scoring rubric, flag definitions
│   ├── email-parsing-prompt.md      # Fallback email parsing instructions
│   └── summary-update-prompt.md     # Journey summary generation instructions
│
├── templates/
│   ├── emails/
│   │   └── email-templates.md       # Email templates for check-ins, onboarding, etc.
│   ├── knowledge-chunks/
│   │   └── chunking-guide.md        # Guide for preparing program content
│   └── model-responses/
│       └── all-model-responses.md   # Model response reference by stage
│
├── scripts/
│   ├── setup_supabase.py            # Supabase setup helper
│   └── export_finetune_data.py      # Fine-tuning dataset exporter
│                                    # Converts corrections to OpenAI JSONL format
│
├── tests/
│   ├── conftest.py                  # Shared test fixtures and service mocks
│   ├── test_email_processing.py     # Inbound pipeline tests
│   ├── test_evaluation_routing.py   # Confidence/flag routing logic tests
│   ├── test_proactive_outreach.py   # Check-in and re-engagement tests
│   ├── test_send_approved.py        # Outbound pipeline tests
│   ├── test_edge_cases.py           # Boundary conditions and error handling
│   └── test_new_features.py         # Onboarding, thread cap, satisfaction,
│                                    # stage changes, personalized scheduling
│
└── .github/workflows/
    ├── process_emails.yml           # Hourly email processing (8am-9pm ET)
    ├── send_approved.yml            # 3x daily response sending
    ├── check_in.yml                 # Daily check-in at 9am ET
    ├── re_engagement.yml            # Daily re-engagement at 10am ET
    └── cleanup.yml                  # Nightly cleanup at 11pm ET
```

---

## Test Suite

The system includes a comprehensive test suite with **78 tests across 6 test files**. All external services (OpenAI, Gmail, Supabase) are fully mocked, ensuring tests run fast, deterministically, and without any network dependencies or API costs.

### Test Coverage Areas

| Test File | Focus Area | Key Scenarios |
|---|---|---|
| `test_email_processing.py` | Inbound pipeline | Email fetching, sender filtering, user matching, new user creation, email parsing (deterministic + fallback), intent detection (pause/resume), context building, response generation |
| `test_evaluation_routing.py` | Evaluation and routing | Confidence scoring boundaries, flag detection (all 4 types), auto-approve threshold logic, routing to correct status (auto-approved, pending, flagged) |
| `test_proactive_outreach.py` | Check-ins and re-engagement | Day-of-week matching, personalized vs. default schedules, check-in question generation, fallback templates, re-engagement targeting of silent users |
| `test_send_approved.py` | Outbound pipeline | Batch sending, sign-off appending, threading header construction, delay timing, summary generation, status updates |
| `test_edge_cases.py` | Error handling and boundaries | Empty messages, malformed emails, API failures, retry exhaustion, missing user data, thread cap enforcement, duplicate processing |
| `test_new_features.py` | Recent additions | Onboarding sequence flow (all 3 steps), thread reply cap behavior, satisfaction score rolling average calculation, stage change detection and recording, personalized check-in day scheduling |

### Test Infrastructure

- **Framework**: pytest with fixtures defined in `conftest.py`.
- **Mocking strategy**: All external service calls (OpenAI completions, Gmail IMAP/SMTP, Supabase queries) are replaced with deterministic mock responses. This allows testing the full pipeline logic without external dependencies.
- **Assertion patterns**: Tests verify both the correct orchestration of service calls (e.g., that the evaluation model is called after generation) and the correct handling of service responses (e.g., that a confidence score of 6 with no flags routes to Pending Review).
