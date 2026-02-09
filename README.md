# Automated Email Coaching System

An automated email-based coaching system that sends check-in emails 1-2x weekly, receives user responses, generates AI coaching feedback grounded in your resources, and manages quality through confidence scoring and manual review.

**Stack:** n8n + Airtable + OpenAI GPT-4 + Gmail

---

## Quick Start

1. Read the [Setup Guide](docs/setup-guide.md)
2. Set up Airtable using [schema.md](airtable/schema.md)
3. Import n8n workflows from [n8n/workflows/](n8n/workflows/)
4. Populate your knowledge base using [chunking-guide.md](templates/knowledge-chunks/chunking-guide.md)
5. Add model responses from [model-responses.csv](templates/model-responses/model-responses.csv)
6. Test with the checklist in the setup guide
7. Go live with a pilot group

---

## Project Structure

```
Coaching System/
├── README.md                    # This file
├── airtable/
│   ├── schema.md               # Complete Airtable schema
│   └── sample-users.csv        # Sample data for testing
├── n8n/
│   ├── env-template.txt        # Environment variables template
│   └── workflows/
│       ├── 1-check-in-scheduler.json
│       ├── 2-response-processor.json
│       ├── 3-send-approved-responses.json
│       ├── 4-re-engagement.json
│       └── 5-cleanup.json
├── prompts/
│   ├── main-response-prompt.md # Primary AI coaching prompt
│   ├── email-parsing-prompt.md # Email content extraction
│   └── summary-update-prompt.md# User journey summaries
├── templates/
│   ├── emails/
│   │   └── email-templates.md  # All email templates
│   ├── knowledge-chunks/
│   │   ├── chunking-guide.md   # How to chunk your resources
│   │   └── chunks-template.csv # CSV import template
│   └── model-responses/
│       ├── all-model-responses.md  # Full reference
│       └── model-responses.csv     # CSV for Airtable import
└── docs/
    ├── setup-guide.md          # Complete setup instructions
    └── quick-reference.md      # Daily operations reference
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gmail                                    │
│            (coachwes@thelaunchpadincubator.com)                 │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │ incoming                       │ outgoing
                  ▼                                ▲
┌─────────────────────────────────────────────────────────────────┐
│                         n8n Workflows                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Check-in     │  │ Response     │  │ Send Approved        │  │
│  │ Scheduler    │  │ Processor    │  │ Responses            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Re-engage    │  │ Cleanup      │                            │
│  │ Silent Users │  │ (catch-up)   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │                               │
                  ▼                               ▼
┌─────────────────────────────┐   ┌───────────────────────────────┐
│        Airtable             │   │         OpenAI GPT-4          │
│  • Users                    │   │  • Generate responses         │
│  • Conversations            │   │  • Score confidence           │
│  • Knowledge Chunks         │   │  • Detect stage transitions   │
│  • Model Responses          │   │  • Update user summaries      │
│  • Corrected Responses      │   │  • Parse email content        │
└─────────────────────────────┘   └───────────────────────────────┘
```

---

## Workflows

| # | Workflow | Schedule | Purpose |
|---|----------|----------|---------|
| 1 | Check-in Scheduler | Tue & Fri 9am | Send check-in emails to active users |
| 2 | Response Processor | Daily 8am & 6pm | Process incoming emails, generate AI responses |
| 3 | Send Approved | Daily 9am & 7pm | Send approved coaching responses |
| 4 | Re-engagement | Daily 10am | Nudge users who haven't responded in 10+ days |
| 5 | Cleanup | Daily 11pm | Catch any missed emails |

---

## Key Features

- **Confidence Scoring:** AI rates its own responses 1-10, auto-approving high confidence
- **Flagging System:** Automatically flags sensitive topics for human review
- **Pause/Resume:** Users can pause check-ins by saying "pause" and resume with "resume"
- **Email Threading:** Maintains conversation threads in Gmail
- **Knowledge Grounding:** Responses reference your books and lectures
- **Learning Loop:** Corrected Responses table improves AI over time
- **User Summaries:** Running summaries of each user's journey

---

## Estimated Costs

For ~50 active users with 2 check-ins per week:

| Service | Monthly Cost |
|---------|--------------|
| OpenAI GPT-4 | $15-40 |
| n8n Cloud | $0-20 |
| Airtable | $0-20 |
| **Total** | **$35-80** |

---

## Support

For issues with:
- **n8n:** [community.n8n.io](https://community.n8n.io)
- **Airtable:** [support.airtable.com](https://support.airtable.com)
- **OpenAI:** [help.openai.com](https://help.openai.com)
