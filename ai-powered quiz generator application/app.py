import os, json, re, time, requests, streamlit as st
from pptx import Presentation
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
MODEL              = "anthropic/claude-haiku-4-5"

DIFF_HINTS = {
    "Simple":  "Definitions, key terms & basic concepts — straight from the slides.",
    "Medium":  "Mix of recall + scenario reasoning spread across all topics.",
    "Complex": "Analytical edge-cases, trade-offs & best-among-goods challenges.",
}
DIFF_PROMPTS = {
    "Simple":  "Generate straightforward factual recall questions. Focus on definitions, key terms, and basic concepts directly stated in the slides.",
    "Medium":  "Generate balanced questions mixing factual recall and scenario-based reasoning. Include some best answer questions that require understanding relationships between concepts.",
    "Complex": "Generate challenging analytical questions requiring deep understanding. Focus on edge cases, subtle distinctions, trade-offs, and application of concepts in novel scenarios. Make distractors highly plausible.",
}

st.set_page_config(page_title="AI Quiz Generator", page_icon="🎯", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body { font-family: 'Inter', sans-serif; }

/* ── ANIMATED BACKGROUND ── */
[data-testid="stAppViewContainer"] {
    background: #060818;
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
}
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: -40%;
    left: -20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(139,92,246,0.25) 0%, transparent 70%);
    border-radius: 50%;
    animation: orb1 8s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    bottom: -30%;
    right: -15%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(6,182,212,0.18) 0%, transparent 70%);
    border-radius: 50%;
    animation: orb2 10s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}
@keyframes orb1 { from { transform: translate(0,0) scale(1); } to { transform: translate(60px,80px) scale(1.15); } }
@keyframes orb2 { from { transform: translate(0,0) scale(1); } to { transform: translate(-50px,-60px) scale(1.2); } }

/* Extra orb via a div we inject */
.orb3 {
    position: fixed;
    top: 40%;
    left: 50%;
    transform: translate(-50%,-50%);
    width: 800px;
    height: 400px;
    background: radial-gradient(ellipse, rgba(99,102,241,0.08) 0%, transparent 70%);
    border-radius: 50%;
    animation: orb3 12s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}
@keyframes orb3 { from { opacity:.4; } to { opacity:1; } }

[data-testid="stHeader"] { background: transparent !important; display:none; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }

[data-testid="stMain"] > div { padding-top: 0 !important; }
[data-testid="block-container"] { padding-top: 0 !important; position: relative; z-index: 1; }

/* ── NAVBAR ── */
.navbar {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 40px;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nb-brand {
    display: flex; align-items: center; gap: 12px;
    font-size: 17px; font-weight: 800; color: #fff;
    letter-spacing: -0.4px;
}
.nb-logo {
    width: 38px; height: 38px; border-radius: 12px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 20px rgba(139,92,246,0.6), 0 0 40px rgba(139,92,246,0.2);
}
.nb-step {
    font-size: 12px; font-weight: 600; letter-spacing: .06em;
    color: rgba(255,255,255,0.5);
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 6px 16px; border-radius: 30px;
}

/* ── SECTION HEADER ── */
.sec-header { text-align: center; margin-bottom: 32px; }
.sec-tag {
    display: inline-block;
    font-size: 10px; font-weight: 700; letter-spacing: .15em;
    color: #8b5cf6; text-transform: uppercase;
    background: rgba(139,92,246,0.12);
    border: 1px solid rgba(139,92,246,0.25);
    padding: 4px 14px; border-radius: 20px;
    margin-bottom: 14px;
}
.sec-title {
    font-size: 30px; font-weight: 900; color: #fff;
    letter-spacing: -0.6px; line-height: 1.15;
    margin-bottom: 8px;
}
.sec-title span {
    background: linear-gradient(135deg, #a78bfa, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sec-sub { font-size: 14px; color: rgba(255,255,255,0.4); }

/* ── GLASS CARD ── */
.gcard {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.gcard::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.6), rgba(6,182,212,0.4), transparent);
}

/* ── UPLOAD ── */
.upload-area {
    border: 2px dashed rgba(139,92,246,0.4);
    border-radius: 16px;
    padding: 56px 24px;
    text-align: center;
    background: rgba(139,92,246,0.04);
    margin-bottom: 16px;
    transition: all .3s;
    position: relative;
    overflow: hidden;
}
.upload-area::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 0%, rgba(139,92,246,0.1), transparent 60%);
    pointer-events: none;
}
.upload-icon { font-size: 52px; margin-bottom: 14px; display: block; filter: drop-shadow(0 0 20px rgba(139,92,246,0.8)); }
.upload-area h2 { font-size: 20px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.upload-area p  { font-size: 13px; color: rgba(255,255,255,0.35); }

.parsed-card {
    background: rgba(16,185,129,0.07);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 14px; padding: 16px 20px;
    display: flex; align-items: center; gap: 14px;
    margin: 14px 0;
    box-shadow: 0 0 20px rgba(16,185,129,0.08);
}
.parsed-card .pi { font-size: 26px; filter: drop-shadow(0 0 8px rgba(16,185,129,0.6)); }
.parsed-card .pt { flex: 1; }
.parsed-card .pt strong { color: #fff; font-size: 14px; display: block; margin-bottom: 2px; }
.parsed-card .pt span  { color: rgba(255,255,255,0.45); font-size: 12px; }
.parsed-badge {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff; font-size: 11px; font-weight: 700;
    padding: 5px 14px; border-radius: 20px;
    box-shadow: 0 0 14px rgba(16,185,129,0.4);
}

/* ── SOURCE PILL ── */
.src-pill {
    display: flex; align-items: center; gap: 10px;
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.22);
    border-radius: 12px; padding: 12px 18px;
    font-size: 13px; color: #c4b5fd;
    margin-bottom: 28px;
}
.sec-lbl {
    font-size: 10px; font-weight: 700; letter-spacing: .12em;
    color: rgba(255,255,255,0.3); text-transform: uppercase;
    margin-bottom: 12px; display: block;
}

/* ── DIFFICULTY CARDS ── */
.diff-grid { display: flex; gap: 12px; margin-bottom: 12px; }
.diff-tile {
    flex: 1; padding: 18px 12px; border-radius: 14px;
    border: 1.5px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    text-align: center; cursor: pointer;
    transition: all .25s;
    position: relative; overflow: hidden;
}
.diff-tile.on {
    border-color: #8b5cf6;
    background: rgba(139,92,246,0.12);
    box-shadow: 0 0 24px rgba(139,92,246,0.2), inset 0 1px 0 rgba(255,255,255,0.1);
}
.diff-tile.on::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #8b5cf6, #06b6d4);
}
.diff-tile .de { font-size: 26px; margin-bottom: 8px; display: block; }
.diff-tile .dn { font-size: 13px; font-weight: 700; color: #fff; }
.diff-tile.on .dn { color: #c4b5fd; }

.hint-box {
    background: rgba(6,182,212,0.06);
    border: 1px solid rgba(6,182,212,0.18);
    border-radius: 12px; padding: 12px 16px;
    font-size: 12px; color: #67e8f9;
    margin-bottom: 24px;
    display: flex; align-items: flex-start; gap: 8px;
}

/* ── QUIZ ── */
.q-meta {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px;
}
.q-num {
    font-size: 11px; font-weight: 700; letter-spacing: .1em;
    color: #8b5cf6;
}
.timer {
    background: rgba(251,146,60,0.1);
    border: 1px solid rgba(251,146,60,0.25);
    color: #fb923c; font-size: 13px; font-weight: 700;
    padding: 5px 14px; border-radius: 20px;
    display: inline-flex; align-items: center; gap: 6px;
    box-shadow: 0 0 12px rgba(251,146,60,0.1);
}

.pbar-wrap {
    height: 6px; border-radius: 6px;
    background: rgba(255,255,255,0.07);
    margin-bottom: 28px; overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.4);
}
.pbar-fill {
    height: 100%; border-radius: 6px;
    background: linear-gradient(90deg, #8b5cf6, #06b6d4);
    box-shadow: 0 0 10px rgba(139,92,246,0.6);
    transition: width .5s ease;
}

.q-text {
    font-size: 19px; font-weight: 700; color: #fff;
    line-height: 1.55; margin-bottom: 24px;
    letter-spacing: -0.2px;
}

/* ── SCORE SCREEN ── */
.score-hero {
    text-align: center; padding: 40px 28px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px; margin-bottom: 24px;
    position: relative; overflow: hidden;
}
.score-hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(circle at 50% 0%, rgba(139,92,246,0.15), transparent 60%);
    pointer-events: none;
}
.score-hero::after {
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, transparent, #8b5cf6, #06b6d4, transparent);
}
.score-big {
    font-size: 80px; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, #a78bfa, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 30px rgba(139,92,246,0.5));
    margin-bottom: 4px;
}
.score-pct { font-size: 24px; font-weight: 700; color: rgba(255,255,255,0.7); margin-bottom: 8px; }
.score-hl  { font-size: 15px; color: rgba(255,255,255,0.45); margin-bottom: 20px; }
.chips { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
.chip {
    padding: 7px 18px; border-radius: 30px;
    font-size: 13px; font-weight: 600;
}
.chip-g { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); color: #34d399; box-shadow: 0 0 12px rgba(16,185,129,0.1); }
.chip-r { background: rgba(239,68,68,0.1);   border: 1px solid rgba(239,68,68,0.25);  color: #f87171; box-shadow: 0 0 12px rgba(239,68,68,0.08); }
.chip-o { background: rgba(251,146,60,0.1);  border: 1px solid rgba(251,146,60,0.25); color: #fb923c; }

.rev-lbl {
    font-size: 10px; font-weight: 700; letter-spacing: .12em;
    color: rgba(255,255,255,0.28); text-transform: uppercase;
    margin: 22px 0 12px;
}
.rev-item { border-radius: 14px; padding: 15px 18px; margin-bottom: 10px; }
.rev-ok  { background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.18); }
.rev-bad { background: rgba(239,68,68,0.06);  border: 1px solid rgba(239,68,68,0.18);  }
.rev-hd  { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 5px; }
.rev-ic  { font-size: 15px; flex-shrink:0; margin-top:2px; }
.rev-tl  { font-size: 13px; font-weight: 700; color: #fff; }
.rev-q   { font-size: 12px; color: rgba(255,255,255,0.45); margin: 4px 0 4px 25px; }
.ans-ok  { font-size: 12px; color: #34d399; margin-left: 25px; }
.ans-bad { font-size: 12px; color: #f87171; margin-left: 25px; }
.ai-row  {
    background: rgba(139,92,246,0.07);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 10px; padding: 10px 14px;
    font-size: 12px; color: #c4b5fd;
    margin: 8px 0 0 0;
    display: flex; gap: 8px;
    box-shadow: 0 0 12px rgba(139,92,246,0.06);
}

/* ── STREAMLIT WIDGET OVERRIDES ── */
div[data-testid="stFileUploaderDropzone"] {
    background: rgba(139,92,246,0.05) !important;
    border: 2px dashed rgba(139,92,246,0.35) !important;
    border-radius: 16px !important;
}
div[data-testid="stFileUploaderDropzone"] p { color: rgba(255,255,255,0.5) !important; }
div[data-testid="stFileUploaderDropzone"] small { color: rgba(255,255,255,0.3) !important; }
div[data-testid="stFileUploaderDropzone"] svg { fill: rgba(139,92,246,0.6) !important; }

/* Slider */
div[data-testid="stSlider"] label { color: rgba(255,255,255,0.8) !important; font-weight: 600 !important; font-size: 14px !important; }
div[data-testid="stSlider"] p { color: rgba(255,255,255,0.4) !important; }
[data-testid="stSlider"] [role="slider"] { background: #8b5cf6 !important; box-shadow: 0 0 12px rgba(139,92,246,0.7) !important; }
[data-testid="stSlider"] [data-baseweb="slider"] [role="progressbar"] { background: linear-gradient(90deg,#8b5cf6,#06b6d4) !important; }

/* Radio buttons */
[data-testid="stRadio"] label { color: rgba(255,255,255,0.85) !important; font-size: 14px !important; }
[data-testid="stRadio"] > div { gap: 8px !important; }
[data-testid="stRadio"] > div > label {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all .2s !important;
    margin-bottom: 6px !important;
}
[data-testid="stRadio"] > div > label:hover {
    border-color: #8b5cf6 !important;
    background: rgba(139,92,246,0.1) !important;
}
[data-testid="stRadio"] > div > label[data-checked="true"] {
    border-color: #8b5cf6 !important;
    background: rgba(139,92,246,0.15) !important;
    box-shadow: 0 0 20px rgba(139,92,246,0.2), inset 0 1px 0 rgba(255,255,255,0.07) !important;
}
[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
[data-testid="stRadio"] > div > label > div { color: rgba(255,255,255,0.85) !important; font-weight: 500 !important; }
[data-testid="stRadio"] > div > label[data-checked="true"] > div { color: #c4b5fd !important; font-weight: 600 !important; }

/* Buttons */
.stButton > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 14px 22px !important;
    transition: all .25s !important;
    letter-spacing: .02em !important;
    width: 100% !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 24px rgba(99,102,241,0.45), 0 0 0 1px rgba(139,92,246,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 32px rgba(99,102,241,0.65), 0 0 0 1px rgba(139,92,246,0.5) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.7) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(139,92,246,0.1) !important;
    border-color: rgba(139,92,246,0.4) !important;
    color: #c4b5fd !important;
}
.stButton > button:disabled { opacity: .3 !important; transform: none !important; box-shadow: none !important; cursor: not-allowed !important; }

/* Spinner */
[data-testid="stSpinner"] > div { border-top-color: #8b5cf6 !important; }

/* Caption */
.stCaption, [data-testid="stCaptionContainer"] p { color: rgba(255,255,255,0.3) !important; font-size: 11px !important; }

/* Alert */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* Divider */
hr { border-color: rgba(255,255,255,0.07) !important; }

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
.shine-text {
    background: linear-gradient(90deg, #a78bfa 0%, #06b6d4 30%, #fff 50%, #06b6d4 70%, #a78bfa 100%);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
}
</style>

<div class="orb3"></div>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init():
    for k, v in {
        "step":"upload","slides":[],"filename":"","slide_count":0,
        "word_count":0,"preview":"","num_questions":10,"difficulty":"Medium",
        "questions":[],"user_answers":{},"current_q":0,
        "start_time":None,"elapsed":0,"explanations":{},
        "radio_key":0,
    }.items():
        if k not in st.session_state: st.session_state[k] = v
init()

# ── BACKEND ───────────────────────────────────────────────────────────────────
def extract_pptx(b):
    prs = Presentation(BytesIO(b))
    slides, words = [], 0
    for i, slide in enumerate(prs.slides, 1):
        txt = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    t = p.text.strip()
                    if t: txt.append(t)
        c = " ".join(txt)
        if c: slides.append({"slide":i,"text":c}); words += len(c.split())
    return slides, words

def llm(prompt):
    r = requests.post(OPENROUTER_URL, headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Quiz Generator",
    }, json={"model":MODEL,"messages":[{"role":"user","content":prompt}],"temperature":.7,"max_tokens":4096}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def gen_mcqs(slides, n, diff):
    txt = "\n\n".join(f"[Slide {s['slide']}]: {s['text']}" for s in slides)
    raw = llm(f"""Expert quiz designer. Generate exactly {n} MCQs from these slides.
DIFFICULTY: {diff} — {DIFF_PROMPTS[diff]}
SLIDES:\n{txt}
Rules: 4 options A-D, one correct, plausible distractors, spread across topics.
Return ONLY valid JSON array, no markdown:
[{{"id":1,"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct":"B","topic":"label"}}]""")
    return json.loads(re.sub(r"```(?:json)?","",raw).strip().strip("`").strip())

def gen_exp(questions, answers):
    wrong = [q for q in questions if answers.get(str(q["id"])) and answers[str(q["id"])] != q["correct"]]
    if not wrong: return {}
    block = "\n\n".join(
        f"Q{w['id']}: {w['question']}\nStudent: {answers[str(w['id'])]} — {w['options'].get(answers[str(w['id'])],'')} \nCorrect: {w['correct']} — {w['options'][w['correct']]}"
        for w in wrong)
    raw = llm(f"For each wrong answer write 1-2 sentences: why wrong + why correct is right.\n{block}\nReturn ONLY JSON: {{\"1\":\"...\"}}")
    return json.loads(re.sub(r"```(?:json)?","",raw).strip().strip("`").strip())

# ── NAVBAR ────────────────────────────────────────────────────────────────────
steps = {"upload":"Step 1 of 3","config":"Step 2 of 3",
         "quiz":f"Q {st.session_state.current_q+1}/{len(st.session_state.questions)}",
         "results":"Complete ✓"}
st.markdown(f"""
<div class="navbar">
  <div class="nb-brand"><div class="nb-logo">🎯</div> AI Quiz Generator</div>
  <span class="nb-step">{steps.get(st.session_state.step,'')}</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "upload":
    st.markdown("""
    <div class="sec-header">
      <div class="sec-tag">Step 1 of 3</div>
      <div class="sec-title">Upload Your <span>Presentation</span></div>
      <div class="sec-sub">Drop your .pptx and we'll extract every word automatically</div>
    </div>
    <div class="upload-area">
      <span class="upload-icon">📂</span>
      <h2>Drag & drop your .pptx here</h2>
      <p>.pptx only &nbsp;·&nbsp; max 25 MB</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload your PowerPoint file", type=["pptx"], label_visibility="collapsed")

    if uploaded:
        if uploaded.size > 25*1024*1024:
            st.error("File exceeds 25 MB.")
        else:
            with st.spinner("Parsing slides…"):
                try:
                    slides, wc = extract_pptx(uploaded.read())
                    if not slides: st.error("No text found in this file.")
                    else:
                        st.session_state.update(slides=slides, filename=uploaded.name,
                            slide_count=len(slides), word_count=wc,
                            preview=slides[0]["text"][:220])
                        st.markdown(f"""
                        <div class="parsed-card">
                          <span class="pi">📄</span>
                          <div class="pt">
                            <strong>{uploaded.name}</strong>
                            <span>{len(slides)} slides parsed &nbsp;·&nbsp; {wc:,} words extracted</span>
                          </div>
                          <span class="parsed-badge">✓ Ready</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Preview: {st.session_state.preview}…")
                except Exception as e:
                    st.error(f"Parse error: {e}")

    st.write("")
    if st.button("Continue →", type="primary", disabled=not bool(st.session_state.slides)):
        st.session_state.step = "config"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — CONFIGURE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "config":
    st.markdown("""
    <div class="sec-header">
      <div class="sec-tag">Step 2 of 3</div>
      <div class="sec-title">Configure Your <span>Quiz</span></div>
      <div class="sec-sub">Choose difficulty and how many questions to generate</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="src-pill">
      📎 &nbsp;<strong style="color:#fff">{st.session_state.filename}</strong>
      &nbsp;·&nbsp; {st.session_state.slide_count} slides &nbsp;·&nbsp; {st.session_state.word_count:,} words
    </div>
    """, unsafe_allow_html=True)

    st.session_state.num_questions = st.slider(
        "Number of questions", min_value=5, max_value=30,
        value=st.session_state.num_questions)

    st.markdown('<span class="sec-lbl">Difficulty Level</span>', unsafe_allow_html=True)
    DMETA = [("Simple","🟢"),("Medium","🟡"),("Complex","🔴")]
    cols = st.columns(3)
    for col,(name,emoji) in zip(cols, DMETA):
        with col:
            on = "on" if st.session_state.difficulty == name else ""
            st.markdown(f'<div class="diff-tile {on}"><span class="de">{emoji}</span><span class="dn">{name}</span></div>', unsafe_allow_html=True)
            if st.button(name, key=f"d_{name}", type="primary" if on else "secondary"):
                st.session_state.difficulty = name; st.rerun()

    st.markdown(f'<div class="hint-box"><span>💡</span><span>{DIFF_HINTS[st.session_state.difficulty]}</span></div>', unsafe_allow_html=True)

    if st.button(f"⚡  Generate {st.session_state.num_questions} Questions", type="primary"):
        with st.spinner("AI is crafting your quiz — takes ~15 sec…"):
            try:
                qs = gen_mcqs(st.session_state.slides, st.session_state.num_questions, st.session_state.difficulty)
                st.session_state.update(questions=qs, user_answers={}, current_q=0,
                                        start_time=time.time(), step="quiz", radio_key=0)
                st.rerun()
            except json.JSONDecodeError:
                st.error("AI returned malformed JSON — please retry.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — QUIZ
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz":
    questions = st.session_state.questions
    total = len(questions)
    i     = st.session_state.current_q
    q     = questions[i]
    qid   = str(q["id"])

    elapsed    = int(time.time() - (st.session_state.start_time or time.time()))
    m, s       = divmod(elapsed, 60)
    pct        = int((i / total) * 100)
    answered   = len(st.session_state.user_answers)

    c1, c2 = st.columns([3,1])
    with c1:
        st.markdown(f'<div class="q-num">QUESTION {i+1} OF {total} &nbsp;·&nbsp; {answered} ANSWERED</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="timer">⏱ {m:02d}:{s:02d}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="pbar-wrap"><div class="pbar-fill" style="width:{pct}%"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="q-text">{q["question"]}</div>', unsafe_allow_html=True)

    # Radio for answer — only one element, no duplicates
    opts    = [f"**{k}** &nbsp; {v}" for k, v in q["options"].items()]
    keys    = list(q["options"].keys())
    current = st.session_state.user_answers.get(qid)
    default = keys.index(current) if current in keys else None

    choice = st.radio(
        "Choose your answer",
        options=opts,
        index=default,
        key=f"radio_{i}_{st.session_state.radio_key}",
        label_visibility="collapsed",
    )
    if choice is not None:
        chosen_key = keys[opts.index(choice)]
        st.session_state.user_answers[qid] = chosen_key

    st.write("")
    cp, cn = st.columns(2)
    with cp:
        if i > 0:
            if st.button("← Previous", type="secondary"):
                st.session_state.current_q -= 1
                st.rerun()
    with cn:
        lbl = "Submit Quiz ✓" if i == total-1 else "Next →"
        if st.button(lbl, type="primary"):
            if i < total-1:
                st.session_state.current_q += 1; st.rerun()
            else:
                st.session_state.elapsed = int(time.time()-st.session_state.start_time)
                with st.spinner("Generating AI explanations…"):
                    try: st.session_state.explanations = gen_exp(questions, st.session_state.user_answers)
                    except: st.session_state.explanations = {}
                st.session_state.step = "results"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 4 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "results":
    questions = st.session_state.questions
    total   = len(questions)
    correct = sum(1 for q in questions if st.session_state.user_answers.get(str(q["id"]))==q["correct"])
    wrong   = total - correct
    pct     = round((correct/total)*100) if total else 0
    m, s    = divmod(st.session_state.elapsed, 60)

    hl = ("Perfect score! 🎉" if pct==100 else "Outstanding! 🌟" if pct>=90
          else "Great job! 💪" if pct>=80 else "Good effort 📚" if pct>=60 else "Keep going 🚀")

    st.markdown(f"""
    <div class="sec-header" style="margin-bottom:20px">
      <div class="sec-tag">Results</div>
      <div class="sec-title"><span class="shine-text">{hl}</span></div>
    </div>
    <div class="score-hero">
      <div class="score-big">{correct}/{total}</div>
      <div class="score-pct">{pct}% Score</div>
      <div class="score-hl">{st.session_state.difficulty} difficulty &nbsp;·&nbsp; {st.session_state.slide_count} slides</div>
      <div class="chips">
        <span class="chip chip-g">✓ {correct} correct</span>
        <span class="chip chip-r">✗ {wrong} wrong</span>
        <span class="chip chip-o">⏱ {m:02d}:{s:02d}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="rev-lbl">Review &amp; AI Feedback</div>', unsafe_allow_html=True)

    for idx, q in enumerate(questions):
        qid = str(q["id"])
        ua  = st.session_state.user_answers.get(qid)
        ok  = ua == q["correct"]
        cls = "rev-ok" if ok else "rev-bad"
        ic  = "✅" if ok else "❌"

        if ok:
            ans = f'<div class="ans-ok">Your answer: {ua} — {q["options"].get(ua,"")} ✓</div>'
        elif ua:
            ans = f'<div class="ans-bad">You chose {ua}: {q["options"].get(ua,"")} &nbsp;·&nbsp; Correct: {q["correct"]}: {q["options"][q["correct"]]}</div>'
        else:
            ans = f'<div class="ans-bad">Not answered &nbsp;·&nbsp; Correct: {q["correct"]}: {q["options"][q["correct"]]}</div>'

        exp = st.session_state.explanations.get(qid,"")
        ai  = f'<div class="ai-row"><span>🤖</span><span>{exp}</span></div>' if (not ok and exp) else ""

        st.markdown(f"""
        <div class="rev-item {cls}">
          <div class="rev-hd"><span class="rev-ic">{ic}</span><span class="rev-tl">Q{idx+1} · {q.get('topic','')}</span></div>
          <div class="rev-q">{q['question']}</div>
          {ans}{ai}
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("↺  Retake Quiz", type="primary"):
            st.session_state.update(user_answers={}, current_q=0,
                start_time=time.time(), explanations={}, step="quiz", radio_key=st.session_state.radio_key+1)
            st.rerun()
    with c2:
        if st.button("↑  Upload New PPT", type="secondary"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
