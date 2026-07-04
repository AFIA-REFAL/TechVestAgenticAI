"""
BVRIT Hyderabad College FAQ Chatbot - Streamlit Application

Production-ready Streamlit UI for the RAG-powered FAQ chatbot.
Features:
- Professional UI inspired by BVRIT Hyderabad branding
- Chat interface with streaming responses
- Dark/Light mode toggle
- Sidebar with system information and metrics
- Evaluation dashboard with RAGAS scores
- Export chat functionality

Author: Senior GenAI Engineer
Version: 1.0.0
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
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings, logger
from ingest import DocumentIngestor, run_ingestion
from rag import RAGPipeline, RAGResponse, create_rag_pipeline
from evaluation import Evaluator, TestCaseGenerator
from ragas_eval import RAGASEvaluator

# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="BVRIT Hyderabad | Campus Compass",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS - BVRIT Hyderabad Branding
# ============================================================

BVRIT_PRIMARY = "#7C1D12"
BVRIT_SECONDARY = "#F2B544"
BVRIT_DARK = "#0B1220"
BVRIT_LIGHT = "#F6F1E8"

CUSTOM_CSS = """
<style>
    :root {
        --bg: #f4efe6;
        --surface: rgba(255, 255, 255, 0.84);
        --text: #142033;
        --muted: #5d687a;
        --line: rgba(20, 32, 51, 0.10);
        --brand: #7C1D12;
        --brand-2: #D97706;
        --brand-3: #0F766E;
        --shadow: 0 24px 60px rgba(16, 24, 40, 0.12);
        --radius-xl: 28px;
        --radius-lg: 22px;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(124, 29, 18, 0.16), transparent 30%),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.15), transparent 26%),
            linear-gradient(180deg, #f8f3eb 0%, #f2ede3 100%);
        color: var(--text);
        font-family: "Segoe UI", "Trebuchet MS", sans-serif;
    }

    .main {
        padding: 1rem 1.25rem 1.5rem;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 17, 31, 0.97) 0%, rgba(21, 34, 56, 0.95) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: #f7f2e8;
    }

    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stDownloadButton button {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        color: #fff !important;
        box-shadow: none !important;
    }

    .hero-panel {
        position: relative;
        overflow: hidden;
        border-radius: var(--radius-xl);
        padding: 1.4rem 1.5rem;
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(43, 28, 19, 0.94));
        color: #fff;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.10);
    }

    .hero-panel::after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(255, 255, 255, 0.08) 0%, transparent 30%, transparent 70%, rgba(255, 255, 255, 0.05) 100%);
        pointer-events: none;
    }

    .hero-panel h1 {
        margin: 0.45rem 0 0.3rem 0;
        font-size: clamp(2rem, 3vw, 3.4rem);
        line-height: 1.02;
        letter-spacing: -0.04em;
        color: #fff !important;
    }

    .hero-panel p {
        margin: 0;
        max-width: 70ch;
        color: rgba(255, 255, 255, 0.84) !important;
        font-size: 1rem;
        line-height: 1.6;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.14);
        color: #fff;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 700;
    }

    .hero-note {
        margin-top: 1rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .ui-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 999px;
        padding: 0.45rem 0.8rem;
        background: rgba(255, 255, 255, 0.12);
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.10);
        font-size: 0.85rem;
        backdrop-filter: blur(10px);
    }

    .surface-card {
        background: var(--surface);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
        border-radius: var(--radius-xl);
        backdrop-filter: blur(14px);
    }

    .section-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--muted);
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 243, 235, 0.92));
        padding: 1rem 1.05rem;
        border-radius: var(--radius-lg);
        box-shadow: 0 12px 30px rgba(16, 24, 40, 0.08);
        border: 1px solid rgba(20, 32, 51, 0.08);
        margin: 0.55rem 0;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 5px;
        background: linear-gradient(180deg, var(--brand), var(--brand-2));
    }

    .metric-card h4 {
        color: var(--brand);
        margin: 0 0 0.35rem 0;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .metric-card p {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1.35;
        word-break: break-word;
    }

    .hero-stat {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: var(--radius-lg);
        padding: 1rem 1.1rem;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .hero-stat .label {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.72rem;
        opacity: 0.8;
    }

    .hero-stat .value {
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 0.25rem;
    }

    .hero-stat .hint {
        margin-top: 0.25rem;
        color: rgba(255, 255, 255, 0.75);
        font-size: 0.82rem;
    }

    .citation-badge,
    .refused-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin: 0.2rem 0.25rem 0.2rem 0;
    }

    .citation-badge {
        background: rgba(124, 29, 18, 0.12);
        color: var(--brand);
        border: 1px solid rgba(124, 29, 18, 0.16);
    }

    .refused-badge {
        background: rgba(185, 28, 28, 0.12);
        color: #B91C1C;
        border: 1px solid rgba(185, 28, 28, 0.16);
    }

    .ragas-card,
    .dashboard-card,
    .chat-panel {
        background: var(--surface);
        border-radius: var(--radius-xl);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
    }

    .chat-panel {
        padding: 1rem 1rem 1.25rem;
    }

    .dashboard-card {
        padding: 1.25rem;
        margin: 1rem 0;
    }

    .dashboard-card h3 {
        color: var(--brand);
        margin: 0 0 1rem 0;
        font-size: 1.05rem;
    }

    .stChatMessage {
        border-radius: 22px !important;
        padding: 0.2rem 0.1rem !important;
        margin: 0.55rem 0 !important;
    }

    [data-testid="stChatMessageContent"] {
        border-radius: 22px !important;
        padding: 1rem 1.1rem !important;
        box-shadow: 0 12px 25px rgba(16, 24, 40, 0.08) !important;
        border: 1px solid rgba(20, 32, 51, 0.08) !important;
    }

    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li {
        line-height: 1.65;
    }

    [data-testid="user-message"] [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #7C1D12 0%, #A63A22 100%) !important;
        color: #fff !important;
        border: none !important;
    }

    [data-testid="assistant-message"] [data-testid="stChatMessageContent"] {
        background: rgba(255, 255, 255, 0.96) !important;
    }

    [data-testid="stChatInput"] {
        border-radius: 24px !important;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 24px !important;
        padding: 1rem 1.1rem !important;
        border: 1px solid rgba(20, 32, 51, 0.14) !important;
        background: rgba(255, 255, 255, 0.94) !important;
        box-shadow: 0 12px 24px rgba(16, 24, 40, 0.08) !important;
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 999px !important;
        border: 1px solid rgba(20, 32, 51, 0.10) !important;
        background: linear-gradient(135deg, #ffffff 0%, #f6f1e8 100%) !important;
        color: var(--text) !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 20px rgba(16, 24, 40, 0.08) !important;
        transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease !important;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 28px rgba(16, 24, 40, 0.12) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.6rem;
        background: rgba(255, 255, 255, 0.64);
        padding: 0.35rem;
        border-radius: 999px;
        border: 1px solid rgba(20, 32, 51, 0.08);
        box-shadow: 0 14px 28px rgba(16, 24, 40, 0.06);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px !important;
        padding: 0.7rem 1.05rem !important;
        font-weight: 700 !important;
        color: var(--muted) !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7C1D12 0%, #A63A22 100%) !important;
        color: #fff !important;
    }

    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(20, 32, 51, 0.08) !important;
        font-weight: 700 !important;
    }

    .footer {
        text-align: center;
        padding: 1rem;
        color: rgba(255, 255, 255, 0.72);
        font-size: 0.8rem;
    }

    .sidebar-brand {
        padding: 1.1rem;
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255,255,255,0.11), rgba(255,255,255,0.05));
        border: 1px solid rgba(255,255,255,0.09);
        text-align: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }

    .sidebar-brand h3 {
        margin: 0.55rem 0 0.25rem 0;
        font-size: 1.1rem;
        color: #fff;
    }

    .sidebar-brand p {
        margin: 0;
        color: rgba(255,255,255,0.76);
        font-size: 0.88rem;
        line-height: 1.45;
    }

    .sidebar-section-title {
        margin: 1rem 0 0.5rem 0;
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(255,255,255,0.7);
        font-weight: 700;
    }

    .sidebar-mini-card {
        border-radius: 18px;
        padding: 0.9rem 1rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 0.55rem;
    }

    .sidebar-mini-card .label {
        color: rgba(255,255,255,0.68);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        font-weight: 700;
    }

    .sidebar-mini-card .value {
        margin-top: 0.25rem;
        color: #fff;
        font-size: 0.98rem;
        font-weight: 700;
        line-height: 1.4;
        word-break: break-word;
    }
</style>
"""


# ============================================================
# Session State Initialization
# ============================================================

def init_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = None
    
    if "ingestor" not in st.session_state:
        st.session_state.ingestor = None
    
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    
    if "total_latency" not in st.session_state:
        st.session_state.total_latency = 0.0
    
    if "ragas_metrics" not in st.session_state:
        st.session_state.ragas_metrics = {}
    
    if "evaluation_report" not in st.session_state:
        st.session_state.evaluation_report = None


def render_metric_card(title: str, value: str):
    """Render a compact metric card."""
    st.markdown(
        f'<div class="metric-card"><h4>{title}</h4><p>{value}</p></div>',
        unsafe_allow_html=True,
    )


def render_sidebar_card(label: str, value: str):
    """Render a compact sidebar card."""
    st.markdown(
        f'<div class="sidebar-mini-card"><div class="label">{label}</div><div class="value">{value}</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_image_index() -> Dict[str, Any]:
    """Load the scraped image index keyed by source page URL."""
    image_index_path = Path(settings.image_index_path)
    if not image_index_path.exists():
        return {}

    try:
        with open(image_index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as exc:
        logger.warning(f"Failed to load image index: {exc}")
        return {}

    if isinstance(data, dict):
        pages = data.get("pages", data)
        if isinstance(pages, dict):
            return pages
        if isinstance(pages, list):
            return {item.get("page_url", ""): item for item in pages if item.get("page_url")}

    if isinstance(data, list):
        return {item.get("page_url", ""): item for item in data if item.get("page_url")}

    return {}


def resolve_related_images(retrieved_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map retrieved chunks to images scraped from their source pages."""
    image_index = load_image_index()
    seen_urls = set()
    related_images: List[Dict[str, Any]] = []

    for meta in retrieved_metadata:
        source_url = meta.get("source_url")
        if not source_url or source_url in seen_urls:
            continue

        seen_urls.add(source_url)
        page_entry = image_index.get(source_url)
        if not page_entry:
            continue

        images = page_entry.get("images", []) if isinstance(page_entry, dict) else []
        page_title = page_entry.get("page_title") if isinstance(page_entry, dict) else ""

        for image in images:
            image_url = image.get("image_url")
            if not image_url or any(existing.get("image_url") == image_url for existing in related_images):
                continue

            related_images.append({
                "image_url": image_url,
                "alt_text": image.get("alt_text", ""),
                "page_title": page_title or meta.get("title") or meta.get("section", ""),
                "page_url": source_url,
                "is_primary": image.get("is_primary", False),
            })

            if len(related_images) >= 4:
                return related_images

    return related_images


# ============================================================
# Initialize Backend
# ============================================================

@st.cache_resource
def initialize_backend():
    """Initialize the ingestion pipeline and RAG pipeline."""
    try:
        ingestor = run_ingestion()
        rag = create_rag_pipeline(
            vector_store=ingestor.vector_store,
            debug=False,
        )
        return ingestor, rag
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        st.error(f"Failed to initialize: {e}")
        return None, None


# ============================================================
# Sidebar
# ============================================================

def render_sidebar():
    """Render the sidebar with system information and controls."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            '<div class="eyebrow">Campus Compass</div>'
            '<h3>BVRIT Hyderabad</h3>'
            '<p>Ask questions about admissions, programs, campus life, placements, and policies in one place.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-title">Assistant</div>', unsafe_allow_html=True)
        st.markdown("Use the chat for grounded, source-backed answers.")
        
        st.divider()
        
        # Knowledge Base Status
        st.markdown('<div class="sidebar-section-title">Knowledge Base</div>', unsafe_allow_html=True)
        
        ingestor = st.session_state.ingestor
        if ingestor and ingestor.vector_store:
            stats = ingestor.get_collection_stats()
            render_sidebar_card("Status", stats.get("status", "Unknown"))
            render_sidebar_card("Document", settings.document_path.split("/")[-1])
            render_sidebar_card("Vector Count", f'{stats.get("total_vectors", 0):,}')
        else:
            st.warning("⚠️ Not initialized")
        
        st.divider()
        
        # Model Configuration
        st.markdown('<div class="sidebar-section-title">Configuration</div>', unsafe_allow_html=True)
        render_sidebar_card("Embedding Model", settings.embedding_model)
        render_sidebar_card("LLM Model", settings.llm_model)
        render_sidebar_card("Chunk Size", str(settings.chunk_size))
        render_sidebar_card("Chunk Overlap", str(settings.chunk_overlap))
        render_sidebar_card("Top-K", str(settings.top_k))
        
        st.divider()
        
        # Query Statistics
        st.markdown('<div class="sidebar-section-title">Usage</div>', unsafe_allow_html=True)
        render_sidebar_card("Total Queries", str(st.session_state.query_count))
        
        avg_latency = (
            st.session_state.total_latency / st.session_state.query_count
            if st.session_state.query_count > 0 else 0
        )
        render_sidebar_card("Avg Latency", f"{avg_latency:.2f}s")
        
        st.divider()
        
        # RAGAS Scores
        if st.session_state.ragas_metrics:
            st.markdown('<div class="sidebar-section-title">RAGAS Scores</div>', unsafe_allow_html=True)
            for metric, score in st.session_state.ragas_metrics.items():
                label = metric.replace("_", " ").title()
                st.progress(score, text=f"{label}: {score:.2%}")
        
        st.divider()
        
        # Controls
        st.markdown('<div class="sidebar-section-title">Controls</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("🌙 Dark Mode", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        # Export Chat
        if st.session_state.messages:
            chat_export = json.dumps(
                [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                indent=2,
            )
            st.download_button(
                label="📥 Export Chat",
                data=chat_export,
                file_name=f"bvrit_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
        
        st.divider()
        
        # Footer
        st.markdown(
            '<div class="footer">'
            'BVRIT Hyderabad Campus Compass v2.0<br>'
            'Built with LangChain, ChromaDB, OpenRouter, and Streamlit'
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# Chat Interface
# ============================================================

def render_chat():
    """Render the main chat interface."""
    st.markdown(
        '<div class="hero-panel">'
        '<div class="eyebrow">BVRIT Hyderabad College of Engineering for Women</div>'
        '<h1>Campus Compass for instant, grounded college answers.</h1>'
        '<p>Explore admissions, programs, facilities, placements, and student life with answers drawn from the knowledge base and surfaced in a cleaner, more focused workspace.</p>'
        '<div class="hero-note">'
        '<span class="ui-chip">🎓 Admissions</span>'
        '<span class="ui-chip">📚 Academics</span>'
        '<span class="ui-chip">🏫 Campus Life</span>'
        '<span class="ui-chip">📈 Placement Insights</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="hero-stat"><div class="label">Knowledge Base</div><div class="value">Grounded FAQ search</div><div class="hint">Answers stay tied to indexed documents.</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        avg_latency = (
            st.session_state.total_latency / st.session_state.query_count
            if st.session_state.query_count > 0 else 0
        )
        st.markdown(
            f'<div class="hero-stat"><div class="label">Average Latency</div><div class="value">{avg_latency:.2f}s</div><div class="hint">Typical response time across your session.</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="hero-stat"><div class="label">Questions Answered</div><div class="value">{st.session_state.query_count}</div><div class="hint">Conversation history kept in session.</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("📋 View Details"):
                    meta = message["metadata"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Latency", f"{meta.get('latency', 0):.2f}s")
                    with col2:
                        st.metric("Tokens Used", meta.get('tokens', 0))
                    with col3:
                        st.metric("Chunks Retrieved", meta.get('chunks', 0))
                    
                    if meta.get("citations"):
                        st.markdown("**📚 Citations:**")
                        for citation in meta["citations"]:
                            st.markdown(f'<span class="citation-badge">{citation}</span>', unsafe_allow_html=True)
                    
                    if meta.get("refused"):
                        st.markdown('<span class="refused-badge">⛔ REFUSED</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about BVRIT Hyderabad..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching knowledge base..."):
                try:
                    rag = st.session_state.rag_pipeline
                    if rag is None:
                        st.error("RAG pipeline not initialized. Please check your API key and restart.")
                        st.stop()
                    
                    # Prior turns (excluding the message we just appended)
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    response: RAGResponse = rag.answer(prompt, chat_history=history)
                    
                    # Update statistics
                    st.session_state.query_count += 1
                    st.session_state.total_latency += response.latency_seconds
                    
                    # Display answer
                    st.markdown(response.answer)

                    related_images = resolve_related_images(response.retrieved_metadata)
                    if related_images:
                        st.markdown("**🖼️ Related Images**")
                        image_cols = st.columns(min(2, len(related_images)))
                        for idx, image in enumerate(related_images[:2]):
                            with image_cols[idx % len(image_cols)]:
                                st.image(
                                    image["image_url"],
                                    caption=image.get("page_title") or image.get("alt_text") or "Related image",
                                    use_container_width=True,
                                )
                    
                    # Display metadata
                    metadata = {
                        "latency": response.latency_seconds,
                        "tokens": response.token_usage.get("total_tokens", 0),
                        "chunks": len(response.retrieved_chunks),
                        "citations": response.citations,
                        "refused": response.refused,
                        "related_images": len(related_images),
                        "tool_calls": response.tool_calls,
                    }
                    
                    with st.expander("📋 View Details"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Latency", f"{response.latency_seconds:.2f}s")
                        with col2:
                            st.metric("Tokens Used", response.token_usage.get("total_tokens", 0))
                        with col3:
                            st.metric("Chunks Retrieved", len(response.retrieved_chunks))
                        
                        if response.citations:
                            st.markdown("**📚 Citations:**")
                            for citation in response.citations:
                                st.markdown(f'<span class="citation-badge">{citation}</span>', unsafe_allow_html=True)
                        
                        if response.refused:
                            st.markdown('<span class="refused-badge">⛔ REFUSED</span>', unsafe_allow_html=True)

                        if related_images:
                            st.markdown("**🖼️ Related Images:**")
                            for image in related_images:
                                st.markdown(f"- [{image.get('page_title') or 'Image source'}]({image.get('page_url')})")
                        
                        # Show retrieved chunks
                        st.markdown("**📄 Retrieved Sources:**")
                        for i, (chunk, meta) in enumerate(
                            zip(response.retrieved_chunks, response.retrieved_metadata)
                        ):
                            with st.expander(f"Source {i+1}: {meta.get('section', 'Unknown')}"):
                                st.markdown(f"**Section:** {meta.get('section', 'Unknown')}")
                                st.markdown(f"**Chunk ID:** {meta.get('chunk_id', 'N/A')}")
                                st.markdown(f"**Content:**")
                                st.text(chunk[:500] + ("..." if len(chunk) > 500 else ""))
                    
                    # Save to session
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "metadata": metadata,
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error generating response: {e}")
                    logger.error(f"Chat error: {e}", exc_info=True)


# ============================================================
# Evaluation Dashboard
# ============================================================

def render_dashboard():
    """Render the evaluation dashboard."""
    st.markdown('<div class="dashboard-card"><h3>📊 Evaluation Studio</h3>', unsafe_allow_html=True)
    
    # Run evaluation button
    if st.button("🚀 Run Full Evaluation", type="primary", use_container_width=True):
        with st.spinner("Running evaluation pipeline..."):
            try:
                rag = st.session_state.rag_pipeline
                if rag is None:
                    st.error("RAG pipeline not initialized.")
                    st.stop()
                
                # Generate test cases
                generator = TestCaseGenerator()
                test_cases = generator.generate()
                
                # Run evaluation
                evaluator = Evaluator(rag)
                evaluator.run_all(test_cases)
                report = evaluator.generate_report()
                evaluator.save_report(report)
                
                st.session_state.evaluation_report = report
                
                # Calculate RAGAS metrics
                questions = [r["question"] for r in evaluator.results]
                answers = [r["actual_answer"] for r in evaluator.results]
                contexts = [r["retrieved_chunks"] for r in evaluator.results]
                ground_truths = [[r["expected_answer"]] for r in evaluator.results]
                
                ragas_eval = RAGASEvaluator()
                ragas_metrics = ragas_eval.evaluate(questions, answers, contexts, ground_truths)
                st.session_state.ragas_metrics = ragas_metrics
                
                st.success("✅ Evaluation complete!")
                
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                logger.error(f"Evaluation error: {e}", exc_info=True)
    
    # Display evaluation report if available
    report = st.session_state.evaluation_report
    if report and "error" not in report:
        st.divider()
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", report["total_test_cases"])
        with col2:
            st.metric("✅ Passed", report["passed"])
        with col3:
            st.metric("❌ Failed", report["failed"])
        with col4:
            st.metric("📊 Pass Rate", f"{report['pass_rate_percentage']}%")
        
        st.divider()
        
        # Dimension breakdown
        st.markdown("### 📈 Dimension Performance")
        
        dim_data = []
        for dim, stats in report["dimension_breakdown"].items():
            dim_data.append({
                "Dimension": dim,
                "Pass Rate (%)": stats["pass_rate"],
                "Average Score": stats["average_score"],
                "Total": stats["total"],
                "Passed": stats["passed"],
            })
        
        if dim_data:
            df = pd.DataFrame(dim_data)
            
            # Bar chart
            fig = px.bar(
                df,
                x="Dimension",
                y="Pass Rate (%)",
                color="Pass Rate (%)",
                color_continuous_scale="RdYlGn",
                title="Pass Rate by Dimension",
                text="Pass Rate (%)",
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # RAGAS Metrics
        if st.session_state.ragas_metrics:
            st.markdown("### 🎯 RAGAS Metrics")
            
            metrics = st.session_state.ragas_metrics
            cols = st.columns(4)
            
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
        
        st.divider()
        
        # Failed test cases
        if report["failed_test_cases"]:
            st.markdown("### ❌ Failed Test Cases")
            
            for case in report["failed_test_cases"]:
                with st.expander(f"❌ {case['question'][:100]}..."):
                    st.markdown(f"**Dimension:** {case['dimension']}")
                    st.markdown(f"**Score:** {case['score']}/10")
                    st.markdown(f"**Reason:** {case['failure_reason']}")
        
        # Recommendations
        st.divider()
        st.markdown("### 💡 Recommendations")
        for rec in report.get("recommendations", []):
            st.info(rec)
        
        # Download report
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            with open(settings.evaluation_report_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download JSON Report",
                    data=f,
                    file_name="evaluation_report.json",
                    mime="application/json",
                    use_container_width=True,
                )
        with col2:
            if Path(settings.evaluation_csv_path).exists():
                with open(settings.evaluation_csv_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download CSV Report",
                        data=f,
                        file_name="evaluation_report.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
    
    else:
        st.info("No evaluation results yet. Click 'Run Full Evaluation' to start.")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# Main Application
# ============================================================

def main():
    """Main application entry point."""
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Apply dark mode if enabled
    if st.session_state.get("dark_mode", False):
        st.markdown(
            """
            <style>
                .main { background: #1a1a2e; color: #e0e0e0; }
                .stChatMessage { background: #2d2d2d !important; }
                .metric-card { background: #2d2d2d !important; color: #e0e0e0 !important; }
                .dashboard-card { background: #2d2d2d !important; color: #e0e0e0 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    
    # Initialize session state
    init_session_state()
    
    # Initialize backend
    if st.session_state.ingestor is None:
        with st.spinner("🚀 Initializing BVRIT Knowledge Base..."):
            ingestor, rag = initialize_backend()
            st.session_state.ingestor = ingestor
            st.session_state.rag_pipeline = rag
    
    # Render sidebar
    render_sidebar()
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["💬 Conversation Studio", "📊 Evaluation Studio"])
    
    with tab1:
        render_chat()
    
    with tab2:
        render_dashboard()


if __name__ == "__main__":
    main()