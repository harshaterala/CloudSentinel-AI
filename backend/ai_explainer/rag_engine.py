"""
RAG Engine – embeds knowledge base documents and retrieves relevant context.
Uses lightweight hashed embeddings + FAISS for vector similarity search.
"""

from __future__ import annotations

import pickle
from pathlib import Path
import re

import numpy as np

from backend.ai_explainer.knowledge_base import KNOWLEDGE_DOCUMENTS
from backend.config import VECTOR_DB_DIR


class RAGEngine:
    """Retrieval-Augmented Generation engine backed by FAISS."""

    def __init__(self, force_rebuild: bool = False):
        self.documents = KNOWLEDGE_DOCUMENTS
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self.index = None
        self.dim = 256
        self.mode = "vector"
        self._build(force_rebuild=force_rebuild)

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype="float32")
        for i, text in enumerate(texts):
            tokens = re.findall(r"[a-z0-9_]+", text.lower())
            for token in tokens:
                idx = hash(token) % self.dim
                vectors[i, idx] += 1.0
        return vectors

    def _build(self, force_rebuild: bool = False):
        self.texts = [f"{doc['title']}\n{doc['content']}" for doc in self.documents]
        self.metadata = [
            {
                "title": doc.get("title", "Untitled"),
                "category": doc.get("category", "general"),
                "source": doc.get("source", "inline"),
            }
            for doc in self.documents
        ]

        try:
            import faiss
        except ModuleNotFoundError:
            self.mode = "lexical"
            return

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
            if getattr(self.index, "d", self.dim) != self.dim:
                force_rebuild = True
                self.index = None
        if force_rebuild or self.index is None:
            embeddings = self._embed_texts(self.texts)

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
        if self.mode == "lexical" or self.index is None:
            query_terms = {t for t in query.lower().split() if t}
            scored: list[tuple[float, int]] = []
            for idx, text in enumerate(self.texts):
                tokens = set(text.lower().split())
                overlap = len(query_terms & tokens)
                score = overlap / max(1, len(query_terms))
                scored.append((score, idx))
            scored.sort(key=lambda x: x[0], reverse=True)
            results: list[dict] = []
            for score, idx in scored[:top_k]:
                meta = self.metadata[idx] if idx < len(self.metadata) else {}
                results.append(
                    {
                        "title": meta.get("title", "Untitled"),
                        "category": meta.get("category", "general"),
                        "source": meta.get("source", "inline"),
                        "score": round(float(score), 4),
                        "content": self.texts[idx],
                    }
                )
            return results

        import faiss

        query_vec = self._embed_texts([query])
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
