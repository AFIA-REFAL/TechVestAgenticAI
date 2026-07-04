"""
BVRIT Hyderabad College FAQ Chatbot - Complete RAG Pipeline

Implements the full Retrieval-Augmented Generation pipeline:
1. Question → Embedding → Vector Search → Relevant Chunks
2. Chunks + Grounding Prompt → OpenRouter LLM → Generated Answer
3. Post-processing: Citation extraction, metadata enrichment, timing

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from langchain_core.documents import Document as LangchainDocument
from langchain_chroma import Chroma

from config import settings, logger
from utils import (
    get_llm_client,
    get_embedding_client,
    parse_citations,
    Timer,
    estimate_tokens,
)
from prompts import get_prompts

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """
    Structured response from the RAG pipeline.

    Attributes:
        question: Original user question
        answer: Generated answer text
        citations: List of cited section names
        retrieved_chunks: List of retrieved document chunks
        retrieved_metadata: List of chunk metadata dictionaries
        latency_seconds: Total pipeline latency
        token_usage: Token usage statistics
        context_used: Concatenated context string
        model: LLM model used
        embedding_model: Embedding model used
        refused: Whether the answer was refused (no context found)
    """
    question: str = ""
    answer: str = ""
    citations: List[str] = field(default_factory=list)
    retrieved_chunks: List[str] = field(default_factory=list)
    retrieved_metadata: List[Dict[str, Any]] = field(default_factory=list)
    latency_seconds: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    context_used: str = ""
    model: str = ""
    embedding_model: str = ""
    refused: bool = False
    related_images: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return asdict(self)


class RAGPipeline:
    """
    Complete Retrieval-Augmented Generation pipeline.

    Orchestrates retrieval, prompt formatting, LLM generation,
    and response post-processing.
    """

    def __init__(
        self,
        vector_store: Chroma,
        top_k: int = None,
        section_filter: str = None,
        debug: bool = False
    ):
        """
        Initialize the RAG pipeline.

        Args:
            vector_store: Initialized ChromaDB vector store
            top_k: Number of chunks to retrieve (default: from settings)
            section_filter: Optional section name to filter by
            debug: Enable debug mode for verbose logging
        """
        self.vector_store = vector_store
        self.top_k = top_k or settings.top_k
        self.section_filter = section_filter
        self.debug = debug

        # Initialize clients
        self.llm = get_llm_client()
        self.embeddings = get_embedding_client()

        # Load prompts
        self.prompts = get_prompts()

        # Configure retriever
        self._setup_retriever()

        logger.info(
            f"RAG Pipeline initialized: "
            f"model={settings.llm_model}, "
            f"top_k={self.top_k}, "
            f"filter={section_filter or 'None'}"
        )

    def _setup_retriever(self) -> None:
        """Configure the vector store retriever with search parameters."""
        search_kwargs = {"k": self.top_k}

        if self.section_filter:
            search_kwargs["filter"] = {"section": {"$eq": self.section_filter}}

        self.retriever = self.vector_store.as_retriever(
            search_kwargs=search_kwargs
        )

    def _standalone_query(self, question: str, chat_history: Optional[List[Dict[str, str]]]) -> str:
        """
        Rewrite a follow-up question into a standalone query using recent
        chat history, so retrieval works for things like:
            Turn 1: "What departments does BVRIT have?"
            Turn 2: "Tell me more about the first one."

        Without this, "the first one" retrieves nothing relevant and the
        Context evaluation dimension fails by design.

        Args:
            question: The raw user question for this turn
            chat_history: List of {"role": "user"/"assistant", "content": str}

        Returns:
            str: A standalone version of the question for embedding/retrieval
        """
        if not chat_history:
            return question

        # Only need the last couple of turns for pronoun/reference resolution
        recent = chat_history[-4:]
        history_text = "\n".join(
            f"{turn['role'].capitalize()}: {turn['content']}" for turn in recent
        )

        rewrite_prompt = (
            "Given the conversation so far and a follow-up question, "
            "rewrite the follow-up as a standalone question that contains "
            "all the context needed to search a knowledge base, without "
            "adding any new facts.\n\n"
            f"Conversation so far:\n{history_text}\n\n"
            f"Follow-up question: {question}\n\n"
            "Standalone question:"
        )

        try:
            rewritten = self.llm.invoke(rewrite_prompt).content.strip()
            return rewritten if rewritten else question
        except Exception as e:
            logger.warning(f"Query rewrite failed, falling back to raw question: {e}")
            return question

    def retrieve(
        self, question: str, chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[List[LangchainDocument], str]:
        """
        Retrieve relevant chunks for a question. If chat_history is given,
        the question is first rewritten into a standalone query so that
        follow-up questions ("tell me more about the first one") retrieve
        the right chunks.

        Args:
            question: User's question
            chat_history: Optional prior turns for context resolution

        Returns:
            Tuple of (retrieved_documents, concatenated_context_string)
        """
        search_query = self._standalone_query(question, chat_history)

        try:
            docs = self.retriever.invoke(search_query)
        except Exception as e:
            logger.error(f"Retrieval failed for question '{question}': {e}")
            return [], ""

        # Format context from retrieved documents
        context_parts = []
        for i, doc in enumerate(docs):
            section = doc.metadata.get("section", "Unknown")
            source = doc.metadata.get("source", "Unknown")
            chunk_id = doc.metadata.get("chunk_id", f"chunk_{i}")

            context_parts.append(
                f"[Chunk {i+1}] Section: {section}"
                f"\nSource: {source}"
                f"\nContent:\n{doc.page_content}\n"
            )

        context = "\n---\n".join(context_parts)

        if self.debug:
            logger.info(f"\n{'=' * 60}")
            logger.info("RETRIEVED CHUNKS (DEBUG MODE)")
            logger.info(f"{'=' * 60}")
            for i, doc in enumerate(docs):
                logger.info(
                    f"\n--- Chunk {i+1} ---"
                    f"\nSection: {doc.metadata.get('section', 'Unknown')}"
                    f"\nSource: {doc.metadata.get('source', 'Unknown')}"
                    f"\nChunk ID: {doc.metadata.get('chunk_id', 'N/A')}"
                    f"\nContent Preview: {doc.page_content[:200]}..."
                )
            logger.info(f"{'=' * 60}\n")

        return docs, context

    def generate(
        self,
        question: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate an answer using the LLM with grounded context.

        Args:
            question: User's question
            context: Retrieved document context
            chat_history: Optional prior turns, appended before the
                grounding prompt so the model can resolve references
                like "the first one" or "that department"

        Returns:
            Tuple of (generated_answer, token_usage_dict)
        """
        # Format the grounding prompt
        prompt = self.prompts.format_grounding_prompt(
            context=context,
            question=question
        )

        if chat_history:
            recent = chat_history[-4:]
            history_text = "\n".join(
                f"{turn['role'].capitalize()}: {turn['content']}" for turn in recent
            )
            prompt = (
                f"## PRIOR CONVERSATION (for resolving references only — "
                f"do not treat as knowledge-base content)\n{history_text}\n\n{prompt}"
            )

        try:
            # Call the LLM
            response = self.llm.invoke(prompt)

            # Extract answer
            answer = response.content.strip()

            # Track token usage
            token_usage = {
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0)
                if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.get("output_tokens", 0)
                if response.usage_metadata else 0,
                "total_tokens": (
                    (response.usage_metadata.get("input_tokens", 0) +
                     response.usage_metadata.get("output_tokens", 0))
                    if response.usage_metadata else 0
                ),
            }

            logger.info(
                f"Generation complete: {token_usage['total_tokens']} tokens used"
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer = (
                "I apologize, but I encountered an error while generating "
                "a response. Please try again later."
            )
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        return answer, token_usage

    def _check_if_refused(self, answer: str, context: str) -> bool:
        """
        Check if the answer indicates that information was not found.

        Args:
            answer: Generated answer
            context: Retrieved context

        Returns:
            bool: True if the answer refused (no info found)
        """
        refusal_phrases = [
            "couldn't find this information",
            "cannot find this information",
            "don't have this information",
            "not available in the knowledge base",
            "please contact the college office",
            "information is not available",
        ]

        # If no context was retrieved, it's a refusal
        if not context.strip():
            return True

        # Check for refusal phrases in the answer
        for phrase in refusal_phrases:
            if phrase.lower() in answer.lower():
                return True

        return False

    def answer(
        self, question: str, chat_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Complete RAG pipeline: retrieve → generate → post-process.

        Args:
            question: User's question
            chat_history: Optional list of {"role", "content"} prior turns.
                Pass the session's message history to support follow-up
                questions (Evaluation Dimension 07 — Context).

        Returns:
            RAGResponse: Structured response with answer and metadata
        """
        timer = Timer()
        timer.__enter__()

        # Step 1: Retrieve relevant chunks (query rewritten using history)
        docs, context = self.retrieve(question, chat_history=chat_history)

        # Step 2: Generate answer
        answer, token_usage = self.generate(question, context, chat_history=chat_history)

        # Step 3: Post-process
        refused = self._check_if_refused(answer, context)
        citations = parse_citations(answer)

        # Extract metadata from retrieved chunks
        retrieved_metadata = [
            {
                "section": doc.metadata.get("section", "Unknown"),
                "source": doc.metadata.get("source", "Unknown"),
                "source_url": doc.metadata.get("source_url", ""),
                "title": doc.metadata.get("title", ""),
                "category": doc.metadata.get("category", ""),
                "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                "section_index": doc.metadata.get("section_index", -1),
                "relevance_score": getattr(doc, "score", None),
            }
            for doc in docs
        ]

        timer.__exit__(None, None, None)

        response = RAGResponse(
            question=question,
            answer=answer,
            citations=citations,
            retrieved_chunks=[doc.page_content for doc in docs],
            retrieved_metadata=retrieved_metadata,
            latency_seconds=timer.elapsed,
            token_usage=token_usage,
            context_used=context,
            model=settings.llm_model,
            embedding_model=settings.embedding_model,
            refused=refused,
            related_images=[],
        )

        if self.debug:
            logger.info(f"\n{'=' * 60}")
            logger.info("RAG RESPONSE SUMMARY")
            logger.info(f"{'=' * 60}")
            logger.info(f"Question: {question}")
            logger.info(f"Answer: {answer[:300]}...")
            logger.info(f"Citations: {citations}")
            logger.info(f"Latency: {timer}")
            logger.info(f"Tokens: {token_usage}")
            logger.info(f"Refused: {refused}")
            logger.info(f"{'=' * 60}\n")

        return response


def create_rag_pipeline(
    vector_store: Chroma,
    top_k: int = None,
    section_filter: str = None,
    debug: bool = False
) -> RAGPipeline:
    """
    Factory function to create a configured RAG pipeline.

    Args:
        vector_store: Initialized ChromaDB vector store
        top_k: Number of chunks to retrieve
        section_filter: Optional section filter
        debug: Enable debug mode

    Returns:
        RAGPipeline: Configured pipeline instance
    """
    return RAGPipeline(
        vector_store=vector_store,
        top_k=top_k,
        section_filter=section_filter,
        debug=debug,
    )