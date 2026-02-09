# Implementation Checklist

Print this out and check off each step as you complete it.

---

## Phase 1: Prerequisites
- [ ] Gmail account ready (coachwes@thelaunchpadincubator.com)
- [ ] Credit card for OpenAI billing
- [ ] Coaching content accessible (books, lecture notes)

---

## Phase 2: Airtable Setup

### Create Account & Base
- [ ] Created Airtable account
- [ ] Created base named "Email Coaching System"

### Create Tables
- [ ] Users table (12 fields)
- [ ] Conversations table (17 fields)
- [ ] Knowledge Chunks table (8 fields)
- [ ] Model Responses table (7 fields)
- [ ] Corrected Responses table (7 fields)

### Create Views
- [ ] Conversations > Pending Review
- [ ] Conversations > Flagged
- [ ] Conversations > Ready to Send
- [ ] Conversations > Recently Sent
- [ ] Users > Active Users

### Get Credentials
- [ ] Created API token (starts with "pat")
- [ ] Copied Base ID (starts with "app")
- [ ] Copied all 5 Table IDs (start with "tbl")
- [ ] Saved all credentials somewhere safe

---

## Phase 3: n8n Setup
- [ ] Created n8n account
- [ ] Accessed n8n workspace

---

## Phase 4: Connect Services

### Gmail
- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Created OAuth credentials
- [ ] Added OAuth callback URL
- [ ] Connected Gmail in n8n

### Airtable
- [ ] Added Airtable Token credential in n8n

### OpenAI
- [ ] Created OpenAI account
- [ ] Generated API key
- [ ] Added billing/payment method
- [ ] Connected OpenAI in n8n

### Environment Variables
- [ ] Added AIRTABLE_BASE_ID
- [ ] Added USERS_TABLE_ID
- [ ] Added CONVERSATIONS_TABLE_ID
- [ ] Added KNOWLEDGE_TABLE_ID
- [ ] Added MODEL_RESPONSES_TABLE_ID
- [ ] Added CORRECTED_TABLE_ID

---

## Phase 5: Import Workflows

### Import Files
- [ ] Imported 1-check-in-scheduler.json
- [ ] Imported 2-response-processor.json
- [ ] Imported 3-send-approved-responses.json
- [ ] Imported 4-re-engagement.json
- [ ] Imported 5-cleanup.json

### Connect Credentials
- [ ] Connected credentials in Workflow 1
- [ ] Connected credentials in Workflow 2
- [ ] Connected credentials in Workflow 3
- [ ] Connected credentials in Workflow 4
- [ ] Connected credentials in Workflow 5

### Update Email Addresses
- [ ] Updated email in Workflow 5 notification node

---

## Phase 6: Add Content

### Model Responses
- [ ] Imported model-responses.csv
- [ ] Reviewed and customized responses to match my voice

### Knowledge Chunks
- [ ] Added 5+ chunks from Launch System
- [ ] Added 5+ chunks from Ideas That Spread
- [ ] Added 5+ chunks from lectures
- [ ] Total: 20+ knowledge chunks minimum

### Test User
- [ ] Created test user with my personal email

---

## Phase 7: Testing

### Test 1: Check-in Email
- [ ] Triggered Workflow 1
- [ ] Received check-in email
- [ ] Conversation record created in Airtable

### Test 2: Response Processing
- [ ] Replied to check-in email
- [ ] Triggered Workflow 2
- [ ] AI response generated
- [ ] Confidence score assigned

### Test 3: Sending Responses
- [ ] Set status to Approved
- [ ] Triggered Workflow 3
- [ ] Response email received
- [ ] Status updated to Sent

### Test 4: Pause/Resume
- [ ] Tested pause keyword
- [ ] User status changed to Paused
- [ ] Tested resume keyword
- [ ] User status changed to Active

### Test 5: Flagging
- [ ] Sent message with sensitive content
- [ ] Conversation was flagged
- [ ] Reason populated

---

## Phase 8: Launch

### Pilot Setup
- [ ] Selected 5-10 pilot users
- [ ] Added pilot users to Airtable
- [ ] Sent onboarding emails
- [ ] Updated user records with responses

### Activate
- [ ] Activated Workflow 1
- [ ] Activated Workflow 2
- [ ] Activated Workflow 3
- [ ] Activated Workflow 4
- [ ] Activated Workflow 5

---

## Phase 9: First Week Monitoring

### Daily Checks
- [ ] Day 1: Reviewed Pending Review, checked Flagged
- [ ] Day 2: Reviewed Pending Review, checked Flagged
- [ ] Day 3: Reviewed Pending Review, checked Flagged
- [ ] Day 4: Reviewed Pending Review, checked Flagged
- [ ] Day 5: Reviewed Pending Review, checked Flagged
- [ ] Day 6: Reviewed Pending Review, checked Flagged
- [ ] Day 7: Reviewed Pending Review, checked Flagged

### Corrections Made
- [ ] Added corrections to Corrected Responses table
- [ ] Noted patterns in AI mistakes

---

## Launch Complete!

Date completed: _______________

Notes:
_________________________________
_________________________________
_________________________________
_________________________________
