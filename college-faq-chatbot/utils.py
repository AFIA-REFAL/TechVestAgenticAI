"""
BVRIT Hyderabad College FAQ Chatbot - Utility Functions Module

Provides shared utility functions used across the application:
- Document loading and text extraction
- Intelligent text chunking with metadata
- LLM client setup via OpenRouter
- Token counting and response parsing
- Embedding model setup

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import re
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import docx2txt
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI

# Local (fallback) embeddings using sentence-transformers
try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except Exception:
    SentenceTransformer = None

from config import settings, logger

logger = logging.getLogger(__name__)


# ============================================================
# Document Loading
# ============================================================

def load_knowledge_base_entries(filepath: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load the JSON-structured knowledge base entries from a markdown file.

    Returns:
        List[dict] when the file contains a JSON array, otherwise None.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
        if not raw.startswith('['):
            return None

        entries = json.loads(raw)
        if not isinstance(entries, list):
            return None

        normalized: List[Dict[str, Any]] = []
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            normalized.append({
                **entry,
                "id": entry.get("id", f"entry_{idx}"),
                "category": entry.get("category", "General"),
                "title": entry.get("title", f"Entry {idx + 1}"),
                "content": entry.get("content", ""),
                "source_url": entry.get("source_url", ""),
            })

        return normalized or None
    except (json.JSONDecodeError, OSError) as exc:
        logger.info(f"Knowledge base is not structured JSON: {exc}")
        return None

def load_document(filepath: str) -> str:
    """
    Load and extract text from a file.
    Supports .docx and .md (JSON-structured) files.

    Args:
        filepath: Path to the document

    Returns:
        str: Extracted text content

    Raises:
        FileNotFoundError: If the document doesn't exist
        Exception: For other loading errors
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")

    logger.info(f"Loading document: {filepath}")

    try:
        ext = path.suffix.lower()

        if ext == '.docx':
            # Extract text from docx while preserving structure
            text = docx2txt.process(str(path))
            # Basic cleanup
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()
            logger.info(f"Document loaded: {len(text)} characters")
            return text
        elif ext == '.md':
            # Try loading as JSON-structured knowledge base first
            try:
                entries = load_knowledge_base_entries(filepath)
                if entries:
                    sections = []
                    for entry in entries:
                        category = entry.get('category', 'General')
                        title = entry.get('title', '')
                        content = entry.get('content', '')
                        sections.append(f"## {category}\n### {title}\n{content}")
                    text = '\n\n'.join(sections)
                    logger.info(f"MD (JSON-structured) loaded: {len(entries)} entries, {len(text)} characters")
                    return text
            except Exception as e:
                logger.info(f"Not JSON-structured .md, reading as plain text: {e}")

            # Fallback: read as plain markdown text
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()
            logger.info(f"MD (plain) loaded: {len(text)} characters")
            return text
        else:
            # Generic text file loading
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            text = text.strip()
            logger.info(f"File loaded: {len(text)} characters")
            return text

    except Exception as e:
        logger.error(f"Error loading document {filepath}: {e}")
        raise


# ============================================================
# Intelligent Text Chunking
# ============================================================

def extract_sections(text: str) -> List[Dict[str, str]]:
    """
    Extract section headings and their content from the document.
    Detects markdown-style headings (##, ###, etc.) and plain text headings.

    Args:
        text: Full document text

    Returns:
        List[Dict]: List of sections with 'heading' and 'content' keys
    """
    sections = []
    lines = text.split('\n')
    current_heading = "General"
    current_content = []

    heading_pattern = re.compile(r'^(#{1,4}\s+|Page:|Page Structure|Content|Lists|Tables|Internal Links)')

    for line in lines:
        stripped = line.strip()
        # Detect headings
        if stripped.startswith('## ') or stripped.startswith('### ') or stripped.startswith('#### '):
            if current_content:
                sections.append({
                    'heading': current_heading,
                    'content': '\n'.join(current_content).strip()
                })
                current_content = []
            current_heading = stripped.lstrip('#').strip()
        elif stripped.startswith('Page:') and 'BVRIT' in stripped:
            if current_content:
                sections.append({
                    'heading': current_heading,
                    'content': '\n'.join(current_content).strip()
                })
                current_content = []
            current_heading = stripped.replace('Page:', '').strip()
        else:
            if stripped:
                current_content.append(stripped)

    # Add last section
    if current_content:
        sections.append({
            'heading': current_heading,
            'content': '\n'.join(current_content).strip()
        })

    return sections


def create_chunks_with_metadata(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
    source_filename: str = "knowledge_base.md",
    structured_entries: Optional[List[Dict[str, Any]]] = None,
) -> List[LangchainDocument]:
    """
    Split document text into chunks with rich metadata.
    Uses RecursiveCharacterTextSplitter with section-aware splitting.

    IMPROVEMENTS over original:
    - Heading prefix injection: every chunk starts with its section heading
      so the embedding captures the topic even for short chunks.
    - Deduplication: near-identical chunks (Jaccard similarity > 0.92) are
      dropped to avoid the vector store being flooded with duplicate vectors
      that would all return for the same query, wasting the top-k budget.
    - Better separators: markdown headings are split on first so context
      boundaries respect the document structure.

    Args:
        text: Document text to chunk
        chunk_size: Characters per chunk (default: 600)
        chunk_overlap: Overlap between chunks (default: 100)
        source_filename: Source document filename for metadata
        structured_entries: Optional list of structured KB entries

    Returns:
        List[LangchainDocument]: De-duplicated chunks with metadata
    """
    logger.info(
        f"Creating chunks: size={chunk_size}, overlap={chunk_overlap}"
    )

    # Build sections list
    if structured_entries:
        sections = [
            {
                "heading": f"{entry.get('category', 'General')} - {entry.get('title', 'Untitled')}",
                "content": entry.get('content', ''),
                "entry": entry,
            }
            for entry in structured_entries
        ]
        logger.info(f"Loaded {len(sections)} structured knowledge base entries")
    else:
        sections = extract_sections(text)
        logger.info(f"Extracted {len(sections)} sections from document")

    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # IMPROVEMENT: Use markdown heading boundaries as primary split points
        # so chunks respect the document's own structure rather than splitting
        # in the middle of a fact.
        separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    # Helper: fast token-set Jaccard similarity for deduplication
    def _jaccard(a: str, b: str) -> float:
        """Return word-level Jaccard similarity between two strings."""
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    # Create chunked documents with metadata
    all_chunks: List[LangchainDocument] = []
    seen_content: List[str] = []  # for deduplication

    for idx, section in enumerate(sections):
        section_heading = section['heading']
        section_content = section['content']
        entry = section.get('entry', {}) if isinstance(section, dict) else {}

        if not section_content.strip():
            continue

        # Split section content into chunks
        chunk_texts = text_splitter.split_text(section_content)

        for chunk_idx, chunk_text in enumerate(chunk_texts):
            if not chunk_text.strip():
                continue

            # IMPROVEMENT: Heading prefix injection
            # Prepend the section heading to every chunk so the embedding
            # always encodes the topic. Without this, short chunks like
            # "The intake is 660 seats." give zero signal about what they
            # describe, causing irrelevant retrieval for topic queries.
            prefixed_text = f"{section_heading}\n{chunk_text}"

            # IMPROVEMENT: Deduplication
            # Check if this chunk is near-identical to any previously seen
            # chunk. Common in JSON KBs where the same fact appears in
            # multiple entries (e.g. NAAC Grade mentioned in both "About"
            # and "Accreditation" entries). Jaccard > 0.92 → skip.
            is_duplicate = False
            if seen_content:
                # Only compare against the last ~30 chunks for performance
                for prev in seen_content[-30:]:
                    if _jaccard(chunk_text, prev) > 0.92:
                        is_duplicate = True
                        logger.debug(
                            f"Dedup: skipping near-duplicate chunk in '{section_heading}'"
                        )
                        break

            if is_duplicate:
                continue

            seen_content.append(chunk_text)

            metadata = {
                "source": source_filename,
                "section": section_heading,
                "chunk_id": f"chunk_{idx}_{chunk_idx}",
                "section_index": idx,
                "chunk_index": chunk_idx,
                "total_chunks_in_section": len(chunk_texts),
                "metadata_schema_version": settings.knowledge_base_schema_version,
            }

            if entry:
                metadata.update({
                    "entry_id": entry.get("id", f"entry_{idx}"),
                    "category": entry.get("category", "General"),
                    "title": entry.get("title", section_heading),
                    "source_url": entry.get("source_url", ""),
                })

            doc = LangchainDocument(
                page_content=prefixed_text,
                metadata=metadata
            )
            all_chunks.append(doc)

    # Calculate statistics
    avg_length = (
        sum(len(c.page_content) for c in all_chunks) / len(all_chunks)
        if all_chunks else 0
    )

    logger.info(f"Created {len(all_chunks)} chunks total (after deduplication)")
    logger.info(f"Average chunk length: {avg_length:.0f} characters")

    return all_chunks


# ============================================================
# LLM Client Setup
# ============================================================

def get_llm_client() -> ChatOpenAI:
    """
    Create and return the LLM client configured for OpenRouter.

    Uses OpenAI-compatible API through OpenRouter, allowing access
    to GPT-4o-mini and other models.

    Returns:
        ChatOpenAI: Configured LLM client
    """
    if not settings.openrouter_api_key:
        logger.warning("No OpenRouter API key found. LLM calls will fail.")

    # BUG FIX: temperature and max_tokens were hard-coded here (0.1 and 1024).
    # They must be read from settings so the config.py values actually take
    # effect. Hard-coded values mean no matter what you set in .env, the LLM
    # always runs at temperature=0.1 — higher than necessary for a fact-only
    # FAQ chatbot and inconsistent with the documented config.
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "https://bvrithyderabad.edu.in",
            "X-Title": "BVRIT Hyderabad FAQ Chatbot",
        },
    )

    logger.info(f"LLM client initialized: {settings.llm_model} "
                f"(temperature={settings.llm_temperature}, max_tokens={settings.llm_max_tokens})")
    return llm


def get_embedding_client() -> OpenAIEmbeddings:
    """
    Create and return the embeddings client for vector generation.

    Uses text-embedding-3-small through OpenRouter for consistent
    embedding generation across indexing and retrieval.

    Returns:
        OpenAIEmbeddings: Configured embeddings client
    """
    # Prefer remote OpenRouter/OpenAI embeddings when API key is available
    if settings.openrouter_api_key:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

        logger.info(f"Embedding client initialized (remote): {settings.embedding_model}")
        return embeddings

    # Fallback: use local sentence-transformers model (no external API key required)
    if SentenceTransformer is None:
        logger.error(
            "No OpenRouter API key and sentence-transformers is not installed. "
            "Install 'sentence-transformers' or set OPENROUTER_API_KEY in .env."
        )
        raise RuntimeError("No embedding backend available")

    class LocalEmbeddings:
        """Lightweight local embeddings wrapper compatible with LangChain's expectations."""

        def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
            self.model_name = model_name
            logger.info(f"Loading local embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)

        def embed_documents(self, texts: list):
            # Returns a list of vectors (lists of floats)
            vectors = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return [v.tolist() for v in vectors]

        def embed_query(self, text: str):
            vec = self._model.encode([text], show_progress_bar=False, convert_to_numpy=True)[0]
            return vec.tolist()

    logger.info("Embedding client initialized (local sentence-transformers)")
    return LocalEmbeddings()


def get_openai_client() -> OpenAI:
    """
    Get raw OpenAI client for direct API calls (used in evaluation).

    Returns:
        OpenAI: Configured OpenAI client
    """
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


# ============================================================
# Token Counting
# ============================================================

def estimate_tokens(text: str) -> int:
    """
    Roughly estimate the number of tokens in a text string.
    Uses the approximation: 1 token ≈ 4 characters for English text.

    Args:
        text: Input text

    Returns:
        int: Estimated token count
    """
    if isinstance(text, int):
        return text // 4
    return len(text) // 4


def count_tokens_in_chunks(chunks: List[LangchainDocument]) -> Dict[str, Any]:
    """
    Calculate token statistics for a list of chunks.

    Args:
        chunks: List of document chunks

    Returns:
        Dict: Token statistics
    """
    total_chars = sum(len(c.page_content) for c in chunks)
    total_tokens = estimate_tokens(total_chars)

    return {
        "total_chunks": len(chunks),
        "total_characters": total_chars,
        "estimated_tokens": total_tokens,
        "avg_chars_per_chunk": total_chars / len(chunks) if chunks else 0,
        "avg_tokens_per_chunk": total_tokens / len(chunks) if chunks else 0,
    }


# ============================================================
# Response Parsing
# ============================================================

def parse_citations(response: str) -> List[str]:
    """
    Extract citation section names from a response string.

    Citations follow the format: [Section: Section Name]

    Args:
        response: LLM response text

    Returns:
        List[str]: List of cited section names
    """
    pattern = r'\[Section:\s*(.*?)\]'
    citations = re.findall(pattern, response)
    return list(set(citations))


def extract_json_from_response(response: str) -> Optional[Dict]:
    """
    Extract JSON object from an LLM response.
    Handles cases where JSON is wrapped in markdown code blocks.

    Args:
        response: LLM response text

    Returns:
        Optional[Dict]: Parsed JSON or None on failure
    """
    # Try to find JSON within code blocks first
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try parsing the entire response as JSON
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    # Try finding JSON-like content
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to extract JSON from response")
    return None


# ============================================================
# Timing Utility
# ============================================================

class Timer:
    """
    Context manager for measuring execution time.

    Usage:
        with Timer() as t:
            do_something()
        print(f"Took {t.elapsed:.2f}s")
    """

    def __init__(self):
        self.start: float = 0.0
        self.end: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start

    def __str__(self):
        if self.elapsed < 1:
            return f"{self.elapsed * 1000:.0f}ms"
        elif self.elapsed < 60:
            return f"{self.elapsed:.2f}s"
        else:
            return f"{self.elapsed / 60:.1f}min"