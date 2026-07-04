"""
SimpleVectorStore

A minimal local vector store implementation that persists embeddings and metadata
to disk and provides a cosine-similarity retriever. Avoids external vector DB
dependencies so the project can run offline with sentence-transformers.

Files created under `<chroma_db_dir>/simple_store/`:
- vectors.npy        : numpy array of shape (n, dim)
- metadatas.json     : list of metadata dicts (aligned with vectors)
- ids.json           : list of ids for vectors

Usage:
    store = SimpleVectorStore(path)
    store.add_documents(docs, embedding_client)
    results = store.similarity_search(query, k=5)
"""
from pathlib import Path
import json
import numpy as np
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


class SimpleVectorStore:
    def __init__(self, persist_dir: str):
        self.base = Path(persist_dir) / "simple_store"
        _ensure_dir(self.base)
        self.vectors_path = self.base / "vectors.npy"
        self.metadatas_path = self.base / "metadatas.json"
        self.ids_path = self.base / "ids.json"

        self.vectors = None
        self.metadatas = []
        self.ids = []

        self._load()

    def _load(self):
        if self.vectors_path.exists():
            try:
                self.vectors = np.load(self.vectors_path)
            except Exception:
                logger.exception("Failed to load vectors.npy")
                self.vectors = None

        if self.metadatas_path.exists():
            with open(self.metadatas_path, 'r', encoding='utf-8') as f:
                self.metadatas = json.load(f)

        if self.ids_path.exists():
            with open(self.ids_path, 'r', encoding='utf-8') as f:
                self.ids = json.load(f)

    def _persist(self):
        if self.vectors is not None:
            np.save(self.vectors_path, self.vectors)
        with open(self.metadatas_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadatas, f, ensure_ascii=False, indent=2)
        with open(self.ids_path, 'w', encoding='utf-8') as f:
            json.dump(self.ids, f, ensure_ascii=False, indent=2)

    def add_documents(self, docs: List[Dict[str, Any]], embedding_client) -> None:
        """Embed and add documents. `docs` is a list of dicts with 'page_content' and 'metadata'.

        We store the chunk text inside the metadata under the key 'text' so that
        the retriever can return the original chunk content along with metadata.
        """
        texts = [d['page_content'] for d in docs]
        metadatas = [d.get('metadata', {}) for d in docs]
        ids = [d.get('metadata', {}).get('chunk_id', f"id_{i}") for i, d in enumerate(docs)]

        # Embed texts
        vectors = embedding_client.embed_documents(texts)
        vectors = np.array(vectors, dtype=np.float32)

        # Ensure each metadata includes the original text for retrieval
        for md, txt in zip(metadatas, texts):
            md.setdefault('text', txt)

        if self.vectors is None:
            self.vectors = vectors
            self.metadatas = metadatas
            self.ids = ids
        else:
            self.vectors = np.vstack([self.vectors, vectors])
            self.metadatas.extend(metadatas)
            self.ids.extend(ids)

        self._persist()

    def similarity_search(self, query: str, embedding_client, k: int = 5) -> List[Dict[str, Any]]:
        if self.vectors is None or len(self.vectors) == 0:
            return []

        qvec = np.array(embedding_client.embed_query(query), dtype=np.float32)
        # cosine similarity
        norms = np.linalg.norm(self.vectors, axis=1) * (np.linalg.norm(qvec) + 1e-12)
        sims = (self.vectors @ qvec) / norms
        idxs = np.argsort(-sims)[:k]

        results = []
        for i in idxs:
            results.append({
                'score': float(sims[i]),
                'metadata': self.metadatas[i] if i < len(self.metadatas) else {},
                'id': self.ids[i] if i < len(self.ids) else str(i),
                'text': None,
            })

        return results
