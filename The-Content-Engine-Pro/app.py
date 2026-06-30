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
# Enhanced modern UI styling — glassmorphism + refined palette
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1140px;
    }

    .stApp {
        background: linear-gradient(135deg, #f6f5f1 0%, #f0ede5 50%, #faf9f6 100%);
    }

    /* ── Typography ── */
    h1, h2, h3 {
        letter-spacing: -0.02em;
        font-weight: 700;
    }
    h1 {
        background: linear-gradient(135deg, #2d2a26 30%, #b8860b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.2rem !important;
    }
    h2 { color: #2d2a26; font-size: 1.5rem !important; }
    h3 { color: #3d3a36; font-size: 1.15rem !important; font-weight: 600; }

    /* ── Section header with accent line ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.8rem 0 1rem 0;
    }
    .section-header span {
        font-size: 1.2rem;
        font-weight: 700;
        color: #2d2a26;
        letter-spacing: -0.01em;
    }
    .section-header .accent-line {
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, #b8860b44, transparent);
        border-radius: 2px;
    }

    /* ── Glass card ── */
    .glass-card {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
        color: #3d3a36;
        line-height: 1.55;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .glass-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.07), 0 2px 6px rgba(0,0,0,0.04);
        transform: translateY(-1px);
    }

    .glass-card.dark {
        background: rgba(45, 42, 38, 0.06);
        border: 1px solid rgba(45, 42, 38, 0.08);
    }

    .asset-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #a8a095;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .asset-label i { font-size: 0.75rem; }

    /* ── Pill badges ── */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        margin-left: 0.3rem;
        letter-spacing: 0.02em;
    }
    .pill-pass {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        border: 1px solid #b8daff44;
    }
    .pill-fail {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        color: #721c24;
        border: 1px solid #f5c6cb44;
    }
    .pill-warn {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        color: #856404;
        border: 1px solid #ffeaa744;
    }

    /* ── Stepper / Progress indicator ── */
    .stepper {
        display: flex;
        align-items: center;
        gap: 0;
        margin: 1.5rem 0 2rem 0;
        padding: 0.75rem 0.5rem;
        background: rgba(255,255,255,0.5);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.8);
    }
    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 1rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #a8a095;
        transition: all 0.25s ease;
    }
    .step.active {
        background: linear-gradient(135deg, #b8860b22, #b8860b11);
        color: #7a5e0a;
        font-weight: 600;
    }
    .step.completed {
        color: #2e7d4f;
    }
    .step .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        font-size: 0.7rem;
        font-weight: 700;
        background: #e8e4dc;
        color: #8a8276;
        flex-shrink: 0;
    }
    .step.active .step-num {
        background: linear-gradient(135deg, #b8860b, #a0760a);
        color: #fff;
    }
    .step.completed .step-num {
        background: #2e7d4f;
        color: #fff;
    }
    .step-arrow {
        color: #ddd5c5;
        font-size: 0.75rem;
        margin: 0 0.25rem;
    }

    /* ── Buttons ── */
    .stButton > button, .stFormSubmitButton > button {
        background: linear-gradient(135deg, #f5f0e8, #ede5d5) !important;
        color: #5a5347 !important;
        border: 1px solid #ddd5c5 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #ede5d5, #e5dcc8) !important;
        border: 1px solid #cfc4ac !important;
        color: #4a4439 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    .stButton > button:active {
        transform: scale(0.98) !important;
    }
    .stButton > button p, .stFormSubmitButton > button p {
        color: inherit !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #b8860b, #a0760a) !important;
        color: #fff !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #a0760a, #8a6508) !important;
        color: #fff !important;
    }

    /* ── Text inputs ── */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid #e0dbd0 !important;
        color: #3d3a36 !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.9rem !important;
        transition: border 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput input:focus {
        border: 1px solid #b8860b !important;
        box-shadow: 0 0 0 3px #b8860b22 !important;
    }
    .stTextInput input::placeholder {
        color: #c4beb0 !important;
        font-weight: 400;
    }

    /* ── Selectbox ── */
    div[data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid #e0dbd0 !important;
        border-radius: 10px !important;
        color: #3d3a36 !important;
        transition: border 0.2s ease !important;
    }
    div[data-baseweb="select"]:hover > div {
        border-color: #cfc4ac !important;
    }
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] ul[role="listbox"] {
        background: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid #e8e4dc !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08) !important;
    }
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] div[role="option"] {
        background: transparent !important;
        color: #3d3a36 !important;
        padding: 0.5rem 0.8rem !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] div[role="option"]:hover,
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] div[aria-selected="true"] {
        background: #f5f0e8 !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] details {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(6px) !important;
        border: 1px solid rgba(232, 228, 220, 0.8) !important;
        border-radius: 12px !important;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    [data-testid="stExpander"] summary {
        background: rgba(255, 255, 255, 0.5) !important;
        padding: 0.7rem 1rem !important;
        border-radius: 12px !important;
        color: #3d3a36 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: background 0.2s ease;
    }
    [data-testid="stExpander"] summary:hover {
        background: rgba(250, 247, 241, 0.8) !important;
    }
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary svg {
        color: #3d3a36 !important;
        fill: #3d3a36 !important;
    }
    [data-testid="stExpanderDetails"] {
        background: transparent !important;
        padding: 0.5rem 1rem 1rem 1rem !important;
        color: #3d3a36 !important;
    }

    /* ── Sucess / Error / Warning alerts ── */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
    .stAlert > div {
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
    }

    /* ── Audio player ── */
    audio {
        border-radius: 10px;
        width: 100%;
        margin: 0.5rem 0;
    }

    /* ── Divider ── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #e8e4dc, transparent) !important;
        margin: 2rem 0 !important;
    }

    /* ── Pre / Code block ── */
    pre {
        background: rgba(251, 250, 247, 0.8) !important;
        backdrop-filter: blur(4px);
        border: 1px solid #e8e4dc !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
        color: #3d3a36 !important;
        font-size: 0.82rem !important;
        overflow-x: auto !important;
        line-height: 1.6;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f5f0e8, #ede5d5) !important;
        border: 1px solid #ddd5c5 !important;
        border-radius: 10px !important;
        color: #5a5347 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #ede5d5, #e5dcc8) !important;
        border-color: #cfc4ac !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }

    /* ── Status dots ── */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.35rem;
    }
    .status-dot.green { background: #2e7d4f; box-shadow: 0 0 6px #2e7d4f44; }
    .status-dot.red { background: #c0392b; box-shadow: 0 0 6px #c0392b44; }
    .status-dot.amber { background: #b8860b; box-shadow: 0 0 6px #b8860b44; }

    /* ── Before/After comparison ── */
    .compare-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    .compare-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #a8a095;
        margin-bottom: 0.4rem;
    }

    /* ── Spinner override ── */
    .stSpinner > div {
        border-top-color: #b8860b !important;
    }

    /* ── Metric cards ── */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 0.75rem 0;
    }
    .metric-item {
        flex: 1;
        background: rgba(255,255,255,0.5);
        border: 1px solid rgba(232,228,220,0.6);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        text-align: center;
    }
    .metric-item .metric-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2d2a26;
    }
    .metric-item .metric-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #a8a095;
        margin-top: 0.15rem;
    }

    /* ── Responsive tweaks ── */
    @media (max-width: 768px) {
        .compare-container { grid-template-columns: 1fr; }
        .stepper { flex-wrap: wrap; gap: 0.25rem; }
        .step { padding: 0.3rem 0.6rem; font-size: 0.7rem; }
        .step-arrow { display: none; }
    }

    /* ── Channel badge ── */
    .channel-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        background: linear-gradient(135deg, #b8860b22, #b8860b11);
        border: 1px solid #b8860b33;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #7a5e0a;
        margin-bottom: 0.5rem;
    }

    /* ── Fade-in animation ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeInUp 0.35s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    st.markdown("""
        <div style="
            width: 42px; height: 42px; background: linear-gradient(135deg, #b8860b, #a0760a);
            border-radius: 12px; display: flex; align-items: center; justify-content: center;
            font-size: 1.3rem; box-shadow: 0 4px 12px rgba(184,134,11,0.3);
        ">🛠️</div>
    """, unsafe_allow_html=True)
with col_title:
    st.markdown("**Content Engine Pro**  <span style='color:#a8a095; font-weight:400; font-size:0.9rem;'>— GenAI campaign pipeline</span>", unsafe_allow_html=True)

st.caption(
    "Generate suite → self-critique loop → voiceover → multi-channel adaptation. "
    "Homework — GenAI & Agentic AI Engineering."
)

# ---------------------------------------------------------------------------
# Pipeline stepper (shows current progress)
# ---------------------------------------------------------------------------
if "pipeline_step" not in st.session_state:
    st.session_state.pipeline_step = 0  # 0=idle, 1=generated, 2=critiqued, 3=voiceover, 4=adapted

steps = [
    ("1", "Generate", "fa-pen-fancy"),
    ("2", "Critique", "fa-microscope"),
    ("3", "Voiceover", "fa-microphone"),
    ("4", "Adapt", "fa-rss"),
]

def render_stepper(current_step):
    parts = []
    for i, (num, label, icon) in enumerate(steps):
        if i < current_step:
            cls = "completed"
            icon_html = f'<i class="fas fa-check" style="font-size:0.6rem;"></i>'
        elif i == current_step:
            cls = "active"
            icon_html = f'<i class="fas {icon}" style="font-size:0.7rem;"></i>'
        else:
            cls = ""
            icon_html = f'<span class="step-num">{num}</span>'

        parts.append(
            f'<div class="step {cls}">'
            f'  {icon_html}'
            f'  <span>{label}</span>'
            f'</div>'
        )
        if i < len(steps) - 1:
            parts.append('<span class="step-arrow"><i class="fas fa-chevron-right"></i></span>')
    return '<div class="stepper">' + "".join(parts) + "</div>"

st.markdown(render_stepper(st.session_state.pipeline_step), unsafe_allow_html=True)

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
# Input form — glass card
# ---------------------------------------------------------------------------
st.markdown("""
    <div class="section-header fade-in">
        <span><i class="fas fa-pen-fancy" style="color:#b8860b;"></i> Campaign Brief</span>
        <div class="accent-line"></div>
    </div>
""", unsafe_allow_html=True)

with st.form("brief_form"):
    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input(
            "🏷️ Product name",
            placeholder="e.g. Aurora Smart Lamp",
            help="Enter the name of your product or service"
        )
        tone = st.selectbox(
            "🎨 Tone",
            ["Playful", "Professional", "Bold", "Warm", "Minimal"],
            help="Select the campaign's voice and personality"
        )
    with col2:
        audience = st.text_input(
            "👥 Target audience",
            placeholder="e.g. remote workers who hate clutter",
            help="Describe who you're speaking to"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Generate Campaign Suite", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    is_valid, error_msg = validate_inputs(product_name, audience, tone)
    if not is_valid:
        st.error(f"⚠️  {error_msg}")
    else:
        st.session_state.pipeline_step = 1  # generating
        with st.spinner("🧠 Generating suite (tagline, blog, social, image brief, video brief)..."):
            suite = generate_suite(product_name.strip(), audience.strip(), tone)

        st.session_state.pipeline_step = 2  # critiquing
        with st.spinner("🔍 Running self-critique loop (auto-regenerating weak output)..."):
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

        st.session_state.pipeline_step = 2  # critiqued
        st.rerun()

# ---------------------------------------------------------------------------
# Render current suite
# ---------------------------------------------------------------------------
suite = st.session_state.current

if suite:
    st.markdown("""
        <div class="section-header fade-in">
            <span><i class="fas fa-box-open" style="color:#b8860b;"></i> Generated Suite</span>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    # === Quick metrics ===
    last_run = st.session_state.run_history[-1]
    still_failing = last_run["still_failing"]
    n_attempts = len(last_run["critic_history"])

    st.markdown('<div class="metric-row fade-in">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="metric-item"><div class="metric-value">{suite["product_name"]}</div>'
        f'<div class="metric-label">Product</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="metric-item"><div class="metric-value">{suite["tone"]}</div>'
        f'<div class="metric-label">Tone</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="metric-item"><div class="metric-value">{n_attempts}</div>'
        f'<div class="metric-label">Critique Passes</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="metric-item"><div class="metric-value">{len(still_failing)}</div>'
        f'<div class="metric-label">Remaining Issues</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # === ADDITION 1 DISPLAY: Self-Critique Verdict Panel ===
    with st.expander(
        f"🧐 Self-Critique Verdict  (ran {n_attempts} pass{'es' if n_attempts != 1 else ''})",
        expanded=bool(still_failing)
    ):
        for i, verdict in enumerate(last_run["critic_history"]):
            st.markdown(f"<div class='fade-in'><b>Attempt {i + 1}</b></div>", unsafe_allow_html=True)
            for asset_name, result in verdict.items():
                ok = result.get("pass", True)
                pill_class = "pill-pass" if ok else "pill-fail"
                pill_text = "PASS" if ok else "FAIL"
                icon_html = f'<span class="status-dot {"green" if ok else "red"}"></span>'
                issue = result.get("issue") or "—"
                st.markdown(
                    f'<div style="margin:0.2rem 0;">'
                    f'{icon_html}<code>{asset_name}</code> '
                    f'<span class="pill {pill_class}">{pill_text}</span>'
                    + (f'  <em style="color:#8a8276;font-size:0.85rem;">— {issue}</em>' if not ok else "")
                    + '</div>',
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
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-quote-right"></i> Tagline</div>'
            f'{suite["tagline"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-feather"></i> Blog Intro</div>'
            f'{suite["blog"]}</div>',
            unsafe_allow_html=True,
        )
    with c2:
        social = suite["social"]
        social_html = "<br><br>".join(
            f'<b style="font-size:0.85rem;"><i class="fab fa-{p.lower()}" style="color:#b8860b;"></i> '
            f'{p.title()}</b><br><span style="font-size:0.92rem;">{text}</span>'
            for p, text in social.items()
        )
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-hashtag"></i> Social Posts</div>'
            f'{social_html}</div>',
            unsafe_allow_html=True,
        )

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-image"></i> Image Brief</div>'
            f'{suite["image_brief"]}</div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-video"></i> Video Brief</div>'
            f'{suite["video_brief"]}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="section-header fade-in">
            <span><i class="fas fa-microphone" style="color:#b8860b;"></i> Voiceover</span>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    # === ADDITION 2 DISPLAY: Voiceover Panel ===
    vo_col1, vo_col2 = st.columns([1, 2])
    with vo_col1:
        if st.button("🎤 Generate Voiceover from Blog Intro", use_container_width=True):
            with st.spinner("🎙️ Adapting script for voiceover..."):
                script = generate_voiceover_script(suite["blog"])
                st.session_state.voiceover_script = script
            with st.spinner("🔊 Synthesizing audio..."):
                try:
                    audio_bytes = synthesize_voiceover(script)
                    st.session_state.voiceover_audio = audio_bytes
                except Exception as e:
                    st.error(f"Voiceover synthesis failed: {e}")
            st.session_state.pipeline_step = 3

    with vo_col2:
        if st.session_state.voiceover_script:
            with st.expander("📝 Voiceover script", expanded=False):
                st.markdown(
                    f'<div class="glass-card dark" style="font-style:italic;">'
                    f'{st.session_state.voiceover_script}</div>',
                    unsafe_allow_html=True
                )

    if st.session_state.voiceover_audio:
        st.audio(st.session_state.voiceover_audio, format="audio/mp3")
        col_dl, col_spacer = st.columns([1, 3])
        with col_dl:
            st.download_button(
                "⬇️ Download MP3",
                data=st.session_state.voiceover_audio,
                file_name=f"{suite['product_name'].replace(' ', '_').lower()}_voiceover.mp3",
                mime="audio/mp3",
                use_container_width=True,
            )

    st.markdown("""
        <div class="section-header fade-in">
            <span><i class="fas fa-rss" style="color:#b8860b;"></i> Multi-Channel Adaptation</span>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    # === ADDITION 3 DISPLAY: Multi-Channel Adaptation Panel ===
    ch_col1, ch_col2 = st.columns([1, 2])
    with ch_col1:
        channel = st.selectbox("📡 Target channel", CHANNEL_OPTIONS, key="channel_select")
        if st.button("🔄 Adapt Suite for Channel", use_container_width=True):
            with st.spinner(f"✏️ Adapting text assets for {channel}..."):
                st.session_state.adapted = adapt_for_channel(suite, channel)
                st.session_state.pipeline_step = 4

    if st.session_state.adapted:
        adapted = st.session_state.adapted
        st.markdown(
            f'<div class="channel-badge"><i class="fas fa-satellite-dish"></i> Preview — adapted for <strong>{channel}</strong></div>'
            f'<div style="font-size:0.78rem;color:#8a8276;margin-bottom:0.8rem;">'
            f'Image & video briefs remain unchanged per spec.</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="compare-container">', unsafe_allow_html=True)

        # Before column
        st.markdown(
            f'<div><div class="compare-label"><i class="far fa-circle" style="color:#bbb;"></i> Before</div>'
            f'<div class="glass-card"><div class="asset-label">Tagline</div>{suite["tagline"]}</div>'
            f'<div class="glass-card"><div class="asset-label">Blog Intro</div>{suite["blog"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # After column
        st.markdown(
            f'<div><div class="compare-label"><i class="fas fa-circle" style="color:#b8860b;"></i> After</div>'
            f'<div class="glass-card" style="border-left:3px solid #b8860b;">'
            f'<div class="asset-label">Tagline</div>{adapted["tagline"]}</div>'
            f'<div class="glass-card" style="border-left:3px solid #b8860b;">'
            f'<div class="asset-label">Blog Intro</div>{adapted["blog"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)

        adapted_social_html = "<br><br>".join(
            f'<b style="font-size:0.85rem;"><i class="fab fa-{p.lower()}" style="color:#b8860b;"></i> '
            f'{p.title()}</b><br><span>{text}</span>'
            for p, text in adapted["social"].items()
        )
        st.markdown(
            f'<div class="glass-card"><div class="asset-label"><i class="fas fa-hashtag"></i> Adapted Social Posts</div>'
            f'{adapted_social_html}</div>',
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------------------
    # Run History
    # ---------------------------------------------------------------------------
    if len(st.session_state.run_history) > 0:
        with st.expander(
            f"📜 Run History ({len(st.session_state.run_history)} run(s) captured)",
            expanded=False
        ):
            for i, run in enumerate(st.session_state.run_history):
                s = run["suite"]
                st.markdown(
                    f'<div class="glass-card" style="margin:0.5rem 0;">'
                    f'<b>Run {i + 1}: {s["product_name"]}</b> — '
                    f'<span style="color:#8a8276;">audience:</span> <em>{s["audience"]}</em>, '
                    f'<span style="color:#8a8276;">tone:</span> <em>{s["tone"]}</em>',
                    unsafe_allow_html=True,
                )

                run_summary = {
                    "tagline": s["tagline"],
                    "critic_attempts": len(run["critic_history"]),
                    "still_failing": run["still_failing"] or "none",
                }
                import json as _json
                pretty = _json.dumps(run_summary, indent=2)
                st.markdown(
                    f'<pre style="margin-top:0.6rem;">{pretty}</pre>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

    # Pipeline step reset when no suite is active
    else:
        st.session_state.pipeline_step = 0