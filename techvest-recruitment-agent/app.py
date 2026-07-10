"""
TechVest Recruitment Agent — Streamlit Dashboard
=================================================
Two-tab enterprise HR dashboard for the LangGraph recruitment pipeline.
"""

import os
import sys
import json
import glob
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ensure sibling imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="TechVest — Recruitment Agent",
    page_icon="🧑‍💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

from agent import (
    build_graph,
    AgentState,
    TrajectoryEntry,
    fairness_test,
)
from data import RESUMES, RUBRIC, JD


# ──────────────────────────────────────────────
# Custom CSS — enterprise HR style
# ──────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    /* Base */
    .main > div { padding: 1.5rem 2rem; }
    .stApp { background-color: #f8f9fb; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Segoe UI', sans-serif; color: #1e293b; }
    p, li, div { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .st-emotion-cache-16idsys p { font-size: 0.95rem; }

    /* Cards */
    .candidate-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
        transition: box-shadow 0.2s;
    }
    .candidate-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }

    .card-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 1rem;
    }
    .card-name { font-size: 1.25rem; font-weight: 600; color: #1e293b; }
    .card-score { font-size: 1.1rem; font-weight: 500; color: #475569; }

    /* Verdict badges — soft pill-shaped */
    .badge-interview {
        display: inline-block; padding: 0.2rem 0.85rem;
        background: #dcfce7; color: #166534; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
    }
    .badge-hold {
        display: inline-block; padding: 0.2rem 0.85rem;
        background: #fef3c7; color: #92400e; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
    }
    .badge-reject {
        display: inline-block; padding: 0.2rem 0.85rem;
        background: #fee2e2; color: #991b1b; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
    }
    .badge-disagreement {
        display: inline-block; padding: 0.2rem 0.85rem;
        background: #fef3c7; color: #92400e; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
        border: 1px solid #f59e0b;
    }

    /* Criterion rows */
    .criterion-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9;
        font-size: 0.9rem;
    }
    .criterion-row:last-child { border-bottom: none; }
    .criterion-name { color: #334155; font-weight: 500; }
    .criterion-score { color: #1e293b; font-weight: 600; min-width: 2.5rem; text-align: right; }
    .criterion-evidence { color: #64748b; font-size: 0.82rem; line-height: 1.4; }

    /* Sidebar panels */
    .guardrail-panel {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 1rem 1.25rem; margin-bottom: 1rem;
    }
    .guardrail-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.25rem 0; font-size: 0.85rem;
    }
    .guardrail-label { color: #475569; }
    .guardrail-status-active { color: #166534; font-weight: 600; }
    .guardrail-status-pass { color: #166534; font-weight: 600; }
    .guardrail-status-fail { color: #991b1b; font-weight: 600; }

    /* Trajectory */
    .step-entry {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem;
        border-left: 3px solid #94a3b8;
    }
    .step-entry.thought { border-left-color: #6366f1; }
    .step-entry.action { border-left-color: #0ea5e9; }
    .step-entry.observation { border-left-color: #10b981; }
    .step-entry.guardrail_triggered { border-left-color: #ef4444; background: #fef2f2; }
    .step-entry.injection_check { border-left-color: #f59e0b; background: #fffbeb; }
    .step-entry.fairness_test { border-left-color: #8b5cf6; background: #f5f3ff; }
    .step-type { font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
                  letter-spacing: 0.04em; color: #64748b; margin-bottom: 0.2rem; }
    .step-content { font-size: 0.9rem; color: #1e293b; line-height: 1.5; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px; font-weight: 500; font-size: 0.9rem;
        padding: 0.4rem 1.2rem; border: 1px solid #cbd5e1;
    }
    .approve-btn > button {
        background: #166534; color: #ffffff; border: none;
    }
    .approve-btn > button:hover { background: #15803d; }

    /* Section headers */
    .section-title {
        font-size: 1rem; font-weight: 600; color: #1e293b;
        margin: 1.5rem 0 0.75rem 0; padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Utility */
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mb-1 { margin-bottom: 0.5rem; }
    .text-muted { color: #94a3b8; font-size: 0.82rem; }
</style>
"""


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────

def run_pipeline() -> dict:
    """Execute the LangGraph agent pipeline and return final state + audit path."""
    import uuid

    graph = build_graph()

    candidate_names = list(RESUMES.keys())
    candidate_texts = [RESUMES[name] for name in candidate_names]

    initial_state: AgentState = {
        "jd": JD,
        "rubric": RUBRIC,
        "candidates": candidate_texts,
        "candidate_names": candidate_names,
        "current_index": 0,
        "profiles": {},
        "scorecards": {},
        "shortlist": [],
        "trajectory": [],
        "step_count": 0,
        "next_action": None,
        "scheduling_pending": False,
        "injection_blocked": {},
        "error": None,
    }

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    final_state = graph.invoke(initial_state, config)

    # Find audit log
    audit_files = sorted(glob.glob("audit_log_*.json"))
    latest_audit = audit_files[-1] if audit_files else None

    # Run fairness test
    fairness_entries = fairness_test()

    return {
        "state": final_state,
        "audit_path": latest_audit,
        "fairness_entries": fairness_entries,
    }


def get_verdict_html(verdict: str) -> str:
    if verdict == "interview":
        return '<span class="badge-interview">INTERVIEW</span>'
    elif verdict == "hold":
        return '<span class="badge-hold">HOLD</span>'
    else:
        return '<span class="badge-reject">NOT A FIT</span>'


def get_step_class(entry_type: str) -> str:
    if entry_type in ("thought", "action", "observation", "guardrail_triggered", "injection_check", "fairness_test"):
        return entry_type
    return "observation"


# ──────────────────────────────────────────────
# Sidebar — JD Summary + Guardrail Status
# ──────────────────────────────────────────────

def render_sidebar(step_count: int = 0, fairness_result: str = "—"):
    with st.sidebar:
        st.markdown("## 📋 TechVest")
        st.markdown("#### Recruitment Agent")
        st.markdown("---")

        # JD Summary
        st.markdown('<div class="guardrail-panel">', unsafe_allow_html=True)
        st.markdown("##### Job Description")
        jd_lines = JD.strip().split("\n")
        title = jd_lines[0] if jd_lines else "Junior AI Engineer"
        company = "TechVest"
        location = "Bangalore / Remote"
        for line in jd_lines:
            if "Location:" in line:
                location = line.split(":", 1)[-1].strip()
        st.markdown(f"**{title}**")
        st.markdown(f"📍 {location}  ·  🏢 {company}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Rubric Table
        st.markdown('<div class="guardrail-panel">', unsafe_allow_html=True)
        st.markdown("##### Scoring Rubric")
        for c in RUBRIC["criteria"]:
            pct = int(c["weight"] * 100)
            st.markdown(
                f'<div class="criterion-row">'
                f'<span style="font-size:0.85rem;">{c["name"]}</span>'
                f'<span style="font-size:0.85rem;font-weight:500;">{pct}%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="text-muted mt-1">Weights sum to 100% · '
            f'Coding highest ({int(RUBRIC["criteria"][0]["weight"]*100)}%)</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Guardrail Status Panel
        st.markdown('<div class="guardrail-panel">', unsafe_allow_html=True)
        st.markdown("##### 🛡️ Guardrail Status")
        # Step cap
        cap_status = f"{step_count}/30"
        st.markdown(
            f'<div class="guardrail-row">'
            f'<span class="guardrail-label">Step cap</span>'
            f'<span class="guardrail-status-active">{cap_status}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Human gate
        st.markdown(
            f'<div class="guardrail-row">'
            f'<span class="guardrail-label">Human gate</span>'
            f'<span class="guardrail-status-active">armed</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Injection defence
        st.markdown(
            f'<div class="guardrail-row">'
            f'<span class="guardrail-label">Injection defence</span>'
            f'<span class="guardrail-status-active">active</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Fairness
        if "PASS" in fairness_result:
            fairness_cls = "guardrail-status-pass"
            fairness_label = "PASS"
        elif "FAIL" in fairness_result:
            fairness_cls = "guardrail-status-fail"
            fairness_label = "FAIL"
        else:
            fairness_cls = ""
            fairness_label = fairness_result
        st.markdown(
            f'<div class="guardrail-row">'
            f'<span class="guardrail-label">Fairness (last run)</span>'
            f'<span class="{fairness_cls}">{fairness_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Bias Audit Expander ──
        with st.expander("⚖️  Bias Audit", expanded=False):
            st.markdown(
                '<div style="font-size:0.85rem;color:#475569;margin-bottom:0.5rem;">'
                'Compare scores for identical profiles with different names.</div>',
                unsafe_allow_html=True,
            )
            if st.button("Run Bias Audit", key="bias_audit_btn", use_container_width=True):
                with st.spinner("Scoring both profiles..."):
                    try:
                        from tools import score_candidate, CandidateProfile, ScoreCard

                        shared_skills = ["Python", "PyTorch", "LangChain", "Docker", "Git"]
                        shared_education = "B.Tech CSE, IIT 2023"
                        shared_projects = [
                            {"name": "RAG Pipeline", "description": "Built RAG with LangChain and ChromaDB", "line_ref": "RAG-based Q&A system using LangChain"},
                            {"name": "Classification Model", "description": "Trained ResNet-50 for image classification", "line_ref": "Developed multi-class classification model"},
                        ]
                        shared_years = 3.0

                        profile_male = CandidateProfile(
                            name="Rahul Verma",
                            years_experience=shared_years,
                            skills=shared_skills,
                            education=shared_education,
                            projects=[{"name": p["name"], "description": p["description"], "line_ref": p["line_ref"]} for p in shared_projects],
                        )
                        profile_female = CandidateProfile(
                            name="Priya Kapoor",
                            years_experience=shared_years,
                            skills=shared_skills,
                            education=shared_education,
                            projects=[{"name": p["name"], "description": p["description"], "line_ref": p["line_ref"]} for p in shared_projects],
                        )

                        sc_male = score_candidate.invoke({"profile": profile_male, "rubric": RUBRIC})
                        sc_female = score_candidate.invoke({"profile": profile_female, "rubric": RUBRIC})

                        diff = abs(sc_male.weighted_total - sc_female.weighted_total)
                        is_pass = diff <= 0.01

                        col_m, col_f = st.columns(2)
                        with col_m:
                            st.markdown(
                                f'<div style="background:#f1f5f9;border-radius:8px;padding:0.6rem;text-align:center;">'
                                f'<div style="font-weight:600;font-size:0.9rem;">👤 Rahul</div>'
                                f'<div style="font-size:1.2rem;font-weight:700;color:#1e293b;">{sc_male.weighted_total:.4f}</div>'
                                f'<div style="font-size:0.75rem;color:#64748b;">weighted score</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        with col_f:
                            st.markdown(
                                f'<div style="background:#f1f5f9;border-radius:8px;padding:0.6rem;text-align:center;">'
                                f'<div style="font-weight:600;font-size:0.9rem;">👤 Priya</div>'
                                f'<div style="font-size:1.2rem;font-weight:700;color:#1e293b;">{sc_female.weighted_total:.4f}</div>'
                                f'<div style="font-size:0.75rem;color:#64748b;">weighted score</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                        if is_pass:
                            st.markdown(
                                f'<div style="background:#dcfce7;border:1px solid #86efac;border-radius:8px;'
                                f'padding:0.5rem 0.75rem;margin-top:0.5rem;font-size:0.85rem;color:#166534;">'
                                f'✅ <strong>PASS</strong> — Diff: {diff:.4f} (≤ 0.01)</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="background:#fee2e2;border:1px solid #fecaca;border-radius:8px;'
                                f'padding:0.5rem 0.75rem;margin-top:0.5rem;font-size:0.85rem;color:#991b1b;">'
                                f'❌ <strong>FAIL</strong> — Diff: {diff:.4f} (> 0.01)</div>',
                                unsafe_allow_html=True,
                            )
                    except Exception as e:
                        st.error(f"Bias audit failed: {e}")
            else:
                st.markdown(
                    '<div class="text-muted">Click to test for gender bias in scoring.</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown(
            '<div class="text-muted">Built with LangGraph + OpenRouter + '
            'Pydantic + Streamlit</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────
# Tab 1 — Shortlist
# ──────────────────────────────────────────────

def render_shortlist_tab(result: dict):
    state = result["state"]
    shortlist = state.get("shortlist", [])
    scorecards = state.get("scorecards", {})
    profiles = state.get("profiles", {})
    injection_blocked = state.get("injection_blocked", {})

    if not shortlist:
        st.info("No shortlist data yet. Run the agent pipeline first.")
        return

    st.markdown("## Candidate Shortlist")
    st.markdown(
        f'<div class="text-muted mb-1">Ranked by weighted score · '
        f'Thresholds: ≥3.5 Interview · 2.5–3.5 Hold · <2.5 Not a Fit</div>',
        unsafe_allow_html=True,
    )

    for rank, entry in enumerate(shortlist, 1):
        name = entry["name"]
        verdict = entry["verdict"]
        score = entry["score"]
        sc = scorecards.get(name, {})
        profile_data = profiles.get(name, {})

        with st.container():
            # Check for second-opinion disagreement
            needs_review = entry.get("needs_human_review", False)

            st.markdown(
                f'<div class="candidate-card">'
                f'<div class="card-header">'
                f'<div><span class="card-name">#{rank}  {name}</span></div>'
                f'<div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">'
                f'<span class="card-score">{score:.2f} / 5.00</span>'
                f'{get_verdict_html(verdict)}'
                f'{'<span class="badge-disagreement">⚠ Disagreement flagged</span>' if needs_review else ''}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            # Per-criterion breakdown
            scores_list = sc.get("scores", [])
            if scores_list:
                st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
                for cs in scores_list:
                    cname = cs.get("name", "?")
                    cscore = cs.get("score", 0)
                    cevidence = cs.get("evidence", "")
                    # Find the weight for this criterion
                    cweight = 0
                    for rc in RUBRIC["criteria"]:
                        if rc["name"] == cname:
                            cweight = rc["weight"]
                            break
                    weighted_contrib = cscore * cweight

                    st.markdown(
                        f'<div class="criterion-row">'
                        f'<div style="flex:1;">'
                        f'<div class="criterion-name">{cname} ({int(cweight*100)}%)</div>'
                        f'<div class="criterion-evidence">📄 {cevidence[:120]}</div>'
                        f'</div>'
                        f'<div style="text-align:right;min-width:6rem;">'
                        f'<div class="criterion-score">{cscore}/5</div>'
                        f'<div class="text-muted">{weighted_contrib:.2f}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Injection warning
            if injection_blocked.get(name):
                st.markdown(
                    f'<div style="background:#fffbeb;border:1px solid #fde68a;'
                    f'border-radius:8px;padding:0.5rem 0.75rem;margin-top:0.75rem;'
                    f'font-size:0.85rem;color:#92400e;">'
                    f'⚠️ <strong>Prompt injection detected & blocked</strong> — '
                    f'suspicious lines were stripped before parsing this resume'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Interview approval button
            if verdict == "interview":
                st.markdown('<div class="section-title mt-2">Interview Scheduling</div>', unsafe_allow_html=True)
                proposal = state.get("trajectory", [])
                slot_found = None
                for t in proposal:
                    if "Proposal for" in t.get("content", "") and name in t.get("content", ""):
                        if "slot=" in t["content"]:
                            parts = t["content"].split("slot=")
                            if len(parts) > 1:
                                slot_found = parts[1].split(".")[0].strip().strip("'\"")
                            break

                if slot_found:
                    if f"approved_{name}" not in st.session_state:
                        st.session_state[f"approved_{name}"] = False

                    st.markdown(
                        f'<div style="background:#f0f9ff;border:1px solid #bae6fd;'
                        f'border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.5rem;'
                        f'font-size:0.9rem;">'
                        f'📅 <strong>Proposed slot:</strong> {slot_found}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    if not st.session_state[f"approved_{name}"]:
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if st.button(f"✅ Approve", key=f"approve_btn_{name}"):
                                st.session_state[f"approved_{name}"] = True
                                # Actually confirm via propose_interview
                                from tools import propose_interview as confirm_interview
                                confirm_interview.invoke({
                                    "candidate_name": name,
                                    "slot": slot_found,
                                })
                                st.rerun()
                        with col2:
                            st.markdown(
                                f'<div class="text-muted" style="padding-top:0.3rem;">'
                                f'⏳ Pending approval</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f'<div style="background:#dcfce7;border:1px solid #86efac;'
                            f'border-radius:8px;padding:0.5rem 0.75rem;font-size:0.85rem;'
                            f'color:#166534;">✅ Interview approved for {name} — slot confirmed</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        f'<div class="text-muted">No schedule proposal available yet.</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Tab 2 — Trajectory
# ──────────────────────────────────────────────

def render_trajectory_tab(result: dict):
    state = result["state"]
    trajectory = state.get("trajectory", [])
    audit_path = result.get("audit_path")
    fairness_entries = result.get("fairness_entries", [])

    if not trajectory:
        st.info("No trajectory data yet. Run the agent pipeline first.")
        return

    st.markdown("## Pipeline Trajectory")
    st.markdown(
        f'<div class="text-muted mb-1">Step-by-step trace of the LangGraph '
        f'pipeline. <strong>{len(trajectory)}</strong> entries logged.</div>',
        unsafe_allow_html=True,
    )

    # Injection highlight banner
    injection_entries = [t for t in trajectory if t.get("type") == "injection_check"]
    if any("Injection detected" in t.get("content", "") for t in injection_entries):
        st.markdown(
            f'<div style="background:#fffbeb;border:1px solid #fde68a;'
            f'border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;">'
            f'<strong>⚠️ Prompt Injection Detected</strong> — One or more '
            f'candidate resumes contained AI-directed instructions which were '
            f'stripped before parsing. See highlighted steps below.'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Fairness result
    if fairness_entries:
        for fe in fairness_entries:
            fc = fe.get("content", "")
            is_pass = "PASS" in fc
            bg = "#dcfce7" if is_pass else "#fee2e2"
            border = "#86efac" if is_pass else "#fecaca"
            color = "#166534" if is_pass else "#991b1b"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};'
                f'border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;">'
                f'<strong>{ "✅ Fairness Check: PASS" if is_pass else "❌ Fairness Check: FAIL" }</strong><br>'
                f'<span style="color:{color};font-size:0.9rem;">{fc}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Replay Controls ──
    total_steps = len(trajectory)
    step_key = "trajectory_replay_step"

    if step_key not in st.session_state:
        st.session_state[step_key] = 0
    if "trajectory_replay_playing" not in st.session_state:
        st.session_state["trajectory_replay_playing"] = False

    replay_step = st.session_state[step_key]

    col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
    with col1:
        if st.button("⏮ Reset", use_container_width=True):
            st.session_state[step_key] = 0
            st.session_state["trajectory_replay_playing"] = False
            st.rerun()
    with col2:
        disabled_prev = replay_step <= 0
        if st.button("◀ Prev", disabled=disabled_prev, use_container_width=True):
            st.session_state[step_key] = max(0, replay_step - 1)
            st.session_state["trajectory_replay_playing"] = False
            st.rerun()
    with col3:
        disabled_next = replay_step >= total_steps - 1
        if st.button("Next ▶", disabled=disabled_next, use_container_width=True):
            st.session_state[step_key] = min(total_steps - 1, replay_step + 1)
            st.session_state["trajectory_replay_playing"] = False
            st.rerun()
    with col4:
        playing = st.session_state["trajectory_replay_playing"]
        if playing:
            if st.button("⏸ Pause", use_container_width=True):
                st.session_state["trajectory_replay_playing"] = False
                st.rerun()
        else:
            disabled_play = replay_step >= total_steps - 1
            if st.button("▶ Play", disabled=disabled_play, use_container_width=True):
                st.session_state["trajectory_replay_playing"] = True
                st.rerun()

    # Slider
    new_step = st.slider(
        "Step through trajectory",
        min_value=0,
        max_value=total_steps - 1,
        value=replay_step,
        key="replay_slider",
        label_visibility="collapsed",
    )
    if new_step != replay_step:
        st.session_state[step_key] = new_step
        st.session_state["trajectory_replay_playing"] = False
        st.rerun()

    st.markdown(
        f'<div class="text-muted mb-1" style="text-align:center;">'
        f'Showing {replay_step + 1} of {total_steps} steps</div>',
        unsafe_allow_html=True,
    )

    # Auto-advance logic (Play)
    if st.session_state["trajectory_replay_playing"] and replay_step < total_steps - 1:
        import time
        time.sleep(0.6)
        st.session_state[step_key] = replay_step + 1
        st.rerun()

    # ── Reveal entries up to current step ──
    expander_labels = {
        "thought": "🧠 Thought",
        "action": "⚡ Action",
        "observation": "📊 Observation",
        "guardrail_triggered": "🛑 Guardrail Triggered",
        "injection_check": "🔍 Injection Check",
        "fairness_test": "⚖️ Fairness Test",
        "second_opinion": "🔁 Second Opinion",
    }

    visible_trajectory = trajectory[: replay_step + 1]

    for idx, entry in enumerate(visible_trajectory):
        etype = entry.get("type", "observation")
        content = entry.get("content", "")
        timestamp = entry.get("timestamp", "")

        label = expander_labels.get(etype, "📋 Step")
        step_class = get_step_class(etype)

        # Last (newest) step is expanded by default
        is_last = (idx == len(visible_trajectory) - 1)

        with st.expander(f"{label}  ·  Step {idx+1}", expanded=is_last):
            st.markdown(
                f'<div class="step-entry {step_class}">'
                f'<div class="step-type">{etype.replace("_", " ").title()}</div>'
                f'<div class="step-content">{content}</div>'
                f'<div class="text-muted mt-1">{timestamp}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Audit log download
    if audit_path and os.path.exists(audit_path):
        st.markdown("---")
        st.markdown("#### 📄 Audit Log")
        with open(audit_path, "r", encoding="utf-8") as f:
            audit_json = f.read()
        st.download_button(
            label="⬇️ Download Audit Log (JSON)",
            data=audit_json,
            file_name=os.path.basename(audit_path),
            mime="application/json",
        )
    else:
        st.markdown(
            '<div class="text-muted mt-2">No audit log file found.</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not os.getenv("OPENROUTER_API_KEY"):
        st.info(
            "OpenRouter is not configured, so the app is running in deterministic offline mode. "
            "Parsing, scoring, and injection screening will still complete."
        )

    # Session state for pipeline results
    if "pipeline_result" not in st.session_state:
        st.session_state.pipeline_result = None
    if "pipeline_run" not in st.session_state:
        st.session_state.pipeline_run = False

    # Sidebar (show status even before run)
    fairness_pre = "—"
    step_count = 0
    if st.session_state.pipeline_result:
        step_count = st.session_state.pipeline_result["state"].get("step_count", 0)
        fairness_entries = st.session_state.pipeline_result.get("fairness_entries", [])
        if fairness_entries:
            fairness_pre = fairness_entries[0].get("content", "—")

    render_sidebar(step_count=step_count, fairness_result=fairness_pre)

    # Main area
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## 🧑‍💼 TechVest Recruitment Agent")
    with col2:
        if st.button("▶️ Run Agent", type="primary", use_container_width=True):
            st.session_state.pipeline_run = True
            st.session_state.pipeline_result = None

    st.markdown("---")

    # Run if triggered
    if st.session_state.pipeline_run and st.session_state.pipeline_result is None:
        with st.spinner("Running recruitment pipeline — parsing, scoring, deciding ..."):
            try:
                result = run_pipeline()
                st.session_state.pipeline_result = result
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.session_state.pipeline_run = False

    # Tabs
    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result
        tab1, tab2 = st.tabs(["📋  Shortlist", "📊  Trajectory"])

        with tab1:
            render_shortlist_tab(result)

        with tab2:
            render_trajectory_tab(result)
    else:
        st.info(
            "Click **Run Agent** to execute the LangGraph recruitment pipeline. "
            "The pipeline will parse all candidate resumes in the dataset, "
            "score them against the rubric, build a ranked shortlist, and propose "
            "interviews for qualifying candidates — then halt for your approval."
        )

        # Preview cards before run
        st.markdown("### Candidates Ready")
        preview_names = list(RESUMES.keys())
        cols = st.columns(len(preview_names))
        for i, name in enumerate(preview_names):
            with cols[i]:
                st.markdown(
                    f'<div class="candidate-card" style="text-align:center;">'
                    f'<div style="font-size:2rem;margin-bottom:0.3rem;">👤</div>'
                    f'<div style="font-weight:600;font-size:1.1rem;">{name}</div>'
                    f'<div class="text-muted">Resume loaded</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()