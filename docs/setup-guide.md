# Automated Email Coaching System - Setup Guide

Complete setup instructions for the automated email coaching system using n8n, Airtable, OpenAI, and Gmail.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Airtable Setup](#phase-1-airtable-setup)
3. [Phase 2: n8n Setup](#phase-2-n8n-setup)
4. [Phase 3: Connect Services](#phase-3-connect-services)
5. [Phase 4: Import Workflows](#phase-4-import-workflows)
6. [Phase 5: Configure Environment](#phase-5-configure-environment)
7. [Phase 6: Populate Data](#phase-6-populate-data)
8. [Phase 7: Testing](#phase-7-testing)
9. [Phase 8: Go Live](#phase-8-go-live)

---

## Prerequisites

### Required Accounts
- [ ] Gmail account (coachwes@thelaunchpadincubator.com)
- [ ] Airtable account (free tier works for MVP)
- [ ] OpenAI API account with GPT-4 access
- [ ] n8n account (cloud) or server (self-hosted)

### Required Access
- [ ] Gmail API enabled for your Google account
- [ ] OpenAI API key with GPT-4 access
- [ ] Airtable personal access token

---

## Phase 1: Airtable Setup

### Step 1.1: Create Base

1. Go to [airtable.com](https://airtable.com)
2. Create a new base named "Email Coaching System"
3. Delete the default table

### Step 1.2: Create Tables

Refer to `/airtable/schema.md` for complete field specifications. Create these 5 tables:

1. **Users** - Coaching program members
2. **Conversations** - All email exchanges
3. **Knowledge Chunks** - Your chunked resources
4. **Model Responses** - Example coaching responses
5. **Corrected Responses** - Learning data from your edits

### Step 1.3: Create Views

For each table, create the views listed in `/airtable/schema.md`. Key views:

**Conversations table:**
- Pending Review (Status = "Pending Review")
- Flagged (Status = "Flagged")
- Approved (Status = "Approved", Sent At is empty)
- Recently Sent (Status = "Sent", Sent At in last 7 days)

### Step 1.4: Get API Credentials

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Create a new personal access token
3. Add scopes: `data.records:read`, `data.records:write`
4. Add access to your "Email Coaching System" base
5. Save the token securely

### Step 1.5: Get Table IDs

1. Open your base
2. Go to Help > API Documentation
3. Note down:
   - Base ID (starts with "app")
   - Each table ID (starts with "tbl")

---

## Phase 2: n8n Setup

### Option A: n8n Cloud

1. Go to [n8n.io](https://n8n.io) and create an account
2. Start a new workflow
3. Note your instance URL

### Option B: Self-Hosted

1. Install n8n via Docker:
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

2. Access at `http://localhost:5678`

---

## Phase 3: Connect Services

### Step 3.1: Gmail OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Set redirect URI to your n8n OAuth callback URL
6. In n8n, create Gmail OAuth2 credential
7. Complete OAuth flow

### Step 3.2: Airtable Token

1. In n8n, go to Credentials
2. Create new "Airtable Token API" credential
3. Paste your personal access token

### Step 3.3: OpenAI API

1. In n8n, go to Credentials
2. Create new "OpenAI API" credential
3. Paste your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Phase 4: Import Workflows

### Step 4.1: Import Each Workflow

For each JSON file in `/n8n/workflows/`:

1. In n8n, click "Add Workflow"
2. Click the three dots menu → Import from File
3. Select the JSON file
4. Save the workflow

Import in this order:
1. `1-check-in-scheduler.json`
2. `2-response-processor.json`
3. `3-send-approved-responses.json`
4. `4-re-engagement.json`
5. `5-cleanup.json`

### Step 4.2: Update Credentials

After importing, update each workflow:

1. Open the workflow
2. Click on each node that uses credentials (Gmail, Airtable, OpenAI)
3. Select your credentials from the dropdown
4. Save the workflow

---

## Phase 5: Configure Environment

### Step 5.1: Set Environment Variables

In n8n Settings → Environment Variables, add:

```
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
USERS_TABLE_ID=tblXXXXXXXXXXXXXX
CONVERSATIONS_TABLE_ID=tblXXXXXXXXXXXXXX
KNOWLEDGE_TABLE_ID=tblXXXXXXXXXXXXXX
MODEL_RESPONSES_TABLE_ID=tblXXXXXXXXXXXXXX
CORRECTED_TABLE_ID=tblXXXXXXXXXXXXXX
```

### Step 5.2: Update Email Addresses

In each workflow, search for "coachwes@thelaunchpadincubator.com" and update if using a different email.

---

## Phase 6: Populate Data

### Step 6.1: Chunk Your Resources

Follow `/templates/knowledge-chunks/chunking-guide.md` to:

1. Break down your books and lectures
2. Tag each chunk with Source, Stage, Topic
3. Import to Knowledge Chunks table

### Step 6.2: Add Model Responses

1. Import `/templates/model-responses/model-responses.csv` to Model Responses table
2. Review and customize responses to match your voice
3. Add additional scenarios as needed

### Step 6.3: Add Test User

Create one test user in the Users table:
- Email: your personal email
- First Name: Test
- Stage: Ideation
- Status: Active

---

## Phase 7: Testing

### Test Checklist

Run through each test before going live:

#### Test 1: Check-in Scheduler
- [ ] Manually trigger Workflow 1
- [ ] Verify email arrives in test user's inbox
- [ ] Verify Conversation record created in Airtable
- [ ] Verify Thread ID stored in Users table

#### Test 2: Response Processor
- [ ] Reply to the check-in email
- [ ] Manually trigger Workflow 2
- [ ] Verify email is parsed correctly
- [ ] Verify AI response generated
- [ ] Verify Conversation record created with correct status
- [ ] Verify email marked as read

#### Test 3: Send Approved Responses
- [ ] Set a Conversation status to "Approved" (or verify auto-approved)
- [ ] Manually trigger Workflow 3
- [ ] Verify response email sent
- [ ] Verify Status updated to "Sent"
- [ ] Verify Sent At timestamp populated
- [ ] Verify User Summary updated

#### Test 4: Pause/Resume
- [ ] Reply with "I need to pause"
- [ ] Trigger Workflow 2
- [ ] Verify User Status changed to "Paused"
- [ ] Verify confirmation email sent
- [ ] Reply with "resume"
- [ ] Verify User Status changed to "Active"
- [ ] Verify welcome back email sent

#### Test 5: Flagging
- [ ] Reply with "I need legal advice about incorporating"
- [ ] Trigger Workflow 2
- [ ] Verify Conversation flagged
- [ ] Verify flag_reason populated

#### Test 6: Re-engagement
- [ ] Set test user's Last Response Date to 15 days ago
- [ ] Trigger Workflow 4
- [ ] Verify re-engagement email sent
- [ ] Verify Conversation record created (Type: Re-engagement)

#### Test 7: Cleanup
- [ ] Send an email that doesn't get processed
- [ ] Wait for Workflow 5 to run (or trigger manually)
- [ ] Verify email logged as Flagged
- [ ] Verify notification email received

---

## Phase 8: Go Live

### Step 8.1: Activate Workflows

1. Open each workflow
2. Toggle "Active" switch to ON
3. Save

### Step 8.2: Start with Pilot Group

1. Add 5-10 real users to Users table
2. Send them the onboarding email (manually)
3. Process their onboarding responses
4. Begin automated check-ins

### Step 8.3: Daily Review Process

For the first 1-2 weeks, review ALL responses:

1. Check "Pending Review" view daily
2. Edit responses as needed in "Sent Response" field
3. Add significant corrections to Corrected Responses table
4. Update Status to "Approved"
5. Check "Flagged" view and handle manually

### Step 8.4: Gradual Automation

As confidence improves:

1. Let more responses auto-approve (confidence 8+)
2. Reduce review to just flagged items
3. Continue adding to Corrected Responses for learning

---

## Troubleshooting

### Common Issues

**Emails not being received:**
- Check Gmail API is enabled
- Verify OAuth token hasn't expired
- Check n8n execution logs

**Airtable errors:**
- Verify table IDs are correct
- Check field names match exactly (including spaces)
- Ensure API token has correct permissions

**GPT responses not parsing:**
- Check OpenAI API key is valid
- Verify model has GPT-4 access
- Review prompt formatting

**Threading not working:**
- Ensure Thread ID is being stored and passed correctly
- Check Gmail is set to reply to thread, not new message

### Getting Help

- n8n Community: [community.n8n.io](https://community.n8n.io)
- Airtable Support: [support.airtable.com](https://support.airtable.com)
- OpenAI Help: [help.openai.com](https://help.openai.com)

---

## Maintenance

### Weekly
- Review Corrected Responses for patterns
- Check for stuck/failed workflow executions
- Review flagged conversations

### Monthly
- Analyze response quality trends
- Update Model Responses if needed
- Refine Knowledge Chunks based on usage

### As Needed
- Add new Knowledge Chunks when resources updated
- Adjust confidence thresholds based on review workload
- Update prompts to improve response quality
