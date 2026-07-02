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
    generate_image, generate_video_storyboard,
)
from tts import synthesize_voiceover
from validators import validate_inputs
from prompts import CHANNEL_OPTIONS
import base64

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

    :root {
        --bg: #fbfaf7;
        --bg-soft: #f4f1ea;
        --surface: rgba(255, 255, 255, 0.92);
        --surface-strong: #ffffff;
        --border: #e8e1d4;
        --border-strong: #ddd4c1;
        --text: #27313f;
        --muted: #6f7a88;
        --accent: #b88924;
        --accent-strong: #9f7517;
        --accent-soft: #f5ebd3;
        --shadow: 0 16px 40px rgba(36, 46, 62, 0.08);
    }

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    html, body {
        background: var(--bg);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    /* Hide Streamlit's built-in top chrome so the page header starts cleanly */
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(184, 137, 36, 0.08), transparent 26%),
            radial-gradient(circle at top right, rgba(41, 101, 183, 0.05), transparent 24%),
            linear-gradient(180deg, #fcfbf8 0%, #f6f3ec 100%);
    }

    /* ── Typography ── */
    h1, h2, h3 {
        letter-spacing: -0.02em;
        font-weight: 700;
    }
    h1 { color: var(--text); font-size: 2.1rem !important; }
    h2 { color: var(--text); font-size: 1.45rem !important; }
    h3 { color: var(--text); font-size: 1.08rem !important; font-weight: 600; }

    /* ── Override ALL Streamlit default colors to warm palette ── */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        color: var(--text);
    }

    .hero-shell {
        background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(251,248,241,0.9));
        border: 1px solid rgba(232, 225, 212, 0.95);
        border-radius: 24px;
        box-shadow: var(--shadow);
        padding: 1.35rem 1.5rem 1.2rem 1.5rem;
        margin: 0.25rem 0 1.1rem 0;
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.28rem 0.72rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid rgba(184, 137, 36, 0.18);
        color: var(--accent-strong);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.85rem;
    }
    .hero-title {
        margin: 0;
        font-size: 2.35rem;
        line-height: 1.05;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.04em;
    }
    .hero-subtitle {
        margin: 0.6rem 0 0 0;
        max-width: 760px;
        color: var(--muted);
        font-size: 0.98rem;
        line-height: 1.6;
    }
    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.94);
        border: 1px solid var(--border);
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* ── Input labels ── */
    .stTextInput label, .stSelectbox label, .stTextInput label p, .stSelectbox label p {
        color: #566170 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* ── Streamlit text written via st.write / st.markdown ── */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .element-container, .row-widget {
        color: #3d3a36 !important;
    }

    /* ── Section header with accent line ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.8rem 0 1rem 0;
    }
    .section-header i {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid rgba(184, 137, 36, 0.18);
    }
    .section-header span {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.01em;
    }
    .section-header .accent-line {
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, rgba(184, 137, 36, 0.28), transparent);
        border-radius: 2px;
    }

    /* ── Glass card ── */
    .glass-card {
        background: var(--surface);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
        color: var(--text);
        line-height: 1.55;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .glass-card:hover {
        box-shadow: 0 18px 42px rgba(36, 46, 62, 0.12);
        transform: translateY(-1px);
    }

    .glass-card.soft {
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(251,248,241,0.98));
        border: 1px solid rgba(232, 225, 212, 0.95);
    }

    /* ── Structured run history card ── */
    .history-card {
        background: var(--surface);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        margin: 0.6rem 0;
        box-shadow: var(--shadow);
    }
    .history-card .hc-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(232,228,220,0.6);
    }
    .history-card .hc-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--text);
    }
    .history-card .hc-badge {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(184, 137, 36, 0.14), rgba(184, 137, 36, 0.08));
        color: var(--accent-strong);
        border: 1px solid rgba(184, 137, 36, 0.18);
    }
    .history-card .hc-row {
        display: flex;
        gap: 0.6rem;
        padding: 0.35rem 0;
        font-size: 0.85rem;
        align-items: flex-start;
    }
    .history-card .hc-key {
        font-weight: 600;
        color: #738091;
        min-width: 110px;
        flex-shrink: 0;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .history-card .hc-value {
        color: var(--text);
        flex: 1;
        line-height: 1.5;
    }
    .history-card .hc-value.pass {
        color: #2e7d4f;
        font-weight: 600;
    }
    .history-card .hc-value.fail {
        color: #c0392b;
        font-weight: 600;
    }

    .asset-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #7f8a98;
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
        background: linear-gradient(135deg, #e7f6ea, #d7f0de);
        color: #1f6b3d;
        border: 1px solid rgba(31, 107, 61, 0.12);
    }
    .pill-fail {
        background: linear-gradient(135deg, #fdebec, #f9dfe2);
        color: #9b2f39;
        border: 1px solid rgba(155, 47, 57, 0.12);
    }
    .pill-warn {
        background: linear-gradient(135deg, #fff5dc, #ffefd0);
        color: #8a640f;
        border: 1px solid rgba(138, 100, 15, 0.12);
    }

    /* ── Stepper / Progress indicator ── */
    .stepper {
        display: flex;
        align-items: center;
        gap: 0;
        margin: 1.5rem 0 2rem 0;
        padding: 0.75rem 0.5rem;
        background: rgba(255,255,255,0.82);
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 10px 28px rgba(36, 46, 62, 0.05);
    }
    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 1rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #7f8a98;
        transition: all 0.25s ease;
    }
    .step.active {
        background: linear-gradient(135deg, rgba(184, 137, 36, 0.16), rgba(184, 137, 36, 0.08));
        color: var(--accent-strong);
        font-weight: 600;
    }
    .step.completed {
        color: #2f7a4b;
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
        background: #ece7dc;
        color: #7f8a98;
        flex-shrink: 0;
    }
    .step.active .step-num {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: #fff;
    }
    .step.completed .step-num {
        background: #2f7a4b;
        color: #fff;
    }
    .step-arrow {
        color: #c8c0b3;
        font-size: 0.75rem;
        margin: 0 0.25rem;
    }

    /* ── Buttons ── */
    .stButton > button, .stFormSubmitButton > button {
        background: linear-gradient(135deg, #ffffff, #f7f2e7) !important;
        color: #445162 !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 6px 18px rgba(36, 46, 62, 0.06) !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #fffdf9, #f3ebdb) !important;
        border: 1px solid #cfc2a9 !important;
        color: #2f3947 !important;
        box-shadow: 0 10px 24px rgba(36, 46, 62, 0.09) !important;
    }
    .stButton > button:active {
        transform: scale(0.98) !important;
    }
    .stButton > button p, .stFormSubmitButton > button p {
        color: inherit !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
        color: #fff !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #c5962e, #91670f) !important;
        color: #fff !important;
    }

    /* ── Text inputs ── */
    .stTextInput input, .stTextInput input:focus, .stTextInput input:active {
        background: rgba(255, 255, 255, 0.94) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 12px !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.9rem !important;
        transition: border 0.2s ease, box-shadow 0.2s ease !important;
        caret-color: var(--accent) !important;
    }
    .stTextInput input:focus {
        border: 1px solid var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(184, 137, 36, 0.14) !important;
    }
    .stTextInput input::placeholder {
        color: #aab3bf !important;
        font-weight: 400;
    }
    /* Ensure the text input container and value text are warm */
    .stTextInput div[data-baseweb="input"] {
        background: transparent !important;
    }
    .stTextInput div[data-baseweb="input"] > div {
        color: #2d2a26 !important;
        background: transparent !important;
    }

    /* ── Choice controls (tone field) ── */
    .stRadio [role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding-top: 0.15rem;
    }
    .stRadio [role="radiogroup"] label {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        padding: 0.45rem 0.75rem !important;
        box-shadow: 0 4px 14px rgba(36, 46, 62, 0.04) !important;
        transition: all 0.18s ease !important;
    }
    .stRadio [role="radiogroup"] label:hover {
        border-color: rgba(184, 137, 36, 0.42) !important;
        background: #fffdf9 !important;
        transform: translateY(-1px);
    }
    .stRadio [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(184, 137, 36, 0.16), rgba(184, 137, 36, 0.08)) !important;
        border-color: rgba(184, 137, 36, 0.4) !important;
    }
    .stRadio [role="radiogroup"] label p,
    .stRadio [role="radiogroup"] label span {
        color: var(--text) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--text) !important;
        transition: border 0.2s ease !important;
        min-height: 42px !important;
    }
    div[data-baseweb="select"]:hover > div {
        border-color: #cfc2a9 !important;
    }
    /* Selectbox selected value text */
    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] div[role="button"] {
        color: var(--text) !important;
    }
    /* Selectbox single-value (displayed selected text) */
    div[data-baseweb="select"] div[data-testid="stMarkdownContainer"] *,
    div[data-baseweb="select"] [class*="singleValue"] {
        color: var(--text) !important;
    }
    /* Selectbox dropdown arrow */
    div[data-baseweb="select"] svg {
        color: #7f8a98 !important;
        fill: #7f8a98 !important;
    }
    /* Popover listbox container - LIGHTER & CLEANER */
    div[data-baseweb="popover"] {
        background: transparent !important;
    }
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] ul[role="listbox"] {
        background: #ffffff !important;
        backdrop-filter: none !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 30px rgba(36, 46, 62, 0.1) !important;
        padding: 4px !important;
    }
    /* All text inside select popover */
    div[data-baseweb="popover"] * {
        color: var(--text) !important;
    }
    /* Option items - CLEAN WHITE */
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] div[role="option"] {
        background: #ffffff !important;
        padding: 0.6rem 0.8rem !important;
        border-radius: 6px !important;
        color: var(--text) !important;
        font-size: 0.85rem !important;
        margin: 1px 0 !important;
        transition: background 0.1s ease !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] div[role="option"]:hover {
        background: #f6efe0 !important;
    }
    /* Active/highlighted option */
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] div[aria-selected="true"] {
        background: #f2ead8 !important;
        font-weight: 600 !important;
        color: var(--text) !important;
    }
    /* Already-selected option indicator */
    div[data-baseweb="select"] [aria-selected="true"] {
        color: #2d2a26 !important;
        font-weight: 600;
    }
    /* Ensure the select container text inherits warm color */
    .stSelectbox label, .stSelectbox label p {
        color: #566170 !important;
    }
    /* Remove any dark overlay or backdrop */
    div[data-baseweb="popover"]::before,
    div[data-baseweb="popover"]::after {
        display: none !important;
        background: transparent !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] details {
        background: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(6px) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    [data-testid="stExpander"] summary {
        background: rgba(255, 255, 255, 0.84) !important;
        padding: 0.7rem 1rem !important;
        border-radius: 14px !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: background 0.2s ease;
    }
    [data-testid="stExpander"] summary:hover {
        background: rgba(247, 242, 232, 0.9) !important;
    }
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary svg {
        color: var(--text) !important;
        fill: var(--text) !important;
    }
    [data-testid="stExpanderDetails"] {
        background: transparent !important;
        padding: 0.5rem 1rem 1rem 1rem !important;
        color: var(--text) !important;
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
        background: linear-gradient(90deg, transparent, #e4dccf, transparent) !important;
        margin: 2rem 0 !important;
    }

    /* ── Pre / Code block ── */
    pre {
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(4px);
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        color: var(--text) !important;
        font-size: 0.82rem !important;
        overflow-x: auto !important;
        line-height: 1.6;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #ffffff, #f7f2e7) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 12px !important;
        color: #445162 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #fffdf9, #f3ebdb) !important;
        border-color: #cfc2a9 !important;
        box-shadow: 0 10px 24px rgba(36, 46, 62, 0.09) !important;
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
    .status-dot.amber { background: var(--accent); box-shadow: 0 0 6px rgba(184,137,36,0.24); }

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
        color: #7f8a98;
        margin-bottom: 0.4rem;
    }

    /* ── Spinner override ── */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }
    .stSpinner {
        color: #445162 !important;
    }

    /* ── Metric cards ── */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 0.75rem 0;
    }
    .metric-item {
        flex: 1;
        background: rgba(255,255,255,0.92);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.6rem 0.9rem;
        text-align: center;
        box-shadow: 0 8px 20px rgba(36, 46, 62, 0.05);
    }
    .metric-item .metric-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text);
    }
    .metric-item .metric-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #7f8a98;
        margin-top: 0.15rem;
    }

    /* ── Caption ── */
    [data-testid="stCaptionContainer"] {
        color: #7f8a98 !important;
    }

    /* ── Responsive tweaks ── */
    @media (max-width: 768px) {
        .compare-container { grid-template-columns: 1fr; }
        .stepper { flex-wrap: wrap; gap: 0.25rem; }
        .step { padding: 0.3rem 0.6rem; font-size: 0.7rem; }
        .step-arrow { display: none; }
        .history-card .hc-header { flex-direction: column; align-items: flex-start; gap: 0.3rem; }
    }

    /* ── Channel badge ── */
    .channel-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        background: linear-gradient(135deg, rgba(184, 137, 36, 0.12), rgba(184, 137, 36, 0.06));
        border: 1px solid rgba(184, 137, 36, 0.18);
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--accent-strong);
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
st.markdown(
    """
    <div class="hero-shell fade-in">
        <div class="hero-kicker"><i class="fas fa-sparkles"></i> Content Strategy Studio</div>
        <h1 class="hero-title">Content Engine Pro</h1>
        <p class="hero-subtitle">Generate a campaign suite, refine it through self-critique, create a voiceover script, and adapt everything for each channel in one polished workflow.</p>
        <div class="hero-meta">
            <span class="hero-pill"><i class="fas fa-wand-magic-sparkles"></i> Suite generation</span>
            <span class="hero-pill"><i class="fas fa-brain"></i> Free LLM (Phi-3.5/Zephyr/Mistral)</span>
            <span class="hero-pill"><i class="fas fa-shield-halved"></i> Self-critique loop</span>
            <span class="hero-pill"><i class="fas fa-image"></i> Image generation</span>
            <span class="hero-pill"><i class="fas fa-video"></i> Video storyboard</span>
            <span class="hero-pill"><i class="fas fa-microphone-lines"></i> Voiceover ready</span>
            <span class="hero-pill"><i class="fas fa-bullhorn"></i> Channel adaptation</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
    tone_options = ["Executive", "Professional", "Conversational", "Bold", "Playful", "Minimal"]
    with col1:
        product_name = st.text_input(
            "🏷️ Product name",
            placeholder="e.g. Aurora Smart Lamp",
            help="Enter the name of your product or service"
        )
        tone = st.radio(
            "🎨 Tone of voice",
            tone_options,
            index=1,
            horizontal=True,
            help="Choose the voice and personality for the campaign"
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

    # ---------------------------------------------------------------------------
    # === IMAGE & VIDEO GENERATION — actual visual output ===
    # ---------------------------------------------------------------------------

    st.markdown("""
        <div class="section-header fade-in">
            <span><i class="fas fa-palette" style="color:#b8860b;"></i> Visual Media Generation</span>
            <div class="accent-line"></div>
        </div>
    """, unsafe_allow_html=True)

    img_col, vid_col = st.columns(2)

    # ---- Image Generation ----
    with img_col:
        st.markdown(
            f'<div class="glass-card soft">'
            f'<div class="asset-label"><i class="fas fa-image"></i> Generate Campaign Image</div>'
            f'<p style="font-size:0.85rem;color:#6f7a88;margin-bottom:0.8rem;">'
            f'Create an actual AI-generated image from the image brief using Pollinations.ai (free, no API key).</p>',
            unsafe_allow_html=True
        )

        if "generated_image" not in st.session_state:
            st.session_state.generated_image = None

        if st.button("🎨 Generate Image", key="gen_image_btn", use_container_width=True):
            with st.spinner("🖼️ Generating image via AI (free, no API key needed)..."):
                img_bytes = generate_image(suite["image_brief"])
                if img_bytes:
                    st.session_state.generated_image = img_bytes
                    st.success("✅ Image generated successfully!")
                else:
                    st.session_state.generated_image = None
            st.rerun()

        if st.session_state.generated_image:
            st.image(
                st.session_state.generated_image,
                caption=f'AI-generated campaign visual for {suite["product_name"]}',
                use_container_width=True,
            )
            st.download_button(
                "⬇️ Download PNG",
                data=st.session_state.generated_image,
                file_name=f"{suite['product_name'].replace(' ', '_').lower()}_campaign_image.png",
                mime="image/png",
                use_container_width=True,
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- Video Storyboard ----
    with vid_col:
        st.markdown(
            f'<div class="glass-card soft">'
            f'<div class="asset-label"><i class="fas fa-video"></i> Generate Video Storyboard</div>'
            f'<p style="font-size:0.85rem;color:#6f7a88;margin-bottom:0.8rem;">'
            f'Create an animated HTML5 storyboard from the video brief with scene breakdown.</p>',
            unsafe_allow_html=True
        )

        if "video_storyboard_html" not in st.session_state:
            st.session_state.video_storyboard_html = None

        if st.button("🎬 Generate Storyboard", key="gen_video_btn", use_container_width=True):
            with st.spinner("🎞️ Generating video storyboard..."):
                storyboard_html = generate_video_storyboard(suite["video_brief"])
                st.session_state.video_storyboard_html = storyboard_html
                st.success("✅ Video storyboard generated!")
            st.rerun()

        if st.session_state.video_storyboard_html:
            # Display storyboard HTML in an iframe
            b64_html = base64.b64encode(
                st.session_state.video_storyboard_html.encode("utf-8")
            ).decode("utf-8")
            
            st.components.v1.html(
                st.session_state.video_storyboard_html,
                height=420,
                scrolling=False,
            )
            
            st.download_button(
                "⬇️ Download Storyboard HTML",
                data=st.session_state.video_storyboard_html,
                file_name=f"{suite['product_name'].replace(' ', '_').lower()}_storyboard.html",
                mime="text/html",
                use_container_width=True,
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
    # Run History — structured card format
    # ---------------------------------------------------------------------------
    if len(st.session_state.run_history) > 0:
        with st.expander(
            f"📜 Run History ({len(st.session_state.run_history)} run(s) captured)",
            expanded=False
        ):
            for i, run in enumerate(st.session_state.run_history):
                s = run["suite"]
                still_fail = run["still_failing"]
                status_badge = "✅ All passed" if not still_fail else f"⚠️ {len(still_fail)} issue(s)"

                st.markdown(
                    f'<div class="history-card fade-in">'
                    f'  <div class="hc-header">'
                    f'    <div class="hc-title">Run {i + 1}: {s["product_name"]}</div>'
                    f'    <div class="hc-badge">{status_badge}</div>'
                    f'  </div>'
                    f'  <div class="hc-row">'
                    f'    <div class="hc-key">Audience</div>'
                    f'    <div class="hc-value">{s["audience"]}</div>'
                    f'  </div>'
                    f'  <div class="hc-row">'
                    f'    <div class="hc-key">Tone</div>'
                    f'    <div class="hc-value">{s["tone"]}</div>'
                    f'  </div>'
                    f'  <div class="hc-row">'
                    f'    <div class="hc-key">Tagline</div>'
                    f'    <div class="hc-value">{s["tagline"]}</div>'
                    f'  </div>'
                    f'  <div class="hc-row">'
                    f'    <div class="hc-key">Critique Passes</div>'
                    f'    <div class="hc-value">{len(run["critic_history"])}</div>'
                    f'  </div>'
                    f'  <div class="hc-row">'
                    f'    <div class="hc-key">Issues</div>'
                    f'    <div class="hc-value {"pass" if not still_fail else "fail"}">'
                    f'      {still_fail if still_fail else "No remaining issues"}'
                    f'    </div>'
                    f'  </div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # Pipeline step reset when no suite is active
    else:
        st.session_state.pipeline_step = 0