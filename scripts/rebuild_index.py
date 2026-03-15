"""Rebuild the RAG vector index from local knowledge documents.

Usage:
  python scripts/rebuild_index.py
"""

from backend.ai_explainer.rag_engine import RAGEngine


def main() -> None:
    engine = RAGEngine(force_rebuild=True)
    print(f"Rebuilt vector index with {len(engine.documents)} knowledge documents.")


if __name__ == "__main__":
    main()
