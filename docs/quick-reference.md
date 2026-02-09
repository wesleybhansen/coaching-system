# Quick Reference Card

Handy reference for daily operations.

---

## Workflow Schedule

| Workflow | Runs | Purpose |
|----------|------|---------|
| 1. Check-in Scheduler | Tue & Fri 9am | Send check-in emails |
| 2. Response Processor | Daily 8am & 6pm | Process incoming emails |
| 3. Send Approved | Daily 9am & 7pm | Send approved responses |
| 4. Re-engagement | Daily 10am | Nudge silent users |
| 5. Cleanup | Daily 11pm | Catch missed emails |

---

## Confidence Score Actions

| Score | Status | Action Needed |
|-------|--------|---------------|
| 8-10 | Approved | Auto-sends (if no flags) |
| 5-7 | Pending Review | Review before sending |
| 1-4 | Flagged | Manual attention needed |

---

## User Status Flow

```
Active → (10 days no response) → Re-engagement sent
       → (7 more days) → Silent

Paused → (user says "resume") → Active

Silent → (user responds) → Active
```

---

## Airtable Views (Daily Check)

1. **Conversations > Pending Review** - Responses to approve
2. **Conversations > Flagged** - Items needing attention
3. **Conversations > Recently Sent** - Monitor what went out

---

## Flag Triggers

Responses are automatically flagged when:
- User asks about legal matters
- Mental health concerns detected
- Strong frustration/distress
- Question outside coaching scope
- Stage transition detected
- User asks to speak directly with Wes
- Situation is unclear/ambiguous

---

## Pause Keywords

User says any of these → Paused:
- "pause"
- "break"
- "stop"
- "unsubscribe"
- "take a break"
- "stepping back"

---

## Resume Keywords

User says any of these → Active:
- "resume"
- "I'm back"
- "start again"
- "ready"

---

## Adding a New User

1. Create record in Users table
2. Fill in: Email, First Name, Status = "Active"
3. Set Stage based on onboarding response
4. Send onboarding email manually (or use template)
5. Update Business Idea and Current Challenge from their response

---

## Making a Correction

When you edit an AI response before sending:

1. Edit the "Sent Response" field in Conversations
2. Change Status to "Approved"
3. If significant edit, also add to Corrected Responses table:
   - Original User Message
   - AI Response (what AI wrote)
   - Corrected Response (what you wrote)
   - Notes (why you changed it)

---

## Common Airtable Formulas

**Users needing check-in:**
```
AND(
  {Status}='Active',
  OR(
    {Last Response Date}='',
    DATETIME_DIFF(TODAY(), {Last Response Date}, 'days') >= 3
  )
)
```

**Silent users (10+ days):**
```
AND(
  {Status}='Active',
  DATETIME_DIFF(TODAY(), {Last Response Date}, 'days') >= 10
)
```

**Approved but not sent:**
```
AND(
  {Status}='Approved',
  {Sent At}=BLANK()
)
```

---

## Cost Tracking

Estimated monthly costs at 50 users:

| Service | Estimate |
|---------|----------|
| OpenAI GPT-4 | $15-40 |
| n8n Cloud | $0-20 |
| Airtable | $0-20 |
| **Total** | **$35-80** |

---

## Emergency Procedures

### To pause ALL emails immediately:
1. Deactivate Workflow 1 (Check-in Scheduler)
2. Deactivate Workflow 3 (Send Approved)

### To process urgent response manually:
1. Find conversation in Airtable
2. Write response in "Sent Response" field
3. Send email manually via Gmail
4. Update Status to "Sent" and Sent At

### To re-process a failed email:
1. Find the email in Gmail
2. Mark as unread
3. Trigger Workflow 2 manually
