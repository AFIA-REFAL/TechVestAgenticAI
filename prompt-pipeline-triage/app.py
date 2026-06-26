"""
app.py
The Prompt Pipeline -- Support Ticket Triage.
Streamlit UI. Light theme only (enforced via .streamlit/config.toml) --
no dark mode, no theme toggle.
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

from pipeline import run, PipelineError, DEFAULT_MODEL
from sample_inputs import SAMPLE_INPUTS

# Load .env from the same folder as this script, regardless of the
# working directory Streamlit was launched from (fixes silent failures
# when load_dotenv() can't find .env due to a cwd mismatch).
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
env_loaded = load_dotenv(dotenv_path=_ENV_PATH)

st.set_page_config(
    page_title="The Prompt Pipeline · Support Ticket Triage",
    page_icon="🩺",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Minimal extra CSS -- only for the reply container.
# Stays light: white background, light-grey border, dark-grey text.
# Everything else relies on .streamlit/config.toml's theme, not custom CSS.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .reply-box {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1.1rem 1.3rem;
        color: #111827;
        line-height: 1.55;
        font-size: 0.97rem;
    }
    .technique-tag {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        border-radius: 999px;
        padding: 0.1rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 500;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🩺 The Prompt Pipeline — Support Ticket Triage")
st.caption("Three chained prompts · structured JSON handoffs · no RAG · no tools")
st.divider()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Input")

    choice = st.radio(
        "Choose input",
        options=list(SAMPLE_INPUTS.keys()) + ["Custom (paste text)"],
        index=0,
    )

    if choice == "Custom (paste text)":
        default_text = ""
    else:
        default_text = SAMPLE_INPUTS[choice]

    st.divider()
    st.subheader("Options")

    use_critique = st.checkbox(
        "Enable Stage 4 self-check (stretch goal)",
        value=False,
        help="Adds a critic pass that grades the drafted reply and, if it "
             "fails, triggers a single redo of Stage 3.",
    )

    model = st.selectbox(
        "Model",
        options=[
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-001",
        ],
        index=0,
        help="Any OpenRouter model id. Swap this to compare reasoning quality "
             "across models (see stretch goal: model-mix).",
    )

    st.divider()
    if not os.environ.get("OPENROUTER_API_KEY"):
        st.warning("OPENROUTER_API_KEY not found.", icon="⚠️")
        st.caption(f".env path checked: `{_ENV_PATH}`")
        st.caption(f".env file found: {os.path.exists(_ENV_PATH)}")
        st.caption(f"load_dotenv() succeeded: {env_loaded}")
    else:
        st.caption("✅ OPENROUTER_API_KEY loaded")

# ---------------------------------------------------------------------------
# Main panel -- editable input + run button
# ---------------------------------------------------------------------------
raw_text = st.text_area(
    "Raw customer message (editable)",
    value=default_text,
    height=140,
    key=f"input_{choice}",
)

run_clicked = st.button("Run Pipeline", type="primary")

st.divider()

# ---------------------------------------------------------------------------
# Run + render
# ---------------------------------------------------------------------------
if run_clicked:
    if not raw_text.strip():
        st.error("Please enter or select a customer message before running.")
    else:
        trace = {}
        try:
            with st.status("Running pipeline...", expanded=True) as status:
                st.write("Stage 1 — extracting facts from the raw message...")
                from pipeline import stage1_understand, stage2_reason, stage3_produce, stage4_critique

                brief = stage1_understand(raw_text, model=model)
                trace["stage1"] = brief
                st.write("Stage 1 done.")

                st.write("Stage 2 — reasoning about priority and routing...")
                decision = stage2_reason(brief, model=model)
                trace["stage2"] = decision
                st.write("Stage 2 done.")

                st.write("Stage 3 — drafting the reply...")
                draft = stage3_produce(brief, decision, model=model)
                trace["stage3"] = draft
                st.write("Stage 3 done.")

                trace["stage4"] = None
                trace["redo_triggered"] = False

                if use_critique:
                    st.write("Stage 4 — running self-check critique...")
                    critique = stage4_critique(brief, decision, draft, model=model)
                    trace["stage4"] = critique
                    if critique.get("should_redo") and critique.get("issues"):
                        st.write("Critique flagged issues — redoing Stage 3 once...")
                        draft = stage3_produce(
                            brief, decision, model=model,
                            redo_issues=critique["issues"],
                        )
                        trace["stage3"] = draft
                        trace["redo_triggered"] = True
                    st.write("Stage 4 done.")

                trace["input"] = raw_text
                trace["final_reply"] = draft.get("reply_text", "")
                status.update(label="Pipeline complete", state="complete")

            st.session_state["last_trace"] = trace

        except PipelineError as e:
            st.error(
                f"**{e.stage_name} returned invalid JSON after retry.** "
                f"Parse error: `{e.parse_error}`"
            )
            st.code(e.raw_output, language="text")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ---------------------------------------------------------------------------
# Render the last successful trace (glass-box: every stage visible)
# ---------------------------------------------------------------------------
trace = st.session_state.get("last_trace")

if trace:
    st.subheader("Pipeline trace")

    with st.expander("STAGE 1 · Understand", expanded=True):
        st.markdown('<span class="technique-tag">role + structured output</span>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Input to this stage")
            st.code(trace["input"], language="text")
        with col2:
            st.caption("Output from this stage")
            st.json(trace["stage1"])

    with st.expander("STAGE 2 · Reason", expanded=True):
        st.markdown('<span class="technique-tag">chain-of-thought</span>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Input to this stage (Stage 1's JSON)")
            st.json(trace["stage1"])
        with col2:
            st.caption("Output from this stage")
            st.json(trace["stage2"])

    with st.expander("STAGE 3 · Produce", expanded=True):
        st.markdown('<span class="technique-tag">goal-oriented + constraints</span>',
                    unsafe_allow_html=True)
        if trace.get("redo_triggered"):
            st.info("This output is the result of a redo, triggered by Stage 4's critique.")
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Input to this stage (Stage 1 + Stage 2 JSON)")
            st.json({"brief": trace["stage1"], "decision": trace["stage2"]})
        with col2:
            st.caption("Output from this stage")
            st.json(trace["stage3"])

    if trace.get("stage4"):
        with st.expander("STAGE 4 · Critique (stretch goal)", expanded=True):
            st.markdown('<span class="technique-tag">self-check</span>',
                        unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Input to this stage (Stage 1 + 2 + 3 JSON)")
                st.json({
                    "brief": trace["stage1"],
                    "decision": trace["stage2"],
                    "draft": trace["stage3"],
                })
            with col2:
                st.caption("Output from this stage")
                st.json(trace["stage4"])

    st.divider()
    st.subheader("✅ Final structured ticket")

    s1, s2 = trace["stage1"], trace["stage2"]
    ticket_table = {
        "Customer": s1.get("customer_name") or "—",
        "Order ID": s1.get("order_id") or "—",
        "Issue": s1.get("issue_summary", "—"),
        "Sentiment": s1.get("sentiment", "—"),
        "Priority": s2.get("priority", "—"),
        "Route": s2.get("route", "—"),
        "Missing fields": ", ".join(s1.get("missing_fields", [])) or "none",
        "Flagged garbled": "Yes" if s1.get("is_garbled") else "No",
    }
    st.table(ticket_table)

    st.subheader("✅ Final drafted reply")
    st.markdown(
        f'<div class="reply-box">{trace["final_reply"]}</div>',
        unsafe_allow_html=True,
    )

    flags = trace["stage3"].get("flags_for_human", [])
    if flags:
        st.caption("Flags for human review: " + ", ".join(flags))

else:
    st.info("Select or paste a message, then click **Run Pipeline** to see the full trace.")