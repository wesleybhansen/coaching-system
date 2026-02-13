# Launchpad Incubator Coaching System -- Operator's Guide

This is the definitive operations manual for the AI-powered email coaching system used by The Launchpad Incubator. It covers every aspect of day-to-day system management: reviewing AI-generated responses, managing users, configuring settings, monitoring health, tuning performance, and handling edge cases.

The system runs on a simple, powerful loop: users email in, the AI drafts a coaching response in Wes's voice, and you review and approve it before it goes out. Everything flows through the Streamlit dashboard. Your corrections teach the AI over time, making it smarter with every edit.

---

## 1. Your Role as Operator

You are the human in the loop. The AI generates coaching responses; you steer them. Your job is to ensure every response that leaves this system is something Wes would actually send -- direct, focused, warm, and grounded in the program's content.

### What You Are Responsible For

- **Quality control** -- Reviewing, editing, and approving every AI-generated response before it reaches a user (until you trust the system enough to auto-approve high-confidence responses).
- **Flagged response triage** -- Handling conversations the AI flagged for safety, sensitivity, or uncertainty. These need your personal judgment, not a rubber stamp.
- **User management** -- Adding new users, updating profiles, adjusting stages, handling pauses and reactivations. The richer the user profile, the better the AI performs.
- **System health** -- Monitoring workflow runs, checking for errors, verifying that emails are flowing in and out smoothly.
- **Continuous improvement** -- Your corrections teach the AI. Every edit you make feeds back into the system's context, making future responses better. You are not just fixing a single email -- you are training the system.

### Cadence

| Frequency | Tasks |
|-----------|-------|
| **Daily** | Review Flagged and Pending Review queues. Check workflow run history for errors. |
| **Weekly** | Review Analytics page for trends. Check correction patterns. Verify all workflows ran over the past 7 days. Monitor satisfaction trends across users. |
| **Monthly** | Evaluate auto-approve threshold using calibration data. Audit user list for accuracy. Review fine-tuning readiness. Update assistant instructions if coaching approach has evolved. Check resource references for relevance. |

### The Core Philosophy

**AI generates, you steer.** The system is designed so that your corrections make the AI smarter over time. When you edit a response before approving it, a correction record is automatically saved. That correction becomes part of the context the AI uses for future responses. You are not just fixing a single email -- you are building a corpus of teaching examples that make the system progressively better.

Start by reviewing everything manually. As the AI proves itself, gradually let high-confidence responses auto-approve. This is a trust-building process, not a switch you flip. The Analytics page gives you the data to make that decision confidently.

---

## 2. Daily Operations

### Morning Routine (Recommended)

This takes approximately 15-30 minutes depending on volume. Do it at the start of your workday, ideally before the 9am ET send window so your approved responses go out in the first batch of the day.

**Step 1: Open the Dashboard**

Navigate to the Streamlit dashboard and log in with the dashboard password. The home page shows four key metrics at a glance: Pending Review count, Flagged count, Active Users, and Total Users. Below that, you will see the most recent workflow runs from the last 24 hours.

Scan the home page quickly. If Pending Review and Flagged are both at zero, your queue is clear. If you see any failed workflow runs (marked with a red X), investigate those first -- they may indicate a credential issue, API outage, or database problem.

**Step 2: Go to Flagged First**

Navigate to the **Flagged** page in the sidebar. These are conversations the AI determined need human judgment before proceeding. Each flagged conversation displays the flag reason prominently.

Common flag reasons and how to handle them:

- **Legal matters** -- The user asked about contracts, liability, incorporation, or legal structure. Do not give legal advice. Redirect them to a professional. Edit the response to acknowledge their question and suggest they consult a lawyer or accountant.
- **Mental health mentions** -- The user expressed burnout, personal crisis, emotional distress, or family emergencies. Respond with empathy, acknowledge the situation, and suggest they seek appropriate support. Keep the coaching light and human.
- **Stage transitions** -- The AI detected that the user may be moving from one stage to another (e.g., Ideation to Early Validation). Confirm whether the stage change is real based on the context, and update their profile on the Users page if so.
- **Low confidence** -- The AI scored its own response below 5. Read carefully; there is likely something it struggled with -- ambiguous user message, unfamiliar topic, or conflicting context.
- **URLs detected in response** -- The AI included a link or URL, which violates the coaching system's design rules. Remove the URL and replace with a resource name reference (e.g., "Lecture 7 covers this" instead of a link).
- **Out-of-scope topics** -- The user asked about something outside entrepreneurship coaching. Gently redirect them back to their business focus.
- **Direct request for Wes** -- The user wants to speak with Wes directly or meet in person. Handle according to your current policy.
- **Ambiguous situations** -- The user's message was unclear or confusing. You may need to write the response yourself or ask a clarifying question.

For each flagged conversation:

1. Read the user's message carefully.
2. Read the AI's draft response (if one exists -- cleanup-caught items may not have a draft).
3. Click "View user context" to see their business idea, journey summary, and stage.
4. If the AI draft is salvageable: edit the text, then click **Approve**.
5. If the AI draft is unusable: write your own response in the text area, then click **Approve**.
6. If you need more time: click **Move to Pending** to revisit later.
7. If the conversation should not receive a response: click **Reject**.

**Step 3: Go to Pending Review**

Navigate to the **Pending Review** page. These are standard AI-drafted responses waiting for your approval. Each conversation card shows:

- The user's name and stage
- The confidence score (X/10)
- The user's message (read-only)
- The AI response (editable text area)
- A "View user context" expander with their business idea, journey summary, and recent exchanges

For each pending conversation:

1. Check the confidence score. Higher scores (8-10) generally need less scrutiny, but still read them.
2. Read the user's message to understand what they are asking or reporting.
3. Read the AI response. Ask yourself: "Would Wes send this?"
4. Click "View user context" if you need more background on the user's journey.
5. If the response is good as-is: click **Approve**.
6. If the response needs changes: edit the text in the text area, then click **Approve**. The correction is automatically saved and will help the AI improve.
7. If the response is wrong or inappropriate: click **Reject** to discard it, or click **Flag** to revisit it later.

**Step 4: Check Workflow Health**

Navigate to **Run Workflows** in the sidebar. Scan the Workflow Run History section at the bottom. Look for:

- Any runs with a red X (failed). Click the expander to see the error message.
- Unusually low item counts (e.g., Process Emails showing 0 items for multiple consecutive runs when you know users are active and replying).
- Any "running" status that has been stuck for more than a few minutes.

If you see failures, check whether the issue is transient (network blip, temporary API error) or persistent (expired credentials, database issue). The System Status section at the top of the page shows live health checks for Database, Gmail, Python version, and Migration status.

### Understanding Confidence Scores

The AI evaluates its own responses on a 1-10 scale. The evaluation model (GPT-4o-mini) considers relevance, tone match, actionability, length, accuracy, resource usage, and stage alignment.

| Score | Meaning | Typical Action |
|-------|---------|----------------|
| 9-10 | Excellent response, highly likely correct | Quick scan, approve |
| 7-8 | Good response, minor improvements possible | Read carefully, light edits if needed |
| 5-6 | Decent but may miss nuance or tone | Read thoroughly, expect edits |
| 3-4 | Significant issues with relevance, tone, or advice | Heavy editing or full rewrite |
| 1-2 | Wrong, inappropriate, or completely off-base | Reject and write your own |

Your **auto-approve threshold** (configured in Settings) determines which scores bypass review. The default is 10, meaning nothing auto-approves and you review everything. As you build trust through the calibration data on the Analytics page, you can lower this gradually.

### The Correction Loop

This is the most important mechanism in the system. Every time you edit an AI response before approving it:

1. A correction record is automatically saved to the `corrected_responses` table.
2. The record captures three things: what the user said, what the AI wrote, and what you changed it to.
3. Recent stage-scoped corrections are included in the AI's context for future responses. The AI literally sees your past edits and adjusts its approach accordingly.
4. Over time, this means fewer corrections are needed. The AI converges toward your voice and judgment.

The effect is cumulative. The first few weeks require the most attention. After 50+ corrections, you will notice the AI getting noticeably better. After 100+, it starts to feel like the AI genuinely understands your coaching style.

You can also add corrections manually on the **Corrections** page. This is useful for creating teaching examples from scratch -- scenarios where you want to show the AI "here is the ideal response to this type of question" without waiting for that scenario to occur naturally.

Correction types help categorize what went wrong and identify patterns:

| Type | When to Use |
|------|-------------|
| **Tone** | The response was too formal, too casual, too enthusiastic, or too blunt |
| **Content** | The advice was wrong, irrelevant, or missed the point entirely |
| **Length** | Too long (the most common issue) or too short |
| **Focus** | Tried to address too many things at once, or focused on the wrong thing |
| **Factual** | Referenced something incorrectly or gave inaccurate information |
| **Style** | Structural issues -- used bullet points, sounded generic, lacked a question at the end |

---

## 3. Managing Users

### User Statuses

| Status | Meaning | System Behavior |
|--------|---------|-----------------|
| **Active** | Enrolled and receiving coaching | Gets check-ins on their scheduled days. Emails are processed through the full AI pipeline. |
| **Onboarding** | Going through the multi-step welcome flow | Receives onboarding prompts. Not yet receiving regular check-ins. |
| **Paused** | Voluntarily paused (user replied "pause" or similar) | No check-ins sent. Emails are still processed if received, and the system will detect resume intent. |
| **Silent** | No response for 17+ days (auto-set by re-engagement workflow) | No check-ins sent. Status automatically changes back to Active if the user replies. |

### Adding Users

Navigate to the **Users** page and expand the "Add new user" section.

- **Email** (required): Must match exactly what the user will send from. The system matches incoming emails by address, and even one character difference means their emails will not be linked to their profile.
- **First name** (required): Used in check-in greetings and response personalization. Use whatever the user goes by.
- **Stage**: Set based on where they are -- Ideation, Early Validation, Late Validation, or Growth. This determines the entire coaching approach, from the tone of advice to the resources referenced.
- **Business idea**: A brief description of what they are working on. The more specific and current this is, the better the AI's responses will be. Update it as you learn more from their messages.
- **Check-in days**: Select up to 3 days per week. Leave empty to use the system default (configured in Settings). Individual users can have personalized schedules that override the default.

Users can also be auto-created when they email the coaching address for the first time. In that case, they start in Onboarding status and go through the multi-step intake flow. See the Admin Onboarding Guide for full details.

### Editing Users

Click any user on the Users page to expand their profile. You can update:

- **First name, stage, status** -- Core profile fields that affect coaching behavior.
- **Business idea** -- Keep this current. The AI uses it heavily in every response. When a user pivots or refines their idea, update this field.
- **Current challenge** -- What they are struggling with right now. Updated during onboarding and can be manually refreshed anytime.
- **Notes** -- Free-form operator notes. These are for your eyes only -- not shown to the AI or the user. Use them for context like "Referred by John," "Premium member," "Has a co-founder named Alex," "Prefers very direct feedback."
- **Check-in days** -- Override the system default for this specific user.

Read-only fields visible at the bottom of each user's profile:

- **Journey Summary** -- The automatically maintained running narrative of their progress, updated after every sent response.
- **Satisfaction score** -- A rolling average (1-10) of engagement analysis based on their messages.
- **Onboarding step** -- Where they are in the onboarding flow (1, 2, or 3/complete).
- **Last response date** -- When the system last received or sent something for this user.
- **Joined date** -- When their account was created.

### User Journey Summary

The system automatically maintains a running summary for each user. After every response is sent, GPT-4o-mini generates a brief summary update that gets appended to the user's journey log with a date prefix.

This summary is included in the AI's context for every future response, giving it persistent memory across conversations. It tracks milestones, stage changes, key decisions, evolving challenges, and patterns in the user's behavior.

You do not need to maintain this manually. However, if you notice the summary is missing important context or has drifted from reality, you can supplement it by updating the user's business idea, current challenge, or notes fields.

### The Onboarding Flow

When a new person emails the coaching address for the first time:

1. A user record is created with status "Onboarding" and `onboarding_step: 1`.
2. An intake email is drafted and placed in Pending Review for your approval.
3. After you approve and the system sends it, the user replies with their stage, idea, and context.
4. Their reply triggers step 2: a follow-up asking for their biggest challenge (also goes to Pending Review).
5. After that reply, their status is set to Active and `onboarding_step: 3`. Regular check-ins begin on their scheduled days.

All onboarding messages go through Pending Review. Nothing sends without your approval.

---

## 4. Settings Deep Dive

All settings are configurable from the **Settings** page in the dashboard. Changes take effect immediately -- no restart or redeployment needed.

### Auto-Approve Threshold

This is the single most important setting in the system. It controls whether responses bypass your review queue.

- **Scale**: 1 (approve almost everything automatically) to 10 (review everything manually).
- **Default**: 10 -- nothing auto-approves. You review every response.
- **How it works**: If an AI response receives a confidence score greater than or equal to this threshold AND has no flags, it is automatically marked as "Approved" and will be sent at the next send window. If any flags are present, it always goes to the Flagged queue regardless of score.

**Recommended approach for building trust:**

1. **Start at 10.** Review everything for the first 2-4 weeks. This builds your correction corpus and gives you a feel for the AI's strengths and weaknesses.
2. **After 50+ reviewed responses**, check the Analytics page. Look at the Confidence Calibration section.
3. **If score 9-10 responses rarely need edits** (less than 5% edit rate), try lowering the threshold to 9.
4. **Continue lowering gradually.** Score 8 is a common long-term target for established programs. Going below 7 is not recommended -- even well-trained AI benefits from occasional human review.

Per-user overrides are also possible via the `auto_approve_threshold` field on each user record, though this requires direct database access (not exposed in the dashboard UI).

### Check-in Schedule

- **Default check-in days**: The system-wide default days for sending check-ins (e.g., Tue, Fri). Individual users can override this with their own schedule.
- **Max check-in days per week**: A cap per user (default: 3). Even if a user has more days selected, they will not receive more than this many check-ins per week.
- **Check-in hour**: The hour (in 24h format) when the check-in workflow runs (default: 9, meaning 9am in the configured timezone).

The check-in workflow runs daily via GitHub Actions, but it only sends to users whose personal schedule (or the system default) includes that day.

### Thread Cap

- **Max thread replies**: How many follow-up replies per check-in cycle (default: 4).
- After the cap is reached, the system stops generating responses to that user's emails until the next check-in resets the cycle.
- This prevents runaway back-and-forth conversations and keeps coaching focused on one or two key points per cycle.
- The user does not receive an error or notification. Their emails are still marked as read and their `last_response_date` is updated (so they do not trigger re-engagement), but no AI response is generated.

### Email Processing

- **Process interval (minutes)**: How often the system checks for new emails (default: 60). This maps conceptually to the GitHub Actions cron schedule.
- **Start hour / End hour**: The active processing window (default: 8am to 9pm in the configured timezone). Outside this window, emails accumulate as unread and are processed when the window opens.
- **Send hours**: Comma-separated hours when approved responses are sent (default: 9,13,19 -- meaning 9am, 1pm, and 7pm). Responses approved between send windows queue until the next window.

### Response Settings

- **Max response paragraphs**: Keeps AI responses concise (default: 3). This constraint is included in the AI's prompt context, encouraging focused, actionable responses rather than long essays.

### Notifications

- **Notification email**: The address where error alerts are sent (default: the coaching Gmail address). When any workflow fails or encounters errors, an alert email is sent to this address with details about what went wrong.

### Re-engagement

- **Days of silence before nudge**: How many days of no response before the system sends a re-engagement email (default: 10). After an additional 7 days beyond that (17 total by default), the user is automatically marked as "Silent" and check-ins stop.

---

## 5. Workflow Operations

### Automated Schedule

All workflows run automatically via GitHub Actions. Times are in Eastern (or your configured timezone).

| Workflow | Schedule | What It Does |
|----------|----------|-------------|
| **Process Emails** | Every hour, 8am-9pm ET | Fetches unread emails from Gmail, parses them, generates AI responses, evaluates and routes them to Pending Review, Flagged, or Auto-Approved. |
| **Send Approved** | 9am, 1pm, 7pm ET | Sends all approved responses that have not been sent yet. Adds the "Wes" sign-off. Updates journey summaries after sending. |
| **Check In** | Daily at 9am ET | Generates and sends personalized check-in questions to active users scheduled for today. Each check-in is unique, tailored to the user's context. |
| **Re-engagement** | Daily at 10am ET | Part 1: Sends a nudge to users silent 10+ days (if no nudge sent in the last 14 days). Part 2: Marks users silent 17+ days as "Silent" status. |
| **Cleanup** | Daily at 11pm ET | Catches any unread emails older than 24 hours that were missed by regular processing. Flags them for review and notifies the operator. Acts as a safety net. |

### Manual Triggers

The **Run Workflows** page provides buttons to trigger any workflow on demand. This is useful for:

- **Testing**: After making configuration changes, trigger Process Emails to verify things work.
- **Urgent processing**: If you know a user just sent an important email, trigger Process Emails immediately rather than waiting for the next hourly run.
- **Immediate sending**: After approving a batch of responses, trigger Send Approved to send them right away instead of waiting for the next send window.

Results appear in the Workflow Run History section below the trigger buttons.

Note: Running workflows from the Streamlit dashboard uses Streamlit Community Cloud's resources. For large batches (processing many emails at once), GitHub Actions is more reliable as it has higher resource limits and longer timeout windows.

### System Status Health Checks

The top of the Run Workflows page shows four status indicators:

| Indicator | What It Checks | If It Fails |
|-----------|---------------|-------------|
| **Database** | Can the system connect to Supabase and read the settings table? | Check your SUPABASE_URL and SUPABASE_KEY secrets. Verify the Supabase project is running and has not been paused. |
| **Gmail** | Can the system connect to Gmail via IMAP? | Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD. Verify the Google app password has not expired or been revoked. Confirm 2FA is still enabled. |
| **Python** | Is the Python version 3.9 or higher? | This should always pass on Streamlit Cloud and GitHub Actions. If it fails, there is a deployment issue. |
| **Migration v2** | Have the latest database schema changes been applied? | Run the `db/migration_v2.sql` file in the Supabase SQL Editor. |

### Monitoring Workflow Health

Check the Workflow Run History regularly. The history view lets you filter by time period (24 hours, 48 hours, 72 hours, or 7 days) and groups runs by workflow name with expandable details.

Warning signs to watch for:

- **Failed runs** (red X): Click into the expander to read the error message. Common causes: expired Gmail app password, Supabase downtime, OpenAI API errors, rate limits.
- **Zero items processed for multiple consecutive runs**: The system may be failing silently, or there may genuinely be no new emails. Cross-reference with the Gmail inbox to confirm.
- **"Running" status stuck for more than 5 minutes**: The workflow may have timed out. It will eventually be marked as failed by the next run.

Error alerts are automatically emailed to the notification address configured in Settings.

---

## 6. Analytics and Performance

The **Analytics** page provides four sections of operational intelligence that help you tune the system and track program health.

### Confidence Calibration

This is your primary tool for making data-driven decisions about the auto-approve threshold. It shows:

- **Top-line metrics**: Total reviewed responses, responses edited, and overall edit rate.
- **A table grouped by confidence score**: For each score (1-10), how many responses received that score, how many were edited, the edit rate percentage, and the average response time.
- **A bar chart**: Edit rate by confidence score, visualizing where the AI's self-assessment is well-calibrated vs. where it over- or under-estimates.

**How to use it**: If the edit rate for scores 8, 9, and 10 is below 5%, you can confidently set the auto-approve threshold to 8 -- the AI's self-assessment is reliable at those levels. If score 7 responses have a 20% edit rate, keep the threshold above 7 for now. The data tells you exactly when it is safe to increase automation.

### Response Time Tracking

Shows how quickly responses are getting to users, measured from when the email is received to when the response is sent.

- **Metrics**: Average, median, fastest, and slowest response times in hours.
- **Distribution histogram**: Buckets responses into time ranges (under 1 hour, 1-2 hours, 2-4 hours, etc.).
- **Goal**: Keep the average under 24 hours. If responses are consistently taking more than 12 hours, you may need to check the dashboard more frequently, increase your send windows, or lower the auto-approve threshold to reduce the review bottleneck.

### Correction Analytics

Shows a breakdown of corrections by type (Tone, Content, Length, Focus, Factual, Style) with a bar chart and table.

**How to use it to improve the system**: If most corrections are concentrated in the same type, that indicates a systemic issue with a specific fix:

- **Heavy on Tone corrections**: The coaching persona definition in `prompts/assistant_instructions.md` may need updating to better define the voice. Add more specific tone examples.
- **Heavy on Content corrections**: The AI may lack context. Check that user profiles (business idea, summary) are populated. Consider uploading more program content to the vector store.
- **Heavy on Length corrections**: Adjust the `max_response_paragraphs` setting or add stronger emphasis in the assistant instructions about keeping responses concise.
- **Heavy on Focus corrections**: The AI may be trying to address too many things at once. This often improves naturally as more corrections accumulate and the AI learns to focus.

### Satisfaction Trends

Shows member engagement and satisfaction over time, based on automated analysis of user messages.

- **Metrics**: Average satisfaction score (1-10), number of scored responses, unique users tracked.
- **Line chart**: Satisfaction trend over time.
- **What to watch for**: Declining trends across multiple users may indicate a systemic issue -- check-ins may be too frequent, responses may feel generic, or users may be losing momentum. Rising trends confirm the system is working well. Individual user dips may need personal attention.

---

## 7. Fine-Tuning (Advanced)

### What It Is

Fine-tuning takes a base AI model and trains it specifically on your corrections. The result is a custom model that generates responses closer to your coaching voice out of the box, requiring fewer edits over time. It is the ultimate expression of the learning loop -- going beyond in-context corrections to permanently encoding your preferences into the model's weights.

### When to Do It

- **Minimum**: 50 corrections. OpenAI can work with fewer, but results improve significantly with more data.
- **Ideal**: 100+ corrections covering a variety of user stages, topics, and correction types.
- **Re-fine-tune**: Every 2-3 months as you accumulate more corrections. Each fine-tune uses a fresh, complete dataset.

### How to Do It

1. Navigate to **Run Workflows** and scroll to the Fine-Tuning Export section.
2. Review the metrics: Total Corrections, Usable for Training (corrections with sufficient context), and the recommended minimum.
3. Set the output filename (default: `finetune_data.jsonl`) and minimum corrections threshold.
4. Click **Export Fine-Tuning Data**. The system generates a JSONL file formatted for OpenAI's fine-tuning API.
5. Click **Download JSONL File** to save it to your computer.
6. Go to [platform.openai.com/finetune](https://platform.openai.com/finetune).
7. Click **Create**, select **gpt-4o-mini** as the base model, and upload your JSONL file.
8. Wait 15-45 minutes for training to complete. OpenAI sends an email when done.
9. Copy the fine-tuned model ID (it looks like `ft:gpt-4o-mini-2024-07-18:your-org::abc123`).
10. Update the model setting in your configuration to use the fine-tuned model for evaluation tasks.

**Tips:**

- Quality over quantity. 50 thoughtful corrections beat 200 sloppy ones.
- Make sure corrections span different stages, topics, and correction types for the best results. A diverse training set produces a more versatile model.
- Keep the original model ID as a fallback in case you need to revert.
- Fine-tuning gpt-4o-mini is very affordable -- approximately $0.80 per 100 training examples.
- You can also fine-tune GPT-4o for generation tasks once you have 100+ high-quality corrections, though this is more expensive and should be done only when you have a strong, diverse corpus.

---

## 8. Prompt Management

The AI's behavior is controlled by two prompt files that define its coaching persona and evaluation criteria. Changes to these files take effect immediately -- the prompts are loaded fresh with each workflow run. No restart or redeployment needed.

### Assistant Instructions (`prompts/assistant_instructions.md`)

This is the system prompt that defines who the AI is and how it coaches. It is the most important configuration file in the system. It includes:

- **Persona**: The AI responds as Wes, an entrepreneurship coach at The Launchpad Incubator.
- **Coaching style**: Direct and focused, 1-3 paragraphs, one or two key points per response, actionable nudges that push the user forward, warm but not effusive, always ends with a question.
- **Core philosophy**: Ideas come from conversations with real people. Customer conversations come before building. Manual before automated. Focus beats breadth. Challenge busy-but-not-progressing behavior.
- **Coaching pattern**: Name the pattern you see, give a specific next step, ask a question that pushes them to act.
- **Resource referencing rules**: Reference program content by name only -- never include URLs, links, or attachments. Say "Lecture 7 covers this" not "check out this link."
- **What the AI will not do**: No legal/medical/financial/mental health advice. No long essays. No generic motivation. No step-by-step plans. No outcome promises. No bullet points.

**When to edit this file:** If the coaching approach evolves, if you want to adjust the tone, if you want to add new constraints or remove old ones, or if you notice the AI consistently violating a rule that is not currently documented. Be specific in your changes -- the AI follows these instructions closely.

### Evaluation Prompt (`prompts/evaluation_prompt.md`)

This defines how the AI evaluates its own responses. It controls the quality gate that determines whether a response needs your review:

- **Confidence scoring criteria**: Relevance to the user's message, tone match with the coaching persona, actionability of the advice, response length, factual accuracy, resource usage, and stage alignment.
- **Flag detection rules**: The complete list of conditions that trigger a flag (legal matters, mental health indicators, out-of-scope topics, ambiguous situations, stage transitions, direct requests for Wes, low confidence, harmful advice risk, vulnerable populations, URLs in response).
- **Stage detection logic**: How the AI determines which stage a user is in based on their message content.
- **Resource reference detection**: Captures which program resources are mentioned in the response.
- **Summary update generation**: Creates the brief progress update for the user's journey log.

**When to edit this file:** If you want to add or remove flag conditions, adjust scoring criteria, change what triggers a flag, modify how stages are detected, or recalibrate what constitutes high vs. low confidence.

---

## 9. Troubleshooting

### Common Issues and Fixes

**"No pending responses to review"**

The Pending Review queue is empty. This is normal if no new emails have arrived, or if all responses were auto-approved (if your threshold allows it). If you expect responses, check:
- Has Process Emails run recently? Go to Run Workflows and check the history, or trigger it manually.
- Are there new emails in the Gmail inbox? Check directly by logging into the coaching Gmail account.
- Is the user's status Active? Paused and Silent users' emails are handled differently.

**"Emails not sending"**

Approved responses are stuck and not being delivered. Check:
- Gmail connection status on the Settings page. If it shows an error, the Google app password may have expired.
- Go to Google Account -> Security -> App Passwords and regenerate if needed. Update the GMAIL_APP_PASSWORD secret in all locations (GitHub Secrets, Streamlit secrets, and local .env if applicable).
- Trigger Send Approved manually from Run Workflows to retry.

**"Low confidence scores across the board"**

The AI is not confident in its responses for multiple users. Common causes:
- User profiles are sparse. Check that business idea and journey summary are populated for the affected users.
- The user's messages are vague or ambiguous. This is expected -- scores improve with clearer, more detailed messages.
- The AI lacks stage-specific context. Ensure user stages are set correctly.
- The vector store may need more content. Upload additional program materials to give the AI more to draw from.

**"Wrong stage detected"**

The AI thought the user was in a different stage than they actually are. Manually update the user's stage on the Users page. The AI will use the correct stage going forward. If this happens frequently for a particular user, their business idea and summary may need updating to better reflect their actual situation.

**"Thread cap reached"**

The user has hit the maximum number of follow-up replies for this check-in cycle (default: 4). This is by design to keep coaching focused. The user will receive a new check-in on their next scheduled day, which resets the cycle. No action needed unless you want to increase the cap in Settings.

**"User stuck in Onboarding"**

Check the Pending Review queue for unapproved onboarding messages. The onboarding flow cannot proceed until each step's response is approved and sent. If the user's onboarding step is stuck at 1 or 2, there is likely an unapproved message waiting for you.

**"Workflow errors in history"**

Check the error message in the Run Workflows history expander. Common causes:
- **OpenAI API errors**: Rate limits, model unavailable, or API key issues. Usually transient -- the next run succeeds automatically.
- **Supabase errors**: Connection issues or query failures. Check if Supabase is experiencing downtime (supabase.com/status).
- **Gmail errors**: Authentication failures, IMAP connection drops. Usually resolved by the next run.
- You will also receive an email alert at your notification address.

**"Dashboard won't load"**

Check Streamlit Community Cloud status. Verify that:
- The app has not been paused due to inactivity (Streamlit pauses free-tier apps after a period of no usage -- just visit the URL to wake it up).
- Secrets are still configured in the Streamlit app settings (three-dot menu -> Settings -> Secrets).
- Recent code pushes did not introduce syntax errors (check the Streamlit deployment logs).

### Emergency Procedures

**System is completely down (all workflows failing)**

Do not panic. No emails are lost. Incoming emails remain unread in the Gmail inbox, safely waiting. When the system comes back online, the next Process Emails run will pick them up. The Cleanup workflow also acts as a safety net for anything older than 24 hours.

Steps:
1. Identify the root cause: check GitHub Actions logs, Streamlit deployment logs, Supabase status page, and OpenAI status page.
2. Fix the issue: rotate credentials, fix code, or wait for upstream service recovery.
3. Trigger Process Emails manually once the system is back.
4. Check that all queued emails were processed by reviewing the Conversations page.

**A bad response was sent to a user**

There is no undo for sent emails. The response has already been delivered. To correct the situation:
1. Log into the coaching Gmail account directly.
2. Send a manual follow-up email to the user, threading into the existing conversation. Acknowledge the issue naturally -- "Actually, let me rephrase that..." or "I want to add something to my last email..."
3. Review the conversation on the Conversations page to understand what went wrong.
4. If the error was systemic (e.g., the AI consistently gives bad advice on a topic), add a correction and consider updating the assistant instructions to prevent recurrence.

**User complaint about the system**

1. Go to the **Conversations** page and filter by the user.
2. Review their full conversation history to understand what they received and when.
3. Check for any flagged or rejected responses in their history.
4. Respond to the user directly from the coaching Gmail account with a personal, human touch.
5. If the complaint is about response quality, add relevant corrections to improve future responses.

---

## 10. Weekly and Monthly Tasks

### Weekly Checklist

- [ ] **Review the Analytics page.** Check confidence calibration, response times, correction patterns, and satisfaction trends. Look for anything unusual or trending in the wrong direction.
- [ ] **Audit correction patterns.** Are you making the same type of correction repeatedly? If so, consider updating the assistant instructions to address the root cause rather than fixing it response by response.
- [ ] **Verify all workflows ran.** On the Run Workflows page, check the 7-day history. Every scheduled workflow should have run at its expected times. Investigate any gaps.
- [ ] **Check satisfaction trends.** Are any individual users showing declining engagement? They may need a different approach, a stage change, or a personal outreach from Gmail.
- [ ] **Review the Flagged queue.** Make sure nothing has been sitting in Flagged for more than a day or two. Flagged items need timely attention.

### Monthly Checklist

- [ ] **Evaluate auto-approve threshold.** Check the Confidence Calibration chart on Analytics. If high-confidence scores have consistently low edit rates, consider lowering the threshold by one point.
- [ ] **Audit the user list.** Go to the Users page and review all users. Should anyone be paused, reactivated, or have their stage updated? Are business ideas and summaries still accurate?
- [ ] **Check resource references.** On the Conversations page, look at which resources the AI is recommending. Are they appropriate and relevant? Are any outdated or no longer part of the curriculum?
- [ ] **Review fine-tuning readiness.** On Run Workflows, check the fine-tuning metrics. If you have 50+ usable corrections and have not fine-tuned yet (or it has been 2+ months since the last fine-tune), consider exporting and training a new model.
- [ ] **Update assistant instructions.** Has the coaching approach evolved? Are there new resources, new stages, or new topics that need to be reflected in the prompts? Edit `prompts/assistant_instructions.md` and `prompts/evaluation_prompt.md` as needed.
- [ ] **Review system settings.** Are the check-in days, send hours, processing windows, and re-engagement timing still appropriate? Adjust as the program evolves.

---

## Appendix: System Architecture at a Glance

| Component | Platform | Purpose |
|-----------|----------|---------|
| Dashboard | Streamlit Community Cloud | Operator interface for review, management, settings, analytics |
| Scheduled Jobs | GitHub Actions | Automated cron workflows (5 total) running the coaching pipeline |
| Database | Supabase (PostgreSQL) | Users, conversations, corrections, settings, workflow logs |
| AI (Response Generation) | OpenAI GPT-4o | Generates coaching responses with knowledge base search (RAG) |
| AI (Evaluation) | OpenAI GPT-4o-mini | Scores responses, detects flags, detects stages, analyzes satisfaction |
| AI (Parsing Fallback) | OpenAI GPT-4o-mini | Email parsing when deterministic parser returns empty or messy results |
| AI (Summaries) | OpenAI GPT-4o-mini | Generates journey summary updates after each sent response |
| Email | Gmail (Google Workspace) | IMAP for reading, SMTP for sending, with human-like threading |
| Knowledge Base | OpenAI Vector Store | Contains program curriculum (lectures, books, frameworks) for RAG retrieval |

### Key Files for Operators

| File | What It Controls |
|------|-----------------|
| `prompts/assistant_instructions.md` | The AI's coaching persona, style, philosophy, and behavioral constraints |
| `prompts/evaluation_prompt.md` | How responses are scored, flagged, and evaluated for quality |
| `dashboard/pages/6_settings.py` | All configurable settings (also accessible via the Settings page in the dashboard) |
| `config.py` | Environment variable loading (secrets and credential management) |

### Email Filtering

The system automatically ignores emails from these senders. No action required -- this prevents the system from trying to "coach" automated messages.

- The coaching system's own email address (prevents feedback loops)
- No-reply addresses (noreply, no-reply, no_reply patterns)
- System senders (mailer-daemon, postmaster, notifications, calendar-notification)
- Google Workspace system emails (workspace-noreply, admin@google, googleworkspace, accounts.google)

### Deduplication

Every conversation records the Gmail message ID. Before processing any email, the system checks if that ID already exists in the database. This prevents double-processing even if a workflow runs multiple times, the same email is fetched again, or the cleanup workflow catches an already-processed email.

---

*This guide reflects the current state of the Launchpad Incubator Coaching System. As the system evolves, update this document to match.*
