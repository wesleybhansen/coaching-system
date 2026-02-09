# Email Parsing Prompt

This prompt extracts the user's actual message from raw email content, removing signatures, quoted text, and boilerplate.

---

## Prompt Template

```
Extract only the user's actual message from this email. Remove:
- Email signatures
- Previous quoted messages (lines starting with >)
- "On [date], [person] wrote:" headers
- Confidentiality disclaimers
- "Sent from my iPhone" footers
- Any other boilerplate

Return only the user's new content, preserving their formatting.

Email:
{raw_email_content}
```

---

## Configuration

- **Model:** GPT-4 (or GPT-3.5-turbo for cost savings)
- **Temperature:** 0.1 (low for consistent extraction)
- **Max tokens:** 2000 (should be plenty for most emails)

---

## Common Patterns to Remove

### Signature Blocks
```
--
John Smith
CEO, Acme Corp
555-123-4567
```

```
Best,
Jane

---
Jane Doe | Marketing Director
jane@company.com
```

### Quoted Text
```
On Mon, Jan 15, 2026 at 9:00 AM Wes <coachwes@thelaunchpadincubator.com> wrote:
> Hey John,
> Quick check-in...
```

### Mobile Footers
```
Sent from my iPhone
```

```
Sent from my Android
```

### Confidentiality Notices
```
CONFIDENTIALITY NOTICE: This email and any attachments are for the exclusive...
```

### Calendar/Auto-responses (should be flagged, not parsed)
```
I'm out of office until...
```

---

## Edge Cases

### Empty after parsing
If the email contains only quoted text or signatures, return an empty string. The workflow will flag this for review.

### Multiple responses in one email
Sometimes users reply to multiple check-ins at once. Preserve all their content.

### Inline replies
When users reply inline (between quoted text), extract all their new content and concatenate it.

Example input:
```
On [date], Wes wrote:
> What's your current focus?

Working on customer interviews.

> What's your next step?

Have 3 calls scheduled this week.
```

Should extract:
```
Working on customer interviews.

Have 3 calls scheduled this week.
```

---

## Testing the Prompt

Use these test cases to verify the parsing works correctly:

### Test 1: Simple reply
**Input:**
```
Here's my update:

1. Accomplished: Had 3 customer calls
2. Current Focus: Refining the pitch
3. Next Step: Book 5 more calls
4. Approach: LinkedIn outreach

Thanks!
John

On Mon, Jan 15, 2026 at 9:00 AM Wes wrote:
> Hey John, Quick check-in...
```

**Expected output:**
```
Here's my update:

1. Accomplished: Had 3 customer calls
2. Current Focus: Refining the pitch
3. Next Step: Book 5 more calls
4. Approach: LinkedIn outreach

Thanks!
John
```

### Test 2: With signature
**Input:**
```
Quick update - I did the customer calls and learned a lot. The main insight was that people care more about speed than price.

--
Sarah Chen
Founder, StartupX
sarah@startupx.com
```

**Expected output:**
```
Quick update - I did the customer calls and learned a lot. The main insight was that people care more about speed than price.
```

### Test 3: iPhone footer
**Input:**
```
Got it, will do those calls this week!

Sent from my iPhone
```

**Expected output:**
```
Got it, will do those calls this week!
```
