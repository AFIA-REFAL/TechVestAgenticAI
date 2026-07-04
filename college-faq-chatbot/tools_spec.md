# BVRIT Chatbot — Tool Set Specification

## Overview

The current RAG chatbot answers questions strictly from the grounding document (BVRITH Knowledge Base). However, students frequently ask **three types of queries** that the document alone cannot answer correctly because they require **computation** or **real-time data** that isn't in the document. Below are the three queries, the tools designed to fix them, and the reasoning behind each tool's description specificity.

---

## Three Queries the Chatbot Currently Fails On

### 1. Fee Calculation Query

> *"What is the total fee for a CSE student including hostel charges for all 4 years? If I get a 25% scholarship based on my EAMCET rank, how much will I save?"*

**Why it fails:** The knowledge base explicitly states that the fee details page (`https://bvrithyderabad.edu.in/admission/fee-details/`) was **not scraped** (see `admission-004`). Even if fee data were available, the chatbot would need to:
- Multiply single-year tuition by 4 years
- Add hostel fee across 4 years
- Apply a scholarship percentage discount to the total
- None of this is retrievable from a static document — it requires computation.

---

### 2. Date/Deadline Comparison Query

> *"The EAMCET notification says applications close on 30th June. Is that deadline still open today? How many days are left?"*

**Why it fails:** The knowledge base may contain a date (e.g., "applications open after TSEAMCET releases its notification" in `admission-001`), but it has **no concept of "today"**. The chatbot cannot:
- Compare a document date against the current date
- Determine whether a deadline is past, upcoming, or today
- Compute the number of days remaining
- This requires real-time system clock access, not document retrieval.

---

### 3. Percentage / Rate Calculation Query

> *"The placement page says 4 students got offers of 44 LPA each. If the total number of placed students was 180, what percentage of students got the top package? Also, what is the average package if the total placement value is 8.2 crore?"*

**Why it fails:** The knowledge base stores raw numbers (e.g., "highest package of 44 lakhs per annum" in `placements-001`), but it cannot:
- Convert raw counts into percentages
- Divide total placement value by number of students
- Compute scholarship percentage from a rank-based discount tier
- This requires arithmetic computation, not document lookup.

---

## Tool Definitions

### Tool 1: `fee_calculator`

**Purpose:** Compute total fees across multiple years, apply scholarship discounts, and combine hostel + tuition combinations for BVRIT Hyderabad programs.

#### JSON Schema

```json
{
  "name": "fee_calculator",
  "description": "Compute total BVRIT Hyderabad fee amounts across multiple academic years, including tuition, hostel, and scholarship discounts. Use this when a student asks about total cost of a program, fee breakdown by year, hostel + tuition combined cost, or fee savings from a scholarship or EAMCET rank-based concession. Only call this for BVRIT-specific fee-related calculations — do NOT call this for general arithmetic or non-fee math problems.",
  "parameters": {
    "type": "object",
    "properties": {
      "annual_tuition_fee": {
        "type": "number",
        "description": "Annual tuition fee in INR for the specific BVRIT program (e.g., CSE, ECE, EEE, CSE-AIML). Extracted from the fee details section of the knowledge base."
      },
      "annual_hostel_fee": {
        "type": "number",
        "description": "Annual hostel accommodation fee in INR for BVRIT Hyderabad hostel. Set to 0 if the student is not asking about hostel."
      },
      "number_of_years": {
        "type": "integer",
        "description": "Duration of the program in years (4 for B.Tech, 2 for M.Tech at BVRIT)."
      },
      "scholarship_percentage": {
        "type": "number",
        "description": "Scholarship or concession percentage (0–100) applicable to the student. For example, 25 means 25% off the total fee. Set to 0 if no scholarship."
      }
    },
    "required": ["annual_tuition_fee", "number_of_years"]
  }
}
```

#### Why a Generic Description Would Fail

A generic description like **"do math"** or **"calculate fees"** would cause the model to call this tool for:
- Simple arithmetic it can do in-head (e.g., "What is 10+5?")
- Non-BVRIT fee computations (e.g., "Calculate the fee for Osmania University")
- Any math problem unrelated to BVRIT fee structures

**What the specific description fixes:** The description explicitly scopes the tool to **BVRIT-specific fee-related calculations** and lists exact use cases (total cost, fee breakdown, hostel + tuition, scholarship savings). It also includes a **negative constraint** ("do NOT call this for general arithmetic or non-fee math problems") that acts as a guardrail, preventing misuse.

---

### Tool 2: `date_checker`

**Purpose:** Compare a date from the BVRIT knowledge base (admission deadline, exam date, event date) against today's real-time date and return whether it is past, upcoming, or how many days remain.

#### JSON Schema

```json
{
  "name": "date_checker",
  "description": "Compare a BVRIT-related date (admission deadline, exam date, event date, application closing date) against today's date and report whether it is past, upcoming, or how many days remain. Use this when a student asks if a deadline is still open, how many days are left for an exam, or whether an event has already passed. Only call this for BVRIT-specific dates extracted from the knowledge base — do NOT call this for general date formatting, date-to-string conversion, or non-BVRIT date questions.",
  "parameters": {
    "type": "object",
    "properties": {
      "target_date": {
        "type": "string",
        "description": "The date to compare, in ISO 8601 format (YYYY-MM-DD). This is a BVRIT-specific date extracted from the knowledge base, such as an admission deadline, exam date, or event date."
      },
      "date_label": {
        "type": "string",
        "description": "A human-readable label for what this date represents, e.g., 'EAMCET application deadline', 'BVRIT admission form release', 'campus fest date'. This is included in the output for clarity."
      }
    },
    "required": ["target_date", "date_label"]
  }
}
```

#### Why a Generic Description Would Fail

A generic description like **"check dates"** or **"compare dates"** would cause the model to call this tool for:
- Any date mentioned in the document (e.g., "BVRIT was established in 2012" — no comparison needed)
- Non-BVRIT dates (e.g., "What is the date of Diwali?")
- Formatting tasks (e.g., "Convert 01-01-2024 to January 1, 2024")

**What the specific description fixes:** The description explicitly ties the tool to **BVRIT-specific dates** and lists concrete examples of when to use it (deadline checking, days remaining, event status). It also includes a **negative constraint** ("do NOT call this for general date formatting, date-to-string conversion, or non-BVRIT date questions") that prevents the model from invoking it for irrelevant date operations.

---

### Tool 3: `percentage_calculator`

**Purpose:** Compute scholarship percentages, placement rates, admission cutoff conversions, and other percentage-based calculations for BVRIT Hyderabad data.

#### JSON Schema

```json
{
  "name": "percentage_calculator",
  "description": "Compute percentage-based metrics from BVRIT Hyderabad data, such as placement rates (students placed ÷ total students), scholarship percentages (discount off total fee), admission cutoff conversion (raw marks converted to percentage), or any other rate calculation derived from the BVRIT knowledge base. Use this when a student asks about placement percentage, scholarship rate, cutoff percentage, or any proportion/rate based on BVRIT numbers. Only call this for BVRIT-specific percentage calculations — do NOT call this for simple percentage-of-a-number problems (e.g., 'what is 10% of 200') that the LLM can compute in-head, or for non-BVRIT percentage calculations.",
  "parameters": {
    "type": "object",
    "properties": {
      "numerator": {
        "type": "number",
        "description": "The part value — e.g., number of students placed, scholarship discount amount, or marks obtained. Must be a non-negative number extracted from the BVRIT knowledge base."
      },
      "denominator": {
        "type": "number",
        "description": "The total or whole value — e.g., total number of students, total fee amount, or maximum marks. Must be a positive number extracted from the BVRIT knowledge base."
      },
      "calculation_context": {
        "type": "string",
        "description": "A brief description of what this percentage represents in the BVRIT context, e.g., 'placement rate for 2024 batch', 'scholarship discount on CSE tuition', 'EAMCET cutoff conversion'. This is included in the output for clarity."
      }
    },
    "required": ["numerator", "denominator", "calculation_context"]
  }
}
```

#### Why a Generic Description Would Fail

A generic description like **"calculate percentages"** would cause the model to call this tool for:
- Simple percentage questions the LLM can answer from its own knowledge (e.g., "What is 15% of 80?")
- Overlap with `fee_calculator` (e.g., "Calculate 25% scholarship on fees" — both tools could claim it)
- Non-BVRIT percentages (e.g., "What percentage of Indians are engineers?")

**What the specific description fixes:** The description:
1. **Distinguishes this from `fee_calculator`** by explicitly stating it handles **rates and proportions** (placement rates, cutoff conversions) while `fee_calculator` handles **multi-year fee totals and scholarship discounts**. The `fee_calculator` takes `scholarship_percentage` as an input, so the model should use `fee_calculator` for scholarship-on-fee questions and `percentage_calculator` for standalone rate questions.
2. Includes a **negative constraint** ("do NOT call this for simple percentage-of-a-number problems... or for non-BVRIT percentage calculations") that prevents misuse.
3. Requires a `calculation_context` parameter, which forces the model to articulate *why* this BVRIT-specific calculation is needed, reducing false positives.

---

## Guardrail Summary

| Tool | Generic Description Problem | Specific Description Fix |
|------|---------------------------|------------------------|
| `fee_calculator` | Called for any math problem or non-BVRIT fee | Scoped to BVRIT fee calculations with explicit negative constraint |
| `date_checker` | Called for any date mention in text or formatting tasks | Tied to BVRIT dates only, with real-time comparison as the exclusive purpose |
| `percentage_calculator` | Overlaps with `fee_calculator`, called for trivial percentages | Distinguished from `fee_calculator` via use cases, requires `calculation_context` parameter |

---

## Integration Note

These tools are intended to be registered as **LLM-callable functions** (e.g., OpenAI function calling, LangChain tool definitions) in the `RAGPipeline.answer()` method. When the grounding prompt detects a query involving computation or real-time data, the LLM should invoke the appropriate tool rather than attempting to answer from the document alone. The tool's output is then incorporated into the final answer.

No existing code has been modified — this specification defines the tool set for future implementation.