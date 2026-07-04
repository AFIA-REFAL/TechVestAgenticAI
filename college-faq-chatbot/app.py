"""
BVRIT Hyderabad College FAQ Chatbot - Streamlit Application
Clean, lite UI matching BVRIT Hyderabad website branding with evaluation dashboard.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings, logger
from ingest import run_ingestion
from rag import RAGResponse, create_rag_pipeline
from evaluation import Evaluator, TestCaseGenerator
from ragas_eval import RAGASEvaluator
from image_lookup import find_image_for_query

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="BVRIT Hyderabad | Campus Compass",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# BVRIT Brand Colors (from official website)
# ============================================================
BVRIT_MAROON = "#7C1D12"
BVRIT_GOLD = "#F2B544"
BVRIT_DARK = "#1a1a2e"
BVRIT_WHITE = "#FFFFFF"
BVRIT_LIGHT_BG = "#f8f4f0"
BVRIT_TEXT = "#2d2d2d"
BVRIT_MUTED = "#6b7280"

LOGO_URL = "https://bvrithyderabad.edu.in/wp-content/uploads/2023/07/bvrit-hyderabad-engineering-women-college-logo-2.jpg"

# ============================================================
# Custom CSS - Clean, Lite, BVRIT Branded
# ============================================================
CUSTOM_CSS = f"""
<style>
    #MainMenu, header, footer {{visibility: hidden;}}
    .block-container {{padding: 1rem 1.5rem 2rem; max-width: 800px;}}
    
    .stApp {{
        background: {BVRIT_LIGHT_BG};
    }}
    
    /* Header / Brand Bar */
    .brand-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid {BVRIT_GOLD};
    }}
    
    .brand-header img {{
        height: 56px;
        width: auto;
        border-radius: 4px;
    }}
    
    .brand-header .brand-text h1 {{
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: {BVRIT_MAROON};
        line-height: 1.2;
        letter-spacing: -0.01em;
    }}
    
    .brand-header .brand-text p {{
        margin: 0;
        font-size: 0.78rem;
        color: {BVRIT_MUTED};
        font-weight: 500;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.4rem;
        background: {BVRIT_WHITE};
        padding: 0.3rem;
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        color: {BVRIT_MUTED} !important;
        background: transparent !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {BVRIT_MAROON} !important;
        color: {BVRIT_WHITE} !important;
    }}
    
    /* Chat Container */
    .chat-container {{
        background: {BVRIT_WHITE};
        border-radius: 16px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        padding: 0.5rem 0;
        margin-bottom: 0.75rem;
        min-height: 300px;
    }}
    
    /* Messages */
    .stChatMessage {{
        padding: 0.25rem 0.75rem !important;
    }}
    
    [data-testid="stChatMessageContent"] {{
        border-radius: 18px !important;
        padding: 0.75rem 1rem !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 0.92rem !important;
        line-height: 1.6 !important;
    }}
    
    [data-testid="user-message"] [data-testid="stChatMessageContent"] {{
        background: {BVRIT_MAROON} !important;
        color: {BVRIT_WHITE} !important;
    }}
    
    [data-testid="assistant-message"] [data-testid="stChatMessageContent"] {{
        background: #f3f0eb !important;
        color: {BVRIT_TEXT} !important;
    }}
    
    /* Chat Input - ALWAYS VISIBLE */
    [data-testid="stChatInput"] {{
        border: 2px solid #e5e0d8 !important;
        border-radius: 14px !important;
        background: {BVRIT_WHITE} !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        margin-top: 0 !important;
    }}
    
    [data-testid="stChatInput"]:focus-within {{
        border-color: {BVRIT_GOLD} !important;
        box-shadow: 0 0 0 3px rgba(242, 181, 68, 0.15) !important;
    }}
    
    [data-testid="stChatInput"] textarea {{
        border-radius: 14px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.92rem !important;
    }}
    
    /* Welcome message */
    .welcome-box {{
        text-align: center;
        padding: 2rem 1rem 1rem;
    }}
    
    .welcome-box .icon {{
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }}
    
    .welcome-box h2 {{
        font-size: 1.1rem;
        color: {BVRIT_MAROON};
        margin: 0 0 0.35rem 0;
        font-weight: 700;
    }}
    
    .welcome-box p {{
        font-size: 0.85rem;
        color: {BVRIT_MUTED};
        margin: 0 auto;
        max-width: 400px;
        line-height: 1.5;
    }}
    
    /* Citation badges */
    .citation-badge {{
        display: inline-block;
        background: rgba(124, 29, 18, 0.08);
        color: {BVRIT_MAROON};
        border-radius: 999px;
        padding: 0.15rem 0.6rem;
        font-size: 0.7rem;
        font-weight: 600;
        margin: 0.1rem 0.15rem;
    }}
    
    /* Mini metrics */
    .mini-metric {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: #f8f4f0;
        border-radius: 8px;
        padding: 0.3rem 0.65rem;
        font-size: 0.75rem;
        color: {BVRIT_MUTED};
        margin: 0.15rem;
    }}
    
    .mini-metric strong {{
        color: {BVRIT_TEXT};
    }}
    
    /* Dashboard cards */
    .dash-card {{
        background: {BVRIT_WHITE};
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.06);
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }}
    
    .dash-card h3 {{
        margin: 0 0 0.75rem 0;
        font-size: 0.95rem;
        color: {BVRIT_MAROON};
        font-weight: 700;
    }}
    
    /* Footer */
    .chat-footer {{
        text-align: center;
        padding: 0.75rem 0 0.25rem;
        font-size: 0.72rem;
        color: {BVRIT_MUTED};
        border-top: 1px solid rgba(0,0,0,0.05);
        margin-top: 0.5rem;
    }}
    
    .chat-footer strong {{
        color: {BVRIT_MAROON};
    }}
    
    /* Buttons */
    .stButton button {{
        border-radius: 10px !important;
        border: 1px solid #e5e0d8 !important;
        background: {BVRIT_WHITE} !important;
        color: {BVRIT_TEXT} !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.35rem 0.85rem !important;
        transition: all 0.15s ease !important;
    }}
    
    .stButton button:hover {{
        border-color: {BVRIT_MAROON} !important;
        color: {BVRIT_MAROON} !important;
        background: #fefcf9 !important;
    }}
    
    /* Metric in dashboard */
    .stMetric label {{
        color: {BVRIT_MUTED} !important;
        font-size: 0.78rem !important;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        color: {BVRIT_TEXT} !important;
        font-weight: 700 !important;
    }}
</style>
"""

# ============================================================
# Session State
# ============================================================
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = None
    if "ingestor" not in st.session_state:
        st.session_state.ingestor = None
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    if "total_latency" not in st.session_state:
        st.session_state.total_latency = 0.0
    if "ragas_metrics" not in st.session_state:
        st.session_state.ragas_metrics = {}
    if "evaluation_report" not in st.session_state:
        st.session_state.evaluation_report = None
    if "image_entries" not in st.session_state:
        st.session_state.image_entries = {}

# ============================================================
# Initialize Backend
# ============================================================
@st.cache_resource
def initialize_backend():
    try:
        ingestor = run_ingestion()
        rag = create_rag_pipeline(
            vector_store=ingestor.vector_store,
            debug=False,
        )
        return ingestor, rag
    except Exception as e:
        logger.error(f"Backend init failed: {e}")
        st.error(f"Failed to initialize: {e}")
        return None, None

# ============================================================
# Brand Header
# ============================================================
def render_header():
    st.markdown(
        f"""
        <div class="brand-header">
            <img src="{LOGO_URL}" alt="BVRIT Hyderabad Logo">
            <div class="brand-text">
                <h1>BVRIT Hyderabad</h1>
                <p>College of Engineering for Women · Campus Compass</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# Chat Tab
# ============================================================
def render_chat_tab():
    # Chat container with messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown(
            f"""
            <div class="welcome-box">
                <div class="icon">🎓</div>
                <h2>Welcome to Campus Compass</h2>
                <p>Ask me anything about BVRIT Hyderabad — admissions, programs, fees, placements, and campus life.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "metadata" in message:
                    meta = message["metadata"]
                    metrics_html = (
                        f'<span class="mini-metric">⚡ <strong>{meta.get("latency", 0):.1f}s</strong></span>'
                        f'<span class="mini-metric">📝 <strong>{meta.get("tokens", 0)}</strong> tokens</span>'
                        f'<span class="mini-metric">📄 <strong>{meta.get("chunks", 0)}</strong> chunks</span>'
                    )
                    st.markdown(f'<div style="margin-top:0.3rem;">{metrics_html}</div>', unsafe_allow_html=True)
                    if meta.get("citations"):
                        citations_html = "".join(
                            f'<span class="citation-badge">{c}</span>' for c in meta["citations"]
                        )
                        st.markdown(f'<div style="margin-top:0.2rem;">{citations_html}</div>', unsafe_allow_html=True)
                    # Show image if stored for this message
                    img_key = f"assistant_{idx}"
                    if img_key in st.session_state.image_entries:
                        entry = st.session_state.image_entries[img_key]
                        caption = entry["name"]
                        if entry.get("designation"):
                            caption += f" — {entry['designation']}"
                        st.image(entry["image_url"], caption=caption, width=280)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input - ALWAYS visible at bottom
    prompt = st.chat_input("Ask me anything about BVRIT Hyderabad...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    rag = st.session_state.rag_pipeline
                    if rag is None:
                        st.error("Pipeline not initialized.")
                        st.stop()
                    
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    response: RAGResponse = rag.answer(prompt, chat_history=history)
                    
                    st.session_state.query_count += 1
                    st.session_state.total_latency += response.latency_seconds
                    
                    st.markdown(response.answer)
                    
                    metadata = {
                        "latency": response.latency_seconds,
                        "tokens": response.token_usage.get("total_tokens", 0),
                        "chunks": len(response.retrieved_chunks),
                        "citations": response.citations,
                        "refused": response.refused,
                    }
                    
                    metrics_html = (
                        f'<span class="mini-metric">⚡ <strong>{response.latency_seconds:.1f}s</strong></span>'
                        f'<span class="mini-metric">📝 <strong>{response.token_usage.get("total_tokens", 0)}</strong> tokens</span>'
                        f'<span class="mini-metric">📄 <strong>{len(response.retrieved_chunks)}</strong> chunks</span>'
                    )
                    st.markdown(f'<div style="margin-top:0.3rem;">{metrics_html}</div>', unsafe_allow_html=True)
                    
                    if response.citations:
                        citations_html = "".join(
                            f'<span class="citation-badge">{c}</span>' for c in response.citations
                        )
                        st.markdown(f'<div style="margin-top:0.2rem;">{citations_html}</div>', unsafe_allow_html=True)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "metadata": metadata,
                    })
                    
                    # Store image for this assistant message
                    img_entry = find_image_for_query(prompt)
                    if img_entry:
                        st.session_state.image_entries[f"assistant_{len(st.session_state.messages) - 1}"] = img_entry
                        # Also show image immediately in current response
                        caption = img_entry["name"]
                        if img_entry.get("designation"):
                            caption += f" — {img_entry['designation']}"
                        st.image(img_entry["image_url"], caption=caption, width=280)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Chat error: {e}", exc_info=True)

# ============================================================
# Evaluation Dashboard Tab
# ============================================================
def render_evaluation_tab():
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown("<h3>📊 Evaluation Studio</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 Run Full Evaluation", type="primary", use_container_width=True):
            with st.spinner("Running evaluation pipeline..."):
                try:
                    rag = st.session_state.rag_pipeline
                    if rag is None:
                        st.error("RAG pipeline not initialized.")
                        st.stop()
                    
                    generator = TestCaseGenerator()
                    test_cases = generator.generate()
                    
                    evaluator = Evaluator(rag)
                    evaluator.run_all(test_cases)
                    report = evaluator.generate_report()
                    evaluator.save_report(report)
                    
                    st.session_state.evaluation_report = report
                    
                    questions = [r["question"] for r in evaluator.results]
                    answers = [r["actual_answer"] for r in evaluator.results]
                    contexts = [r["retrieved_chunks"] for r in evaluator.results]
                    ground_truths = [[r["expected_answer"]] for r in evaluator.results]
                    
                    try:
                        ragas_eval = RAGASEvaluator()
                        ragas_metrics = ragas_eval.evaluate(questions, answers, contexts, ground_truths)
                        st.session_state.ragas_metrics = ragas_metrics
                    except Exception as ragas_err:
                        logger.warning(f"RAGAS evaluation failed (non-critical): {ragas_err}")
                        st.session_state.ragas_metrics = {"faithfulness": 0.0, "answer_relevancy": 0.0}
                    
                    st.success("✅ Evaluation complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")
                    logger.error(f"Evaluation error: {e}", exc_info=True)
    
    with col2:
        st.markdown(
            f'<p style="font-size:0.85rem;color:{BVRIT_MUTED};margin:0;">'
            f'Test the chatbot across multiple dimensions: accuracy, relevance, '
            f'grounding, and more. Results include RAGAS metrics.</p>',
            unsafe_allow_html=True,
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display report if available
    report = st.session_state.evaluation_report
    if report and "error" not in report:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", report["total_test_cases"])
        with col2:
            st.metric("✅ Passed", report["passed"])
        with col3:
            st.metric("❌ Failed", report["failed"])
        with col4:
            st.metric("📊 Pass Rate", f"{report['pass_rate_percentage']}%")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Dimension breakdown
        if report.get("dimension_breakdown"):
            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            st.markdown("<h3>📈 Dimension Performance</h3>", unsafe_allow_html=True)
            
            dim_data = []
            for dim, stats in report["dimension_breakdown"].items():
                dim_data.append({
                    "Dimension": dim,
                    "Pass Rate (%)": stats["pass_rate"],
                    "Average Score": stats["average_score"],
                })
            
            if dim_data:
                df = pd.DataFrame(dim_data)
                fig = px.bar(
                    df, x="Dimension", y="Pass Rate (%)",
                    color="Pass Rate (%)", color_continuous_scale="RdYlGn",
                    text="Pass Rate (%)", height=350,
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig, use_container_width=False)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # RAGAS Metrics
        if st.session_state.ragas_metrics:
            st.markdown('<div class="dash-card">', unsafe_allow_html=True)
            st.markdown("<h3>🎯 RAGAS Metrics</h3>", unsafe_allow_html=True)
            
            metrics = st.session_state.ragas_metrics
            cols = st.columns(len(metrics))
            labels = {
                "faithfulness": "Faithfulness",
                "answer_relevancy": "Answer Relevancy",
                "context_precision": "Context Precision",
                "context_recall": "Context Recall",
            }
            
            for i, (metric, score) in enumerate(metrics.items()):
                with cols[i]:
                    st.metric(labels.get(metric, metric), f"{score:.1%}")
                    st.progress(score)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif report and "error" in report:
        st.error(f"Report error: {report['error']}")

# ============================================================
# Main App
# ============================================================
def main():
    init_session_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Initialize backend
    if st.session_state.rag_pipeline is None:
        with st.spinner("Loading knowledge base..."):
            ingestor, rag = initialize_backend()
            st.session_state.ingestor = ingestor
            st.session_state.rag_pipeline = rag
    
    # Header
    render_header()
    
    # Tabs: Chat + Evaluation
    tab1, tab2 = st.tabs(["💬 Chat", "📊 Evaluation"])
    
    with tab1:
        render_chat_tab()
    
    with tab2:
        render_evaluation_tab()
    
    # Footer
    st.markdown(
        f"""
        <div class="chat-footer">
            <strong>BVRIT Hyderabad</strong> · Campus Compass · {st.session_state.query_count} queries answered
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()