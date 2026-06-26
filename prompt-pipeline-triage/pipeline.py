"""
pipeline.py
The Prompt Pipeline -- Support Ticket Triage.

Core mechanics:
  call_llm()      -- one HTTP call to OpenRouter's OpenAI-compatible endpoint
  parse_json()    -- parses a model's raw text into a dict, with a single
                      re-ask retry if the JSON is malformed
  stage1..stage4  -- the four pipeline stages
  run()           -- chains the stages and returns a full, inspectable trace
"""

import os
import json
import re
import requests

from prompts import (
    STAGE1_SYSTEM, STAGE1_PROMPT,
    STAGE2_SYSTEM, STAGE2_PROMPT,
    STAGE3_SYSTEM, STAGE3_PROMPT, STAGE3_REDO_SUFFIX,
    STAGE4_SYSTEM, STAGE4_PROMPT,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = "openai/gpt-4o-mini"


class PipelineError(Exception):
    """Raised when a stage cannot recover a valid JSON response after retrying."""
    def __init__(self, stage_name: str, raw_output: str, parse_error: str):
        self.stage_name = stage_name
        self.raw_output = raw_output
        self.parse_error = parse_error
        super().__init__(f"[{stage_name}] failed to produce valid JSON: {parse_error}")


# ---------------------------------------------------------------------------
# call_llm -- one OpenRouter call
# ---------------------------------------------------------------------------

def call_llm(prompt: str, system: str | None = None, model: str = DEFAULT_MODEL,
             temperature: float = 0.3) -> str:
    """
    Single call to OpenRouter's OpenAI-compatible /chat/completions endpoint.
    Returns the raw text content of the model's reply.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file "
            "or environment variables before running the pipeline."
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# parse_json -- strip fences, parse, retry once on failure
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Removes ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def parse_json(raw_text: str, stage_name: str, retry_prompt_fn=None,
                system: str | None = None, model: str = DEFAULT_MODEL) -> dict:
    """
    Attempts to parse raw_text as JSON.

    On failure, if retry_prompt_fn is provided, it is called with the broken
    raw_text and the parse error message to build a follow-up prompt that is
    sent back to the model ONCE. If that also fails, raises PipelineError.

    retry_prompt_fn: Callable[[str, str], str] -> (broken_output, error_msg) -> new_prompt
    """
    cleaned = _strip_code_fences(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        first_error = str(e)

    if retry_prompt_fn is None:
        raise PipelineError(stage_name, raw_text, first_error)

    # Single retry: show the model its own broken output + the error, ask again.
    retry_prompt = retry_prompt_fn(raw_text, first_error)
    retry_raw = call_llm(retry_prompt, system=system, model=model)
    retry_cleaned = _strip_code_fences(retry_raw)

    try:
        return json.loads(retry_cleaned)
    except json.JSONDecodeError as e2:
        raise PipelineError(stage_name, retry_raw, str(e2))


def _default_retry_prompt(broken_output: str, error_msg: str) -> str:
    return f"""Your previous response could not be parsed as JSON.

YOUR PREVIOUS RESPONSE:
{broken_output}

PARSE ERROR:
{error_msg}

Return ONLY a single valid JSON object that fixes this. No markdown fences,
no explanation, no text before or after the JSON."""


# ---------------------------------------------------------------------------
# Stage functions
# ---------------------------------------------------------------------------

def stage1_understand(raw_text: str, model: str = DEFAULT_MODEL) -> dict:
    prompt = STAGE1_PROMPT.format(raw_text=raw_text)
    raw_output = call_llm(prompt, system=STAGE1_SYSTEM, model=model)
    return parse_json(
        raw_output, "Stage 1 (Understand)",
        retry_prompt_fn=lambda out, err: _default_retry_prompt(out, err),
        system=STAGE1_SYSTEM, model=model,
    )


def stage2_reason(brief: dict, model: str = DEFAULT_MODEL) -> dict:
    prompt = STAGE2_PROMPT.format(brief_json=json.dumps(brief, indent=2))
    raw_output = call_llm(prompt, system=STAGE2_SYSTEM, model=model)
    return parse_json(
        raw_output, "Stage 2 (Reason)",
        retry_prompt_fn=lambda out, err: _default_retry_prompt(out, err),
        system=STAGE2_SYSTEM, model=model,
    )


def stage3_produce(brief: dict, decision: dict, model: str = DEFAULT_MODEL,
                    redo_issues: list[str] | None = None) -> dict:
    prompt = STAGE3_PROMPT.format(
        brief_json=json.dumps(brief, indent=2),
        decision_json=json.dumps(decision, indent=2),
    )
    if redo_issues:
        issues_list = "\n".join(f"- {issue}" for issue in redo_issues)
        prompt += STAGE3_REDO_SUFFIX.format(issues_list=issues_list)

    raw_output = call_llm(prompt, system=STAGE3_SYSTEM, model=model)
    return parse_json(
        raw_output, "Stage 3 (Produce)",
        retry_prompt_fn=lambda out, err: _default_retry_prompt(out, err),
        system=STAGE3_SYSTEM, model=model,
    )


def stage4_critique(brief: dict, decision: dict, draft: dict,
                     model: str = DEFAULT_MODEL) -> dict:
    prompt = STAGE4_PROMPT.format(
        brief_json=json.dumps(brief, indent=2),
        decision_json=json.dumps(decision, indent=2),
        draft_json=json.dumps(draft, indent=2),
    )
    raw_output = call_llm(prompt, system=STAGE4_SYSTEM, model=model)
    return parse_json(
        raw_output, "Stage 4 (Critique)",
        retry_prompt_fn=lambda out, err: _default_retry_prompt(out, err),
        system=STAGE4_SYSTEM, model=model,
    )


# ---------------------------------------------------------------------------
# run -- chains all stages, returns a full inspectable trace
# ---------------------------------------------------------------------------

def run(raw_text: str, use_critique: bool = False, model: str = DEFAULT_MODEL) -> dict:
    """
    Runs the full pipeline on one input.

    Returns a dict with every stage's input/output so the UI (or a test
    script) can render the complete trace end to end:

    {
      "input": str,
      "stage1": dict,
      "stage2": dict,
      "stage3": dict,
      "stage4": dict | None,
      "redo_triggered": bool,
      "final_reply": str,
    }

    Raises PipelineError if any stage exhausts its retry budget.
    """
    trace = {
        "input": raw_text,
        "stage1": None,
        "stage2": None,
        "stage3": None,
        "stage4": None,
        "redo_triggered": False,
        "final_reply": None,
    }

    brief = stage1_understand(raw_text, model=model)
    trace["stage1"] = brief

    decision = stage2_reason(brief, model=model)
    trace["stage2"] = decision

    draft = stage3_produce(brief, decision, model=model)
    trace["stage3"] = draft

    if use_critique:
        critique = stage4_critique(brief, decision, draft, model=model)
        trace["stage4"] = critique

        if critique.get("should_redo") and critique.get("issues"):
            # Single retry guard: redo Stage 3 exactly once with the feedback.
            draft = stage3_produce(
                brief, decision, model=model, redo_issues=critique["issues"]
            )
            trace["stage3"] = draft
            trace["redo_triggered"] = True

    trace["final_reply"] = draft.get("reply_text", "")
    return trace
