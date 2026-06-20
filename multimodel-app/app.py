import streamlit as st
from main import ask, PRICES

st.set_page_config(page_title="LLM Arena", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

ALL_MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
]

MODEL_LABELS   = {"google/gemma-4-31b-it:free":"Gemma 4 31B","openai/gpt-oss-20b:free":"GPT-OSS 20B","openai/gpt-oss-120b:free":"GPT-OSS 120B"}
MODEL_PROVIDER = {"google/gemma-4-31b-it:free":"Google","openai/gpt-oss-20b:free":"OpenAI OSS","openai/gpt-oss-120b:free":"OpenAI OSS"}
MODEL_ICON     = {"google/gemma-4-31b-it:free":"🟣","openai/gpt-oss-20b:free":"🟢","openai/gpt-oss-120b:free":"🔵"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"],*{font-family:'Inter',sans-serif!important;box-sizing:border-box;}
.stApp{background:#07080f!important;}
#MainMenu,footer,header,[data-testid="collapsedControl"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0 40px 80px!important;max-width:1200px!important;margin:0 auto!important;}
textarea{background:#12142a!important;border:1.5px solid #23265c!important;border-radius:14px!important;color:#eef0ff!important;font-size:1rem!important;padding:18px!important;line-height:1.75!important;resize:none!important;transition:border-color .2s,box-shadow .2s!important;}
textarea:focus{border-color:#6366f1!important;box-shadow:0 0 0 4px rgba(99,102,241,0.12),0 0 32px rgba(99,102,241,0.08)!important;outline:none!important;}
textarea::placeholder{color:#2a2e5a!important;}
div[data-testid="stCheckbox"] label{color:#7b82c4!important;font-size:0.82rem!important;font-weight:600!important;}
div[data-testid="stCheckbox"] svg{color:#6366f1!important;}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)!important;color:#fff!important;border:none!important;border-radius:14px!important;padding:15px 0!important;font-size:0.97rem!important;font-weight:700!important;letter-spacing:0.02em!important;width:100%!important;box-shadow:0 4px 24px rgba(99,102,241,0.45),0 1px 0 rgba(255,255,255,0.08) inset!important;transition:all .2s!important;cursor:pointer!important;}
div[data-testid="stButton"] button:hover{box-shadow:0 8px 36px rgba(99,102,241,0.65)!important;transform:translateY(-2px)!important;}
div[data-testid="stButton"] button:active{transform:translateY(0)!important;}
@keyframes sk{0%{background-position:-900px 0}100%{background-position:900px 0}}
.sk{background:linear-gradient(90deg,#0d0f20 0%,#171a36 50%,#0d0f20 100%);background-size:900px 100%;animation:sk 1.6s ease-in-out infinite;border-radius:8px;}
</style>""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:72px 20px 52px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:900px;height:500px;background:radial-gradient(ellipse,rgba(99,102,241,0.13) 0%,rgba(139,92,246,0.06) 40%,transparent 70%);pointer-events:none"></div>
  <div style="position:relative">
    <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:999px;padding:7px 20px;margin-bottom:28px;backdrop-filter:blur(8px)">
      <span style="width:6px;height:6px;background:#818cf8;border-radius:50%;box-shadow:0 0 8px #818cf8;display:inline-block;animation:pulse 2s infinite"></span>
      <span style="color:#818cf8;font-size:0.68rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase">AI Benchmark Suite</span>
    </div>
    <h1 style="font-size:3.6rem;font-weight:900;letter-spacing:-0.05em;line-height:1.0;margin:0 0 20px;background:linear-gradient(150deg,#fff 0%,#c7d2fe 45%,#818cf8 75%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
      One Prompt.<br>Every Model.
    </h1>
    <p style="color:#363a6e;font-size:1rem;line-height:1.7;margin:0 auto;max-width:420px;font-weight:400">
      Compare answers, speed &amp; cost across leading LLMs — simultaneously, in real time.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── PROMPT + CONTROLS CARD ────────────────────────────────────────────────────
st.markdown("""<div style="background:linear-gradient(145deg,#0e1028,#0b0d22);border:1.5px solid #1e2248;border-radius:24px;padding:32px;box-shadow:0 32px 96px rgba(0,0,0,0.6),0 0 0 1px rgba(255,255,255,0.03) inset;margin-bottom:6px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
    <div style="width:8px;height:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;box-shadow:0 0 10px rgba(99,102,241,0.7)"></div>
    <span style="color:#3d4280;font-size:0.62rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase">Your Prompt</span>
  </div>
""", unsafe_allow_html=True)

question = st.text_area("q", placeholder="Ask anything — e.g. What is the most important skill for a software engineer in 2025?", height=140, label_visibility="collapsed")

# model chips row
st.markdown("""<div style="display:flex;align-items:center;justify-content:space-between;margin:24px 0 14px">
  <div style="display:flex;align-items:center;gap:8px">
    <div style="width:8px;height:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;box-shadow:0 0 10px rgba(99,102,241,0.7)"></div>
    <span style="color:#3d4280;font-size:0.62rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase">Select Models</span>
  </div>
  <span style="color:#252850;font-size:0.72rem;font-weight:500">All free · via OpenRouter</span>
</div>""", unsafe_allow_html=True)

chk_cols = st.columns(len(ALL_MODELS), gap="small")
selected_models = []
for col, model in zip(chk_cols, ALL_MODELS):
    with col:
        icon = MODEL_ICON[model]
        label = f"{icon}  {MODEL_LABELS[model]}"
        if st.checkbox(label, value=True, key=f"m_{model}"):
            selected_models.append(model)

st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
run = st.button("⚡  Compare Models")
st.markdown("</div>", unsafe_allow_html=True)

# ── VALIDATION ────────────────────────────────────────────────────────────────
if run and not question.strip():
    st.markdown('<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.18);border-radius:12px;padding:14px 18px;color:#f87171;font-size:0.85rem;margin-top:10px">⚠  Please enter a prompt above.</div>', unsafe_allow_html=True)
    st.stop()
if run and not selected_models:
    st.markdown('<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.18);border-radius:12px;padding:14px 18px;color:#f87171;font-size:0.85rem;margin-top:10px">⚠  Select at least one model.</div>', unsafe_allow_html=True)
    st.stop()

# ── RESULTS ───────────────────────────────────────────────────────────────────
if run:
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

    # results header
    q_preview = question[:60] + ("…" if len(question) > 60 else "")
    st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #131630">
  <div style="display:flex;align-items:center;gap:12px">
    <span style="color:#e8eaf6;font-size:1.1rem;font-weight:800;letter-spacing:-0.02em">Results</span>
    <span style="background:#13162e;border:1px solid #1e2248;border-radius:6px;padding:3px 10px;color:#3d4280;font-size:0.68rem;font-weight:600">{len(selected_models)} model{"s" if len(selected_models)!=1 else ""}</span>
  </div>
  <span style="color:#252850;font-size:0.75rem;font-weight:500;font-style:italic">"{q_preview}"</span>
</div>
""", unsafe_allow_html=True)

    cols = st.columns(len(selected_models), gap="large")

    skeleton = """
<div style="background:linear-gradient(145deg,#0e1028,#0b0d22);border:1.5px solid #151830;border-radius:20px;padding:26px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px">
    <div>
      <div class="sk" style="height:15px;width:100px;margin-bottom:8px"></div>
      <div class="sk" style="height:10px;width:64px"></div>
    </div>
    <div class="sk" style="height:24px;width:64px;border-radius:20px"></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:22px">
    <div class="sk" style="height:68px;border-radius:14px"></div>
    <div class="sk" style="height:68px;border-radius:14px"></div>
    <div class="sk" style="height:68px;border-radius:14px"></div>
  </div>
  <div class="sk" style="height:1px;margin-bottom:18px"></div>
  <div class="sk" style="height:11px;margin-bottom:10px"></div>
  <div class="sk" style="height:11px;width:88%;margin-bottom:10px"></div>
  <div class="sk" style="height:11px;width:95%;margin-bottom:10px"></div>
  <div class="sk" style="height:11px;width:74%;margin-bottom:10px"></div>
  <div class="sk" style="height:11px;width:82%"></div>
</div>"""

    slots = []
    for col in cols:
        with col:
            ph = st.empty()
            ph.markdown(skeleton, unsafe_allow_html=True)
            slots.append(ph)

    for i, model in enumerate(selected_models):
        try:
            answer, latency, (in_tok, out_tok), cost = ask(question, model)
            safe    = answer.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            label   = MODEL_LABELS.get(model, model.split("/")[-1])
            provider= MODEL_PROVIDER.get(model, model.split("/")[0])
            icon    = MODEL_ICON.get(model, "⚪")
            lat_col = "#34d399" if latency < 20 else "#fbbf24" if latency < 40 else "#f87171"
            lat_bg  = "rgba(52,211,153,0.08)" if latency < 20 else "rgba(251,191,36,0.08)" if latency < 40 else "rgba(248,113,113,0.08)"
            lat_bd  = "rgba(52,211,153,0.2)"  if latency < 20 else "rgba(251,191,36,0.2)"  if latency < 40 else "rgba(248,113,113,0.2)"

            card = f"""
<div style="background:linear-gradient(145deg,#0e1028,#0b0d22);border:1.5px solid #1a1e42;border-radius:20px;padding:26px;height:100%">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:22px">
    <div>
      <div style="color:#e8eaf6;font-size:1rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:4px">{icon} {label}</div>
      <div style="color:#2a2e58;font-size:0.7rem;font-weight:500">{provider}</div>
    </div>
    <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);border-radius:20px;padding:4px 11px;color:#34d399;font-size:0.62rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;white-space:nowrap">✓ Done</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:22px">
    <div style="background:{lat_bg};border:1px solid {lat_bd};border-radius:14px;padding:14px 8px;text-align:center">
      <div style="color:#2a2e58;font-size:0.55rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">⏱ Latency</div>
      <div style="color:{lat_col};font-size:1.15rem;font-weight:800;letter-spacing:-0.02em">{latency:.1f}s</div>
    </div>
    <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:14px;padding:14px 8px;text-align:center">
      <div style="color:#2a2e58;font-size:0.55rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">🔤 Tokens</div>
      <div style="color:#a5b4fc;font-size:1.15rem;font-weight:800;letter-spacing:-0.02em">{out_tok}</div>
    </div>
    <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:14px;padding:14px 8px;text-align:center">
      <div style="color:#2a2e58;font-size:0.55rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">💵 Cost</div>
      <div style="color:#a5b4fc;font-size:1.15rem;font-weight:800;letter-spacing:-0.02em">${cost:.4f}</div>
    </div>
  </div>
  <div style="height:1px;background:linear-gradient(90deg,transparent,#1e2248 30%,#1e2248 70%,transparent);margin-bottom:18px"></div>
  <div style="color:#4a5090;font-size:0.84rem;line-height:1.85;max-height:400px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:rgba(99,102,241,0.25) transparent">{safe}</div>
</div>"""

        except Exception as e:
            label = MODEL_LABELS.get(model, model.split("/")[-1])
            card = f"""
<div style="background:linear-gradient(145deg,#100a18,#0c0814);border:1.5px solid rgba(239,68,68,0.18);border-radius:20px;padding:26px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
    <div>
      <div style="color:#e8eaf6;font-size:1rem;font-weight:800;margin-bottom:4px">{MODEL_ICON.get(model,"⚪")} {label}</div>
      <div style="color:#2a2e58;font-size:0.7rem">{MODEL_PROVIDER.get(model,"")}</div>
    </div>
    <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:20px;padding:4px 11px;color:#f87171;font-size:0.62rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase">✕ Error</div>
  </div>
  <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:14px;padding:18px;color:#9f4060;font-size:0.8rem;line-height:1.7">{str(e)[:300]}</div>
</div>"""

        slots[i].markdown(card, unsafe_allow_html=True)
