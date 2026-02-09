# Summary Update Prompt

This prompt generates brief updates to add to a user's ongoing journey summary after each coaching exchange.

---

## Prompt Template

```
You are helping update a user's coaching summary. Based on the recent exchange below, provide a brief 1-2 sentence update to add to their ongoing summary.

Current Summary:
{current_summary}

User's Message:
{user_message_parsed}

Coach's Response:
{sent_response}

Provide only the new summary text to append (1-2 sentences). Focus on key progress, challenges, or direction changes.
```

---

## Configuration

- **Model:** GPT-4 (or GPT-3.5-turbo for cost savings)
- **Temperature:** 0.5 (some variation is fine)
- **Max tokens:** 200

---

## What to Capture

Good summary updates focus on:

1. **Progress milestones:** "Completed 10 customer interviews."
2. **Key insights:** "Discovered target market cares more about speed than price."
3. **Direction changes:** "Pivoting from B2C to B2B approach."
4. **Challenges identified:** "Struggling with pricing conversations."
5. **Decisions made:** "Chose to focus on the invoicing problem."
6. **Stage transitions:** "Moving from ideation into validation."

---

## What to Avoid

Don't include:
- Routine updates ("Had another check-in")
- Vague statements ("Making progress")
- Coaching advice given (that's in Conversations)
- Full conversation recaps

---

## Examples

### Example 1: Progress Update

**User's Message:**
```
1. Accomplished: Did 8 customer interviews this week, all with e-commerce store owners
2. Current Focus: Analyzing what I heard
3. Next Step: Identify the top 3 patterns
4. Approach: Going through my notes systematically
```

**Coach's Response:**
```
Great volume on the interviews. When you're looking for patterns, pay attention to: which problems came up multiple times, which ones had the strongest emotional reaction, and which ones people have already tried to solve...
```

**Summary Update:**
```
Completed 8 customer interviews with e-commerce store owners. Now analyzing patterns and insights from the conversations.
```

---

### Example 2: Insight Discovered

**User's Message:**
```
Big realization this week - I was asking about their "workflow" but what they actually struggle with is just remembering to follow up. It's not a process problem, it's a memory/reminder problem.
```

**Coach's Response:**
```
That's a significant reframe. "Workflow optimization" is a crowded space. "Never forget to follow up" is a much sharper problem to solve...
```

**Summary Update:**
```
Key insight: The problem isn't workflow optimization but rather remembering to follow up. Reframing the problem space.
```

---

### Example 3: Stage Transition

**User's Message:**
```
Got my first paying customer! They paid $200 for the manual version of what I was describing. Feeling really validated.
```

**Coach's Response:**
```
First paying customer - that's real validation. Now the question becomes: can you get 4 more at that price point?...
```

**Summary Update:**
```
Achieved first paying customer ($200). Moving from validation into proving repeatability.
```

---

### Example 4: Challenge Identified

**User's Message:**
```
I keep getting stuck when people ask about pricing. I freeze up and say "we're still figuring that out" which feels weak. Not sure how to handle it.
```

**Coach's Response:**
```
Pricing conversations feel awkward because they're real. Here's the reframe: you're not asking them to buy, you're asking them to help you understand value...
```

**Summary Update:**
```
Identified challenge with pricing conversations - tendency to avoid or deflect when price comes up.
```

---

## Summary Format in Airtable

The summary builds over time with dated entries:

```
2026-01-10: Started coaching with a SaaS idea for small business bookkeeping.

2026-01-14: Completed first 5 customer interviews. Discovered invoice tracking is the biggest pain point.

2026-01-18: Narrowed focus to invoice tracking for service businesses. Planning manual pilot.

2026-01-22: Key insight: The problem isn't workflow optimization but rather remembering to follow up. Reframing the problem space.
```

This gives you (and the AI) a quick overview of the user's entire journey when responding to new messages.
