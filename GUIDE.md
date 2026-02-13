# Coaching System — Operator's Guide

This guide covers how to use the coaching system day-to-day, week-to-week, and how to handle specific situations as they come up.

---

## Your Daily Routine (~15-30 minutes)

### 1. Open the dashboard

Go to your Streamlit dashboard URL and log in with your password.

The home page shows four numbers at the top:

| Metric | What it means |
|--------|---------------|
| **Pending Review** | Responses waiting for you to approve — this is your main task |
| **Flagged** | Responses the AI flagged for your attention (sensitive topics, odd situations) |
| **Active Users** | How many users are currently receiving coaching |
| **Total Users** | Everyone in the system, including paused and silent users |

Below that you'll see recent workflow runs. Glance at these to make sure everything shows green checkmarks. A red X means something failed — more on troubleshooting later.

### 2. Review pending responses

Click **Pending Review** in the sidebar. For each conversation you'll see:

- The user's name, their stage, and the AI's confidence score (1-10)
- **Their message** — what the user wrote to you
- **AI Response** — what the AI drafted in your voice

For each one, you have three choices:

**Approve** — The response is good. Click Approve and it will be sent at the next send window (9am, 1pm, or 7pm ET). If the response is close but needs tweaking, edit it directly in the text box first, then click Approve. Your edit is saved automatically and the AI learns from the correction.

**Reject** — The AI got it completely wrong and it's not worth editing. The user's email will stay unread in your inbox — you'll need to handle it yourself outside the system.

**Flag** — Something about this conversation needs more thought. Moves it to the Flagged page where you can come back to it.

**Tip:** Click "View user context" to see the user's business idea, journey summary, and recent exchanges. This helps you evaluate whether the AI's response is on-target.

### 3. Check flagged responses

Click **Flagged** in the sidebar. These are conversations the AI thinks need your personal attention. The flag reason is displayed prominently — common reasons include:

- Legal questions (contracts, incorporation, liability)
- Mental health concerns (burnout, personal crisis)
- User asking to speak with you directly
- Stage transitions (user moving from Ideation to Validation, etc.)
- Missed emails caught by the cleanup workflow

For flagged items, you can:
- Write or rewrite the response and click **Approve**
- **Reject** it if you'll handle it outside the system
- **Move to Pending** if the flag was a false alarm

### 4. You're done

That's it for daily work. The system handles everything else automatically — sending approved responses, sending check-ins, nudging quiet users, and catching missed emails.

---

## Your Weekly Routine (~15 minutes)

### Check user health (Mondays)

Go to the **Users** page and filter by status:

- **Active** — Your engaged users. Scan the list to make sure no one looks stuck.
- **Onboarding** — New users who haven't been moved to Active yet. After they reply to the onboarding email with their stage and business idea, update their profile (see "Setting up a new user" below).
- **Silent** — Users who haven't responded in 17+ days. The system already sent them a nudge. Decide if you want to reach out personally or let them go.
- **Paused** — Users who asked for a break. No action needed unless you want to check in personally.

### Review the Corrections page (every week or two)

The **Corrections** page shows every time you edited an AI response. Scan through recent corrections to spot patterns:

- If the AI keeps getting the same thing wrong, you may want to update the system prompt or add model responses (see "Improving the AI" below).
- If corrections are getting rarer, the system is learning and working well.

---

## How To: Common Tasks

### Setting up a new user

When someone new emails `coachwes@thelaunchpadincubator.com`:

1. The system automatically creates them as "Onboarding" and drafts a welcome email
2. You'll see this on the **Pending Review** page — approve it to send the welcome email
3. When they reply with their stage, business idea, and biggest challenge, you'll see another conversation to review
4. Go to **Users**, find them, and update:
   - **Stage** — Ideation, Early Validation, Late Validation, or Growth (based on what they told you)
   - **Business idea** — A brief description
   - **Status** — Change from "Onboarding" to "Active"
5. They'll now start receiving check-ins on Tuesdays and Fridays

### Adding a user manually

If you want to add someone proactively (they didn't email first):

1. Go to **Users** and expand "Add new user"
2. Fill in their email, name, stage, and business idea
3. Click **Add User** — they'll be created as Active and start receiving check-ins
4. Note: this does NOT send them an onboarding email. If you want to introduce them to the system, email them separately or create a conversation for them in the dashboard.

### Pausing a user

Users can pause themselves by replying "pause" or "take a break" to any email. The system will draft a confirmation for you to approve.

To pause someone manually:
1. Go to **Users**, find them, change Status to "Paused", click Save
2. They won't receive any more check-ins until their status changes back to Active

### Resuming a user

Users can resume by replying "resume" or "I'm back". The system drafts a confirmation for you to approve.

To resume someone manually:
1. Go to **Users**, find them, change Status to "Active", click Save

### Handling a flagged conversation about a sensitive topic

If the AI flags something involving legal questions, mental health, or other sensitive areas:

1. Read the user's message carefully
2. Don't try to address the sensitive topic directly in the coaching response
3. For mental health: acknowledge what they shared, express support, and gently redirect to the coaching focus. If it's serious, suggest they talk to a professional.
4. For legal questions: acknowledge the question, say this is outside your coaching scope, and suggest they consult a lawyer.
5. Write your response in the text box on the Flagged page and click Approve

### Running a workflow manually

If you need to process emails or send responses outside the normal schedule:

1. Go to **Run Workflows** in the sidebar
2. Click the button for the workflow you want:
   - **Process Emails** — Fetch and process any unread emails right now
   - **Send Approved** — Send all approved responses immediately
   - **Check In** — Send check-ins to users who are due
   - **Re-engagement** — Send nudges to silent users
   - **Cleanup** — Catch any missed emails
3. The page will show a spinner while it runs, then confirm success or show an error

### Adjusting the auto-approve threshold

The system starts with everything going through manual review (threshold = 10). As you build confidence in the AI:

1. Go to **Settings**
2. Move the "Global threshold" slider down — try 8 first
3. Now responses with confidence 8+ will auto-approve and send at the next send window without your review
4. You can always go back to the **Conversations** page to review what was auto-sent

**Recommendation:** Keep the threshold at 10 for at least the first 2-3 weeks. Lower to 8 once you've reviewed ~50 responses and feel comfortable with the AI's quality.

---

## How To: Improving the AI Over Time

The AI gets better three ways. All of them happen naturally, but you can be intentional about it.

### 1. Correcting responses (automatic)

Every time you edit a response before approving it, the original and your edited version are saved as a "correction." The AI sees the 10 most recent corrections when generating new responses, so it gradually learns your preferences.

You don't need to do anything extra — just keep editing responses when they need it.

### 2. Adding model responses (occasional)

Model responses are examples of ideal coaching exchanges for each stage. The AI uses these as style guides.

To add one:
1. Think of a common scenario for a particular stage (e.g., an Ideation user who is stuck brainstorming)
2. Write out what a user might say and what your ideal response would be
3. Add it to the `model_responses` table in Supabase (or ask your developer to add it via SQL)

Good times to add model responses:
- When you notice the AI consistently handles a certain type of question poorly
- When you start coaching users in a new stage you haven't had many examples for
- After you've developed a new coaching technique you want the AI to adopt

### 3. Updating the knowledge base (rare)

The AI searches a knowledge base containing your books and lectures when generating responses. To add new content:

1. Go to the OpenAI platform (platform.openai.com)
2. Navigate to Storage → Vector Stores → find the coaching system vector store
3. Upload new files (PDFs, text files, etc.)

Do this when you publish new material or want the AI to reference specific new content.

---

## Understanding the Automated Schedules

Everything runs automatically. Here's what happens and when (all times Eastern):

| Time | What happens |
|------|-------------|
| **Every hour, 8am-9pm** | System checks for new emails, processes them, and generates AI responses |
| **Tue & Fri, 9am** | Check-in emails sent to active users who haven't been contacted in 3+ days |
| **9am, 1pm, 7pm** | Approved responses are sent out |
| **Daily, 10am** | Re-engagement nudges sent to users silent 10+ days; users silent 17+ days marked Silent |
| **Daily, 11pm** | Cleanup catches any emails that slipped through and flags them for review |

You don't need to think about this. If you see a failed workflow on the dashboard home page, check "Troubleshooting" below.

---

## Troubleshooting

### "I see a red X on a workflow run"

Click the home page and look at the error message next to the failed run.

- **IMAP connection error** — Gmail connection issue. Usually temporary. Wait for the next scheduled run. If it persists, check that the Gmail app password hasn't expired.
- **OpenAI API error** — Check your OpenAI account for billing issues or API outages.
- **Supabase error** — Check that the Supabase project is running and not paused (free tier projects pause after inactivity).

### "A user says they never got my response"

1. Go to **Conversations** and search for the user
2. Check the status of their most recent conversation:
   - **Pending Review** — You haven't approved it yet
   - **Approved** — It's been approved but not sent yet. Wait for the next send window, or go to Run Workflows and click "Send Approved"
   - **Sent** — It was sent. Check your Gmail sent folder to confirm. The user might need to check spam.
   - **Rejected** — You rejected it. The user is waiting for a response that isn't coming.

### "The AI's responses feel off"

- Check the **Corrections** page — are your edits being captured?
- Consider adding model responses for the scenarios where the AI struggles
- Review the user's profile on the **Users** page — is their stage, business idea, and summary accurate? The AI uses all of this as context.

### "I want to respond to someone outside the system"

Just reply to them directly from Gmail. The system won't interfere with your manual emails. When they reply back, the system will pick up their response and process it normally.

### "A user got a check-in but they shouldn't have"

Change their status on the **Users** page:
- Set to **Paused** to stop check-ins but keep them in the system
- Set to **Silent** to stop all outreach

---

## Key Things to Know

**Nothing sends without your approval** (unless you lower the auto-approve threshold). The system is designed to be a drafting assistant, not an autonomous agent.

**Check-ins and re-engagement emails are the exception** — they use fixed templates and send automatically. They don't go through AI generation or your review.

**The system never loses an email.** Even if processing fails, the cleanup workflow catches it within 24 hours and flags it for your attention.

**You can always override.** Edit any response, pause any user, reject any draft. The system adapts to your corrections over time.

**When in doubt, flag it.** Moving something to Flagged gives you time to think about it without losing track of it.
