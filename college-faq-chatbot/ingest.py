"""
BVRIT Hyderabad College FAQ Chatbot - Document Ingestion Pipeline

Handles the complete ingestion workflow:
1. Load .docx document
2. Extract sections with headings
3. Split into chunks with metadata using RecursiveCharacterTextSplitter
4. Generate embeddings using text-embedding-3-small
5. Store in persistent ChromaDB
6. On restart, reuse existing database to avoid re-embedding

Author: Senior GenAI Engineer
Version: 1.0.0
"""

import os
import logging
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document as LangchainDocument

from config import settings, logger
from utils import (
    load_document,
    load_knowledge_base_entries,
    create_chunks_with_metadata,
    get_embedding_client,
    count_tokens_in_chunks,
)
from simple_vectorstore import SimpleVectorStore

logger = logging.getLogger(__name__)


class DocumentIngestor:
    """
    Handles document ingestion into ChromaDB vector store.
    Detects existing database and skips re-embedding when possible.
    """

    def __init__(self):
        """Initialize the ingestor with configuration from settings."""
        self.chroma_db_dir = settings.chroma_db_path
        self.collection_name = settings.collection_name
        self.document_path = settings.document_file_path
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.embeddings = get_embedding_client()
        self.local_store = SimpleVectorStore(str(self.chroma_db_dir))

        # State tracking
        self.chunks: List[LangchainDocument] = []
        self.vector_store: Optional[Chroma] = None

    def database_exists(self) -> bool:
        """
        Check if a persistent ChromaDB database already exists AND
        already contains vectors for our collection.

        NOTE: Chroma's persistent client does NOT create a subfolder
        named after the collection (that was the original bug here —
        `chroma_db_dir / collection_name` never exists in Chroma
        >=0.5, so this always returned False and the app re-embedded
        on every single restart, defeating persistence). The correct
        check is: does the sqlite file exist, and does opening the
        collection give us a non-zero vector count.

        Returns:
            bool: True if database exists and has data
        """
        sqlite_file = self.chroma_db_dir / "chroma.sqlite3"
        if not sqlite_file.exists():
            return False

        try:
            probe_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.chroma_db_dir),
            )
            count = probe_store._collection.count()
            if count > 0:
                sample = probe_store._collection.get(limit=1)
                sample_metadata = sample.get("metadatas", [{}])[0] if sample.get("metadatas") else {}
                schema_version = sample_metadata.get("metadata_schema_version", 0)
                kb_entries = load_knowledge_base_entries(str(self.document_path))
                if kb_entries and schema_version < settings.knowledge_base_schema_version:
                    logger.info(
                        f"Existing ChromaDB uses schema version {schema_version}, "
                        f"expected {settings.knowledge_base_schema_version}; re-ingesting to add image-ready metadata."
                    )
                    return False
                logger.info(
                    f"Existing ChromaDB found at: {self.chroma_db_dir} "
                    f"({count} vectors in '{self.collection_name}')"
                )
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not probe existing ChromaDB, will re-ingest: {e}")
            return False

    def load_and_chunk_document(self) -> List[LangchainDocument]:
        """
        Load the document and split into chunks with metadata.

        Returns:
            List[LangchainDocument]: Document chunks with metadata
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: Document Ingestion")
        logger.info("=" * 60)

        # Load document
        structured_entries = load_knowledge_base_entries(str(self.document_path))
        if structured_entries:
            logger.info(f"Structured knowledge base detected: {len(structured_entries)} entries")
            self.chunks = create_chunks_with_metadata(
                text="",
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                source_filename=self.document_path.name,
                structured_entries=structured_entries,
            )
        else:
            text = load_document(str(self.document_path))

            # Create chunks with metadata
            self.chunks = create_chunks_with_metadata(
                text=text,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                source_filename=self.document_path.name,
            )

        # Print statistics
        token_stats = count_tokens_in_chunks(self.chunks)
        logger.info(f"\n{'=' * 60}")
        logger.info("INGESTION STATISTICS")
        logger.info(f"{'=' * 60}")
        logger.info(f"Document: {self.document_path.name}")
        logger.info(f"Total sections extracted: {len(set(c.metadata.get('section', '') for c in self.chunks))}")
        logger.info(f"Total chunks created: {token_stats['total_chunks']}")
        logger.info(f"Average chunk length: {token_stats['avg_chars_per_chunk']:.0f} characters")
        logger.info(f"Estimated total tokens: {token_stats['estimated_tokens']}")
        logger.info(f"Chunk size: {self.chunk_size}")
        logger.info(f"Chunk overlap: {self.chunk_overlap}")
        logger.info(f"{'=' * 60}\n")

        return self.chunks

    def create_vector_store(self) -> Chroma:
        """
        Create or load the ChromaDB vector store.

        If a persistent database already exists, load it.
        Otherwise, create a new one from the chunks.

        Returns:
            Chroma: ChromaDB vector store instance
        """
        logger.info("=" * 60)
        logger.info("PHASE 2: Vector Store Creation")
        logger.info("=" * 60)

        # If an OpenRouter API key exists and Chroma is available, prefer Chroma
        if settings.openrouter_api_key:
            try:
                if self.database_exists():
                    logger.info("Loading existing ChromaDB...")
                    self.vector_store = Chroma(
                        collection_name=self.collection_name,
                        embedding_function=self.embeddings,
                        persist_directory=str(self.chroma_db_dir),
                    )
                    collection_size = self.vector_store._collection.count()
                    logger.info(
                        f"✅ Loaded existing database with {collection_size} vectors"
                    )
                else:
                    if self.chroma_db_dir.exists():
                        logger.info("Clearing stale ChromaDB cache before rebuild")
                        shutil.rmtree(self.chroma_db_dir, ignore_errors=True)

                    logger.info("Creating new ChromaDB from chunks...")
                    logger.info(f"Embedding model: {settings.embedding_model}")
                    logger.info(f"Number of chunks to embed: {len(self.chunks)}")

                    self.vector_store = Chroma.from_documents(
                        documents=self.chunks,
                        embedding=self.embeddings,
                        persist_directory=str(self.chroma_db_dir),
                        collection_name=self.collection_name,
                    )

                    collection_size = self.vector_store._collection.count()
                    logger.info(
                        f"✅ Created new database with {collection_size} vectors"
                    )
                    logger.info(f"Database persisted at: {self.chroma_db_dir}")

                return self.vector_store
            except Exception as e:
                logger.exception("ChromaDB path failed, falling back to local store: %s", e)

        # Fallback to local SimpleVectorStore when remote embeddings or ChromaDB are not available
        logger.info("Using local SimpleVectorStore for embeddings and retrieval")
        # If we have chunks and no existing vectors, create/append
        if self.chunks:
            # Prepare docs as simple dicts
            docs = [{"page_content": c.page_content, "metadata": c.metadata} for c in self.chunks]
            self.local_store.add_documents(docs, self.embeddings)
        else:
            logger.info("No chunks to embed; assuming existing local store files may exist")

        # Represent local_store as a lightweight wrapper
        self.vector_store = self.local_store

        logger.info(f"{'=' * 60}\n")
        return self.vector_store

    def get_retriever(self, top_k: int = None, section_filter: str = None):
        """
        Get a retriever from the vector store with optional filtering.

        IMPROVEMENT: When settings.use_mmr is True, the retriever uses
        Maximal Marginal Relevance instead of plain similarity search.
        MMR fetches mmr_fetch_k candidates from the vector store and then
        re-ranks them to maximise both relevance AND diversity, so the
        top-k results cover different aspects of the query rather than
        repeating the same paragraph 8 times.

        Args:
            top_k: Number of chunks to retrieve (default: from settings)
            section_filter: Optional section name to filter by

        Returns:
            Retriever: Configured retriever object
        """
        if self.vector_store is None:
            raise ValueError(
                "Vector store not initialized. Run create_vector_store() first."
            )

        k = top_k or settings.top_k

        # If using local SimpleVectorStore, return a lightweight retriever
        from simple_vectorstore import SimpleVectorStore as _SimpleStore
        if isinstance(self.vector_store, _SimpleStore):
            class LocalRetriever:
                def __init__(self, store, k, emb_client):
                    self.store = store
                    self.k = k
                    self.emb = emb_client

                def get_relevant_documents(self, query: str):
                    results = self.store.similarity_search(query, embedding_client=self.emb, k=self.k)
                    docs = []
                    for r in results:
                        md = r.get('metadata', {})
                        text = md.get('text', '')
                        from langchain_core.documents import Document as LangchainDocument
                        docs.append(LangchainDocument(page_content=text, metadata=md))
                    return docs

            logger.info(f"Local retriever created: k={k}")
            return LocalRetriever(self.vector_store, k, self.embeddings)

        # --- ChromaDB retriever ---
        # BUG FIX: The original code always used "similarity" search.
        # With use_mmr=True we switch to "mmr" which fetches fetch_k
        # candidates and re-ranks for diversity. Without MMR all top-k
        # chunks can be near-copies of the same sentence.
        search_type = "mmr" if settings.use_mmr else "similarity"

        if section_filter:
            if settings.use_mmr:
                search_kwargs = {
                    "k": k,
                    "fetch_k": settings.mmr_fetch_k,
                    "lambda_mult": settings.mmr_lambda,
                    "filter": {"section": {"$eq": section_filter}},
                }
            else:
                search_kwargs = {
                    "k": k,
                    "filter": {"section": {"$eq": section_filter}},
                }
        else:
            if settings.use_mmr:
                search_kwargs = {
                    "k": k,
                    "fetch_k": settings.mmr_fetch_k,
                    "lambda_mult": settings.mmr_lambda,
                }
            else:
                search_kwargs = {"k": k}

        retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

        logger.info(
            f"Retriever created: search_type={search_type}, k={k}"
            + (f", section={section_filter}" if section_filter else "")
        )

        return retriever

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            Dict: Collection statistics
        """
        if self.vector_store is None:
            return {"status": "Not initialized"}

        try:
            collection = self.vector_store._collection
            count = collection.count()

            # Get sample metadata to understand structure
            sample = collection.get(limit=1)
            sample_metadata = sample.get("metadatas", [{}])[0] if sample.get("metadatas") else {}

            return {
                "status": "Ready",
                "total_vectors": count,
                "collection_name": self.collection_name,
                "embedding_model": settings.embedding_model,
                "sample_metadata_keys": list(sample_metadata.keys()) if sample_metadata else [],
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"status": "Error", "error": str(e)}


def run_ingestion() -> DocumentIngestor:
    """
    Run the complete ingestion pipeline.
    Can be called from app.py or standalone.

    Returns:
        DocumentIngestor: Configured ingestor with vector store
    """
    ingestor = DocumentIngestor()

    # Only load and chunk if database doesn't exist
    if not ingestor.database_exists():
        ingestor.load_and_chunk_document()
    else:
        logger.info("Database exists. Skipping document loading and chunking.")

    # Create/load vector store
    ingestor.create_vector_store()

    # Print stats
    stats = ingestor.get_collection_stats()
    logger.info(f"Collection stats: {stats}")

    return ingestor


if __name__ == "__main__":
    """Run ingestion standalone."""
    print("\n" + "=" * 60)
    print("BVRIT Hyderabad - Document Ingestion Pipeline")
    print("=" * 60 + "\n")

    ingestor = run_ingestion()

    print("\n" + "=" * 60)
    print("✅ Ingestion Complete!")
    print("=" * 60)
    print(f"Database location: {settings.chroma_db_dir}")
    print(f"Collection: {settings.collection_name}")
    print(f"Embedding model: {settings.embedding_model}")
    print("=" * 60 + "\n")