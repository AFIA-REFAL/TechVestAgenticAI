import os
import json
import re
import time
import requests
import streamlit as st
from pptx import Presentation
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

# ── CONFIG ──────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4-5"

DIFF_HINTS = {
    "Simple":  "Straightforward factual recall — definitions, key terms, basic concepts from the slides.",
    "Medium":  "Balanced mix of recall and scenario-based reasoning across all slides.",
    "Complex": "Deep analytical questions with subtle distinctions, edge-cases, and 'best-among-goods' choices.",
}
DIFF_PROMPTS = {
    "Simple":  "Generate straightforward factual recall questions. Focus on definitions, key terms, and basic concepts directly stated in the slides.",
    "Medium":  "Generate balanced questions mixing factual recall and scenario-based reasoning. Include some 'best answer' questions that require understanding relationships between concepts.",
    "Complex": "Generate challenging analytical questions requiring deep understanding. Focus on edge cases, subtle distinctions, trade-offs, and application of concepts in novel scenarios. Make distractors highly plausible.",
}

st.set_page_config(page_title="AI Quiz Generator", page_icon="🎯", layout="centered")

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #0d1b2a; }
[data-testid="stHeader"] { background: #1a2a3a; }
section[data-testid="stSidebar"] { display: none; }

/* Hide default streamlit footer/menu */
#MainMenu, footer, header { visibility: hidden; }

/* Card wrapper */
.quiz-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 32px 36px;
    margin: 0 auto;
    max-width: 620px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}

/* Nav bar */
.top-nav {
    background: #1a2a3a;
    padding: 12px 24px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}
.nav-brand { color: #fff; font-size: 17px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
.nav-logo {
    background: #f5a623; color: #1a2a3a;
    width: 32px; height: 32px; border-radius: 8px;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 18px;
}
.nav-step { color: #9ca3af; font-size: 14px; }

/* Drop zone */
.drop-hint {
    border: 2px dashed #00b5a3;
    border-radius: 12px;
    padding: 40px 24px;
    text-align: center;
    background: #f8fffe;
    margin-bottom: 16px;
}
.drop-hint h3 { font-size: 18px; color: #1a2a3a; margin-bottom: 6px; }
.drop-hint p  { font-size: 13px; color: #6b7280; }

/* Success / error banners */
.success-box {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; padding: 14px 16px;
    display: flex; align-items: center; gap: 12px;
    margin-top: 12px;
}
.success-box .info strong { display: block; font-size: 14px; color: #1a2a3a; }
.success-box .info span  { font-size: 12px; color: #6b7280; }
.badge-ready {
    background: #22c55e; color: #fff;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
}

/* Source box */
.source-box {
    background: #f4f6f9; border: 1px solid #e5e7eb;
    border-radius: 8px; padding: 12px 16px;
    font-size: 14px; color: #6b7280;
    margin-bottom: 20px;
}

/* Difficulty buttons */
.diff-row { display: flex; gap: 8px; margin-bottom: 8px; }

/* Progress bar */
.prog-wrap { background: #e5e7eb; border-radius: 4px; height: 7px; margin-bottom: 6px; }
.prog-fill  { background: #00b5a3; border-radius: 4px; height: 7px; transition: width .4s; }

/* Option cards */
.option-card {
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    padding: 13px 16px;
    margin-bottom: 9px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: #1a2a3a;
    background: #fff;
    transition: all .15s;
}
.option-card:hover { border-color: #f5a623; background: #fffbf0; }
.option-card.selected { border-color: #f5a623; background: #fffbf0; }
.opt-key {
    width: 28px; height: 28px; border-radius: 50%;
    border: 1.5px solid #e5e7eb;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 13px; flex-shrink: 0;
}
.opt-key.sel { background: #f5a623; color: #fff; border-color: #f5a623; }

/* Timer */
.timer-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #fff7ed; border: 1px solid #fed7aa;
    color: #ea580c; padding: 4px 12px; border-radius: 20px;
    font-size: 14px; font-weight: 700;
}

/* Review items */
.review-correct {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; padding: 13px 15px; margin-bottom: 9px;
}
.review-wrong {
    background: #fef2f2; border: 1px solid #fecaca;
    border-radius: 10px; padding: 13px 15px; margin-bottom: 9px;
}
.ai-explain {
    background: #f0fffe; border: 1px solid #a7f3d0;
    border-radius: 8px; padding: 9px 12px;
    font-size: 12px; color: #065f46;
    margin-top: 8px; display: flex; gap: 8px;
}

/* Score circle placeholder */
.score-big {
    font-size: 52px; font-weight: 900;
    text-align: center; color: #1a2a3a;
}
.score-pct { font-size: 20px; color: #22c55e; font-weight: 700; text-align: center; }
.score-headline { font-size: 20px; font-weight: 700; color: #1a2a3a; margin-bottom: 4px; }
.score-meta { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.pill-c { display:inline-block; background:#f0fdf4; color:#22c55e; border:1px solid #bbf7d0; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; margin-right:8px; }
.pill-w { display:inline-block; background:#fef2f2; color:#ef4444; border:1px solid #fecaca; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; }

/* Streamlit button overrides */
.stButton > button {
    width: 100%;
    border-radius: 9px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 12px !important;
}
.stButton > button[kind="primary"] {
    background: #f5a623 !important;
    color: #fff !important;
    border: none !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important;
    border: 1.5px solid #e5e7eb !important;
    color: #1a2a3a !important;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE DEFAULTS ───────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": "upload",           # upload | config | quiz | results
        "slides": [],
        "filename": "",
        "slide_count": 0,
        "word_count": 0,
        "preview": "",
        "num_questions": 10,
        "difficulty": "Medium",
        "questions": [],
        "user_answers": {},         # {q_id: "A"|"B"|"C"|"D"}
        "current_q": 0,
        "start_time": None,
        "elapsed": 0,
        "explanations": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── BACKEND HELPERS ──────────────────────────────────────────────────────────
def extract_pptx(file_bytes):
    prs = Presentation(BytesIO(file_bytes))
    slides, total_words = [], 0
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = para.text.strip()
                    if t:
                        texts.append(t)
        combined = " ".join(texts)
        if combined:
            slides.append({"slide": i, "text": combined})
            total_words += len(combined.split())
    return slides, total_words


def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Quiz Generator",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def generate_mcqs(slides, num_q, difficulty):
    slide_text = "\n\n".join(f"[Slide {s['slide']}]: {s['text']}" for s in slides)
    prompt = f"""You are an expert quiz designer. Based on the slide content below, generate exactly {num_q} multiple-choice questions.

DIFFICULTY: {difficulty}
INSTRUCTION: {DIFF_PROMPTS[difficulty]}

SLIDE CONTENT:
{slide_text}

RULES:
- Exactly 4 options per question labeled A, B, C, D
- Only one correct answer; three plausible distractors
- Balance questions across all slides/topics
- Favor scenario-based questions over pure recall

Return ONLY a valid JSON array — no markdown fences, no extra text:
[
  {{
    "id": 1,
    "question": "Question text?",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct": "B",
    "topic": "Brief topic label"
  }}
]"""
    raw = call_llm(prompt)
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    return json.loads(raw)


def generate_explanations(questions, user_answers):
    wrong = [
        q for q in questions
        if user_answers.get(str(q["id"])) and user_answers[str(q["id"])] != q["correct"]
    ]
    if not wrong:
        return {}

    block = "\n\n".join(
        f"Q{w['id']}: {w['question']}\n"
        f"Student answered: {user_answers[str(w['id'])]} — {w['options'].get(user_answers[str(w['id'])], '')}\n"
        f"Correct answer: {w['correct']} — {w['options'][w['correct']]}"
        for w in wrong
    )
    prompt = f"""A student answered the following questions incorrectly. For each, write a concise 1-2 sentence explanation of WHY their answer is wrong and WHY the correct answer is right.

{block}

Return ONLY a JSON object mapping question id (string) to explanation string:
{{"1": "Explanation...", "3": "Explanation..."}}"""
    raw = call_llm(prompt)
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    return json.loads(raw)

# ── NAV BAR ─────────────────────────────────────────────────────────────────
step_labels = {
    "upload":  "Step 1 of 3 — Upload",
    "config":  "Step 2 of 3 — Configure",
    "quiz":    f"Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}",
    "results": "Quiz Complete",
}
st.markdown(f"""
<div class="top-nav">
  <div class="nav-brand"><span class="nav-logo">Q</span> AI Quiz Generator</div>
  <span class="nav-step">{step_labels.get(st.session_state.step, '')}</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — UPLOAD
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "upload":
    st.markdown('<div class="drop-hint"><h3>📂 Upload your .pptx file</h3><p>.pptx only · max 25 MB</p></div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload your PowerPoint file", type=["pptx"], label_visibility="collapsed")

    if uploaded:
        if not uploaded.name.lower().endswith(".pptx"):
            st.error("Only .pptx files are supported.")
        elif uploaded.size > 25 * 1024 * 1024:
            st.error("File exceeds 25 MB limit.")
        else:
            with st.spinner("Parsing your presentation…"):
                try:
                    slides, word_count = extract_pptx(uploaded.read())
                    if not slides:
                        st.error("No text content found in this file.")
                    else:
                        st.session_state.slides = slides
                        st.session_state.filename = uploaded.name
                        st.session_state.slide_count = len(slides)
                        st.session_state.word_count = word_count
                        st.session_state.preview = slides[0]["text"][:220]
                        st.markdown(f"""
                        <div class="success-box">
                          <span style="font-size:22px">✅</span>
                          <div class="info" style="flex:1">
                            <strong>{uploaded.name}</strong>
                            <span>Parsed successfully · {len(slides)} slides · {word_count:,} words extracted</span>
                          </div>
                          <span class="badge-ready">Ready</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Preview: {st.session_state.preview}…")
                except Exception as e:
                    st.error(f"Failed to parse file: {e}")

    disabled = not bool(st.session_state.slides)
    if st.button("Continue →", type="primary", disabled=disabled):
        st.session_state.step = "config"
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — CONFIGURE
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "config":
    st.markdown(f'<div class="source-box">📄 {st.session_state.filename} · {st.session_state.slide_count} slides</div>', unsafe_allow_html=True)

    st.session_state.num_questions = st.slider(
        "Number of questions", min_value=5, max_value=30,
        value=st.session_state.num_questions, step=1,
    )

    st.markdown("**Difficulty level**")
    col1, col2, col3 = st.columns(3)
    for col, label in zip([col1, col2, col3], ["Simple", "Medium", "Complex"]):
        with col:
            is_active = st.session_state.difficulty == label
            style = "background:#f5a623;color:#fff;border:none;" if is_active else "background:#f4f6f9;color:#1a2a3a;border:1px solid #e5e7eb;"
            if st.button(label, key=f"diff_{label}",
                         type="primary" if is_active else "secondary"):
                st.session_state.difficulty = label
                st.rerun()

    st.caption(DIFF_HINTS[st.session_state.difficulty])
    st.write("")

    if st.button("⚡ Generate Quiz", type="primary"):
        with st.spinner(f"AI is crafting {st.session_state.num_questions} {st.session_state.difficulty} questions…"):
            try:
                qs = generate_mcqs(
                    st.session_state.slides,
                    st.session_state.num_questions,
                    st.session_state.difficulty,
                )
                st.session_state.questions = qs
                st.session_state.user_answers = {}
                st.session_state.current_q = 0
                st.session_state.start_time = time.time()
                st.session_state.step = "quiz"
                st.rerun()
            except json.JSONDecodeError:
                st.error("AI returned a malformed response. Please try again.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — QUIZ
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz":
    questions = st.session_state.questions
    total = len(questions)
    i = st.session_state.current_q
    q = questions[i]
    qid = str(q["id"])

    # Progress + timer
    pct = int(((i + 1) / total) * 100)
    elapsed = int(time.time() - (st.session_state.start_time or time.time()))
    mins, secs = divmod(elapsed, 60)

    col_prog, col_timer = st.columns([4, 1])
    with col_prog:
        st.markdown(f"""
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
        """, unsafe_allow_html=True)
    with col_timer:
        st.markdown(f'<div class="timer-badge">⏱ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)

    # Update nav step
    st.markdown(f"""
    <p style="color:#00b5a3;font-size:12px;font-weight:700;letter-spacing:.08em;margin-bottom:6px">
    QUESTION {i + 1} OF {total}</p>
    <p style="font-size:18px;font-weight:700;color:#1a2a3a;margin-bottom:18px;line-height:1.4">
    {q['question']}</p>
    """, unsafe_allow_html=True)

    # Answer options
    selected = st.session_state.user_answers.get(qid)
    for key in ["A", "B", "C", "D"]:
        is_sel = selected == key
        key_style = "sel" if is_sel else ""
        card_class = "option-card selected" if is_sel else "option-card"
        st.markdown(f"""
        <div class="{card_class}">
          <span class="opt-key {key_style}">{key}</span>
          <span>{q['options'][key]}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Select {key}", key=f"opt_{i}_{key}", use_container_width=True,
                     help=q["options"][key]):
            st.session_state.user_answers[qid] = key
            st.rerun()

    st.write("")
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if i > 0:
            if st.button("← Previous", type="secondary"):
                st.session_state.current_q -= 1
                st.rerun()
    with col_next:
        label = "Submit Quiz ✓" if i == total - 1 else "Next →"
        if st.button(label, type="primary"):
            if i < total - 1:
                st.session_state.current_q += 1
                st.rerun()
            else:
                st.session_state.elapsed = int(time.time() - st.session_state.start_time)
                with st.spinner("Generating AI feedback for your answers…"):
                    try:
                        exp = generate_explanations(questions, st.session_state.user_answers)
                        st.session_state.explanations = exp
                    except Exception:
                        st.session_state.explanations = {}
                st.session_state.step = "results"
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — RESULTS
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "results":
    questions = st.session_state.questions
    total = len(questions)
    correct_count = sum(
        1 for q in questions
        if st.session_state.user_answers.get(str(q["id"])) == q["correct"]
    )
    wrong_count = total - correct_count
    pct = round((correct_count / total) * 100) if total else 0

    # Score header
    col_score, col_info = st.columns([1, 2])
    with col_score:
        color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 60 else "#ef4444"
        st.markdown(f"""
        <div style="text-align:center;padding:12px 0">
          <div style="font-size:48px;font-weight:900;color:#1a2a3a">{correct_count}/{total}</div>
          <div style="font-size:20px;font-weight:700;color:{color}">{pct}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col_info:
        headline = (
            "Perfect score! 🎉" if pct == 100 else
            f"Nice work — {correct_count} correct, {wrong_count} to review" if pct >= 80 else
            f"Good effort — {correct_count} correct, {wrong_count} to review" if pct >= 60 else
            f"Keep studying — {correct_count} correct, {wrong_count} to review"
        )
        mins, secs = divmod(st.session_state.elapsed, 60)
        st.markdown(f"""
        <div class="score-headline">{headline}</div>
        <div class="score-meta">{st.session_state.difficulty} difficulty · {st.session_state.slide_count}-slide deck · {mins:02d}:{secs:02d} taken</div>
        <span class="pill-c">✓ {correct_count} correct</span>
        <span class="pill-w">✗ {wrong_count} wrong</span>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<p style="color:#00b5a3;font-size:12px;font-weight:700;letter-spacing:.08em">REVIEW & AI FEEDBACK</p>', unsafe_allow_html=True)

    for idx, q in enumerate(questions):
        qid = str(q["id"])
        user_ans = st.session_state.user_answers.get(qid)
        is_correct = user_ans == q["correct"]
        box_class = "review-correct" if is_correct else "review-wrong"
        icon = "✅" if is_correct else "❌"

        if is_correct:
            ans_line = f'<span style="color:#22c55e">Your answer: {user_ans} ({q["options"].get(user_ans,"")}) — correct</span>'
        elif user_ans:
            ans_line = f'<span style="color:#ef4444">Your answer: {user_ans} ({q["options"].get(user_ans,"")}) · Correct: {q["correct"]} ({q["options"][q["correct"]]})</span>'
        else:
            ans_line = f'<span style="color:#ef4444">Not answered · Correct: {q["correct"]} ({q["options"][q["correct"]]})</span>'

        explanation_html = ""
        exp = st.session_state.explanations.get(qid, "")
        if not is_correct and exp:
            explanation_html = f"""
            <div class="ai-explain">
              <span>🤖</span><span>{exp}</span>
            </div>"""

        st.markdown(f"""
        <div class="{box_class}">
          <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:4px">
            <span style="font-size:17px">{icon}</span>
            <strong style="font-size:14px;color:#1a2a3a">Q{idx+1} · {q.get('topic','Question')}</strong>
          </div>
          <p style="font-size:13px;margin:0 0 2px 27px;color:#1a2a3a">{q['question']}</p>
          <p style="font-size:12px;margin:0 0 0 27px">{ans_line}</p>
          {explanation_html}
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    col_r, col_n = st.columns(2)
    with col_r:
        if st.button("↺ Retake Quiz", type="primary"):
            st.session_state.user_answers = {}
            st.session_state.current_q = 0
            st.session_state.start_time = time.time()
            st.session_state.explanations = {}
            st.session_state.step = "quiz"
            st.rerun()
    with col_n:
        if st.button("↓ Upload New PPT", type="secondary"):
            for key in ["slides","filename","slide_count","word_count","preview",
                        "questions","user_answers","current_q","start_time","elapsed","explanations"]:
                st.session_state[key] = [] if key in ["slides","questions"] else {} if key in ["user_answers","explanations"] else "" if key in ["filename","preview"] else 0 if key in ["slide_count","word_count","current_q","elapsed"] else 10 if key == "num_questions" else None
            st.session_state.difficulty = "Medium"
            st.session_state.step = "upload"
            st.rerun()
