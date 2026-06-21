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
    "Simple":  "Generate straightforward factual recall questions focusing on definitions, key terms, and basic concepts directly stated in the slides.",
    "Medium":  "Generate balanced questions mixing factual recall and scenario-based reasoning. Include best-answer questions requiring understanding of relationships between concepts.",
    "Complex": "Generate challenging analytical questions requiring deep understanding. Focus on edge cases, subtle distinctions, trade-offs, and novel application of concepts.",
}

st.set_page_config(page_title="AI Quiz Generator", page_icon="🎯", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: #f0f4f8;
}

[data-testid="stHeader"] { display: none !important; }
#MainMenu, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }
[data-testid="stMain"] > div { padding-top: 0 !important; }
[data-testid="block-container"] { padding: 0 1rem 3rem !important; max-width: 780px !important; }

/* ── TOPBAR ── */
.topbar {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 36px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    position: sticky; top: 0; z-index: 99;
}
.topbar-brand {
    display: flex; align-items: center; gap: 10px;
    font-size: 16px; font-weight: 800; color: #0f172a;
}
.topbar-logo {
    width: 34px; height: 34px; border-radius: 10px;
    background: linear-gradient(135deg, #2563eb, #0ea5e9);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
    box-shadow: 0 2px 8px rgba(37,99,235,0.35);
}
.topbar-badge {
    background: #eff6ff; color: #2563eb;
    border: 1px solid #bfdbfe;
    font-size: 11px; font-weight: 700;
    padding: 4px 12px; border-radius: 20px;
    letter-spacing: .04em;
}

/* ── STEP INDICATOR ── */
.steps-row {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin-bottom: 32px;
}
.step-item { display: flex; align-items: center; gap: 0; }
.step-circle {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700;
    border: 2px solid #e2e8f0;
    background: #fff; color: #94a3b8;
    position: relative; z-index: 1;
}
.step-circle.done  { background: #2563eb; border-color: #2563eb; color: #fff; }
.step-circle.active{ background: #fff; border-color: #2563eb; color: #2563eb; box-shadow: 0 0 0 4px #dbeafe; }
.step-label {
    font-size: 11px; font-weight: 600; color: #94a3b8;
    margin-left: 8px; white-space: nowrap;
}
.step-label.active-lbl { color: #2563eb; }
.step-line { width: 60px; height: 2px; background: #e2e8f0; margin: 0 4px; }
.step-line.done-line { background: #2563eb; }

/* ── PAGE HEADING ── */
.pg-heading { text-align: center; margin-bottom: 28px; }
.pg-heading h1 { font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 6px; letter-spacing: -.4px; }
.pg-heading p  { font-size: 14px; color: #64748b; }

/* ── WHITE CARD ── */
.wcard {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 28px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04);
}

/* ── UPLOAD ── */
.upload-zone {
    border: 2px dashed #93c5fd;
    border-radius: 14px; padding: 52px 24px;
    text-align: center;
    background: #f8faff;
    margin-bottom: 16px;
    transition: all .2s;
}
.upload-zone:hover { border-color: #2563eb; background: #eff6ff; }
.upload-zone .uz-icon { font-size: 48px; margin-bottom: 14px; display: block; }
.upload-zone h3 { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
.upload-zone p  { font-size: 13px; color: #94a3b8; }

.parsed-row {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 12px; padding: 14px 18px;
    display: flex; align-items: center; gap: 14px;
    margin: 14px 0;
}
.parsed-row .pr-icon { font-size: 22px; }
.parsed-row .pr-info { flex: 1; }
.parsed-row .pr-info strong { font-size: 14px; color: #0f172a; display: block; margin-bottom: 2px; }
.parsed-row .pr-info span  { font-size: 12px; color: #64748b; }
.badge-ok {
    background: #16a34a; color: #fff;
    font-size: 11px; font-weight: 700;
    padding: 4px 12px; border-radius: 20px;
}

/* ── SOURCE STRIP ── */
.src-strip {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 11px 16px;
    font-size: 13px; color: #64748b; margin-bottom: 24px;
    display: flex; align-items: center; gap: 8px;
}
.src-strip strong { color: #0f172a; }

/* ── SECTION LABEL ── */
.slbl { font-size: 11px; font-weight: 700; letter-spacing: .08em; color: #94a3b8; text-transform: uppercase; margin-bottom: 10px; display: block; }

/* ── DIFFICULTY ── */
.diff-row { display: flex; gap: 10px; margin-bottom: 12px; }
.diff-box {
    flex: 1; padding: 14px 10px; border-radius: 12px;
    border: 1.5px solid #e2e8f0; background: #f8fafc;
    text-align: center; cursor: pointer; transition: all .2s;
}
.diff-box:hover { border-color: #93c5fd; }
.diff-box.sel { border-color: #2563eb; background: #eff6ff; box-shadow: 0 0 0 3px #dbeafe; }
.diff-box .db-emoji { font-size: 22px; margin-bottom: 5px; display: block; }
.diff-box .db-name  { font-size: 13px; font-weight: 700; color: #0f172a; }
.diff-box.sel .db-name { color: #2563eb; }

.hint-strip {
    background: #f0f9ff; border: 1px solid #bae6fd;
    border-radius: 10px; padding: 10px 14px;
    font-size: 12px; color: #0369a1;
    margin-bottom: 24px; display: flex; gap: 8px;
}

/* ── QUIZ — ALL QUESTIONS PAGE ── */
.quiz-topbar {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 16px 22px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.qt-left { display: flex; flex-direction: column; gap: 2px; }
.qt-title { font-size: 15px; font-weight: 800; color: #0f172a; }
.qt-sub   { font-size: 12px; color: #64748b; }
.qt-right { display: flex; align-items: center; gap: 12px; }
.timer-box {
    background: #fff7ed; border: 1px solid #fed7aa;
    color: #c2410c; font-size: 14px; font-weight: 700;
    padding: 7px 14px; border-radius: 10px;
    display: flex; align-items: center; gap: 6px;
}
.answered-pill {
    background: #eff6ff; color: #2563eb;
    border: 1px solid #bfdbfe;
    font-size: 12px; font-weight: 600;
    padding: 6px 14px; border-radius: 10px;
}

.pbar-outer { background: #e2e8f0; border-radius: 6px; height: 6px; margin-bottom: 20px; overflow: hidden; }
.pbar-inner { height: 100%; background: linear-gradient(90deg,#2563eb,#0ea5e9); border-radius: 6px; transition: width .5s; }

/* ── QUESTION CARD ── */
.q-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow .2s;
}
.q-card:hover { box-shadow: 0 4px 16px rgba(37,99,235,0.08); }
.q-num-tag {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; color: #2563eb;
    font-size: 11px; font-weight: 700; letter-spacing: .06em;
    padding: 4px 10px; border-radius: 6px;
    margin-bottom: 12px;
}
.q-topic-tag {
    display: inline-flex;
    background: #f1f5f9; color: #475569;
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 6px;
    margin-bottom: 12px; margin-left: 6px;
}
.q-text { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.55; margin-bottom: 16px; }

/* ── RESULTS ── */
.score-banner {
    background: linear-gradient(135deg, #1e40af, #0284c7);
    border-radius: 18px; padding: 36px 32px;
    text-align: center; margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.25);
    position: relative; overflow: hidden;
}
.score-banner::before {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.06); border-radius: 50%;
}
.score-banner::after {
    content: '';
    position: absolute; bottom: -80px; left: -40px;
    width: 240px; height: 240px;
    background: rgba(255,255,255,0.04); border-radius: 50%;
}
.score-num { font-size: 72px; font-weight: 900; color: #fff; line-height: 1; margin-bottom: 4px; }
.score-pct { font-size: 20px; color: rgba(255,255,255,.75); font-weight: 600; margin-bottom: 8px; }
.score-hl  { font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 20px; }
.score-chips { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; position: relative; z-index:1; }
.sc { padding: 7px 18px; border-radius: 30px; font-size: 13px; font-weight: 700; }
.sc-g { background: rgba(16,185,129,.2); color: #6ee7b7; border: 1px solid rgba(16,185,129,.35); }
.sc-r { background: rgba(239,68,68,.18);  color: #fca5a5; border: 1px solid rgba(239,68,68,.3);  }
.sc-w { background: rgba(255,255,255,.12); color: rgba(255,255,255,.8); border: 1px solid rgba(255,255,255,.2); }

.rev-lbl { font-size: 11px; font-weight: 700; letter-spacing: .08em; color: #94a3b8; text-transform: uppercase; margin: 24px 0 12px; }

.rev-card { border-radius: 14px; padding: 16px 18px; margin-bottom: 10px; }
.rev-card.ok  { background: #f0fdf4; border: 1px solid #bbf7d0; }
.rev-card.bad { background: #fef2f2; border: 1px solid #fecaca; }
.rev-hdr { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 5px; }
.rev-ic  { font-size: 15px; flex-shrink: 0; margin-top: 2px; }
.rev-tl  { font-size: 13px; font-weight: 700; color: #0f172a; }
.rev-q   { font-size: 12px; color: #64748b; margin: 4px 0 5px 25px; }
.ans-ok  { font-size: 12px; color: #16a34a; font-weight: 600; margin-left: 25px; }
.ans-bad { font-size: 12px; color: #dc2626; font-weight: 600; margin-left: 25px; }
.ai-card {
    background: #f0f9ff; border: 1px solid #bae6fd;
    border-radius: 10px; padding: 10px 14px;
    font-size: 12px; color: #0369a1;
    margin: 8px 0 0 0; display: flex; gap: 8px;
}

/* ── STREAMLIT OVERRIDES ── */
div[data-testid="stFileUploaderDropzone"] {
    background: #f8faff !important;
    border: 2px dashed #93c5fd !important;
    border-radius: 14px !important;
}
div[data-testid="stFileUploaderDropzone"] p     { color: #64748b !important; }
div[data-testid="stFileUploaderDropzone"] small { color: #94a3b8 !important; }
div[data-testid="stFileUploaderDropzone"] svg   { fill: #93c5fd !important; }

div[data-testid="stSlider"] label { color: #0f172a !important; font-weight: 600 !important; font-size: 14px !important; }
div[data-testid="stSlider"] p { color: #64748b !important; }
[data-testid="stSlider"] [role="slider"] { background: #2563eb !important; box-shadow: 0 0 0 4px #dbeafe !important; }

/* Radio — all questions page */
[data-testid="stRadio"] > div { gap: 8px !important; }
[data-testid="stRadio"] > div > label {
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 13px 16px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all .15s !important;
}
[data-testid="stRadio"] > div > label:hover {
    border-color: #93c5fd !important;
    background: #eff6ff !important;
}
[data-testid="stRadio"] > div > label[data-checked="true"] {
    border-color: #2563eb !important;
    background: #eff6ff !important;
    box-shadow: 0 0 0 3px #dbeafe !important;
}
[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
[data-testid="stRadio"] > div > label > div { color: #0f172a !important; font-weight: 500 !important; font-size: 14px !important; }
[data-testid="stRadio"] > div > label[data-checked="true"] > div { color: #1d4ed8 !important; font-weight: 600 !important; }
[data-testid="stRadio"] label[data-testid="stWidgetLabel"] { display: none !important; }

/* Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 13px 20px !important;
    transition: all .2s !important;
    width: 100% !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(37,99,235,0.5) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important;
    border: 1.5px solid #e2e8f0 !important;
    color: #374151 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #93c5fd !important;
    color: #2563eb !important;
    background: #eff6ff !important;
}
.stButton > button:disabled { opacity: .4 !important; transform: none !important; box-shadow: none !important; }

[data-testid="stSpinner"] > div { border-top-color: #2563eb !important; }
.stCaption, [data-testid="stCaptionContainer"] p { color: #94a3b8 !important; font-size: 12px !important; }
[data-testid="stAlert"] { border-radius: 10px !important; }
hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init():
    for k, v in {
        "step":"upload","slides":[],"filename":"","slide_count":0,
        "word_count":0,"preview":"","num_questions":10,"difficulty":"Medium",
        "questions":[],"user_answers":{},"start_time":None,
        "elapsed":0,"explanations":{},"radio_key":0,
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
    }, json={"model":MODEL,"messages":[{"role":"user","content":prompt}],
             "temperature":.7,"max_tokens":4096}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def gen_mcqs(slides, n, diff):
    txt = "\n\n".join(f"[Slide {s['slide']}]: {s['text']}" for s in slides)
    raw = llm(f"""Expert quiz designer. Generate exactly {n} MCQs.\nDIFFICULTY: {diff} — {DIFF_PROMPTS[diff]}\nSLIDES:\n{txt}\nRules: 4 options A-D, one correct, plausible distractors, spread across topics.\nReturn ONLY valid JSON array, no markdown:\n[{{"id":1,"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct":"B","topic":"label"}}]""")
    return json.loads(re.sub(r"```(?:json)?","",raw).strip().strip("`").strip())

def gen_exp(questions, answers):
    wrong = [q for q in questions if answers.get(str(q["id"])) and answers[str(q["id"])] != q["correct"]]
    if not wrong: return {}
    block = "\n\n".join(
        f"Q{w['id']}: {w['question']}\nStudent: {answers[str(w['id'])]} — {w['options'].get(answers[str(w['id'])],'')} \nCorrect: {w['correct']} — {w['options'][w['correct']]}"
        for w in wrong)
    raw = llm(f"For each wrong answer write 1-2 sentences: why it's wrong and why the correct answer is right.\n{block}\nReturn ONLY JSON: {{\"1\":\"...\"}}")
    return json.loads(re.sub(r"```(?:json)?","",raw).strip().strip("`").strip())

# ── TOPBAR ────────────────────────────────────────────────────────────────────
badge = {"upload":"Step 1 of 3","config":"Step 2 of 3","quiz":"In Progress","results":"Completed"}
st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo">🎯</div>
    AI Quiz Generator
  </div>
  <span class="topbar-badge">{badge.get(st.session_state.step,'')}</span>
</div>
""", unsafe_allow_html=True)

# ── STEP INDICATOR ────────────────────────────────────────────────────────────
step_order = ["upload","config","quiz","results"]
step_names = ["Upload","Configure","Quiz","Results"]
cur = step_order.index(st.session_state.step)

steps_html = '<div class="steps-row">'
for idx, (s, name) in enumerate(zip(step_order, step_names)):
    if idx < cur:   cls, lcls = "done", ""
    elif idx == cur: cls, lcls = "active", "active-lbl"
    else:            cls, lcls = "", ""
    steps_html += f'<div class="step-item"><div class="step-circle {cls}">{"✓" if idx < cur else idx+1}</div><span class="step-label {lcls}">{name}</span></div>'
    if idx < 3:
        steps_html += f'<div class="step-line {"done-line" if idx < cur else ""}"></div>'
steps_html += '</div>'
st.markdown(steps_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "upload":
    st.markdown("""
    <div class="pg-heading">
      <h1>Upload Your Presentation</h1>
      <p>Drop your .pptx file — we'll extract all content and generate a quiz from it</p>
    </div>
    <div class="upload-zone">
      <span class="uz-icon">📂</span>
      <h3>Drag & drop your .pptx here</h3>
      <p>.pptx files only &nbsp;·&nbsp; max 25 MB</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload PowerPoint", type=["pptx"], label_visibility="collapsed")

    if uploaded:
        if uploaded.size > 25*1024*1024:
            st.error("File exceeds 25 MB limit.")
        else:
            with st.spinner("Parsing your presentation…"):
                try:
                    slides, wc = extract_pptx(uploaded.read())
                    if not slides:
                        st.error("No readable text found in this file.")
                    else:
                        st.session_state.update(slides=slides, filename=uploaded.name,
                            slide_count=len(slides), word_count=wc,
                            preview=slides[0]["text"][:220])
                        st.markdown(f"""
                        <div class="parsed-row">
                          <span class="pr-icon">📄</span>
                          <div class="pr-info">
                            <strong>{uploaded.name}</strong>
                            <span>{len(slides)} slides parsed &nbsp;·&nbsp; {wc:,} words extracted</span>
                          </div>
                          <span class="badge-ok">✓ Ready</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Preview: {st.session_state.preview}…")
                except Exception as e:
                    st.error(f"Failed to parse: {e}")

    st.write("")
    if st.button("Continue →", type="primary", disabled=not bool(st.session_state.slides)):
        st.session_state.step = "config"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — CONFIGURE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "config":
    st.markdown("""
    <div class="pg-heading">
      <h1>Configure Your Quiz</h1>
      <p>Set the number of questions and choose how challenging you want them</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="src-strip">
      📎 &nbsp;<strong>{st.session_state.filename}</strong>
      &nbsp;·&nbsp; {st.session_state.slide_count} slides &nbsp;·&nbsp; {st.session_state.word_count:,} words
    </div>
    """, unsafe_allow_html=True)

    st.session_state.num_questions = st.slider(
        "Number of questions", min_value=5, max_value=30,
        value=st.session_state.num_questions)

    st.markdown('<span class="slbl">Difficulty Level</span>', unsafe_allow_html=True)

    DMETA = [("Simple","🟢"),("Medium","🟡"),("Complex","🔴")]
    cols = st.columns(3)
    for col, (name, emoji) in zip(cols, DMETA):
        with col:
            sel = "sel" if st.session_state.difficulty == name else ""
            st.markdown(f'<div class="diff-box {sel}"><span class="db-emoji">{emoji}</span><span class="db-name">{name}</span></div>', unsafe_allow_html=True)
            if st.button(name, key=f"d_{name}", type="primary" if sel else "secondary"):
                st.session_state.difficulty = name; st.rerun()

    st.markdown(f'<div class="hint-strip"><span>ℹ️</span><span>{DIFF_HINTS[st.session_state.difficulty]}</span></div>', unsafe_allow_html=True)

    if st.button(f"⚡  Generate {st.session_state.num_questions} Questions", type="primary"):
        with st.spinner("AI is crafting your quiz — takes ~15 seconds…"):
            try:
                qs = gen_mcqs(st.session_state.slides, st.session_state.num_questions, st.session_state.difficulty)
                st.session_state.update(questions=qs, user_answers={}, start_time=time.time(),
                                        step="quiz", radio_key=st.session_state.radio_key+1)
                st.rerun()
            except json.JSONDecodeError:
                st.error("AI returned malformed JSON — please retry.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — QUIZ  (all questions on one scrollable page)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz":
    questions = st.session_state.questions
    total     = len(questions)
    answered  = len(st.session_state.user_answers)
    elapsed   = int(time.time() - (st.session_state.start_time or time.time()))
    m, s      = divmod(elapsed, 60)
    pct       = int((answered / total) * 100)

    st.markdown(f"""
    <div class="quiz-topbar">
      <div class="qt-left">
        <span class="qt-title">{st.session_state.filename}</span>
        <span class="qt-sub">{st.session_state.difficulty} difficulty &nbsp;·&nbsp; {total} questions</span>
      </div>
      <div class="qt-right">
        <span class="answered-pill">{answered}/{total} answered</span>
        <span class="timer-box">⏱ {m:02d}:{s:02d}</span>
      </div>
    </div>
    <div class="pbar-outer"><div class="pbar-inner" style="width:{pct}%"></div></div>
    """, unsafe_allow_html=True)

    # All questions rendered on one page
    for idx, q in enumerate(questions):
        qid  = str(q["id"])
        opts = [f"**{k}.**  {v}" for k, v in q["options"].items()]
        keys = list(q["options"].keys())
        cur  = st.session_state.user_answers.get(qid)
        default = keys.index(cur) if cur in keys else None

        st.markdown(f"""
        <div class="q-card">
          <span class="q-num-tag">Q{idx+1}</span>
          <span class="q-topic-tag">{q.get('topic','')}</span>
          <div class="q-text">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        choice = st.radio(
            f"q_{idx}",
            options=opts,
            index=default,
            key=f"r_{idx}_{st.session_state.radio_key}",
            label_visibility="collapsed",
        )
        if choice is not None:
            chosen = keys[opts.index(choice)]
            st.session_state.user_answers[qid] = chosen

        st.write("")

    st.divider()
    unanswered = total - len(st.session_state.user_answers)
    if unanswered:
        st.warning(f"⚠️  {unanswered} question{'s' if unanswered>1 else ''} not answered yet.")

    if st.button("Submit Quiz ✓", type="primary"):
        st.session_state.elapsed = int(time.time() - st.session_state.start_time)
        with st.spinner("Generating AI feedback…"):
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

    hl = ("Perfect score! 🎉" if pct==100 else "Excellent work! 🌟" if pct>=90
          else "Great job! 💪" if pct>=80 else "Good effort — keep reviewing 📚" if pct>=60
          else "Keep studying — you'll get there! 🚀")

    st.markdown(f"""
    <div class="score-banner">
      <div class="score-num">{correct}/{total}</div>
      <div class="score-pct">{pct}% Score</div>
      <div class="score-hl">{hl}</div>
      <div class="score-chips">
        <span class="sc sc-g">✓ {correct} Correct</span>
        <span class="sc sc-r">✗ {wrong} Wrong</span>
        <span class="sc sc-w">⏱ {m:02d}:{s:02d} Time</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="rev-lbl">Detailed Review &amp; AI Feedback</div>', unsafe_allow_html=True)

    for idx, q in enumerate(questions):
        qid = str(q["id"])
        ua  = st.session_state.user_answers.get(qid)
        ok  = ua == q["correct"]
        cls = "ok" if ok else "bad"
        ic  = "✅" if ok else "❌"

        if ok:
            ans = f'<div class="ans-ok">Your answer: {ua} — {q["options"].get(ua,"")} ✓</div>'
        elif ua:
            ans = (f'<div class="ans-bad">You chose {ua}: {q["options"].get(ua,"")} &nbsp;·&nbsp; '
                   f'Correct: {q["correct"]}: {q["options"][q["correct"]]}</div>')
        else:
            ans = f'<div class="ans-bad">Not answered &nbsp;·&nbsp; Correct: {q["correct"]}: {q["options"][q["correct"]]}</div>'

        exp = st.session_state.explanations.get(qid,"")
        ai  = f'<div class="ai-card"><span>🤖</span><span>{exp}</span></div>' if (not ok and exp) else ""

        st.markdown(f"""
        <div class="rev-card {cls}">
          <div class="rev-hdr"><span class="rev-ic">{ic}</span><span class="rev-tl">Q{idx+1} · {q.get('topic','')}</span></div>
          <div class="rev-q">{q['question']}</div>
          {ans}{ai}
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("↺  Retake Quiz", type="primary"):
            st.session_state.update(user_answers={}, start_time=time.time(),
                explanations={}, step="quiz", radio_key=st.session_state.radio_key+1)
            st.rerun()
    with c2:
        if st.button("↑  Upload New PPT", type="secondary"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
