"""
prompt_doctor/examiner.py

Calls an LLM (via OpenRouter) to grade a student's system prompt against
the principles defined for the current level, and normalizes whatever
shape the LLM hands back into a guaranteed-safe structure:

    {
        "verdict": "pass" | "revise",
        "principles": [
            {"name": str, "pass": bool, "weakness": str, "question": str},
            ...
        ]
    }

or, on failure:

    {"error": "<message>"}

The original bug ('list' object has no attribute 'get') happened because
code assumed every principle entry coming back from the LLM (or being
looked up from LEVELS[level]["principles"]) was either a str or a dict.
LLMs don't always respect that contract -- they can nest a list inside
a field, or return principles as a bare list of strings, etc. Every
lookup below is now defensive: nothing calls .get() on a value without
first confirming it's actually a dict.
"""

import os
import json
import requests
from dotenv import load_dotenv
from levels import LEVELS

load_dotenv()

EXAMINER_SYSTEM = """
You are a strict prompt engineering examiner.

Grade STUDENT_PROMPT for Level {level}.

Principles to evaluate:
{principles}

Rules:
- Evaluate ONLY the listed principles
- Never rewrite the prompt
- For each failure give a weakness + ONE question
- Output ONLY valid JSON in this exact shape, no extra text:
{{
  "verdict": "pass" or "revise",
  "principles": [
    {{
      "name": "exact principle name from the list",
      "pass": true or false,
      "weakness": "only include if failed",
      "question": "only include if failed"
    }}
  ]
}}
"""


def clean_json(text: str) -> str:
    """Strip markdown code fences from an LLM response, if present."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
    return text.strip()


def _principle_name_at(principles, i, fallback=None):
    """
    Safely resolve a display name for principles[i] from the ORIGINAL
    level config (levels.py), which may contain entries that are str,
    dict, or (in malformed configs) something else entirely.

    Never raises -- always returns a string.
    """
    if i < 0 or i >= len(principles):
        return fallback if fallback else f"Principle {i + 1}"

    ref = principles[i]

    if isinstance(ref, str):
        return ref
    if isinstance(ref, dict):
        name = ref.get("name")
        if isinstance(name, str) and name.strip():
            return name
        return fallback if fallback else f"Principle {i + 1}"

    # Anything else (list, int, None, ...) -- never call .get() on it.
    return fallback if fallback else f"Principle {i + 1}"


def _coerce_str(value, default=""):
    """Best-effort conversion of any value to a plain string for display."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        # Join nested list content instead of letting it leak into the UI
        # as a Python repr or crashing a downstream .get() call.
        return "; ".join(_coerce_str(v) for v in value if v is not None)
    if isinstance(value, dict):
        # Pull a sensible field if present, else stringify.
        for key in ("text", "value", "name", "message"):
            if key in value and isinstance(value[key], str):
                return value[key]
        return json.dumps(value)
    return str(value)


def _normalize_principle_entry(entry, index, principles):
    """
    Given ONE entry from the LLM's returned "principles" list (which may be
    a dict, a string, a list, or anything else), return a guaranteed-safe
    dict: {"name": str, "pass": bool, "weakness": str, "question": str}.

    This function never calls .get() on anything that isn't confirmed to
    be a dict first -- this is the fix for the original crash.
    """
    fallback_name = _principle_name_at(principles, index)

    if isinstance(entry, dict):
        name = entry.get("name")
        name = name if isinstance(name, str) and name.strip() else fallback_name

        passed = entry.get("pass", False)
        if not isinstance(passed, bool):
            # Be tolerant of "true"/"false" strings or 0/1 from a sloppy LLM.
            passed = str(passed).strip().lower() in ("true", "1", "yes")

        weakness = _coerce_str(entry.get("weakness", ""))
        question = _coerce_str(entry.get("question", ""))

        return {
            "name": name,
            "pass": passed,
            "weakness": weakness,
            "question": question,
        }

    if isinstance(entry, str):
        # LLM just returned a bare string for this principle -- treat as a
        # failure note rather than crashing.
        return {
            "name": fallback_name,
            "pass": False,
            "weakness": entry,
            "question": "Can you address this principle explicitly in your prompt?",
        }

    if isinstance(entry, list):
        # Defensive case that caused the original bug: an entry that is
        # itself a list (e.g. the LLM nested fields oddly). Flatten it to
        # a readable weakness string instead of indexing/`.get()`-ing it.
        return {
            "name": fallback_name,
            "pass": False,
            "weakness": _coerce_str(entry) or "Could not evaluate this principle.",
            "question": "Can you address this principle explicitly in your prompt?",
        }

    # Anything else (None, int, bool, ...).
    return {
        "name": fallback_name,
        "pass": False,
        "weakness": "Could not evaluate this principle.",
        "question": "Can you address this principle explicitly in your prompt?",
    }


def _extract_raw_principles(parsed):
    """
    Pull a list out of whatever top-level JSON shape the LLM returned.
    Handles: a bare list, a dict with "principles", or a dict with the
    list nested one level deeper under some other common key.
    """
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        candidate = parsed.get("principles", [])
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            # Some models return {"principles": {"0": {...}, "1": {...}}}
            return list(candidate.values())
        return []

    return []


def _extract_verdict(parsed, normalized_principles):
    """
    Safely resolve the verdict string. Falls back to computing it from
    the normalized principles if the LLM omitted or malformed it.
    """
    verdict = None
    if isinstance(parsed, dict):
        raw_verdict = parsed.get("verdict")
        if isinstance(raw_verdict, str):
            verdict = raw_verdict.strip().lower()

    if verdict in ("pass", "revise"):
        return verdict

    all_pass = all(p.get("pass", False) for p in normalized_principles)
    return "pass" if all_pass else "revise"


def assess(level, student_prompt, llm_output):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {"error": "Missing API key"}

    if level not in LEVELS:
        return {"error": f"Level {level} not found in configuration"}

    principles = LEVELS[level].get("principles", [])
    if not isinstance(principles, list):
        principles = []

    # Build principles text for the prompt sent to the grading LLM.
    principles_text = ""
    for i, p in enumerate(principles):
        if isinstance(p, dict):
            name = p.get("name", f"Principle {i + 1}")
            desc = p.get("description", "")
            principles_text += f"{i + 1}. {name}: {desc}\n"
        elif isinstance(p, str):
            principles_text += f"{i + 1}. {p}\n"
        else:
            # Malformed config entry (e.g. accidentally a list/int) --
            # don't crash, just show something reasonable.
            principles_text += f"{i + 1}. Principle {i + 1}\n"

    prompt = EXAMINER_SYSTEM.format(
        level=level,
        principles=principles_text
    )

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"STUDENT_PROMPT:\n{student_prompt}\n\nOUTPUT:\n{llm_output}"}
        ],
        "temperature": 0.2,
        "max_tokens": 800,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://localhost:3000"),
        "X-Title": "Prompt Examiner"
    }

    raw = ""

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

        if res.status_code != 200:
            return {"error": f"API Error (Status {res.status_code}): {res.text}"}

        response_data = res.json()

        if isinstance(response_data, dict) and "error" in response_data:
            err = response_data["error"]
            return {"error": _coerce_str(err, default="Unknown API error")}

        try:
            raw = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return {"error": "Unexpected API response shape (no message content found)", "raw_response": json.dumps(response_data)[:2000]}

        parsed = json.loads(clean_json(raw))

        raw_principles = _extract_raw_principles(parsed)

        normalized = [
            _normalize_principle_entry(entry, i, principles)
            for i, entry in enumerate(raw_principles)
        ]

        # If the LLM returned fewer principles than the level defines,
        # pad with explicit failures so the student still sees every
        # principle they're being graded on instead of a silently
        # incomplete list.
        if len(normalized) < len(principles):
            for i in range(len(normalized), len(principles)):
                normalized.append({
                    "name": _principle_name_at(principles, i),
                    "pass": False,
                    "weakness": "Examiner did not return a result for this principle.",
                    "question": "Try resubmitting your prompt.",
                })

        verdict = _extract_verdict(parsed, normalized)

        return {
            "verdict": verdict,
            "principles": normalized,
        }

    except json.JSONDecodeError as je:
        return {"error": f"Failed to parse LLM response as JSON: {str(je)}", "raw_response": raw}
    except requests.exceptions.RequestException as re_err:
        return {"error": f"Network error while contacting examiner: {str(re_err)}"}
    except Exception as e:
        return {"error": str(e)}