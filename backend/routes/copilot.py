"""Copilot route helpers that always use RAG + generator flow."""

from __future__ import annotations

from typing import Any


def generate_copilot_response(explainer: Any, query: str, resources: list[dict[str, Any]], top_k: int = 5) -> dict[str, Any]:
    """Single-path copilot generation with no intent-based branching."""
    return explainer.answer_query(query=query, resources=resources, top_k=top_k)
