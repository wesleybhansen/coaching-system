# Airtable Schema Documentation

## Overview

This document provides the complete schema for the Automated Email Coaching System Airtable base. Create a new base called "Email Coaching System" and set up the following 5 tables.

---

## Table 1: Users

The primary table storing all coaching program members.

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| Email | Email | Primary identifier - required |
| First Name | Single line text | For personalization |
| Stage | Single select | Options: Ideation, Early Validation, Late Validation, Growth |
| Business Idea | Long text | From onboarding - enable rich text |
| Current Challenge | Long text | Updated from conversations |
| Summary | Long text | Running summary of their journey, updated by AI |
| Status | Single select | Options: Active, Paused, Silent |
| Last Response Date | Date | Track engagement - date only |
| Last Thread ID | Single line text | Gmail thread ID for email threading |
| Last Message ID | Single line text | Gmail message ID for reply tracking |
| Created | Created time | Automatic - when they joined |
| Notes | Long text | Internal notes (optional) |

### Default Values
- Status: Active
- Stage: Ideation

### Views to Create
1. **All Users** - Grid view, all records
2. **Active Users** - Filter: Status = "Active"
3. **Paused Users** - Filter: Status = "Paused"
4. **Silent Users** - Filter: Status = "Silent"
5. **By Stage** - Group by Stage field
6. **Needs Check-in** - Filter: Status = "Active" AND Last Response Date is more than 3 days ago

---

## Table 2: Conversations

Stores all email exchanges with users.

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| User | Link to another record | Link to Users table |
| Type | Single select | Options: Check-in, Follow-up, Re-engagement, Onboarding |
| User Message (Raw) | Long text | Original email including signatures |
| User Message (Parsed) | Long text | Cleaned message content only |
| AI Response | Long text | Generated response from GPT-4 |
| Sent Response | Long text | What was actually sent (after manual edits) |
| Confidence | Number | 1-10 scale, AI self-assessed |
| Status | Single select | Options: Pending Review, Approved, Sent, Flagged |
| Flagged Reason | Single line text | Why it was flagged |
| Gmail Thread ID | Single line text | For email threading |
| Gmail Message ID | Single line text | For reply tracking |
| Created | Created time | When received |
| Sent At | Date time | When response was sent |
| Resource Referenced | Single line text | Which resource was cited (if any) |
| Stage Detected | Single select | Same options as Users.Stage |
| Stage Changed | Checkbox | True if stage transition detected |

### Views to Create
1. **All Conversations** - Grid view sorted by Created (newest first)
2. **Pending Review** - Filter: Status = "Pending Review", sorted by Created (oldest first)
3. **Flagged** - Filter: Status = "Flagged", sorted by Created (oldest first)
4. **Approved (Ready to Send)** - Filter: Status = "Approved" AND Sent At is empty
5. **Recently Sent** - Filter: Status = "Sent" AND Sent At is within past 7 days
6. **By User** - Group by User field

---

## Table 3: Knowledge Chunks

Your coaching resources broken into retrievable chunks.

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| Title | Single line text | Brief descriptive title |
| Source | Single select | Options: Launch System, Ideas That Spread, [Book 3], Lecture 1, Lecture 2, ... Lecture 12, Custom |
| Stage | Multiple select | Options: Ideation, Early Validation, Late Validation, Growth |
| Topic | Multiple select | See topic list below |
| Content | Long text | The actual text chunk (500-1500 words) |
| Summary | Single line text | Brief 1-2 sentence description for matching |
| Usage Count | Number | Track how often this chunk is used |
| Last Used | Date | When this chunk was last referenced |

### Topic Options
- Ideation
- Validation
- Customer Research
- Problem Definition
- Pricing
- Business Model
- Revenue
- Sales
- Marketing
- Positioning
- Mindset
- Motivation
- Productivity
- Systems
- Processes
- Scaling
- Common Mistakes
- What Not To Do

### Views to Create
1. **All Chunks** - Grid view
2. **By Source** - Group by Source field
3. **By Stage** - Group by Stage field
4. **Ideation Stage** - Filter: Stage contains "Ideation"
5. **Early Validation** - Filter: Stage contains "Early Validation"
6. **Late Validation** - Filter: Stage contains "Late Validation"
7. **Growth Stage** - Filter: Stage contains "Growth"
8. **Most Used** - Sort by Usage Count (descending)

---

## Table 4: Model Responses

Example responses that define your coaching voice and style.

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| Title | Single line text | Brief description (e.g., "Stuck - Ideation") |
| Stage | Single select | Options: Ideation, Early Validation, Late Validation, Growth |
| Scenario | Single select | Options: Stuck/No Progress, Overwhelmed, Avoiding Hard Thing, Making Progress, Confused About Next Steps |
| User Example | Long text | Example of what a user might say |
| Ideal Response | Long text | Your ideal coaching response |
| Notes | Long text | Why this response works |
| Created | Created time | When created |

### Views to Create
1. **All Model Responses** - Grid view
2. **By Stage** - Group by Stage field
3. **Ideation** - Filter: Stage = "Ideation"
4. **Early Validation** - Filter: Stage = "Early Validation"
5. **Late Validation** - Filter: Stage = "Late Validation"
6. **Growth** - Filter: Stage = "Growth"

---

## Table 5: Corrected Responses

Learning data from your manual corrections.

| Field Name | Field Type | Configuration |
|------------|------------|---------------|
| Conversation | Link to another record | Link to Conversations table (optional) |
| Original User Message | Long text | What the user said |
| AI Response | Long text | What the AI generated |
| Corrected Response | Long text | What you wrote instead |
| Notes | Long text | Why the correction was needed |
| Correction Type | Single select | Options: Tone, Content, Length, Focus, Factual, Style |
| Created | Created time | For reference |

### Views to Create
1. **All Corrections** - Grid view sorted by Created (newest first)
2. **Recent (Last 30 Days)** - Filter: Created is within past 30 days
3. **By Type** - Group by Correction Type

---

## Relationships Diagram

```
Users (1) ─────< (Many) Conversations
                         │
                         └── Links to Corrected Responses (optional)

Knowledge Chunks (standalone - queried by Stage/Topic)

Model Responses (standalone - queried by Stage/Scenario)
```

---

## Setup Checklist

- [ ] Create new Airtable base named "Email Coaching System"
- [ ] Create Users table with all fields
- [ ] Create Conversations table with all fields
- [ ] Create Knowledge Chunks table with all fields
- [ ] Create Model Responses table with all fields
- [ ] Create Corrected Responses table with all fields
- [ ] Set up link between Conversations → Users
- [ ] Set up link between Corrected Responses → Conversations
- [ ] Create all views listed above
- [ ] Add sample data to test
- [ ] Generate API key for n8n integration

---

## API Integration Notes

### Getting Your API Key
1. Go to https://airtable.com/account
2. Generate a personal access token
3. Grant it access to your "Email Coaching System" base
4. Scopes needed: data.records:read, data.records:write

### Base ID
After creating your base, get the Base ID from the URL:
`https://airtable.com/[BASE_ID]/...`

### Table IDs
Each table has an ID that starts with "tbl". You can find these in the API documentation:
`https://airtable.com/[BASE_ID]/api/docs`

Store these in your n8n credentials:
- AIRTABLE_API_KEY
- AIRTABLE_BASE_ID
- USERS_TABLE_ID
- CONVERSATIONS_TABLE_ID
- KNOWLEDGE_TABLE_ID
- MODEL_RESPONSES_TABLE_ID
- CORRECTED_TABLE_ID
