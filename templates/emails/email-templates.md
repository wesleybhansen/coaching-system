# Email Templates

All email templates used by the coaching system.

---

## Check-in Email (Standardized)

**Subject:** Quick check-in

```
Hey {first_name},

Quick check-in. Reply with:

1. **Accomplished** - What did you get done since we last talked?
2. **Current Focus** - What are you working on now?
3. **Next Step** - What's the single most important thing you need to do next?
4. **Approach** - How are you going about it?

Keep it brief - a sentence or two for each.

Wes
```

**Notes:**
- Same template for all stages
- Structured format makes parsing easier
- Brief responses encouraged to keep exchanges quick

---

## Onboarding Email

**Subject:** Let's get you moving forward

```
Hey {first_name},

Welcome to coaching. Here's how this works:

A couple times a week, I'll check in with a few quick questions about what you're working on. You reply (should take about 5 minutes), and I'll send back focused feedback - usually within a day or so.

That's it. Short exchanges, consistent momentum.

Before we start, I need some context from you. Reply to this email with:

1. **Where you're at right now**:
   - Still figuring out the idea (Ideation)
   - Testing if people want this (Early Validation)
   - Have some traction, refining the model (Late Validation)
   - Growing and scaling (Growth)
2. **Your biggest challenge or question right now**
3. **If you have one, your current business idea** (2-3 sentences is fine; if you don't yet have an idea, this is where we'll get started)

Once I hear back, we'll get started.

Talk soon,
Wes
```

---

## Re-engagement Email

**Subject:** Re: Coaching (maintains thread)

```
Hey {first_name},

Haven't heard from you in a bit. Everything okay?

When you're ready, just reply with a quick update on what you're working on.

Wes
```

---

## Pause Confirmation

**Subject:** Re: Coaching (maintains thread)

```
No problem - I'll pause check-ins for now. Just reply 'resume' whenever you're ready to pick back up.

Wes
```

---

## Resume Confirmation

**Subject:** Re: Coaching (maintains thread)

```
Welcome back! I'll resume the regular check-ins. You'll hear from me soon.

Wes
```

---

## Coaching Response Sign-off

All AI-generated coaching responses should end with:

```
{response_content}

Wes
```

**Notes:**
- Simple sign-off
- No "Best," or "Thanks," - too formal
- First name only - casual and consistent

---

## Notification Email (Internal)

**Subject:** Coaching System: {count} Missed Emails Flagged

```
The cleanup workflow found {count} email(s) that weren't processed by the regular workflow.

They've been logged in Airtable as 'Flagged' for your review.

Summary:
{summary}

Check the 'Flagged' view in the Conversations table.
```

---

## Email Threading

All reply emails use the subject line "Re: Coaching" and include the Gmail `threadId` to maintain threading. This keeps all exchanges with a user in one conversation.

### Why Threading Matters
1. **User experience:** User sees full conversation history
2. **Context:** Easy to scroll back and see previous exchanges
3. **Organization:** One thread per user in Gmail

### How It Works
1. First email to user creates a new thread
2. Store `threadId` in Users table
3. All subsequent emails (check-ins, responses) reply to that thread
4. User replies automatically maintain the thread

---

## Customization Notes

### Changing Check-in Frequency
The check-in scheduler runs Tuesday and Friday at 9am. To change:
1. Edit the Schedule Trigger in Workflow 1
2. Adjust the 3-day filter formula in the Airtable query

### Adjusting Tone
To make emails more/less formal:
1. Edit templates in this file
2. Update corresponding content in n8n workflow nodes

### Adding Email Variants
For A/B testing different check-in formats:
1. Create variants in this file
2. Add random selection logic in the Check-in Scheduler workflow
3. Track which variant was sent in Conversations table
