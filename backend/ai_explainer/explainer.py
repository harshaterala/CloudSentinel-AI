"""RAG-grounded AI explainer and copilot response generation."""

from __future__ import annotations

import json
from typing import Any

from backend.ai_explainer.rag_engine import RAGEngine
from backend.config import GOOGLE_API_KEY, LLM_PROVIDER


class AIExplainer:
    """Generates explanations and copilot answers using RAG + Gemini/fallback."""

    def __init__(self):
        self.rag = RAGEngine()

    @staticmethod
    def _context_block(context_docs: list[dict[str, Any]]) -> str:
        return "\n\n---\n\n".join(
            [
                (
                    f"[{doc.get('category', 'general')}] {doc.get('title', 'Untitled')}\n"
                    f"Source: {doc.get('source', 'inline')}\n"
                    f"{doc.get('content', '')}"
                )
                for doc in context_docs
            ]
        )

    @staticmethod
    def _clean_json(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        return cleaned

    def _gemini_generate(self, prompt: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text or ""

    @staticmethod
    def _sources(context_docs: list[dict[str, Any]], top_k: int = 4) -> list[str]:
        return [
            f"{doc.get('category', 'general')}: {doc.get('title', 'Untitled')}"
            for doc in context_docs[:top_k]
        ]

    def _fallback_explanation(self, resource: dict[str, Any], context_docs: list[dict[str, Any]]) -> dict[str, str]:
        exposure = "publicly reachable" if resource.get("exposed_to_public") else "not publicly reachable"
        encryption = "unencrypted" if not resource.get("storage_encrypted", True) else "encrypted"
        mfa = "MFA disabled" if not resource.get("mfa_enabled", True) else "MFA enabled"
        root_cause = (
            f"{resource.get('resource_type', 'Resource')} {resource.get('resource_id', '')} has elevated risk from "
            f"config severity {resource.get('config_severity', 0)}, exposure level {resource.get('exposure_level', 0)}, "
            f"{encryption} storage posture, and identity posture ({mfa}); current network reachability is {exposure}."
        )
        business_impact = (
            f"If exploited, this asset can impact confidentiality and operations for {resource.get('cloud_provider', 'multi-cloud')} "
            f"workloads. Current SRS={resource.get('security_risk_score', 'N/A')} and CRS={resource.get('cost_risk_score', 'N/A')} "
            f"indicate both security and financial exposure."
        )
        remediation_steps = (
            "1) Remove unnecessary public access and tighten ingress rules. "
            "2) Enforce encryption at rest and MFA for privileged identities. "
            "3) Apply least-privilege IAM and baseline controls from cited CIS/NIST guidance. "
            "4) Re-scan and verify score reduction after remediation."
        )
        executive_summary = (
            f"This is a fix-first candidate with UPS {resource.get('unified_priority_score', 'N/A')}. "
            f"Grounded controls from {', '.join(self._sources(context_docs, top_k=2)) or 'knowledge base'} "
            "support immediate remediation."
        )
        return {
            "root_cause": root_cause,
            "business_impact": business_impact,
            "remediation_steps": remediation_steps,
            "executive_summary": executive_summary,
        }

    def explain(self, resource: dict[str, Any]) -> dict[str, str]:
        query = (
            f"Explain risk and remediation for {resource.get('resource_type')} {resource.get('resource_id')} "
            f"with provider {resource.get('cloud_provider')} and exposure {resource.get('exposure_level', 0)}"
        )
        context_docs = self.rag.retrieve_with_metadata(query, top_k=4)

        prompt = f"""
You are a cloud security assistant. Use the provided resource metadata and retrieved references.
Return ONLY valid JSON with exactly these keys and string values:
- root_cause
- business_impact
- remediation_steps
- executive_summary

RESOURCE:
{json.dumps(resource, ensure_ascii=True)}

RETRIEVED_CONTEXT:
{self._context_block(context_docs)}

Constraints:
- Be specific to the resource.
- Ground statements in the retrieved context.
- Do not output extra keys.
""".strip()

        if LLM_PROVIDER == "gemini" and GOOGLE_API_KEY:
            try:
                raw = self._gemini_generate(prompt)
                parsed = json.loads(self._clean_json(raw))
                return {
                    "root_cause": str(parsed.get("root_cause", "")).strip(),
                    "business_impact": str(parsed.get("business_impact", "")).strip(),
                    "remediation_steps": str(parsed.get("remediation_steps", "")).strip(),
                    "executive_summary": str(parsed.get("executive_summary", "")).strip(),
                }
            except Exception:
                return self._fallback_explanation(resource, context_docs)

        return self._fallback_explanation(resource, context_docs)

    def answer_query(
        self,
        query: str,
        resources: list[dict[str, Any]],
        top_k: int = 5,
    ) -> dict[str, Any]:
        context_docs = self.rag.retrieve_with_metadata(query, top_k=top_k)
        compact_resources = resources[: min(len(resources), top_k)]

        prompt = f"""
You are a cloud security and FinOps copilot.
Answer the user's query using retrieved references and resource facts.
Return ONLY valid JSON with exactly:
- answer (string)
- references (array of strings)

USER_QUERY:
{query}

TOP_RESOURCES:
{json.dumps(compact_resources, ensure_ascii=True)}

RETRIEVED_CONTEXT:
{self._context_block(context_docs)}
""".strip()

        if LLM_PROVIDER == "gemini" and GOOGLE_API_KEY:
            try:
                raw = self._gemini_generate(prompt)
                parsed = json.loads(self._clean_json(raw))
                answer = str(parsed.get("answer", "")).strip()
                refs = parsed.get("references", [])
                if not isinstance(refs, list):
                    refs = [str(refs)]
                return {
                    "answer": answer or "Risk and cost posture analyzed using retrieved benchmark guidance.",
                    "sources": [str(r) for r in refs if str(r).strip()] or self._sources(context_docs),
                    "related_resources": compact_resources,
                }
            except Exception:
                pass

        top = sorted(compact_resources, key=lambda r: float(r.get("unified_priority_score", 0)), reverse=True)
        highlights = []
        for rec in top[:3]:
            highlights.append(
                f"{rec.get('resource_id')} (UPS {rec.get('unified_priority_score')}, "
                f"SRS {rec.get('security_risk_score')}, CRS {rec.get('cost_risk_score')})"
            )
        answer = (
            f"Based on retrieved controls and current telemetry, priority resources are: {', '.join(highlights)}. "
            "Address internet exposure, broad ingress rules, and unencrypted assets first, then remove idle/orphaned waste."
        )
        return {
            "answer": answer,
            "sources": self._sources(context_docs),
            "related_resources": compact_resources,
        }
