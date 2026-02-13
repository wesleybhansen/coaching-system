# Admin Onboarding Guide: Adding New Users to the Coaching System

## Overview

This guide walks you through everything you need to do when onboarding a new member into the Launchpad Incubator Coaching System. Whether you are adding a single user before their first day or onboarding an entire cohort at once, this guide covers every step, every option, and every scenario you might encounter.

The onboarding process is designed to be smooth for both you and your members. A well-onboarded user receives better coaching from day one, because the AI has the context it needs to give relevant, personalized advice right out of the gate.

### What This Guide Covers

- How to add a new user manually through the dashboard (the recommended method for most situations)
- How the automatic email-based onboarding flow works when someone emails in cold
- What happens behind the scenes after a user is added
- Post-onboarding verification steps
- Batch onboarding for cohorts and groups
- Troubleshooting common onboarding issues
- Managing the full user lifecycle from onboarding through active coaching

### What the System Needs to Start Coaching Someone

When a new person joins the coaching program, the system needs four things to start coaching them effectively:

1. **Email address** -- This is the primary identifier. The system matches incoming emails by address, so it must be exact. If the address is wrong by even one character, their emails will not be matched to their profile.
2. **First name** -- Used in all outgoing emails to keep things personal and warm. Every check-in and coaching response starts with their name.
3. **Stage** -- Where they are in their entrepreneurial journey (Ideation, Early Validation, Late Validation, or Growth). This determines the coaching style, the resources the AI draws from, and the type of advice it gives. Getting this right matters.
4. **Business idea** -- A brief description of what they are working on. This gives the AI critical context for generating relevant, specific coaching responses rather than generic advice.

Once these are in the system, the user will start receiving check-in emails on their scheduled days. When they reply, the AI generates a coaching response tailored to their stage, their business, and their specific situation -- and you review and approve it before it gets sent.

### Two Methods for Onboarding

| Method | Best For | Admin Effort | User Experience |
|--------|----------|-------------|-----------------|
| **Manual Dashboard Entry** | Controlled enrollment, cohort launches, users you have already spoken with | Low -- you enter their info once | Clean -- they receive their first check-in on schedule |
| **Automatic Email-Based** | Cold inbound, self-service signups, people who email before you add them | Medium -- you review 3 onboarding drafts | Conversational -- the system guides them through setup over 2-3 emails |

Most of the time, you will use manual onboarding. It is faster, gives you more control, and results in a cleaner first impression.

---

## Method 1: Manual Onboarding via Dashboard (Recommended)

Use this method when you already know who the person is, you have their email, and you want to set them up cleanly before they receive their first check-in. This is the most common approach and the one we recommend for most situations.

### Step 1: Add the User

1. Open the Streamlit dashboard. If you are running on Streamlit Cloud, go to your deployed URL (for example, `https://coach-wes.streamlit.app`). If running locally, go to `http://localhost:8501`. Enter the dashboard password if prompted.

2. In the left sidebar, click **Users**. This opens the user management page where you can see all existing users and add new ones.

3. At the top of the page, click the **"Add new user"** expander to reveal the new user form.

4. Fill in the following fields:

   - **Email**: Enter their email address exactly as they will send emails from. This is the single most important field -- the system matches incoming messages to users by email address, and it must be exact. Double-check for typos. Be aware that Gmail aliases (e.g., `name+tag@gmail.com`) are treated as different addresses. Use the address they will actually email from.

   - **First name**: Enter their first name. This appears in every coaching email the system sends them (e.g., "Hey Sarah," at the start of check-ins and coaching responses). Use whatever they go by -- if they prefer a nickname, use that.

   - **Stage**: Select their current entrepreneurial stage from the dropdown. If you are unsure, start with the stage that best fits based on your intake conversation. You can always change it later:

     - **Ideation** -- Still exploring ideas. Has not talked to potential customers yet. May not have a specific business concept. The AI will focus on getting them out of their head and into conversations with real people.
     - **Early Validation** -- Has an idea and is talking to potential customers. Testing whether people actually want this. Has not made money yet (or very little). The AI will push them toward structured customer interviews and their first paying customer.
     - **Late Validation** -- Has some traction. May have paying customers. Refining the business model, working on retention and unit economics. The AI will challenge them to go deep rather than wide.
     - **Growth** -- Business is working. Focused on scaling, hiring, expanding to new channels or markets. The AI will help them think like a CEO, not just a busy founder.

   - **Business idea**: Write a brief description of their business concept in 2-3 sentences. This gives the AI critical context for generating relevant coaching responses. For example: "Building a SaaS tool that helps freelance designers manage client feedback. Currently interviewing designers to understand their workflow pain points." If the user is in pure Ideation and does not have an idea yet, leave this blank or write "still exploring" -- the AI will know to focus on idea discovery and customer conversations.

   - **Check-in days**: Select up to 3 days per week when the user should receive check-in emails. Leave this empty to use the system default (currently Tuesday and Friday). Common configurations:
     - **Tue / Fri** -- 2x per week. The system default. A great starting point for most users.
     - **Mon / Wed / Fri** -- 3x per week. For highly engaged users who want more frequent accountability.
     - **Mon / Thu** -- 2x per week, spread further apart. Good for users who need more time between check-ins.
     - **Tue / Thu** -- 2x per week, close together. For users who prefer mid-week focus.

     Start with 2x per week unless the user specifically requests more. You can always increase it later.

5. Click **"Add User"**.

6. The system will:
   - Create the user record in the database
   - Set their status to **Active**
   - Set their stage, business idea, and check-in days as you entered them
   - The user is immediately eligible for check-ins on their scheduled days

7. You should see a green success message: "User [email] added!" The page will refresh and the new user will appear in the user list below.

### Step 2: Initiate Their First Check-In

The new user is now Active and will automatically receive a check-in email on their next scheduled day. However, you have options for how to handle their first contact depending on timing and preference:

**Option A: Wait for the next scheduled check-in (simplest)**

Do nothing. The Check In workflow runs daily at 9am ET. On the user's next scheduled check-in day, they will automatically receive a personalized check-in email. This is the cleanest approach if the user knows coaching is starting and roughly when to expect the first email.

**Option B: Trigger an immediate check-in**

If you want the user to receive their first email right away:

1. Go to **Run Workflows** in the left sidebar.
2. Click the **"Check In"** button under Manual Triggers.
3. The system will check which users are scheduled for today and send check-ins. If today is one of the new user's check-in days (or if they have no custom schedule and today is a system default day), they will receive an email.

Note: If today is not one of their scheduled days, the manual trigger will not send them a check-in. To send an immediate welcome regardless of the day, use Option C.

**Option C: Send a personal welcome email**

For a more hands-on approach, especially for premium, early, or high-touch users:

1. Open the coaching Gmail account directly in a browser.
2. Compose a new email to the user.
3. Write a brief personal welcome. You can reference your intake conversation, acknowledge their specific business idea, or simply say you are excited to get started.
4. Send it.

When the user replies, the system will automatically pick up their email during the next Process Emails cycle (runs hourly from 8am-9pm ET) and generate an AI coaching response for your review. The conversation thread is established, and the coaching relationship is underway.

### Step 3: Monitor Their First Response

Once the user replies to their first check-in or welcome email, here is what happens automatically behind the scenes:

1. **Process Emails workflow runs** (hourly during business hours, or you can trigger it manually from Run Workflows). It connects to Gmail and fetches the user's unread reply.

2. **The system parses their email** using an intelligent two-tier approach: first a deterministic parser strips out signatures, quoted text, and boilerplate to extract just their new message content. If that produces a messy result, GPT-4o-mini steps in as an intelligent fallback parser.

3. **The AI generates a coaching response** using GPT-4o, drawing from a rich set of context:
   - The user's profile (name, stage, business idea)
   - Their message content
   - Model coaching responses tailored to their stage
   - Any previous corrections you have made to AI responses for similar situations
   - Relevant content from your knowledge base (lectures, book chapters, frameworks) retrieved through RAG

4. **The AI evaluates its own response** for quality, scoring it on a 1-10 confidence scale and checking for safety flags (legal questions, mental health concerns, out-of-scope topics, URLs in the response, etc.).

5. **The response is routed** based on the confidence score and flag status:
   - **Auto-Approved** -- If the confidence score meets or exceeds the auto-approve threshold AND there are no flags. (With the default threshold of 10, nothing auto-approves initially -- everything goes to review.)
   - **Pending Review** -- The standard path. You review and approve before it sends.
   - **Flagged** -- If the AI detected something that needs special attention (legal, mental health, ambiguous, etc.).

6. **Check the Pending Review page** within a few hours of the user replying. You will see the conversation with:
   - The user's parsed message
   - The AI's draft response (in an editable text area)
   - A confidence score (1-10)
   - An expandable user context section showing their stage, business idea, and summary

7. **Review the AI's draft response.** Read it carefully. For the first several exchanges with any new user, be especially thorough -- the AI is still learning their context and communication style. Ask yourself:
   - Does it address what the user actually said?
   - Is the advice relevant to their stage?
   - Does it sound like your coaching voice (direct, warm, focused)?
   - Is it the right length (1-3 paragraphs, not a novel)?
   - Does it end with a good question that pushes them forward?

8. **Edit if needed**, then click **"Approve"**. If you made edits, the system automatically saves your correction -- this is how the AI learns your voice and improves over time. If the response is completely off, click **"Reject"** and either draft a manual response from Gmail or wait for the user's next message.

9. **The approved response will be sent** at the next send window. The Send Approved workflow runs at 9am, 1pm, and 7pm ET. You can also trigger it manually from Run Workflows to send sooner.

### Step 4: Configure Their Profile (Optional Refinements)

After the first exchange or two, you may want to go back and refine the user's profile based on what you have learned from their actual messages. Better profile data means better AI responses.

1. Go to **Users** in the sidebar.
2. Find the user and click their name/expander to open their profile.
3. Update any of the following:

   - **Business idea** -- Now that you have heard from them directly, you can write a more accurate and detailed description. The more specific this is, the better the AI's responses will be. For example, "Building a scheduling tool for freelance designers" is good; "Building a SaaS tool that helps freelance designers collect structured feedback from clients on design revisions, replacing the current messy email chain process" is better.
   - **Stage** -- If their first message reveals they are at a different stage than you initially selected, update it here. Stage determines the entire coaching approach.
   - **Check-in days** -- If the user requested a different schedule, change it.
   - **Current challenge** -- If they mentioned a specific challenge, enter it here. The AI uses this for context when generating responses.
   - **Notes** -- Add any internal notes visible only to you (e.g., "Referred by John," "Premium member," "Has a co-founder named Alex," "Prefers very direct feedback").

4. Click **"Save Changes"**.

These updates take effect immediately. The next time the AI generates a response for this user, it will use the updated profile information.

---

## Method 2: Automatic Email-Based Onboarding (Self-Service)

Use this method when someone emails the coaching address before you have added them to the system. This is the "cold inbound" path -- the system handles the conversational flow automatically, but you review and approve every message before it gets sent. Nothing goes out without your approval.

### How It Works

The email-based onboarding is a 3-step conversational flow that gathers the information the system needs to start coaching effectively.

**Step 1: Initial contact**

When the system receives an email from an address not in the database:
- A new user record is created with status **"Onboarding"** and `onboarding_step` set to 1
- The user's first name is extracted from their email "From" field (if available)
- The system generates a friendly welcome/intake email draft
- This draft appears on the **Pending Review** page as an "Onboarding" type conversation

The welcome email template asks the new user to reply with:
1. Where they are at right now (Ideation, Early Validation, Late Validation, or Growth)
2. Their biggest challenge or question
3. Their current business idea (if they have one)

**Step 2: User replies with their info**

When the user replies to the welcome email:
- The system parses their reply and extracts what it can
- `onboarding_step` advances to 2
- A follow-up draft is generated asking specifically for their biggest challenge (in case they did not cover it in their first reply)
- This draft appears on Pending Review for your approval

**Step 3: User replies with their challenge**

When the user replies again:
- The system extracts their challenge and saves it to the `current_challenge` field
- The user's status changes from "Onboarding" to **"Active"**
- `onboarding_step` advances to 3
- A final welcome/first-nudge draft is generated, confirming they are set up and giving them their first coaching prompt
- This draft appears on Pending Review for your approval

After you approve the final draft and it sends, the user is fully onboarded. Regular check-ins will begin on their scheduled days (system default Tuesday and Friday, since no custom days were set during email onboarding).

### Admin Steps for Email-Based Onboarding

Here is exactly what you do at each stage. The user drives the timing -- you just review and approve.

1. **Someone emails the coaching address for the first time.** You do not need to do anything yet. Wait for the system to process the email.

2. **Wait for Process Emails to run.** This happens automatically every hour from 8am-9pm ET. If you want it faster, go to **Run Workflows** and click **"Process Emails"**.

3. **Go to Pending Review.** You will see a new conversation marked as "Onboarding" type. The user will be listed with whatever name the system extracted from their email. The draft will be the standard welcome/intake email.

4. **Review the welcome email draft.** Read through it. The template is well-tested and generally does not need changes. If you know the person, you may want to add a personal touch (e.g., "Great meeting you at the workshop last week!"). Edit the text area directly if you want to customize.

5. **Click "Approve".**

6. **Wait for Send Approved to run.** Sends at 9am, 1pm, and 7pm ET, or trigger manually from Run Workflows. The welcome email will be sent to the new user.

7. **User replies with their stage and business idea.** They reply to your welcome email with the information you asked for.

8. **Process Emails runs and picks up their reply.** A new Pending Review item appears -- this is the follow-up draft asking for their challenge.

9. **Go to Pending Review.** Review the follow-up draft. At this point, you should also go to the **Users** page and update the user's profile:
   - Set their **Stage** based on what they told you
   - Fill in their **Business idea** based on their description
   - Optionally set their **Check-in days** if you have a preference

10. **Approve the follow-up draft.**

11. **Wait for Send Approved to run.** The follow-up email sends.

12. **User replies with their challenge.**

13. **Process Emails runs.** The system automatically:
    - Sets the user's `current_challenge` field
    - Changes their status from "Onboarding" to **"Active"**
    - Advances `onboarding_step` to 3
    - Generates the final welcome/activation draft

14. **Go to Pending Review.** Review the activation message. This is their first "real" coaching nudge. This is a good time to verify on the Users page that all their profile fields are filled in.

15. **Approve the activation message.**

16. **Onboarding is complete.** The user is now Active. Regular check-ins will begin on their scheduled days. All future exchanges go through the standard AI coaching pipeline.

### Important Notes on Email-Based Onboarding

- The entire email-based flow goes through Pending Review. **Nothing sends to the user without your approval.** You are always in control.
- If the user gives you all the information in their first email (stage, idea, and challenge), you can update their profile on the Users page immediately rather than waiting for the multi-step flow.
- If a user emails in and you would rather onboard them manually, you can change their status from "Onboarding" to "Active" on the Users page, fill in their profile, and reject the onboarding draft. Then trigger a check-in or send a personal welcome email.

---

## Post-Onboarding Checklist

After a user is onboarded (by either method), verify the following on the **Users** page:

- [ ] User appears in the user list with status **"Active"**
- [ ] **Stage** is set correctly (Ideation, Early Validation, Late Validation, or Growth)
- [ ] **Business idea** field is populated with a description of their concept (unless they are in pure Ideation with no idea yet)
- [ ] **Check-in days** are configured (or left empty to use the system default of Tuesday and Friday)
- [ ] First check-in or welcome email has been sent (check the **Conversations** page) or is scheduled for their next check-in day
- [ ] If email-based onboarding: user has replied to the welcome email and their info has been captured

Additionally, after their first 1-2 exchanges:

- [ ] Review the AI's responses carefully on Pending Review -- the first several responses for any new user need close attention as the AI builds context
- [ ] Update the **Business idea** and **Current challenge** fields if you got better information from their replies
- [ ] Confirm their **Stage** still looks correct based on what they have shared
- [ ] Add any internal **Notes** (referral source, special context, communication preferences)

---

## Batch Onboarding (Multiple Users)

When adding a group of users at once -- a new cohort, workshop attendees, intake from a waitlist -- a little planning goes a long way. The key consideration is spreading out check-in days so you do not get flooded with reviews all on the same day.

### Preparation

1. Collect each user's email, first name, stage, and business idea before you start. A simple spreadsheet works well.
2. Decide on check-in day assignments. Stagger users across different days to keep your review workload manageable.

### Recommended Day Staggering for Cohorts

| Cohort Size | Suggested Approach |
|-------------|-------------------|
| 1-5 users | All on the system default (Tue/Fri) is fine |
| 6-15 users | Split evenly: half on Tue/Thu, half on Mon/Fri |
| 16-30 users | Split into thirds: Mon/Thu, Tue/Fri, Wed/Sat |
| 30+ users | Spread across all weekdays, max 10 users per day |

The goal is to have a manageable number of Pending Review items on any given day. If 20 users all check in on Tuesday and all reply by Wednesday, you will have 20 AI responses to review at once. Staggering prevents that pile-up.

### Adding Users

1. Go to the **Users** page.
2. Add each user one at a time using the "Add new user" form. For each user:
   - Enter their email, name, stage, and business idea
   - Set their check-in days according to your staggering plan
   - Click "Add User"
3. After adding all users, scroll through the user list to verify everyone is there and set to "Active."

### First Week with a New Cohort

Here is what to expect and how to manage it:

- **Day 1-2**: Users receive their first check-ins on their scheduled days. Some will reply quickly, others will take a day or two. This is normal.
- **Day 2-4**: Replies start coming in. **Check the Pending Review page at least twice daily** (morning and afternoon). The AI responses for first-time exchanges need more attention than responses for established users -- the AI has limited context and is still learning each user's situation.
- **Day 5-7**: Second round of check-ins goes out. By now you should have a feel for each user's communication style and how well the AI is handling their context.
- **Ongoing**: After the first week, you can settle into a routine of checking Pending Review once or twice a day.

### Tips for Cohort Onboarding

- Start all new users at 2x per week. Increase to 3x only if the user requests it or if they are highly engaged and responding to every check-in.
- If you have a large cohort, keep the auto-approve threshold at 10 (review everything) for the first two weeks. Once you are confident the AI is handling the cohort well, consider lowering to 8.
- Keep notes on each user during the first week. The Notes field on the Users page is useful for things like "Tends to write very long replies" or "Needs more encouragement than challenge" or "Co-founder is also in the program."

---

## Troubleshooting New User Issues

### User's emails are not being picked up

**Symptoms**: The user says they replied, but nothing appears on Pending Review.

**Causes and fixes**:
- **Email address mismatch**: Go to the Users page and verify the email address character by character. Check for typos, extra spaces, or Gmail aliases. The system uses case-insensitive matching, but the address must otherwise be exact. If the user sends from `jane.doe@gmail.com` but you entered `janedoe@gmail.com`, the system will not match them.
- **Email not yet processed**: Process Emails runs hourly. If the user just replied, it may not have been picked up yet. Go to Run Workflows and click "Process Emails" to trigger it manually.
- **Email marked as read**: If something else (another device, Gmail filter, another app) marked the email as read before the system could fetch it, it will be skipped. Check the coaching Gmail inbox directly -- if the email shows as read but was never processed, mark it as unread and re-run Process Emails.
- **Email filtered to spam or a folder**: Check Gmail's Spam folder and any filters or rules that might route incoming emails away from the Inbox.

### User stuck in "Onboarding" status

**Symptoms**: The user was created via email-based onboarding but their status never changed to Active.

**Causes and fixes**:
- **Pending onboarding messages not yet approved**: Go to Pending Review and look for Onboarding-type conversations. There may be a draft waiting for your approval that is blocking the flow from progressing.
- **User never replied to the welcome email**: Check the Conversations page filtered by this user. If the welcome email was sent but they never replied, send a follow-up from Gmail after 3-5 days.
- **Manual override**: If you have the user's information from another source (intake form, phone call, application), go to the Users page, update their stage and business idea, change their status to "Active," and reject any pending onboarding drafts. This skips the email-based flow entirely and gets them straight into regular coaching.

### Wrong stage assigned

**Symptoms**: The user is in "Ideation" but they clearly have paying customers, or vice versa.

**Fix**: Go to the Users page, find the user, change their **Stage** dropdown, and click "Save Changes." The next AI response will use the correct stage-specific coaching prompts, resources, and approach. No need to regenerate existing responses -- the change takes effect going forward.

### User wants different check-in days

**Symptoms**: A user asks to receive check-ins on different days.

**Fix**: Go to the Users page, find the user, update the **Check-in days** multiselect, and click "Save Changes." Changes take effect on the next Check In workflow run (daily at 9am ET). The user will start receiving check-ins on their new schedule immediately.

### User never replied to the welcome email

**Symptoms**: You sent the first check-in or welcome email 3+ days ago and the user has not responded.

**Fix**:
1. Wait 3-5 days from the first email. Some people are busy and will respond eventually.
2. If no response after 5 days, send a brief, personal follow-up from the coaching Gmail. Something like: "Hey [Name], just checking in -- did you get my first email? Reply whenever you're ready and we'll get started."
3. If still no response after 10+ days, the re-engagement workflow will automatically send a nudge. After 17+ days of silence, the user will be marked as "Silent."
4. You can also change their status to "Paused" on the Users page if you want to stop check-ins until they are ready.

### Duplicate user created

**Symptoms**: The same person appears twice in the user list, usually because they emailed from a different address than what you entered.

**Fix**:
1. Identify which record has the conversation history (check the Conversations page for each).
2. On the record you want to keep, make sure the email address matches the address they actually send from.
3. On the duplicate record, change the status to "Paused" so it does not receive check-ins. (You cannot delete users from the dashboard, but pausing them effectively removes them from all workflows.)
4. If conversations are split across both records, note the key context in the "Notes" field of the record you are keeping.

### AI response quality is poor for a new user

**Symptoms**: The AI's draft responses are generic, off-topic, or miss the user's actual question.

**Fix**:
1. Check the user's profile on the Users page. Is the Business idea field populated? Is the Stage correct? The AI relies heavily on these two fields.
2. Edit the AI's response on the Pending Review page before approving. Every edit you make is saved as a correction and helps the AI improve -- not just for this user, but for all users in similar situations.
3. After the first 5-10 exchanges, the AI will have more conversation history and a richer journey summary to draw from. Quality improves significantly with more context.
4. If a response is really off-base, click "Reject" and write a manual response from the coaching Gmail. The user does not need to know the AI was involved -- the experience is seamless.

---

## Managing User Lifecycle

Once a user is onboarded, they move through various statuses throughout their time in the program. The system handles most transitions automatically, but understanding the lifecycle helps you manage your program effectively.

### Status Reference

| Status | Meaning | Gets Check-ins? | How They Enter | How They Exit |
|--------|---------|-----------------|----------------|---------------|
| **Onboarding** | Going through the welcome flow | No | Email-based auto-creation | Complete onboarding steps or manual activation by admin |
| **Active** | Regular coaching in progress | Yes, on their scheduled days | Completing onboarding, or manual creation via dashboard | User pauses, goes silent, or admin changes status |
| **Paused** | User requested a break | No | User replies with "pause," "break," "stop," or similar | User replies with "resume," "I'm back," or similar |
| **Silent** | No response for 17+ days | No (re-engagement nudge already sent) | Automatic -- re-engagement workflow marks them after 17 days of silence | User replies to any email (auto-detected) or admin manually reactivates |

### Automatic Transitions

These happen without admin intervention -- the system detects intent from the user's messages:

- **Active to Silent**: If a user does not reply for 10 days, the re-engagement workflow sends a friendly nudge. If they still do not reply after 17 total days, they are automatically marked as Silent.
- **Active to Paused**: If a user replies with "pause," "break," "stop," "unsubscribe," "take a break," "stepping back," or similar language, the system detects the pause intent, sets them to Paused, and drafts a pause confirmation for your review.
- **Paused/Silent to Active**: If a paused or silent user replies with "resume," "I'm back," "start again," "ready," or similar, the system detects the resume intent, sets them back to Active, and drafts a welcome-back message for your review.

### Manual Transitions

You can change any user's status on the Users page at any time:

- Set to **Active** to start (or restart) check-ins
- Set to **Paused** to temporarily stop check-ins without removing the user
- Set to **Onboarding** if you need to re-trigger the onboarding flow (rare)

---

## Best Practices

### For the First 5-10 Exchanges Per User

- **Review every response carefully.** The AI has limited context during the early exchanges. It gets significantly better after it has a few conversations to draw from and a growing journey summary.
- **Edit generously.** Every correction you make teaches the AI. Do not just approve mediocre responses to save time -- take 60 seconds to make them better. The corrections are stored and used to improve future responses for all users, not just this one.
- **Update the user profile after each exchange.** If you learn something new about their business, stage, or challenge, update it on the Users page. Better profile data means better AI responses.

### Ongoing Review Habits

- **Check Pending Review at least once per day**, ideally twice (morning and afternoon). Responses sit in Pending Review until you approve them, and users expect a reply within roughly 24 hours.
- **Check the Flagged page daily.** Flagged conversations may involve sensitive topics (legal, mental health, personal crises) that need your personal attention rather than an AI-drafted response.
- **Set realistic expectations with users.** Let them know responses typically come within 24 hours, not instantly. Encourage them to reply in the same email thread to maintain conversation continuity.

### Response Quality

- If a user has a complex situation (pivoting their business, dealing with a co-founder conflict, facing a major decision), consider drafting a manual response from Gmail rather than approving an AI draft. The AI handles routine coaching well but may miss nuance in high-stakes situations.
- The AI will never use bullet points, never say "I'm proud of you," and will always end with a question. If you see it breaking these rules, edit the response -- the correction will help prevent it in the future.
- Watch for resource references. When the AI mentions a specific lecture, chapter, or framework from your program content, make sure the reference is relevant to what the user is actually dealing with.

### System Monitoring

- **Run Workflows page**: Check the System Status section periodically. Green checkmarks next to Database, Gmail, Python, and Migration v2 mean everything is healthy.
- **Workflow Run History**: At the bottom of Run Workflows, review recent runs. If you see failed runs, investigate the error messages.
- **Analytics page**: As your user base grows, use the Analytics dashboard to track confidence calibration, response quality trends, correction patterns, and user satisfaction.

---

## Quick Reference: Onboarding Checklist

For each new user, complete the following:

```
[ ] 1. Add user on Users page (email, name, stage, business idea, check-in days)
[ ] 2. Verify status is "Active"
[ ] 3. First check-in sent or scheduled
[ ] 4. User replied to first email
[ ] 5. First AI response reviewed and approved on Pending Review
[ ] 6. Business idea and stage verified/updated after first exchange
[ ] 7. Check-in days confirmed (or adjusted based on user preference)
[ ] 8. Notes added for any special context
```

---

## Dashboard Navigation Reference

Here is where everything lives in the sidebar, for quick reference during onboarding:

| Page | What You Use It For During Onboarding |
|------|--------------------------------------|
| **Home** | Quick stats: see pending review count, active users, recent workflow health |
| **Pending Review** | Review and approve AI responses (including onboarding drafts) |
| **Flagged** | Check for flagged conversations that need your personal attention |
| **Conversations** | Browse a user's full conversation history to understand their journey |
| **Users** | Add new users, edit profiles, change status, configure check-in days |
| **Corrections** | View corrections you have made (these teach the AI over time) |
| **Settings** | Adjust auto-approve threshold, default check-in days, send hours |
| **Run Workflows** | Manually trigger Process Emails, Send Approved, Check In, etc. |
| **Analytics** | Monitor system performance, confidence calibration, and engagement trends |

---

## Workflow Schedule Reference

These workflows run automatically via GitHub Actions. All times are Eastern.

| Workflow | Schedule | What It Does |
|----------|----------|-------------|
| **Process Emails** | Every hour, 8am-9pm ET | Fetches unread emails, generates AI responses, routes to review |
| **Send Approved** | 9am, 1pm, 7pm ET | Sends all approved responses that have not been sent yet |
| **Check In** | Daily at 9am ET | Sends check-in emails to active users scheduled for today |
| **Re-engagement** | Daily at 10am ET | Nudges silent users (10+ days), marks very silent users (17+ days) |
| **Cleanup** | Daily at 11pm ET | Catches any unread emails older than 24 hours, flags for review |

All of these can also be triggered manually from the **Run Workflows** page in the dashboard.
