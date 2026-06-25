import streamlit as st
import random
from levels import LEVELS, DOMAINS
from runner import run
from examiner import assess

st.set_page_config(page_title="Prompt Doctor", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700&display=swap');
    
    html, body, [class*="css"], * {
        font-family: 'Inter', sans-serif!important;
    }
    .stApp {
        background-color: #FFFFFF!important;
        color: #1e293b!important;
    }
    .block-container {
        padding: 24px 40px!important;
    }
    .section-label {
        color: #64748b; 
        font-size: 0.75rem; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.05em; 
        margin-bottom: 8px; 
        margin-top: 16px;
    }
    h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] p {
        color: #1e293b!important;
    }
    textarea {
        background-color: #f8fafc!important; 
        color: #1e293b!important;
        border: 1px solid #cbd5e1!important;
        border-radius: 10px!important; 
        font-size: 0.9rem!important;
    }
    textarea:focus {
        border-color: #4f46e5!important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2)!important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #f8fafc!important;
        border: 1px solid #cbd5e1!important;
        border-radius: 10px!important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #1e293b!important;
    }
    div[data-testid="stButton"] button {
        background: #4f46e5!important; 
        color: #ffffff!important; 
        font-weight: 600!important; 
        border-radius: 8px!important; 
        border: none!important;
        width: 100%!important;
        transition: background 0.2s;
    }
    div[data-testid="stButton"] button:hover {
        background: #4338ca!important;
    }
    .progress-ladder {
        display: flex; 
        gap: 10px; 
        margin-bottom: 24px;
    }
    .ladder-step {
        flex: 1; 
        padding: 12px; 
        border-radius: 8px; 
        text-align: center; 
        border: 1px solid #cbd5e1; 
        font-size: 0.8rem; 
        font-weight: 500;
    }
    .ladder-step.locked {
        background-color: #f1f5f9; 
        color: #94a3b8;
    }
    .ladder-step.active {
        background-color: #fef3c7; 
        border-color: #d97706; 
        color: #78350f;
    }
    .ladder-step.passed {
        background-color: #d1fae5; 
        border-color: #059669; 
        color: #065f46;
    }
    .criterion-box {
        border: 1px solid #e2e8f0; 
        border-radius: 12px; 
        background-color: #f8fafc; 
        padding: 16px; 
        margin-bottom: 20px;
    }
    .principle-row {
        padding: 10px 0; 
        border-bottom: 1px solid #e2e8f0;
    }
    .principle-row:last-child {
        border-bottom: none;
    }
    .principle-name {
        font-weight: 600; 
        font-size: 0.9rem;
    }
    .principle-weakness {
        color: #991b1b; 
        font-size: 0.85rem; 
        margin-top: 4px; 
        background-color: #fee2e2; 
        padding: 6px; 
        border-radius: 4px;
        border-left: 3px solid #ef4444;
    }
    .principle-question {
        color: #3730a3; 
        font-size: 0.85rem; 
        margin-top: 4px; 
        font-style: italic;
    }
    .verdict-header {
        padding: 14px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        font-weight: 700; 
        text-align: center;
        letter-spacing: 0.05em;
    }
    .verdict-header.pass {
        background-color: #d1fae5; 
        color: #065f46; 
        border: 1px solid #34d399;
    }
    .verdict-header.revise {
        background-color: #ffedd5; 
        color: #7c2d12; 
        border: 1px solid #fb923c;
    }
    .raw-output {
        background-color: #f1f5f9; 
        color: #334155; 
        border: 1px solid #cbd5e1;
        border-radius: 8px; 
        padding: 16px; 
        font-family: monospace; 
        white-space: pre-wrap; 
        margin-top: 8px;
    }
    .empty-state {
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        color: #64748b;
    }
    [data-testid="stExpander"] {
        background-color: #f8fafc!important;
        border: 1px solid #e2e8f0!important;
    }
    @keyframes floatEmojiUp {
        0% { transform: translateY(105vh) rotate(0deg); opacity: 1; }
        50% { transform: translateY(50vh) rotate(180deg) scale(1.4); opacity: 0.9; }
        100% { transform: translateY(-15vh) rotate(360deg) scale(1); opacity: 0; }
    }
    .emoji-scene-container {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; z-index: 999999; overflow: hidden;
    }
    .moving-celebration-emoji {
        position: absolute; bottom: -50px;
        font-size: 3.5rem;
        animation: floatEmojiUp 5s linear infinite;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid #e2e8f0;margin-bottom:20px">
    <span style="font-size:1.4rem;font-weight:800;color:#1e293b">🩺 Prompt Doctor</span>
    <span style="background:#e0e7ff;border:1px solid #c7d2fe;border-radius:6px;padding:3px 10px;color:#3730a3;font-size:0.7rem;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;">Strict Prompt Assessor</span>
</div>
""", unsafe_allow_html=True)

if "current_level" not in st.session_state: st.session_state.current_level = 1
if "passed_levels" not in st.session_state: st.session_state.passed_levels = set()
if "level_result" not in st.session_state: st.session_state.level_result = None
if "level_llm_response" not in st.session_state: st.session_state.level_llm_response = None
if "active_domain" not in st.session_state: st.session_state.active_domain = "Healthcare"
if "prompt_cache" not in st.session_state: st.session_state.prompt_cache = {}

left, right = st.columns([1.1, 1], gap="large")

with left:
    st.markdown('<div class="section-label">Select Domain Track</div>', unsafe_allow_html=True)
    selected_domain = st.selectbox("Domain Selector", options=list(DOMAINS.keys()), label_visibility="collapsed")
    
    if selected_domain != st.session_state.active_domain:
        st.session_state.active_domain = selected_domain
        st.session_state.current_level = 1
        st.session_state.passed_levels = set()
        st.session_state.level_result = None
        st.session_state.level_llm_response = None
        st.session_state.prompt_cache = {}
        st.rerun()

    domain_data = DOMAINS[st.session_state.active_domain]
    st.markdown(f"<div style='color:#64748b; font-size:0.88rem; margin-bottom:16px;'>ℹ️ {domain_data['description']}</div>", unsafe_allow_html=True)

    curr_lvl = st.session_state.current_level
    level_info = LEVELS[curr_lvl]

    st.markdown(f'<div class="section-label">Task Objective • Level {curr_lvl} — {level_info["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:1.05rem; font-weight:600; color:#0f172a; margin-bottom:12px;'>{level_info['description']}</div>", unsafe_allow_html=True)

    active_sample = domain_data["tasks"][curr_lvl]
    st.text_area("Sample Input Task Data", value=active_sample, height=80, disabled=True)

    cache_key = f"{st.session_state.active_domain}_L{curr_lvl}"
    if cache_key not in st.session_state.prompt_cache:
        st.session_state.prompt_cache[cache_key] = ""

    student_prompt = st.text_area(
        "Your Prompt",
        value=st.session_state.prompt_cache[cache_key],
        placeholder="Design role constraints and instructions here...",
        height=180
    )
    st.session_state.prompt_cache[cache_key] = student_prompt

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Submit Prompt to Examiner"):
        if not student_prompt.strip():
            st.warning("Please type a system prompt candidate before verifying.")
            st.stop()
            
        with st.spinner("Processing execution text..."):
            llm_out = run(student_prompt, active_sample)
            st.session_state.level_llm_response = llm_out
            
            if llm_out.startswith("[ERROR]"):
                st.session_state.level_result = {"error": llm_out}
            else:
                st.session_state.level_result = assess(curr_lvl, student_prompt, llm_out)
        st.rerun()

with right:
    st.markdown('<div class="section-label">Progress Steps Tracker</div>', unsafe_allow_html=True)
    
    progress_html = '<div class="progress-ladder">'
    for l in range(1, 6):
        step_class = "locked"
        if l in st.session_state.passed_levels: step_class = "passed"
        elif l == st.session_state.current_level: step_class = "active"
        progress_html += f'<div class="ladder-step {step_class}"><b>L{l}</b><br>{LEVELS[l]["name"]}</div>'
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Examiner Assessment Verdict Panel</div>', unsafe_allow_html=True)
    res = st.session_state.level_result

    # Defensive guard: res should always be a dict (either {"error": ...}
    # or {"verdict": ..., "principles": [...]}), but if anything upstream
    # ever returns a non-dict, surface a clear message instead of crashing
    # on res.get(...) below.
    if res is not None and not isinstance(res, dict):
        st.error(f"[ERROR] Examiner returned an unexpected response type: {type(res).__name__}")
        res = None

    if res:
        if "error" in res:
            st.error(res["error"])
        else:
            is_pass = res.get("verdict") == "pass"

            st.markdown('<div class="section-label" style="margin-top:0px;">Level Performance Metrics</div>', unsafe_allow_html=True)
            metric_col1, metric_col2 = st.columns(2)

            principles_list = res.get("principles", [])

            # Guard: filter out any non-dict entries before processing
            principles_list = [p for p in principles_list if isinstance(p, dict)]

            total_principles = len(principles_list)
            passed_principles = sum(1 for p in principles_list if p.get("pass", False))
            accuracy_percentage = int((passed_principles / total_principles) * 100) if total_principles > 0 else 0

            with metric_col1:
                st.metric(label="Prompt Accuracy Score", value=f"{accuracy_percentage}%", delta=f"{passed_principles}/{total_principles} Passed")
            with metric_col2:
                st.metric(label="Evaluation Status", value="PASSED ✅" if is_pass else "REVISE ❌")
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

            if is_pass:
                st.markdown('<div class="verdict-header pass">PASSED LEVEL</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="verdict-header revise">REVISION REQUIRED</div>', unsafe_allow_html=True)

            st.markdown('<div class="criterion-box">', unsafe_allow_html=True)
            for p in principles_list:
                # Guard: skip anything that is not a dict
                if not isinstance(p, dict):
                    continue
                p_passed = p.get("pass", False)
                icon = "🟢" if p_passed else "🔴"
                st.markdown(f'<div class="principle-row"><span class="principle-name" style="color:#0f172a;">{icon} {p.get("name", "Unknown")}</span>', unsafe_allow_html=True)
                if not p_passed:
                    if p.get("weakness"):
                        st.markdown(f'<div class="principle-weakness">❌ {p["weakness"]}</div>', unsafe_allow_html=True)
                    if p.get("question"):
                        st.markdown(f'<div class="principle-question">💡 {p["question"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.level_llm_response:
                st.markdown('<div class="section-label">Live Output (LLM Runner)</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="raw-output">{st.session_state.level_llm_response}</div>', unsafe_allow_html=True)

            if is_pass:
                st.session_state.passed_levels.add(curr_lvl)
                if curr_lvl < 5:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("Unlock and Advance to Next Level ▶"):
                        st.session_state.current_level = curr_lvl + 1
                        st.session_state.level_result = None
                        st.session_state.level_llm_response = None
                        st.rerun()
                else:
                    st.balloons()
                    st.success("Track Completed! You have passed all levels in this domain.")
                    
                    excited_emojis = ["🥳", "🎉", "🩺", "🚀", "🔥", "👑", "👏", "💃", "💊", "✨"]
                    emoji_html_canvas = '<div class="emoji-scene-container">'
                    
                    for count in range(45):
                        picked_emoji = random.choice(excited_emojis)
                        horizontal_viewport_left = random.randint(0, 95)
                        animation_delay = random.uniform(0, 3.5)
                        animation_duration = random.uniform(3.5, 6)
                        
                        emoji_html_canvas += f"""
                        <div class="moving-celebration-emoji" 
                             style="left: {horizontal_viewport_left}vw; 
                                    animation-delay: {animation_delay}s; 
                                    animation-duration: {animation_duration}s;">
                             {picked_emoji}
                        </div>"""
                        
                    emoji_html_canvas += '</div>'
                    st.markdown(emoji_html_canvas, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state">Submit your candidate prompt on the left to initiate grading.</div>', unsafe_allow_html=True)