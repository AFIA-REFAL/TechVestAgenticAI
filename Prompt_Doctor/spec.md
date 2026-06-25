Here’s the **complete, cleaned, production-ready `SPEC.md`** with the level-locking rule included properly:

```md id="spec_prompt_doctor"
# Prompt Doctor — Lab Spec (Day 2 Afternoon)

## Overview
Prompt Doctor is a Streamlit-based interactive lab where students learn prompt engineering by building a **prompt that evaluates other prompts**.

Instead of solving tasks directly, users design prompts that are graded by an AI Examiner.

The system uses a **five-level escalation ladder**, where each level enforces a new prompting technique.

---

## Core Concept

You are NOT building solutions.

You are building:
> A prompt that instructs an AI how to solve a task

Then another AI (the Examiner) evaluates how good your prompt is.

---

## Tech Stack

- Python 3.10+
- Streamlit (UI)
- OpenRouter API (LLM backend)
- No RAG
- No tools / agents
- Prompt-only system

---

## Project Structure

```

prompt_doctor/
├─ app.py          # Streamlit UI (provided; do not change layout)
├─ levels.py       # Level definitions + sample inputs (provided)
├─ runner.py       # Executes student prompt on sample input (provided)
├─ examiner.py     # YOU IMPLEMENT (core logic)
└─ .env            # OPENROUTER_API_KEY

````

---

## System Flow

1. User selects:
   - Domain (support, legal, healthcare, etc.)
   - Current unlocked level

2. UI displays:
   - Level task
   - Sample input

3. User writes a prompt

4. System runs:
   - `runner.py` → executes student prompt on sample input
   - `examiner.py` → evaluates the prompt

5. Examiner returns JSON verdict

6. UI updates:
   - ✓ / ✗ per principle
   - Live output preview
   - Pass / Revise decision

7. If passed:
   - Next level unlocks

---

## Level Unlocking Rule (IMPORTANT)

Users can ONLY access sequential levels.

### Rule:
- Level 1 is always unlocked
- Level N unlocks only after Level N-1 is passed

### Pass condition:

A level is passed ONLY if:

```python
verdict["verdict"] == "pass"
````

AND:

```python
all(p["pass"] for p in verdict["principles"])
```

### Progression:

* Fail → stay at same level
* Pass → unlock next level
* Level 5 is final

---

## Five-Level Ladder

### Level 1 — Basic

Focus:

* Role definition
* Clear instruction

Pass condition:

* Output is correct and on-task

---

### Level 2 — Structured Output

Focus:

* Strict output format (JSON/schema)
* Deterministic structure

Pass condition:

* Valid JSON output every time

---

### Level 3 — Few-shot Learning

Focus:

* Example-driven prompting
* Handling ambiguity

Pass condition:

* Model follows examples correctly in tricky cases

---

### Level 4 — Reasoning

Focus:

* Multi-step reasoning
* Complex decision tasks

Pass condition:

* Correct handling of edge cases with reasoning steps

---

### Level 5 — Robustness

Focus:

* Adversarial inputs
* Defensive constraints
* Input noise handling

Pass condition:

* Stable output under messy or misleading inputs

---

## Examiner System (Core Component)

The Examiner is itself a prompt-based evaluator.

### Responsibilities:

* Evaluate ONLY the given level’s principles
* Act as strict but fair grader
* Never rewrite or fix student prompts
* Return structured JSON only
* Quote exact weaknesses from student prompt
* Ask exactly ONE improvement question per failed principle

---

### Examiner Prompt Template

```text
You are the Examiner: a strict but fair prompt-engineering assessor.

Grade STUDENT_PROMPT for LEVEL {level}.

Judge ONLY these principles:
{principles_for_this_level}

Rules:
1. Be specific and use your own reasoning.
2. Quote exact weak phrases or missing constraints.
3. Ask ONE improvement question per failed principle.
4. NEVER rewrite or suggest a corrected prompt.
5. Think step by step internally, then output ONLY JSON.
```

---

## Examiner Output Schema

```json
{
  "level": 2,
  "principles": [
    {
      "name": "output_format",
      "pass": false,
      "weakness": "no schema provided; instruction is vague",
      "question": "What exact structure must the output follow every time?"
    }
  ],
  "ran_ok": true,
  "verdict": "revise"
}
```

---

## examiner.py Implementation Requirements

You must implement:

### 1. Prompt Builder

* Inject:

  * level
  * level principles
  * student prompt

### 2. OpenRouter API Call

* Use ONE stable judge model (important for consistency)

### 3. JSON Handling

* Parse examiner output safely
* Handle malformed JSON gracefully

### 4. Output Contract

Return:

* Parsed JSON verdict
* Pass/revise decision
* Structured results for UI rendering

---

## Constraints

* No RAG
* No tools or agents
* No function calling
* Prompt-only system
* Examiner must not generate solutions

---

## UI Requirements

Two-panel Streamlit layout:

### Left Panel

* Domain selector
* Level display
* Prompt editor

### Right Panel

* Examiner verdict
* Per-principle pass/fail
* Weakness quotes
* Live model output

---

## Success Criteria

A correct implementation:

* Enforces level unlocking strictly
* Produces stable JSON examiner outputs
* Blocks advancement until full pass
* Clearly separates:

  * diagnosis (examiner)
  * execution (runner)
* Never rewrites student prompts

---

## Learning Outcome

By the end of this lab, the student should understand:

* Prompt = system design, not text
* Structured outputs improve reliability
* Few-shot examples control ambiguity
* Reasoning improves multi-step tasks
* Robust prompts survive adversarial inputs
* LLM-as-judge is itself a prompt engineering problem

```
```
