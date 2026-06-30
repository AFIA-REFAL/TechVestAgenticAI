"""
app.py
Content Engine Pro — Streamlit UI + orchestration.

Pipeline: generate suite (5 calls) -> self-critique loop (Addition 1)
          -> voiceover (Addition 2) -> channel adaptation (Addition 3)

Run with:  streamlit run app.py
"""

import streamlit as st

from engine import (
    generate_suite, run_critique_loop,
    generate_voiceover_script, adapt_for_channel,
)
from tts import synthesize_voiceover
from validators import validate_inputs
from prompts import CHANNEL_OPTIONS

st.set_page_config(
    page_title="Content Engine Pro",
    page_icon="🛠️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Light, pale styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }
    .stApp { background-color: #faf9f6; }
    h1, h2, h3 { letter-spacing: -0.01em; color: #2d2a26; }
    p, span, label { color: #3d3a36; }

    .asset-card {
        background: #ffffff;
        border: 1px solid #e8e4dc;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        color: #3d3a36;
        line-height: 1.5;
    }
    .asset-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #a8a095;
        margin-bottom: 0.4rem;
    }
    .pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.18rem 0.65rem;
        border-radius: 999px;
        margin-left: 0.4rem;
    }
    .pill-pass { background: #e3f2e6; color: #2e7d4f; }
    .pill-fail { background: #fce8e6; color: #c0392b; }
    .pill-warn { background: #fdf2dd; color: #b8860b; }

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button {
        background-color: #f5f0e8 !important;
        color: #5a5347 !important;
        border: 1px solid #ddd5c5 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #ede5d5 !important;
        border: 1px solid #cfc4ac !important;
        color: #4a4439 !important;
    }
    .stButton > button p, .stFormSubmitButton > button p {
        color: inherit !important;
    }

    /* Text inputs */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid #e0dbd0 !important;
        color: #3d3a36 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border: 1px solid #b8860b !important;
        box-shadow: 0 0 0 1px #b8860b22 !important;
    }

    /* Selectbox closed state */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e0dbd0 !important;
        border-radius: 8px !important;
        color: #3d3a36 !important;
    }

    /* Selectbox dropdown popover (renders in a portal, needs its own override) */
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] ul[role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #e8e4dc !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] div[role="option"] {
        background-color: #ffffff !important;
        color: #3d3a36 !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] div[role="option"]:hover,
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] div[aria-selected="true"] {
        background-color: #f5f0e8 !important;
        color: #3d3a36 !important;
    }

    /* Expander — header (summary) and body (content) */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details {
        background-color: #ffffff !important;
        border: 1px solid #e8e4dc !important;
        border-radius: 8px !important;
        color: #3d3a36 !important;
    }
    [data-testid="stExpander"] summary:hover {
        background-color: #faf7f1 !important;
    }
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary svg {
        color: #3d3a36 !important;
        fill: #3d3a36 !important;
    }
    [data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
        color: #3d3a36 !important;
    }

    /* JSON / code viewer */
    [data-testid="stJson"], .stJson {
        background-color: #ffffff !important;
        border: 1px solid #e8e4dc !important;
        border-radius: 8px !important;
    }
    [data-testid="stJson"] * {
        background-color: #ffffff !important;
    }

    /* Markdown / divider / caption */
    hr { border-color: #e8e4dc !important; }
    [data-testid="stCaptionContainer"] { color: #8a8276 !important; }

    /* Header bar */
    [data-testid="stHeader"] {
        background-color: #faf9f6 !important;
    }

    /* Audio player container */
    audio { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Content Engine Pro")
st.caption(
    "Generate suite → self-critique loop → voiceover → multi-channel adaptation. "
    "Day 3 Homework — GenAI & Agentic AI Engineering."
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "run_history" not in st.session_state:
    st.session_state.run_history = []  # list of {suite, critic_history, still_failing}
if "current" not in st.session_state:
    st.session_state.current = None
if "adapted" not in st.session_state:
    st.session_state.adapted = None
if "voiceover_audio" not in st.session_state:
    st.session_state.voiceover_audio = None
if "voiceover_script" not in st.session_state:
    st.session_state.voiceover_script = None

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------
with st.form("brief_form"):
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Product name", placeholder="e.g. Aurora Smart Lamp")
        tone = st.selectbox("Tone", ["Playful", "Professional", "Bold", "Warm", "Minimal"])
    with col2:
        audience = st.text_input("Target audience", placeholder="e.g. remote workers who hate clutter")
    submitted = st.form_submit_button("🚀 Generate Campaign Suite", use_container_width=True)

if submitted:
    is_valid, error_msg = validate_inputs(product_name, audience, tone)
    if not is_valid:
        st.error(f"⚠️ {error_msg}")
    else:
        with st.spinner("Generating suite (tagline, blog, social, image brief, video brief)..."):
            suite = generate_suite(product_name.strip(), audience.strip(), tone)

        with st.spinner("Running self-critique loop (auto-regenerating weak output)..."):
            final_suite, critic_history, still_failing = run_critique_loop(suite)

        st.session_state.current = final_suite
        st.session_state.adapted = None
        st.session_state.voiceover_audio = None
        st.session_state.voiceover_script = None

        st.session_state.run_history.append({
            "suite": final_suite,
            "critic_history": critic_history,
            "still_failing": still_failing,
        })

# ---------------------------------------------------------------------------
# Render current suite
# ---------------------------------------------------------------------------
suite = st.session_state.current

if suite:
    st.divider()
    st.subheader("📦 Generated Suite")

    # === ADDITION 1 DISPLAY: Self-Critique Verdict Panel ===
    last_run = st.session_state.run_history[-1]
    still_failing = last_run["still_failing"]
    n_attempts = len(last_run["critic_history"])

    with st.expander(f"🧐 Self-Critique Verdict  (ran {n_attempts} pass{'es' if n_attempts != 1 else ''})", expanded=bool(still_failing)):
        for i, verdict in enumerate(last_run["critic_history"]):
            st.markdown(f"**Attempt {i + 1}**")
            for asset_name, result in verdict.items():
                ok = result.get("pass", True)
                pill_class = "pill-pass" if ok else "pill-fail"
                pill_text = "PASS" if ok else "FAIL"
                issue = result.get("issue") or "—"
                st.markdown(
                    f"- `{asset_name}` <span class='pill {pill_class}'>{pill_text}</span>"
                    + (f"  — *{issue}*" if not ok else ""),
                    unsafe_allow_html=True,
                )
        if still_failing:
            st.error(
                "⚠️ **Warning flag:** the following assets still fail after "
                f"{n_attempts - 1} retries and are shown as-is: "
                + ", ".join(f"`{k}`" for k in still_failing.keys())
            )
        else:
            st.success("✅ All assets passed critique.")

    # Asset cards
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">Tagline</div>{suite["tagline"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">Blog Intro</div>{suite["blog"]}</div>',
            unsafe_allow_html=True,
        )
    with c2:
        social = suite["social"]
        social_html = "<br><br>".join(
            f"<b>{platform.title()}</b><br>{text}" for platform, text in social.items()
        )
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">Social Posts</div>{social_html}</div>',
            unsafe_allow_html=True,
        )

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">🖼️ Image Brief</div>{suite["image_brief"]}</div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">🎬 Video Brief</div>{suite["video_brief"]}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # === ADDITION 2 DISPLAY: Voiceover Panel ===
    st.subheader("🎙️ Voiceover")
    vo_col1, vo_col2 = st.columns([1, 2])
    with vo_col1:
        if st.button("Generate Voiceover from Blog Intro", use_container_width=True):
            with st.spinner("Adapting script for voiceover..."):
                script = generate_voiceover_script(suite["blog"])
                st.session_state.voiceover_script = script
            with st.spinner("Synthesizing audio..."):
                try:
                    audio_bytes = synthesize_voiceover(script)
                    st.session_state.voiceover_audio = audio_bytes
                except Exception as e:
                    st.error(f"Voiceover synthesis failed: {e}")

    with vo_col2:
        if st.session_state.voiceover_script:
            with st.expander("Voiceover script", expanded=False):
                st.write(st.session_state.voiceover_script)

    if st.session_state.voiceover_audio:
        st.audio(st.session_state.voiceover_audio, format="audio/mp3")
        st.download_button(
            "⬇️ Download .mp3",
            data=st.session_state.voiceover_audio,
            file_name=f"{suite['product_name'].replace(' ', '_').lower()}_voiceover.mp3",
            mime="audio/mp3",
        )

    st.divider()

    # === ADDITION 3 DISPLAY: Multi-Channel Adaptation Panel ===
    st.subheader("📡 Multi-Channel Adaptation")
    ch_col1, ch_col2 = st.columns([1, 2])
    with ch_col1:
        channel = st.selectbox("Target channel", CHANNEL_OPTIONS, key="channel_select")
        if st.button("Adapt Suite for Channel", use_container_width=True):
            with st.spinner(f"Adapting text assets for {channel}..."):
                st.session_state.adapted = adapt_for_channel(suite, channel)

    if st.session_state.adapted:
        adapted = st.session_state.adapted
        st.markdown(f"**Preview — adapted for _{channel}_** (image & video briefs unchanged)")

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("**Before**")
            st.markdown(
                f'<div class="asset-card"><div class="asset-label">Tagline</div>{suite["tagline"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="asset-card"><div class="asset-label">Blog Intro</div>{suite["blog"]}</div>',
                unsafe_allow_html=True,
            )
        with pc2:
            st.markdown("**After**")
            st.markdown(
                f'<div class="asset-card"><div class="asset-label">Tagline</div>{adapted["tagline"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="asset-card"><div class="asset-label">Blog Intro</div>{adapted["blog"]}</div>',
                unsafe_allow_html=True,
            )

        adapted_social_html = "<br><br>".join(
            f"<b>{platform.title()}</b><br>{text}" for platform, text in adapted["social"].items()
        )
        st.markdown(
            f'<div class="asset-card"><div class="asset-label">Adapted Social Posts</div>{adapted_social_html}</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Run History (captures runs across products, with critic verdicts)
# ---------------------------------------------------------------------------
if len(st.session_state.run_history) > 0:
    st.divider()
    with st.expander(f"📜 Run History ({len(st.session_state.run_history)} run(s) captured)", expanded=False):
        for i, run in enumerate(st.session_state.run_history):
            s = run["suite"]
            st.markdown(f"**Run {i + 1}: {s['product_name']}** — audience: _{s['audience']}_, tone: _{s['tone']}_")

            run_summary = {
                "tagline": s["tagline"],
                "critic_attempts": len(run["critic_history"]),
                "still_failing": run["still_failing"] or "none",
            }
            import json as _json
            pretty = _json.dumps(run_summary, indent=2)
            st.markdown(
                f'<pre style="background:#fbfaf7; border:1px solid #e8e4dc; '
                f'border-radius:8px; padding:0.9rem 1.1rem; color:#3d3a36; '
                f'font-size:0.85rem; overflow-x:auto;">{pretty}</pre>',
                unsafe_allow_html=True,
            )
            st.markdown("---")