# Manual Test Plan — Coaching System

This is a structured walkthrough you can complete in about 60-90 minutes. You'll play two roles:

- **The user** — sending emails from a personal email address (Gmail, etc.) to `coachwes@thelaunchpadincubator.com`
- **The admin** — reviewing and acting on those emails in the dashboard

Use a real personal email address you control (not `coachwes@`). This way you'll see exactly what your coaching participants see.

**Before you start:** Have the dashboard open in one browser tab and your personal email open in another.

---

## Test 1: Brand New User Sends First Email

**What you're testing:** Does the onboarding flow work end-to-end?

### As the user:
1. From your personal email, send a new email to `coachwes@thelaunchpadincubator.com`
2. Subject: anything (e.g., "Hey, I just signed up")
3. Body: "Hi, I heard about the coaching program and I'd love to get started. I have an idea for an app that helps freelancers find clients."

### As the admin:
4. Go to **Run Workflows** → click **Process Emails**
5. Go to **Pending Review**

### What to look for:
- [ ] A new conversation appeared with type "Onboarding"
- [ ] The AI response is the standard welcome/intake email (asks about stage, challenge, business idea)
- [ ] The user's name was extracted correctly from your email (check the header — it should show your first name, not your full email address)
- [ ] Go to **Users** — a new user was created with status "Onboarding"

### Finish the test:
6. Click **Approve** on the onboarding conversation
7. Go to **Run Workflows** → click **Send Approved**
8. Check your personal email — you should receive the onboarding email from Wes

### What to look for in your inbox:
- [ ] The email arrived
- [ ] The "From" name shows "Wes" (not the raw email address)
- [ ] The subject line looks right
- [ ] The body reads naturally — proper greeting with your name, clear instructions

**Write down anything that feels off:** tone, formatting, missing info, weird spacing, etc.

---

## Test 2: New User Replies to Onboarding

**What you're testing:** Does the first real coaching exchange work?

### As the user:
1. Reply to the onboarding email you just received. Write something like:

> I'd say I'm in the Ideation stage. My biggest challenge is that I have the idea but I don't know how to figure out if people would actually pay for it. The idea is an app that matches freelancers with small businesses that need short-term help — kind of like a matchmaker instead of a job board.

### As the admin:
2. Go to **Run Workflows** → click **Process Emails**
3. Go to **Pending Review**

### What to look for:
- [ ] The conversation shows the parsed version of the user's message (not the full email with quoted text and signatures)
- [ ] The AI generated a coaching response
- [ ] The response feels like something you'd actually write
- [ ] The response is 1-3 paragraphs (not an essay)
- [ ] It ends with a question that moves them forward
- [ ] It doesn't use bullet points
- [ ] It doesn't include "Wes" at the end (that gets added when sending)
- [ ] The confidence score seems reasonable for the quality

### Before approving:
4. Go to **Users**, find yourself, and update:
   - Stage → Ideation
   - Business idea → "App matching freelancers with small businesses"
   - Status → Active
5. Go back to **Pending Review** and approve the response (edit it first if you want to test the correction feature)
6. **Run Workflows** → **Send Approved**
7. Check your inbox

### What to look for in your inbox:
- [ ] Response arrived as a reply in the same email thread (not a new email)
- [ ] Ends with "Wes" signature
- [ ] Signature appears exactly once (not doubled)
- [ ] The tone and content match what you approved

---

## Test 3: Normal Coaching Exchange

**What you're testing:** Does an ongoing coaching conversation feel natural?

### As the user:
1. Reply again with a realistic update:

> I talked to three people this week about the freelancer problem. Two of them said they already use Upwork and are fine with it. The third one said she hates job boards because they attract the wrong kind of clients. I'm not sure what to make of that — is this even a real problem?

### As the admin:
2. Process emails, then review

### What to look for:
- [ ] The AI picked up on the customer discovery context
- [ ] The response addresses the specific findings (2 satisfied with Upwork, 1 frustrated)
- [ ] It gives a clear next step (probably: talk to more people like the third person)
- [ ] It references relevant content from your books/lectures if appropriate
- [ ] The confidence score reflects the quality
- [ ] The user's journey summary gets updated after you approve and send

### Check the summary:
3. After approving and sending, go to **Users** and look at the user's "Journey Summary"
- [ ] It has a dated entry summarizing this exchange
- [ ] The summary captures what actually matters (not just "user sent a message")

---

## Test 4: Edit a Response Before Approving

**What you're testing:** Does the correction/learning system work?

### As the user:
1. Send another reply:

> So I talked to 5 more people. 4 of them had the same complaint about job boards attracting the wrong clients. I think I might be onto something. Should I start building an MVP?

### As the admin:
2. Process emails, go to Pending Review
3. Read the AI's response. Regardless of quality, **edit it** before approving:
   - Change some of the wording to be more "you"
   - Maybe add a specific reference or remove something generic
4. Click **Approve**

### What to look for:
- [ ] The approval confirmation says "(correction saved)"
- [ ] Go to **Corrections** page — your edit appeared with the original AI text, your corrected version, and "Edited during review" as the note
- [ ] The correction type shows "Content"

---

## Test 5: Pause and Resume

**What you're testing:** Do pause and resume keywords work correctly?

### As the user:
1. Reply to the coaching thread: "Hey, I need to take a break for a couple weeks. Things are crazy at work."

### As the admin:
2. Process emails, check **Pending Review**

### What to look for:
- [ ] A pause confirmation response was drafted (something about pausing check-ins)
- [ ] The conversation status is "Pending Review" (not auto-sent)
- [ ] Go to **Users** — the user's status changed to "Paused"

3. Approve and send the pause confirmation
4. Check your inbox — did the confirmation arrive?

### Now test resume:

### As the user:
5. Reply: "I'm back and ready to pick up where we left off."

### As the admin:
6. Process emails, check Pending Review

### What to look for:
- [ ] A resume confirmation was drafted
- [ ] Status is "Pending Review"
- [ ] Go to **Users** — status changed back to "Active"

7. Approve and send

---

## Test 6: Trigger a Flagged Response

**What you're testing:** Does the flagging system catch sensitive topics?

### As the user:
1. Send a message that should trigger a flag:

> I've been thinking about incorporating as an LLC. Do I need a lawyer for that, or can I just do it online? Also, I'm honestly feeling really burned out lately and wondering if I should just quit everything.

### As the admin:
2. Process emails
3. Check **Pending Review** first, then check **Flagged**

### What to look for:
- [ ] The conversation landed on the **Flagged** page (not Pending Review)
- [ ] The flag reason mentions either the legal question or the burnout/mental health concern
- [ ] If the AI still generated a response, check that it did NOT give legal advice or play therapist
- [ ] You can write your own response in the text box and approve it from the Flagged page

---

## Test 7: Duplicate Email Handling

**What you're testing:** Does the system skip emails it already processed?

### As the admin:
1. Go to **Run Workflows** → click **Process Emails** again (without sending any new email)

### What to look for:
- [ ] No new conversations appeared in Pending Review
- [ ] The workflow run shows "0 items" processed
- [ ] Previously handled conversations are untouched

---

## Test 8: Check-In Email

**What you're testing:** Does the automated check-in look right?

### As the admin:
1. Go to **Users**, find your test user
2. Confirm their status is "Active" and their last response date is at least 3 days ago (if it's not, you can manually edit the `last_response_date` field in Supabase to be 4 days ago, or just skip this test and come back to it in a few days)
3. Go to **Run Workflows** → click **Check In**
4. Check your personal inbox

### What to look for:
- [ ] You received a check-in email
- [ ] It addresses you by your first name
- [ ] The four-part check-in format looks clear (Accomplished, Current Focus, Next Step, Approach)
- [ ] If you had an existing email thread, the check-in arrived in the same thread (not a new conversation)
- [ ] If this is the first outbound, it started a new thread with subject "Quick check-in"

---

## Test 9: Dashboard Walkthrough

**What you're testing:** Does every page work and show accurate data?

Go through each page and verify:

### Home page
- [ ] The four metrics at the top are accurate
- [ ] Recent workflow runs show correct statuses

### Conversations page
- [ ] All your test conversations appear in the history
- [ ] They show the correct statuses (Sent, Rejected, etc.)
- [ ] The user info (name, stage) is attached to each conversation

### Users page
- [ ] Your test user shows correct stage, status, business idea
- [ ] The journey summary has entries from your test conversations
- [ ] You can edit fields and save successfully

### Settings page
- [ ] All settings have reasonable values
- [ ] The Gmail connection check at the bottom shows "OK"
- [ ] Changing a setting and refreshing the page shows the new value persisted

### Corrections page
- [ ] Your edit from Test 4 is listed
- [ ] The original vs. corrected text is accurate

---

## Test 10: The Experience From the User's Side

Go back to your personal email and read through the entire email thread from top to bottom, as if you were a coaching participant seeing this for the first time.

Ask yourself:
- [ ] Does the conversation feel natural and coherent?
- [ ] Does it feel like one person (Wes) writing, or does the tone shift between messages?
- [ ] Are the responses the right length? Too long? Too short?
- [ ] Are the questions at the end of each response actually engaging, or do they feel formulaic?
- [ ] Would you actually reply to these emails if you were a real participant?
- [ ] Is there anything that would make you think "this is clearly AI-generated"?
- [ ] Does the threading work? Is it one continuous conversation in your inbox, or scattered?

---

## After Testing: What to Write Down

Keep a running list as you go. For each issue, note:

1. **What happened** — what you did and what the system did
2. **What you expected** — what should have happened
3. **How it felt** — even if something technically works, note if it felt wrong (awkward wording, weird timing, confusing interface)

Common things to watch for:
- Response tone or length that doesn't feel like you
- Formatting issues (extra line breaks, doubled signatures, missing names)
- Dashboard confusion (buttons not where you'd expect, unclear labels)
- Timing issues (things that should be instant but aren't, or vice versa)
- Missing context (the AI clearly didn't "know" something it should have)

---

## Cleanup After Testing

When you're done, you can either:
- **Keep the test user** as a reference — just set their status to Paused so they don't get check-ins
- **Delete the test user** from Supabase directly if you want a clean slate

The test conversations will remain in the Conversations history either way, which is fine — they serve as a useful reference for what the system's output looks like.
