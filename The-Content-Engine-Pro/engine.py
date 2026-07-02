"""
engine.py
All LLM call functions for Content Engine Pro.

Structure:
  - call_llm()              generic free LLM call (multi-model fallback chain, no key needed)
  - generate_suite()        BASE ENGINE: 5 calls (tagline, blog, social, image, video)
  - run_critique_loop()     === ADDITION 1: SELF-CRITIQUE LOOP ===
  - generate_voiceover_script()  === ADDITION 2: VOICEOVER (script half) ===
  - adapt_for_channel()     === ADDITION 3: MULTI-CHANNEL ADAPTATION ===
  - generate_image()        generates actual image from image_brief via Pollinations.ai (FREE)
  - generate_video_storyboard() generates HTML5 animated video storyboard from video_brief (FREE)

FREE LLM MODELS:
  All text generation uses free Hugging Face Inference API endpoints.
  No API keys required. Falls back through multiple models for reliability.
  
  Primary:   microsoft/Phi-3.5-mini-instruct  (best quality, free)
  Fallback:  HuggingFaceH4/zephyr-7b-beta     (original, reliable fallback)
  Final:     mistralai/Mistral-7B-Instruct-v0.3 (alternative fallback)
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

# ---------------------------------------------------------------------------
# FREE LLM — Hugging Face Inference API (no API key required)
# Uses multiple free, publicly hosted models with fallback for reliability.
# All models are free and require no payment or API key.
# ---------------------------------------------------------------------------

# Free models to try in order of preference (quality + reliability)
FREE_MODELS = [
    {
        "name": "Phi-3.5-mini-instruct",
        "url": "https://api-inference.huggingface.co/models/microsoft/Phi-3.5-mini-instruct",
        "format": "phi3",  # uses <|system|> / <|user|> / <|assistant|> template
    },
    {
        "name": "zephyr-7b-beta",
        "url": "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
        "format": "zephyr",  # uses <|system|> / <|user|> / <|assistant|> template
    },
    {
        "name": "Mistral-7B-Instruct",
        "url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
        "format": "mistral",  # uses [INST] template
    },
]

MAX_RETRIES = 2


def _format_prompt(system_prompt: str, user_prompt: str, model_format: str) -> str:
    """Format the prompt according to the model's expected chat template."""
    if model_format == "phi3":
        # Phi-3.5-mini-instruct chat template
        return f"""<|system|>
{system_prompt}<|end|>
<|user|>
{user_prompt}<|end|>
<|assistant|>"""
    elif model_format == "mistral":
        # Mistral-7B-Instruct chat template
        return f"""<s>[INST] {system_prompt}

{user_prompt} [/INST]"""
    else:
        # Zephyr / default chat template
        return f"""<|system|>
{system_prompt}</s>
<|user|>
{user_prompt}</s>
<|assistant|>"""


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
    """
    Free LLM call via Hugging Face Inference API with multi-model fallback.
    No API key required — uses free public endpoints.
    Tries models in order: Phi-3.5-mini -> Zephyr -> Mistral-7B.
    Returns the generated text or empty string on failure.
    """
    last_error = None
    
    for model in FREE_MODELS:
        prompt = _format_prompt(system_prompt, user_prompt, model["format"])
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": 512,
                "do_sample": True,
                "return_full_text": False,
            },
        }
        
        try:
            resp = requests.post(
                model["url"],
                json=payload,
                timeout=120,
                headers={"Content-Type": "application/json"},
            )
            
            if resp.status_code == 503:
                # Model is loading (cold start) — wait and retry once
                import time
                time.sleep(15)
                resp = requests.post(
                    model["url"],
                    json=payload,
                    timeout=120,
                    headers={"Content-Type": "application/json"},
                )
            
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "")
                if text.strip():
                    return text.strip()
            
            last_error = f"Empty response from {model['name']}"
            
        except requests.exceptions.RequestException as e:
            last_error = f"{model['name']} failed: {e}"
            st.warning(f"Free LLM model '{model['name']}' unavailable, trying next model...")
            continue
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            last_error = f"{model['name']} parse error: {e}"
            st.warning(f"Free LLM model '{model['name']}' parse error, trying next model...")
            continue
    
    # All models failed
    st.warning(f"All free LLM models unavailable. Last error: {last_error}")
    st.info("💡 Tip: Free Hugging Face Inference API models may be cold-starting. Wait a moment and try again, or check your internet connection.")
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
            return suite["social"]
    raise ValueError(f"Unknown asset: {asset_name}")


def run_critique_loop(suite: dict) -> tuple[dict, list[dict], dict]:
    """
    Runs the self-critique loop automatically before output is shown.
    Returns: (suite, history, still_failing)
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
# ...................................................................
def adapt_for_channel(suite: dict, channel: str) -> dict:
    """
    Rewrites tagline/blog/social for the target channel.
    Image and video briefs are NOT sent to the model — they pass through unchanged.
    """
    social_json = json.dumps(suite["social"])
    prompt = ADAPT_SYSTEM.format(
        channel=channel,
        tagline=suite["tagline"],
        blog=suite["blog"],
        social_json=social_json,
    )
    raw = call_llm(prompt, f"Target channel: {channel}", temperature=0.7)
    try:
        adapted = _extract_json(raw)
    except (json.JSONDecodeError, AttributeError):
        st.error("Channel adaptation returned unparseable output. Showing raw text.")
        adapted = {"tagline": raw, "blog": raw, "social": suite["social"]}

    adapted["image_brief"] = suite["image_brief"]
    adapted["video_brief"] = suite["video_brief"]
    return adapted


# ---------------------------------------------------------------------------
# === IMAGE GENERATION — FREE: Pollinations.ai (no API key) ===
# ---------------------------------------------------------------------------

def generate_image(image_brief: str) -> bytes | None:
    """
    Generates an actual image from the image_brief using Pollinations.ai.
    Completely free — no API key required, no credit costs, no LLM calls.
    Uses the image_brief text directly as the prompt.
    Returns: Raw image bytes (PNG) or None if generation failed.
    """
    import urllib.parse
    prompt_text = image_brief[:500]
    encoded_prompt = urllib.parse.quote(prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=-1"

    try:
        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()
        return img_resp.content
    except requests.exceptions.RequestException as e:
        st.warning(f"Image generation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# === VIDEO STORYBOARD GENERATION — FREE: animated HTML5 (no API calls) ===
# ---------------------------------------------------------------------------

def generate_video_storyboard(video_brief: str) -> str:
    """
    Generates an HTML5 animated video storyboard from the video_brief.
    Completely free — no API calls at all. Splits the brief into scenes
    automatically using sentence-based parsing.
    Returns: HTML string containing the animated storyboard.
    """
    sentences = re.split(r'(?<=[.!?])\s+', video_brief.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    scenes_list = []
    if len(sentences) >= 3:
        scenes_list.append({
            "shot": "Opening Hook",
            "description": sentences[0][:100],
            "duration_seconds": 5
        })
        for i, sent in enumerate(sentences[1:-1], 2):
            scenes_list.append({
                "shot": f"Scene {i}",
                "description": sent[:100],
                "duration_seconds": 4
            })
        scenes_list.append({
            "shot": "Call to Action",
            "description": sentences[-1][:100],
            "duration_seconds": 5
        })
    else:
        scenes_list = [{"shot": "Opening", "description": video_brief[:100], "duration_seconds": 5}]

    # Build HTML storyboard with fade animations
    scenes_html_parts = []
    for i, scene in enumerate(scenes_list):
        shot = scene.get("shot", f"Scene {i+1}")
        desc = scene.get("description", video_brief[:100])
        duration = scene.get("duration_seconds", 5)
        bg_hue = (i * 37) % 360

        scenes_html_parts.append(f"""
        <div class="storyboard-scene" id="scene-{i}" 
             style="animation-delay: {sum(scenes_list[j].get('duration_seconds', 5) for j in range(i))}s;
                    animation-duration: {duration}s;
                    background: linear-gradient(135deg, hsl({bg_hue}, 35%, 92%), hsl({(bg_hue + 30) % 360}, 30%, 85%));">
            <div class="scene-number">Scene {i+1}</div>
            <div class="scene-shot">{shot}</div>
            <div class="scene-description">{desc}</div>
            <div class="scene-timing">⏱ {duration}s</div>
            <div class="scene-indicator">
                <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#b8860b" stroke-width="1.5">
                    <polygon points="5,3 19,12 5,21" />
                </svg>
            </div>
        </div>
        """)

    total_duration = sum(s.get("duration_seconds", 5) for s in scenes_list)

    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    .storyboard-container {{
        font-family: 'Inter', -apple-system, sans-serif;
        background: #fbfaf7;
        border: 1px solid #e8e1d4;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 16px 40px rgba(36, 46, 62, 0.08);
    }}
    .storyboard-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.8rem 1.2rem;
        background: linear-gradient(135deg, #f5ebd3, #f0e4c8);
        border-bottom: 1px solid #e8e1d4;
    }}
    .storyboard-header h3 {{ font-size: 0.9rem; font-weight: 700; color: #9f7517; display: flex; align-items: center; gap: 0.5rem; }}
    .storyboard-header .playback-info {{ font-size: 0.75rem; color: #8a7a60; font-weight: 600; }}
    .storyboard-viewport {{ position: relative; width: 100%; height: 300px; overflow: hidden; background: #f4f1ea; }}
    .storyboard-scene {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 1.5rem; text-align: center; opacity: 0;
        animation: fadeInOut var(--duration, 5s) ease-in-out infinite; animation-fill-mode: both;
    }}
    @keyframes fadeInOut {{
        0% {{ opacity: 0; transform: scale(0.95); }}
        8% {{ opacity: 1; transform: scale(1); }}
        85% {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(1.05); }}
    }}
    .scene-number {{
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;
        color: #9f7517; background: rgba(255,255,255,0.7); padding: 0.2rem 0.7rem;
        border-radius: 999px; margin-bottom: 0.6rem; border: 1px solid rgba(184, 137, 36, 0.2);
    }}
    .scene-shot {{ font-size: 1.1rem; font-weight: 700; color: #27313f; margin-bottom: 0.5rem; }}
    .scene-description {{ font-size: 0.85rem; color: #5a6370; line-height: 1.6; max-width: 500px; margin: 0 auto; }}
    .scene-timing {{ font-size: 0.75rem; font-weight: 600; color: #8a7a60; margin-top: 0.6rem; background: rgba(255,255,255,0.6); padding: 0.2rem 0.6rem; border-radius: 999px; }}
    .scene-indicator {{ position: absolute; bottom: 0.8rem; right: 0.8rem; opacity: 0.5; }}
    .storyboard-timeline {{ display: flex; gap: 0.3rem; padding: 0.6rem 1rem; background: #ffffff; border-top: 1px solid #e8e1d4; }}
    .timeline-bar {{ flex: 1; height: 4px; border-radius: 999px; background: #e8e1d4; position: relative; overflow: hidden; }}
    .timeline-bar .fill {{
        position: absolute; top: 0; left: 0; height: 100%;
        background: linear-gradient(90deg, #b8860b, #9f7517); border-radius: 999px;
        animation: fillBar var(--scene-duration, 5s) ease-in-out infinite; animation-delay: var(--scene-delay, 0s);
    }}
    @keyframes fillBar {{ 0% {{ width: 0; }} 100% {{ width: 100%; }} }}
    .storyboard-controls {{
        display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 1rem;
        background: #ffffff; border-top: 1px solid #e8e1d4;
    }}
    .play-btn {{
        display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 1rem;
        background: linear-gradient(135deg, #b8860b, #9f7517); color: #fff; border: none;
        border-radius: 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer;
        transition: all 0.2s ease;
    }}
    .play-btn:hover {{ background: linear-gradient(135deg, #c5962e, #8a6a10); transform: translateY(-1px); }}
    .play-btn.pause {{ background: linear-gradient(135deg, #6f7a88, #5a6370); }}
    .play-btn svg {{ width: 16px; height: 16px; }}
</style>
</head>
<body>
<div class="storyboard-container">
    <div class="storyboard-header">
        <h3>🎬 Video Storyboard</h3>
        <span class="playback-info">{len(scenes_list)} scenes · {total_duration}s total</span>
    </div>
    <div class="storyboard-viewport" id="storyboard-viewport">
        {''.join(scenes_html_parts)}
    </div>
    <div class="storyboard-timeline">
        {''.join(
            f'<div class="timeline-bar" style="--scene-duration: {s.get("duration_seconds", 5)}s; --scene-delay: {sum(scenes_list[j].get("duration_seconds", 5) for j in range(i))}s;">'
            f'<div class="fill"></div></div>'
            for i, s in enumerate(scenes_list)
        )}
    </div>
    <div class="storyboard-controls">
        <button class="play-btn" id="play-btn" onclick="togglePlay()">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5,3 19,12 5,21" id="play-icon"/>
            </svg>
            <span id="play-text">Playing</span>
        </button>
        <span style="font-size:0.75rem;color:#8a7a60;">Auto-playing in sequence</span>
    </div>
</div>
<script>
    let isPlaying = true;
    const viewport = document.getElementById('storyboard-viewport');
    const scenes = viewport.querySelectorAll('.storyboard-scene');
    const playBtn = document.getElementById('play-btn');
    const playText = document.getElementById('play-text');
    const playIcon = document.getElementById('play-icon');
    function togglePlay() {{
        isPlaying = !isPlaying;
        scenes.forEach(s => {{ s.style.animationPlayState = isPlaying ? 'running' : 'paused'; }});
        document.querySelectorAll('.fill').forEach(f => {{ f.style.animationPlayState = isPlaying ? 'running' : 'paused'; }});
        if (isPlaying) {{
            playBtn.classList.remove('pause'); playText.textContent = 'Playing';
            playIcon.innerHTML = '<polygon points="5,3 19,12 5,21"/>';
        }} else {{
            playBtn.classList.add('pause'); playText.textContent = 'Paused';
            playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
        }}
    }}
</script>
</div>
</body>
</html>"""

    return html