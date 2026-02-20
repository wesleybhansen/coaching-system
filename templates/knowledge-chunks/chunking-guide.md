# Knowledge Base Chunking Guide

## Overview

This guide explains how to break down your coaching resources (books, lectures, etc.) into retrievable chunks for the AI system.

---

## Chunking Principles

### Ideal Chunk Size
- **Target:** 500-1500 words per chunk
- **Too small:** Lacks context, AI can't understand the full concept
- **Too large:** Dilutes relevance, uses too many tokens

### What Makes a Good Chunk
1. **Self-contained:** Can be understood without reading surrounding content
2. **Actionable:** Contains advice, frameworks, or examples the AI can reference
3. **Specific:** Addresses a clear topic or scenario
4. **Referenceable:** Easy to cite ("See Chapter 4" or "Lecture 7 covers this")

---

## Chunking Process

### Step 1: Inventory Your Resources

List all resources to chunk:
- [ ] Launch System (book)
- [ ] Ideas That Spread (book)
- [ ] [Book 3] (if applicable)
- [ ] Lecture 1: [Topic]
- [ ] Lecture 2: [Topic]
- [ ] ... continue for all lectures

### Step 2: Identify Natural Break Points

**For Books:**
- Chapter boundaries
- Major section headings
- Distinct frameworks or models
- Case studies or examples
- Key concept explanations

**For Lectures:**
- Topic transitions
- Individual frameworks explained
- Exercise instructions
- Q&A sections worth preserving

### Step 3: Tag Each Chunk

For every chunk, assign:

1. **Source:** Where it comes from (Launch System, Lecture 5, etc.)

2. **Stage(s):** Which stages it applies to
   - Ideation
   - Early Validation
   - Late Validation
   - Growth
   - (Can be multiple)

3. **Topic(s):** What it covers
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

4. **Summary:** 1-2 sentence description for quick reference

---

## Example Chunks

### Example 1: Book Chapter Chunk

**Title:** Customer Interviews - Getting Past Surface Answers

**Source:** Launch System

**Stage:** Early Validation

**Topics:** Customer Research, Validation

**Summary:** Framework for conducting customer interviews that uncover real problems rather than polite agreement.

**Content:**
```
[Paste the actual content here - 500-1500 words covering the customer interview framework, including specific questions to ask, what to listen for, and common mistakes]
```

---

### Example 2: Lecture Segment Chunk

**Title:** The Validation Hierarchy

**Source:** Lecture 4

**Stage:** Early Validation, Late Validation

**Topics:** Validation, Business Model

**Summary:** The three levels of validation (problem, solution, willingness to pay) and how to progress through them.

**Content:**
```
[Paste the lecture content explaining the validation hierarchy - when to move from problem validation to solution validation to payment validation]
```

---

### Example 3: Mindset Chunk

**Title:** Why Smart People Avoid Validation

**Source:** Ideas That Spread

**Stage:** Ideation, Early Validation

**Topics:** Mindset, Validation, Common Mistakes

**Summary:** The psychological reasons entrepreneurs skip validation and build in isolation, plus how to overcome them.

**Content:**
```
[Paste content about the fear of rejection, desire to perfect before showing, and strategies for overcoming these tendencies]
```

---

## Chunking Checklist

For each resource:

- [ ] Read/review the entire resource
- [ ] Mark natural break points
- [ ] Create chunk for each section
- [ ] Assign source tag
- [ ] Assign stage tag(s)
- [ ] Assign topic tag(s)
- [ ] Write summary
- [ ] Copy content
- [ ] Add to Airtable Knowledge Chunks table

---

## CSV Import Format

You can bulk import chunks using this CSV format:

```csv
Title,Source,Stage,Topic,Content,Summary
"Customer Interviews Basics","Launch System","Early Validation","Customer Research,Validation","[Full content here]","How to conduct effective customer interviews"
```

**Note:** For multi-select fields (Stage, Topic), separate values with commas within the cell.

---

## Quality Checks

Before importing, verify each chunk:

1. **Standalone Test:** Can someone understand this without context?
2. **Actionable Test:** Does this give specific guidance?
3. **Length Check:** Is it 500-1500 words?
4. **Tag Accuracy:** Are the stage and topic tags correct?
5. **Citation Test:** Can the AI say "See [Source]" and it makes sense?

---

## Maintenance

### Adding New Content
- Follow the same chunking process
- Tag consistently with existing chunks
- Update chunks if source material changes

### Tracking Usage
- Usage count is updated when a chunk is referenced during response generation
- Review low-usage chunks - they may need better tagging
- Review high-usage chunks - consider if they're too broad

### Refining Over Time
- If AI responses cite irrelevant chunks, review the tags
- If AI misses relevant content, chunk may need different tags
- If responses lack depth, chunks may be too short
