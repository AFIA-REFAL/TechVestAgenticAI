"""
engine.py
All LLM call functions for Content Engine Pro, via OpenRouter.

Structure:
  - call_llm()              generic OpenRouter call helper
  - generate_suite()        BASE ENGINE: 5 calls (tagline, blog, social, image, video)
  - run_critique_loop()     === ADDITION 1: SELF-CRITIQUE LOOP ===
  - generate_voiceover_script()  === ADDITION 2: VOICEOVER (script half) ===
  - adapt_for_channel()     === ADDITION 3: MULTI-CHANNEL ADAPTATION ===
"""

import json
import re
import requests
import streamlit as st

from prompts import (
    TAGLINE_SYSTEM, BLOG_SYSTEM, SOCIAL_SYSTEM,
    IMAGE_BRIEF_SYSTEM, VIDEO_BRIEF_SYSTEM,
    CRITIC_SYSTEM, REGENERATE_PREFIX,
    SCRIPT_ADAPTER, ADAPT_SYSTEM,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # swap here for any OpenRouter model id
MAX_RETRIES = 2  # per spec: "Max 2 retries"


def _api_key() -> str:
    key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not key:
        st.error(
            "Missing OPENROUTER_API_KEY. Add it to `.streamlit/secrets.toml` "
            "(see `.streamlit/secrets.toml.example`)."
        )
        st.stop()
    return key


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
    """Generic single-turn chat completion call to OpenRouter."""
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Content Engine Pro",
    }
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {e}")
        return ""
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        st.error(f"Unexpected API response shape: {e}")
        return ""


def _extract_json(raw: str) -> dict:
    """Strip markdown fences / stray text and parse JSON robustly."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# BASE ENGINE — 5 calls
# ---------------------------------------------------------------------------

def _brief_user_prompt(product_name: str, audience: str, tone: str) -> str:
    return f"Product: {product_name}\nAudience: {audience}\nTone: {tone}"


def generate_suite(product_name: str, audience: str, tone: str) -> dict:
    """Runs all 5 base generation calls and returns the suite dict."""
    brief = _brief_user_prompt(product_name, audience, tone)

    tagline = call_llm(TAGLINE_SYSTEM, brief)
    blog = call_llm(BLOG_SYSTEM, brief)

    social_raw = call_llm(SOCIAL_SYSTEM, brief)
    try:
        social = _extract_json(social_raw)
    except (json.JSONDecodeError, AttributeError):
        social = {"instagram": social_raw, "twitter": social_raw, "linkedin": social_raw}

    image_brief = call_llm(IMAGE_BRIEF_SYSTEM, brief)
    video_brief = call_llm(VIDEO_BRIEF_SYSTEM, brief)

    return {
        "product_name": product_name,
        "audience": audience,
        "tone": tone,
        "tagline": tagline,
        "blog": blog,
        "social": social,
        "image_brief": image_brief,
        "video_brief": video_brief,
    }


# ---------------------------------------------------------------------------
# === ADDITION 1: SELF-CRITIQUE LOOP ===
# ---------------------------------------------------------------------------

def _critique(suite: dict) -> dict:
    """One critic pass. Returns verdict dict per CRITIC_SYSTEM contract."""
    payload = (
        f"Brief — Product: {suite['product_name']}, "
        f"Audience: {suite['audience']}, Tone: {suite['tone']}\n\n"
        f"Tagline: {suite['tagline']}\n\n"
        f"Blog: {suite['blog']}\n\n"
        f"Social: {json.dumps(suite['social'])}"
    )
    raw = call_llm(CRITIC_SYSTEM, payload, temperature=0.3)
    try:
        return _extract_json(raw)
    except (json.JSONDecodeError, AttributeError):
        # If the critic itself misbehaves, treat as pass-all rather than
        # blocking the user indefinitely — but surface a warning.
        st.warning("Critic returned unparseable output; skipping critique for this pass.")
        return {
            "tagline": {"pass": True, "issue": None},
            "blog": {"pass": True, "issue": None},
            "social": {"pass": True, "issue": None},
        }


def _regenerate_asset(asset_name: str, suite: dict, issue: str):
    """Regenerate ONE failed asset with the critic's feedback injected."""
    brief = _brief_user_prompt(suite["product_name"], suite["audience"], suite["tone"])
    feedback = REGENERATE_PREFIX.format(issue=issue) + brief

    if asset_name == "tagline":
        return call_llm(TAGLINE_SYSTEM, feedback)
    if asset_name == "blog":
        return call_llm(BLOG_SYSTEM, feedback)
    if asset_name == "social":
        raw = call_llm(SOCIAL_SYSTEM, feedback)
        try:
            return _extract_json(raw)
        except (json.JSONDecodeError, AttributeError):
            return suite["social"]  # fall back to previous on parse failure
    raise ValueError(f"Unknown asset: {asset_name}")


def run_critique_loop(suite: dict) -> tuple[dict, list[dict], dict]:
    """
    Runs the self-critique loop automatically before output is shown.

    Returns:
        suite (dict)        — possibly-regenerated suite
        history (list)      — one verdict dict per attempt (for display/logging)
        still_failing (dict)— {asset_name: issue} for anything failing after MAX_RETRIES
    """
    history = []
    attempt = 0
    current = dict(suite)

    while attempt <= MAX_RETRIES:
        verdict = _critique(current)
        history.append(verdict)

        failing = {k: v["issue"] for k, v in verdict.items() if not v.get("pass", True)}

        if not failing:
            return current, history, {}

        if attempt == MAX_RETRIES:
            # Out of retries — return last attempt with a warning flag.
            return current, history, failing

        for asset_name, issue in failing.items():
            current[asset_name] = _regenerate_asset(asset_name, current, issue or "quality issue")

        attempt += 1

    return current, history, {}


# ---------------------------------------------------------------------------
# === ADDITION 2: VOICEOVER GENERATION (script half — see tts.py for audio) ===
# ---------------------------------------------------------------------------

def generate_voiceover_script(blog_intro: str) -> str:
    """Adapts the blog intro into a TTS-ready voiceover script."""
    return call_llm(SCRIPT_ADAPTER, blog_intro, temperature=0.5)


# ---------------------------------------------------------------------------
# === ADDITION 3: MULTI-CHANNEL ADAPTATION ===
# ---------------------------------------------------------------------------

def adapt_for_channel(suite: dict, channel: str) -> dict:
    """
    Rewrites tagline/blog/social for the target channel.
    Image and video briefs are NOT sent to the model — they pass through
    unchanged, per spec ("Image and video stay unchanged").
    """
    social_json = json.dumps(suite["social"])
    prompt = ADAPT_SYSTEM.format(
        channel=channel,
        tagline=suite["tagline"],
        blog=suite["blog"],
        social_json=social_json,
    )
    # ADAPT_SYSTEM already contains the full instruction; use it directly
    # as both system and user content isn't necessary — call as system
    # prompt with a minimal user nudge.
    raw = call_llm(prompt, f"Target channel: {channel}", temperature=0.7)
    try:
        adapted = _extract_json(raw)
    except (json.JSONDecodeError, AttributeError):
        st.error("Channel adaptation returned unparseable output. Showing raw text.")
        adapted = {"tagline": raw, "blog": raw, "social": suite["social"]}

    # Pass through visuals untouched
    adapted["image_brief"] = suite["image_brief"]
    adapted["video_brief"] = suite["video_brief"]
    return adapted