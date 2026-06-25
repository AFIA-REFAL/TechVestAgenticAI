import streamlit as st
from main import ask, PRICES

st.set_page_config(page_title="LLM Arena", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

ALL_MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
    "mistralai/mistral-nemo:free",
]

MODEL_LABELS   = {"google/gemma-4-31b-it:free":"Gemma 4 31B","openai/gpt-oss-20b:free":"GPT-OSS 20B","openai/gpt-oss-120b:free":"GPT-OSS 120B","mistralai/mistral-nemo:free":"Mistral Nemo"}
MODEL_PROVIDER = {"google/gemma-4-31b-it:free":"Google","openai/gpt-oss-20b:free":"OpenAI OSS","openai/gpt-oss-120b:free":"OpenAI OSS","mistralai/mistral-nemo:free":"Mistral"}
MODEL_ICON     = {"google/gemma-4-31b-it:free":"🟣","openai/gpt-oss-20b:free":"🟢","openai/gpt-oss-120b:free":"🔵","mistralai/mistral-nemo:free":"🟠"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"],*{font-family:'Inter',sans-serif!important;box-sizing:border-box;}
.stApp{background:#07080f!important;}
#MainMenu,footer,header,[data-testid="collapsedControl"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:14px 24px 10px!important;max-width:100%!important;}
textarea{background:#0d0f22!important;border:1.5px solid #1e2248!important;border-radius:12px!important;color:#c7d2fe!important;font-size:0.88rem!important;padding:14px!important;line-height:1.65!important;resize:none!important;transition:border-color .2s,box-shadow .2s!important;}
textarea:focus{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,0.15)!important;outline:none!important;}
textarea::placeholder{color:#1e2248!important;}
div[data-testid="stCheckbox"]{margin-bottom:2px!important;}
div[data-testid="stCheckbox"] label{color:#6b72b4!important;font-size:0.78rem!important;font-weight:600!important;}
div[data-testid="stCheckbox"] svg{color:#6366f1!important;}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%)!important;color:#fff!important;border:none!important;border-radius:10px!important;padding:11px 0!important;font-size:0.88rem!important;font-weight:700!important;letter-spacing:0.02em!important;width:100%!important;box-shadow:0 4px 20px rgba(99,102,241,0.4)!important;transition:all .18s!important;cursor:pointer!important;}
div[data-testid="stButton"] button:hover{box-shadow:0 6px 30px rgba(99,102,241,0.65)!important;transform:translateY(-1px)!important;}
div[data-testid="stButton"] button:active{transform:translateY(0)!important;}
@keyframes sk{0%{background-position:-700px 0}100%{background-position:700px 0}}
.sk{background:linear-gradient(90deg,#0d0f20 0%,#181b38 50%,#0d0f20 100%);background-size:700px 100%;animation:sk 1.5s ease-in-out infinite;border-radius:6px;}
div[data-testid="column"]{padding:0 6px!important;}
</style>""", unsafe_allow_html=True)

# ── TOP BAR ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid #0f1128;margin-bottom:16px">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:1.25rem;font-weight:900;letter-spacing:-0.04em;background:linear-gradient(135deg,#fff 0%,#c7d2fe 50%,#818cf8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">⚡ LLM Arena</span>
    <span style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.18);border-radius:999px;padding:3px 11px;color:#6366f1;font-size:0.58rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase">Multi-Model Compare</span>
  </div>
  <div style="display:flex;align-items:center;gap:16px">
    <span style="color:#1e2248;font-size:0.68rem;font-weight:500">4 models</span>
    <span style="color:#1e2248;font-size:0.68rem;font-weight:500">Free tier</span>
    <span style="color:#1e2248;font-size:0.68rem;font-weight:500">OpenRouter</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── MAIN LAYOUT: left panel | right results ───────────────────────────────────
left, right = st.columns([1, 2.6], gap="large")

with left:
    st.markdown('<div style="color:#2a2e5a;font-size:0.58rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:7px">Prompt</div>', unsafe_allow_html=True)
    question = st.text_area("q", placeholder="Ask anything — e.g. What is the most important skill for a software engineer in 2025?", height=130, label_visibility="collapsed")

    st.markdown('<div style="color:#2a2e5a;font-size:0.58rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;margin:14px 0 8px">Models</div>', unsafe_allow_html=True)

    selected_models = []
    for model in ALL_MODELS:
        label = f"{MODEL_ICON[model]}  {MODEL_LABELS[model]}"
        if st.checkbox(label, value=True, key=f"m_{model}"):
            selected_models.append(model)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    run = st.button("⚡  Compare Models")

    if run and not question.strip():
        st.markdown('<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:8px;padding:10px 14px;color:#f87171;font-size:0.78rem;margin-top:8px">⚠ Enter a prompt first.</div>', unsafe_allow_html=True)
        st.stop()
    if run and not selected_models:
        st.markdown('<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:8px;padding:10px 14px;color:#f87171;font-size:0.78rem;margin-top:8px">⚠ Select at least one model.</div>', unsafe_allow_html=True)
        st.stop()

    if not run:
        st.markdown("""
<div style="margin-top:28px;padding:18px;background:rgba(99,102,241,0.04);border:1px dashed rgba(99,102,241,0.12);border-radius:12px;text-align:center">
  <div style="color:#1e2248;font-size:0.75rem;line-height:1.7">Enter a prompt<br>select models<br>click Compare</div>
</div>""", unsafe_allow_html=True)

# ── RIGHT: 2×2 RESULTS GRID ───────────────────────────────────────────────────
with right:
    skeleton = """<div style="background:linear-gradient(145deg,#0e1028,#0b0d22);border:1.5px solid #131630;border-radius:16px;padding:18px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">
    <div><div class="sk" style="height:13px;width:88px;margin-bottom:6px"></div><div class="sk" style="height:9px;width:52px"></div></div>
    <div class="sk" style="height:20px;width:50px;border-radius:20px"></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px">
    <div class="sk" style="height:54px;border-radius:10px"></div>
    <div class="sk" style="height:54px;border-radius:10px"></div>
    <div class="sk" style="height:54px;border-radius:10px"></div>
  </div>
  <div class="sk" style="height:1px;margin-bottom:12px"></div>
  <div class="sk" style="height:9px;margin-bottom:7px"></div>
  <div class="sk" style="height:9px;width:85%;margin-bottom:7px"></div>
  <div class="sk" style="height:9px;width:72%"></div>
</div>"""

    if not run:
        # Empty state placeholder grid
        c1, c2 = st.columns(2, gap="medium")
        for c in [c1, c2]:
            with c:
                st.markdown("""<div style="background:rgba(99,102,241,0.03);border:1.5px dashed rgba(99,102,241,0.08);border-radius:16px;height:200px;display:flex;align-items:center;justify-content:center">
  <span style="color:#131630;font-size:1.5rem">◻</span>
</div>""", unsafe_allow_html=True)
        c3, c4 = st.columns(2, gap="medium")
        for c in [c3, c4]:
            with c:
                st.markdown("""<div style="background:rgba(99,102,241,0.03);border:1.5px dashed rgba(99,102,241,0.08);border-radius:16px;height:200px;display:flex;align-items:center;justify-content:center">
  <span style="color:#131630;font-size:1.5rem">◻</span>
</div>""", unsafe_allow_html=True)

    else:
        # Pad to 4 slots so grid is always 2×2
        padded = (selected_models + [None, None, None, None])[:4]
        row1 = padded[:2]
        row2 = padded[2:]

        slots = {}

        # Row 1 skeletons
        r1c1, r1c2 = st.columns(2, gap="medium")
        for col, model in zip([r1c1, r1c2], row1):
            with col:
                ph = st.empty()
                if model:
                    ph.markdown(skeleton, unsafe_allow_html=True)
                    slots[model] = ph
                else:
                    ph.markdown("", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Row 2 skeletons
        r2c1, r2c2 = st.columns(2, gap="medium")
        for col, model in zip([r2c1, r2c2], row2):
            with col:
                ph = st.empty()
                if model:
                    ph.markdown(skeleton, unsafe_allow_html=True)
                    slots[model] = ph
                else:
                    ph.markdown("", unsafe_allow_html=True)

        # Query models and fill cards
        for model in selected_models:
            try:
                answer, latency, (in_tok, out_tok), cost = ask(question, model)
                safe     = answer.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                label    = MODEL_LABELS.get(model, model.split("/")[-1])
                provider = MODEL_PROVIDER.get(model, model.split("/")[0])
                icon     = MODEL_ICON.get(model, "⚪")
                lat_col  = "#34d399" if latency < 20 else "#fbbf24" if latency < 40 else "#f87171"
                lat_bg   = "rgba(52,211,153,0.08)"  if latency < 20 else "rgba(251,191,36,0.08)"  if latency < 40 else "rgba(248,113,113,0.08)"
                lat_bd   = "rgba(52,211,153,0.2)"   if latency < 20 else "rgba(251,191,36,0.2)"   if latency < 40 else "rgba(248,113,113,0.2)"

                card = f"""<div style="background:linear-gradient(145deg,#0e1028,#0b0d22);border:1.5px solid #1a1e42;border-radius:16px;padding:18px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">
    <div>
      <div style="color:#e8eaf6;font-size:0.9rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:3px">{icon} {label}</div>
      <div style="color:#252850;font-size:0.62rem;font-weight:500">{provider}</div>
    </div>
    <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);border-radius:999px;padding:3px 10px;color:#34d399;font-size:0.56rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;white-space:nowrap">✓ Done</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px">
    <div style="background:{lat_bg};border:1px solid {lat_bd};border-radius:10px;padding:10px 6px;text-align:center">
      <div style="color:#252850;font-size:0.48rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">⏱ Latency</div>
      <div style="color:{lat_col};font-size:1.05rem;font-weight:800;letter-spacing:-0.02em">{latency:.1f}s</div>
    </div>
    <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:10px;padding:10px 6px;text-align:center">
      <div style="color:#252850;font-size:0.48rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">🔤 Tokens</div>
      <div style="color:#a5b4fc;font-size:1.05rem;font-weight:800;letter-spacing:-0.02em">{out_tok}</div>
    </div>
    <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:10px;padding:10px 6px;text-align:center">
      <div style="color:#252850;font-size:0.48rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">💵 Cost</div>
      <div style="color:#a5b4fc;font-size:1.05rem;font-weight:800;letter-spacing:-0.02em">${cost:.4f}</div>
    </div>
  </div>
  <div style="height:1px;background:linear-gradient(90deg,transparent,#1a1e42 30%,#1a1e42 70%,transparent);margin-bottom:12px"></div>
  <div style="color:#4a5090;font-size:0.78rem;line-height:1.8;height:150px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:rgba(99,102,241,0.2) transparent;padding-right:4px">{safe}</div>
</div>"""

            except Exception as e:
                label = MODEL_LABELS.get(model, model.split("/")[-1])
                card = f"""<div style="background:linear-gradient(145deg,#100a18,#0c0814);border:1.5px solid rgba(239,68,68,0.18);border-radius:16px;padding:18px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
    <div>
      <div style="color:#e8eaf6;font-size:0.9rem;font-weight:800;margin-bottom:3px">{MODEL_ICON.get(model,"⚪")} {label}</div>
      <div style="color:#252850;font-size:0.62rem">{MODEL_PROVIDER.get(model,"")}</div>
    </div>
    <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:999px;padding:3px 10px;color:#f87171;font-size:0.56rem;font-weight:700;text-transform:uppercase">✕ Error</div>
  </div>
  <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.12);border-radius:10px;padding:14px;color:#9f4060;font-size:0.76rem;line-height:1.65">{str(e)[:280]}</div>
</div>"""

            slots[model].markdown(card, unsafe_allow_html=True)
