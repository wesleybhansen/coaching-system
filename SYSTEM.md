# Coach Wes Coaching System — Complete System Description

## Purpose

This is an AI-assisted email coaching system for **Wes Hansen's entrepreneurship coaching program** (The Launchpad Incubator). The system acts as a scalable extension of Wes — it reads incoming emails from coaching participants, drafts personalized coaching responses in Wes's voice, and sends them after Wes reviews and approves each one.

The goal is to let Wes coach dozens (eventually hundreds) of people via email with a time investment of ~30 minutes per day reviewing AI-generated drafts, rather than hours writing individual responses.

---

## How It Works — End-to-End Flow

### 1. A user sends an email

A coaching participant sends an email to `coachwes@thelaunchpadincubator.com`. This could be:
- A reply to a check-in prompt
- A follow-up question
- A new person emailing for the first time
- A request to pause or resume coaching

### 2. Process Emails workflow runs

The `process_emails` workflow fetches all unread emails from Gmail via IMAP.

**For each email, the system:**

1. **Filters out junk** — no-reply addresses, Google Workspace notifications, mailer-daemon, etc. are auto-marked as read and skipped. The system also skips emails from its own address.

2. **Checks for duplicates** — if we already processed this Gmail message ID, skip it.

3. **Looks up the sender** — searches the `users` table by email address.

4. **If the sender is unknown (new user):**
   - Creates a new user record with status "Onboarding"
   - Generates the standard onboarding/intake email as a draft
   - Sets the conversation to **Pending Review** so Wes can approve before anything is sent
   - The onboarding email asks the new user to reply with: their stage (Ideation/Validation/Growth), their biggest challenge, and their business idea

5. **If the sender is a known user:**
   - **Parses the email** — uses `email-reply-parser` (deterministic, no API call) to strip signatures, quoted text, and boilerplate. Falls back to GPT-4o-mini only if the deterministic parser returns empty.
   - **Detects intent** — checks for pause/resume keywords:
     - **Pause keywords:** "pause", "break", "stop", "unsubscribe", "take a break", "stepping back"
     - **Resume keywords:** "resume", "i'm back", "start again", "ready"
     - If pause detected: sets user status to "Paused", drafts a pause confirmation, sets to Pending Review
     - If resume detected: sets user status to "Active", drafts a resume confirmation, sets to Pending Review
   - **For normal messages — generates an AI response:**
     1. **Builds context** — assembles a prompt with: user profile (name, stage, business idea, journey summary), last 3 conversations, model responses for their stage, recent corrected responses, and the current message
     2. **Generates response** — sends context to GPT-4o via the OpenAI Responses API with `file_search` enabled (searches a vector store containing Wes's books, lectures, and coaching content)
     3. **Evaluates response** — a separate GPT-4o-mini call scores the response on confidence (1-10) and checks for flags
     4. **Routes the conversation** based on confidence score and flags:
        - **Flagged** → if any safety flags triggered (see Guardrails section below)
        - **Approved** → if confidence >= auto-approve threshold (default is 10, meaning nothing auto-approves initially)
        - **Pending Review** → everything else (the default path)

6. **Stores the conversation** in the `conversations` table with all metadata (raw email, parsed email, AI response, confidence score, flag reason, detected stage, etc.)

7. **Updates user metadata** — last response date, Gmail thread/message IDs for threading, stage if changed.

### 3. Wes reviews on the dashboard

Wes opens the Streamlit dashboard and goes to the **Pending Review** page. For each conversation he can:
- **Read** the user's message and the AI's draft response
- **Edit** the response if needed
- **Approve** the response (moves to "Approved" status)
- **Reject** the response (if the AI got it completely wrong)

The **Flagged** page shows conversations that need special attention (legal questions, mental health concerns, stage transitions, etc.).

### 4. Send Approved workflow runs

The `send_approved` workflow:
1. Queries all conversations with status "Approved" and no `sent_at` timestamp
2. For each one:
   - Adds "Wes" as a sign-off
   - Adds a small random delay (0-60 seconds) for natural spacing
   - Sends via Gmail SMTP, threading into the existing conversation if possible
   - Updates the conversation status to "Sent" with timestamp
   - Generates a summary update (via GPT-4o-mini) and appends it to the user's journey summary

### 5. Proactive outreach (Check-in and Re-engagement)

**Check-in workflow** (Tue & Fri at 9am ET):
- Finds active users who haven't been contacted in 3+ days
- Sends a structured check-in email asking for: what they accomplished, current focus, next step, and approach
- These send directly (not through Pending Review) since they're standardized templates

**Re-engagement workflow** (Daily at 10am ET):
- **Part 1:** Users silent for 10+ days get a "Haven't heard from you" nudge (but only if no re-engagement was sent in the last 14 days)
- **Part 2:** Users silent for 17+ days (10 + 7 after nudge) are automatically marked as "Silent" status

**Cleanup workflow** (Daily at 11pm ET):
- Catches any unread emails older than 24 hours that slipped through regular processing
- Logs them as "Flagged" for manual review
- Sends Wes a notification email listing what was found

---

## Architecture

### Infrastructure

| Component | Platform | Details |
|-----------|----------|---------|
| Code & version control | GitHub (`wesleybhansen/coaching-system`, public) | All source code |
| Dashboard | Streamlit Community Cloud | Deploys from GitHub, auto-redeploys on push |
| Scheduled jobs | GitHub Actions | 5 YAML workflows with cron schedules |
| Database | Supabase (PostgreSQL) | `graxrljffyunivjkewer.supabase.co` |
| AI | OpenAI (GPT-4o for response generation, GPT-4o-mini for evaluation/parsing) | Vector store for knowledge base search |
| Email | Gmail (Google Workspace) | `coachwes@thelaunchpadincubator.com` via IMAP/SMTP |

### GitHub Actions Schedules (all times Eastern)

| Workflow | Schedule | Cron (UTC) |
|----------|----------|------------|
| Process Emails | Every hour, 8am–9pm ET | `0 13-23,0-2 * * *` |
| Check In | Tue & Fri at 9am ET | `0 14 * * 2,5` |
| Send Approved | 9am, 1pm, 7pm ET | `0 14 * * *`, `0 18 * * *`, `0 0 * * *` |
| Re-engagement | Daily at 10am ET | `0 15 * * *` |
| Cleanup | Daily at 11pm ET | `0 4 * * *` |

All workflows can also be triggered manually from the dashboard (Run Workflows page) or from GitHub Actions (workflow_dispatch).

### Database Schema (Supabase/PostgreSQL)

**`users`** — coaching participants
- `id` (uuid, PK), `email` (unique), `first_name`, `stage` (Ideation | Early Validation | Late Validation | Growth), `business_idea`, `current_challenge`, `summary` (running journey log), `status` (Active | Paused | Silent | Onboarding), `last_response_date`, `gmail_thread_id`, `gmail_message_id`, `auto_approve_threshold` (per-user override), `notes`

**`conversations`** — every coaching exchange
- `id` (uuid, PK), `user_id` (FK → users), `type` (Check-in | Follow-up | Re-engagement | Onboarding), `user_message_raw`, `user_message_parsed`, `ai_response`, `sent_response` (may differ from ai_response if Wes edited it), `confidence` (1-10), `status` (Pending Review | Approved | Sent | Flagged | Rejected), `flag_reason`, `gmail_message_id` (unique, for dedup), `gmail_thread_id`, `resource_referenced`, `stage_detected`, `stage_changed`, `sent_at`, `approved_at`, `approved_by` ("auto" or null)

**`model_responses`** — example ideal responses the AI learns from
- `id`, `title`, `stage`, `scenario`, `user_example`, `ideal_response`, `notes`

**`corrected_responses`** — when Wes corrects the AI, stored for learning
- `id`, `conversation_id` (FK), `original_message`, `ai_response`, `corrected_response`, `correction_notes`, `correction_type` (Tone | Content | Length | Focus | Factual | Style)

**`settings`** — key-value configuration
- `global_auto_approve_threshold` (default: 10 = manual review everything)
- `check_in_days`, `check_in_hour`, `process_interval_minutes`, `process_start_hour`, `process_end_hour`
- `send_hours`, `re_engagement_days`, `max_response_paragraphs`, `coach_timezone`

**`workflow_runs`** — observability log
- `id`, `workflow_name`, `started_at`, `completed_at`, `status` (running | completed | failed), `items_processed`, `error_message`

### File Structure

```
coaching-system/
├── config.py                    # Loads env vars (supports .env and Streamlit secrets)
├── run_workflow.py              # CLI entry point for GitHub Actions
├── main.py                      # Local APScheduler runner (not used in production)
├── requirements.txt             # Python dependencies
├── .env                         # Local secrets (not in git)
├── .env.example                 # Template for .env
├── .gitignore
│
├── dashboard/
│   ├── app.py                   # Main dashboard with password protection and stats
│   └── pages/
│       ├── 1_pending_review.py  # Review and approve AI responses
│       ├── 2_flagged.py         # Flagged conversations needing attention
│       ├── 3_conversations.py   # Browse all conversation history
│       ├── 4_users.py           # User management (add, edit, view)
│       ├── 5_corrections.py     # Add corrected responses for AI learning
│       ├── 6_settings.py        # Configuration (thresholds, schedules)
│       └── 7_run_workflows.py   # Manual workflow trigger buttons
│
├── workflows/
│   ├── process_emails.py        # Fetch + process unread emails
│   ├── send_approved.py         # Send approved responses via Gmail
│   ├── check_in.py              # Proactive check-in emails
│   ├── re_engagement.py         # Nudge silent users
│   └── cleanup.py               # Catch missed emails
│
├── services/
│   ├── openai_service.py        # GPT-4o response gen, GPT-4o-mini eval/parsing
│   ├── gmail_service.py         # IMAP fetch, SMTP send, email templates
│   └── coaching_service.py      # Core pipeline: parse → detect intent → generate → evaluate → route
│
├── db/
│   ├── supabase_client.py       # All database queries
│   ├── setup.sql                # Full schema (run once in Supabase SQL Editor)
│   └── seed_model_responses.sql # Example model responses (run once)
│
├── prompts/
│   ├── assistant_instructions.md  # System prompt for GPT-4o (Wes's coaching persona)
│   ├── evaluation_prompt.md       # Evaluation/scoring prompt for GPT-4o-mini
│   ├── main-response-prompt.md    # Documentation of the full prompt template
│   ├── email-parsing-prompt.md    # Fallback email parsing prompt
│   └── summary-update-prompt.md   # Journey summary update prompt
│
├── .github/workflows/            # GitHub Actions cron jobs (5 YAML files)
└── .streamlit/config.toml        # Streamlit Cloud appearance config
```

---

## Guardrails and Safety

### Flagging System

The AI evaluation step (GPT-4o-mini) flags conversations for human review when any of these are detected:

- **Legal matters** — contracts, liability, incorporation specifics
- **Mental health** — burnout, personal crisis, emotional distress, family emergencies
- **Out-of-scope topics** — anything outside entrepreneurship coaching
- **Ambiguous situations** — unclear business context, confusing messages
- **Stage transitions** — user appears to be moving between stages
- **Direct requests** — user asks to speak with Wes directly or meet in person
- **Low confidence** — AI evaluation score below 5
- **Harmful advice risk** — response contains advice that could be harmful if wrong
- **Vulnerable populations** — mentions of minors or vulnerable populations

### What the AI will NOT do

- Give legal, medical, financial, or mental health advice
- Write long essay-like responses
- Use generic motivational language
- Provide step-by-step business plans
- Make promises about outcomes

### Auto-Approve Threshold

The `global_auto_approve_threshold` setting (default: 10) controls automatic routing:
- Score of 10 means NOTHING auto-approves — every response goes to Pending Review
- As Wes builds trust in the system, he can lower this (e.g., to 8) to let high-confidence responses auto-approve
- Individual users can have their own threshold override via `auto_approve_threshold`

### Email Filtering

The system ignores emails from:
- Its own address (`coachwes@thelaunchpadincubator.com`)
- No-reply addresses (noreply, no-reply, no_reply)
- System senders (mailer-daemon, postmaster, notifications, calendar-notification)
- Google Workspace system emails (workspace-noreply, admin@google, googleworkspace, accounts.google)

### Deduplication

Every conversation records the `gmail_message_id`. Before processing any email, the system checks if that message ID already exists in the database. This prevents double-processing if a workflow runs multiple times.

### Cleanup Safety Net

The cleanup workflow runs nightly and catches any unread emails older than 24 hours. These are flagged for manual review and Wes receives an email notification. This ensures no user message is ever lost.

---

## AI Models and Prompts

### Response Generation (GPT-4o)

- **Model:** `gpt-4o` via the OpenAI Responses API
- **Temperature:** 0.7 (allows some natural variation)
- **System prompt:** `prompts/assistant_instructions.md` — defines Wes's persona, coaching style, philosophy, and constraints
- **Tool:** `file_search` with vector store `vs_6985fa853f84819196e012018b0defca` — contains Wes's books (The Launch System, Ideas That Spread), lecture materials (Lectures 1-12), and custom coaching content
- **Context includes:** user profile, last 3 conversations, model responses for the user's stage, recent corrected responses, and the current parsed message

### Response Evaluation (GPT-4o-mini)

- **Model:** `gpt-4o-mini` (cheap, fast)
- **Temperature:** 0.2 (consistent evaluation)
- **Output:** JSON with confidence (1-10), flag (bool), flag_reason, detected_stage, stage_changed, resource_referenced, summary_update
- **Prompt:** `prompts/evaluation_prompt.md`

### Email Parsing (deterministic + GPT-4o-mini fallback)

- **Primary:** `email-reply-parser` Python library (no API call, instant)
- **Fallback:** GPT-4o-mini at temperature 0.1 — only used when the deterministic parser returns empty

### Summary Updates (GPT-4o-mini)

- **Model:** `gpt-4o-mini`
- **Temperature:** 0.5
- **Runs after each response is sent** — generates 1-2 sentence update appended to the user's journey summary with a date prefix

---

## User Lifecycle

1. **New email arrives from unknown address** → user created with status "Onboarding" → onboarding draft goes to Pending Review
2. **Wes approves onboarding** → Send Approved sends the intake email → user replies with their info
3. **Wes manually updates user** → sets stage, business idea, status to "Active" based on their reply
4. **Active user** → receives check-ins on Tue/Fri → replies are processed through the AI pipeline → Wes reviews and approves
5. **User goes quiet (10+ days)** → re-engagement nudge sent
6. **User still quiet (17+ days)** → status set to "Silent"
7. **User says "pause"** → status set to "Paused" → pause confirmation drafted for review → no more check-ins
8. **Paused user says "resume"** → status set to "Active" → resume confirmation drafted for review → check-ins resume

### User Stages

| Stage | Description |
|-------|-------------|
| Ideation | Exploring ideas, no customer conversations yet |
| Early Validation | Talking to potential customers, testing the problem |
| Late Validation | Has paying customers, refining the model |
| Growth | Scaling, hiring, expanding |

The AI detects stage transitions and flags them for Wes to confirm.

---

## Wes's Coaching Philosophy (embedded in the AI)

- Ideas come from conversations with real people, not brainstorming alone
- Customer conversations always come before building
- Manual before automated — learn what matters before investing
- Focus beats breadth — do one thing well before expanding
- Uncomfortable conversations (pricing, churn, hiring) are usually the most important
- Activity ≠ progress — challenge people who are busy but not moving forward

### Coaching Pattern

1. Name the pattern you see (stuck, avoiding, overwhelmed, confused, progressing)
2. Give a direct, actionable next step
3. Ask a question that requires them to think and respond

### Style

- Direct and focused — 1-3 paragraphs maximum
- One or two key points only
- Actionable nudges, not lectures
- Warm but not effusive
- References specific resources when relevant
- Never uses bullet points in responses
- Never uses patronizing language ("I'm proud of you")
- Always ends with an engaging question

---

## Learning and Improvement

### Model Responses

The `model_responses` table contains example ideal responses for each stage. These are included in the AI's context as style guides. They can be added and edited via the dashboard.

### Corrected Responses

When Wes edits an AI response before approving, the original and corrected versions can be saved to the `corrected_responses` table with notes about what was wrong (Tone, Content, Length, Focus, Factual, Style). Recent corrections are included in the AI's context so it learns from mistakes.

### Journey Summaries

Each user has a running `summary` field that grows over time with dated entries. This gives the AI persistent memory of the user's progress, key insights, decisions, and challenges across conversations.

---

## Configuration (via Dashboard Settings Page)

| Setting | Default | What it controls |
|---------|---------|-----------------|
| `global_auto_approve_threshold` | 10 | Confidence score needed for auto-approve (10 = manual review everything) |
| `check_in_days` | tue,fri | Days of the week to send check-ins |
| `check_in_hour` | 9 | Hour (24h) to send check-ins |
| `process_interval_minutes` | 60 | How often to check for new emails |
| `process_start_hour` | 8 | Earliest hour to process emails |
| `process_end_hour` | 21 | Latest hour to process emails |
| `send_hours` | 9,13,19 | Hours to send approved responses |
| `re_engagement_days` | 10 | Days of silence before nudge |
| `max_response_paragraphs` | 3 | Max paragraphs in AI responses |
| `coach_timezone` | America/New_York | Timezone for all scheduling |

---

## Secrets and Credentials

Secrets are stored in three places depending on the runtime:

| Runtime | Where secrets live |
|---------|-------------------|
| Local development | `.env` file (not in git) |
| GitHub Actions | GitHub repository secrets (Settings → Secrets) |
| Streamlit Cloud | Streamlit app secrets (Advanced settings) |

**Required secrets:**
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon/public key
- `OPENAI_API_KEY` — OpenAI API key
- `VECTOR_STORE_ID` — OpenAI vector store ID for knowledge base
- `GMAIL_ADDRESS` — `coachwes@thelaunchpadincubator.com`
- `GMAIL_APP_PASSWORD` — Google Workspace app password
- `DASHBOARD_PASSWORD` — password to access the Streamlit dashboard (Streamlit Cloud only)

---

## Known Limitations and Future Considerations

1. **Check-in and re-engagement emails currently send directly** without going through Pending Review. Only emails that trigger AI response generation go through the review pipeline. This is intentional for now (they use fixed templates) but could be changed.

2. **The vector store** (`vs_6985fa853f84819196e012018b0defca`) needs to be maintained separately in the OpenAI platform. Adding new books, lectures, or coaching content requires uploading files to this vector store.

3. **Gmail threading** relies on In-Reply-To and References headers. If a user starts a new email thread (instead of replying), the system treats it as a new conversation.

4. **No webhook/real-time processing** — the system polls Gmail on a schedule. There's a delay between when a user sends an email and when the system processes it (up to 1 hour during business hours).

5. **Streamlit Community Cloud** has resource limits on the free tier. Long-running workflow operations (like processing many emails) may time out if triggered from the dashboard. GitHub Actions is more reliable for large batches.
