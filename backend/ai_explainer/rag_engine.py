"""
RAG Engine – embeds knowledge base documents and retrieves relevant context.
Uses SentenceTransformers + FAISS for vector similarity search.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np

from backend.ai_explainer.knowledge_base import KNOWLEDGE_DOCUMENTS
from backend.config import EMBEDDING_MODEL, VECTOR_DB_DIR


class RAGEngine:
    """Retrieval-Augmented Generation engine backed by FAISS."""

    def __init__(self, force_rebuild: bool = False):
        self.documents = KNOWLEDGE_DOCUMENTS
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self.index = None
        self.model = None
        self._build(force_rebuild=force_rebuild)

    def _build(self, force_rebuild: bool = False):
        from sentence_transformers import SentenceTransformer
        import faiss

        self.model = SentenceTransformer(EMBEDDING_MODEL)

        self.texts = [f"{doc['title']}\n{doc['content']}" for doc in self.documents]
        self.metadata = [
            {
                "title": doc.get("title", "Untitled"),
                "category": doc.get("category", "general"),
                "source": doc.get("source", "inline"),
            }
            for doc in self.documents
        ]

        cache_path = Path(VECTOR_DB_DIR)
        index_file = cache_path / "faiss.index"
        texts_file = cache_path / "texts.pkl"
        meta_file = cache_path / "metadata.pkl"

        if (not force_rebuild) and index_file.exists() and texts_file.exists() and meta_file.exists():
            self.index = faiss.read_index(str(index_file))
            with open(texts_file, "rb") as f:
                self.texts = pickle.load(f)
            with open(meta_file, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            embeddings = self.model.encode(self.texts, show_progress_bar=False)
            embeddings = np.array(embeddings, dtype="float32")

            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)

            cache_path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(index_file))
            with open(texts_file, "wb") as f:
                pickle.dump(self.texts, f)
            with open(meta_file, "wb") as f:
                pickle.dump(self.metadata, f)

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> list[dict]:
        """Return top-k relevant docs with title/category/source/score/content."""
        import faiss

        query_vec = self.model.encode([query])
        query_vec = np.array(query_vec, dtype="float32")
        faiss.normalize_L2(query_vec)

        scores, indices = self.index.search(query_vec, top_k)
        results: list[dict] = []
        for i, idx in enumerate(indices[0]):
            if idx >= len(self.texts):
                continue
            meta = self.metadata[idx] if idx < len(self.metadata) else {}
            results.append(
                {
                    "title": meta.get("title", "Untitled"),
                    "category": meta.get("category", "general"),
                    "source": meta.get("source", "inline"),
                    "score": round(float(scores[0][i]), 4),
                    "content": self.texts[idx],
                }
            )
        return results

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Return the top-k most relevant knowledge documents for a query."""
        return [doc["content"] for doc in self.retrieve_with_metadata(query, top_k=top_k)]
