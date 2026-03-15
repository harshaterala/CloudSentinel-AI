"""AI explainer with RAG-backed, structured enterprise-ready output."""

from __future__ import annotations

import json
from typing import Any

from backend.ai_explainer.rag_engine import RAGEngine
from backend.config import COMPUTE_TYPES, GOOGLE_API_KEY, LLM_PROVIDER, OPENAI_API_KEY


class AIExplainer:
    """Generates risk explanations using RAG + optional LLM providers."""

    def __init__(self):
        self.rag = RAGEngine()

    def _build_query(self, resource: dict[str, Any]) -> str:
        parts = [
            f"Resource type: {resource.get('resource_type', 'Unknown')}",
            f"Publicly exposed: {resource.get('exposed_to_public', False)}",
            f"Open security group: {resource.get('open_security_group', False)}",
            f"Storage encrypted: {resource.get('storage_encrypted', True)}",
            f"Config severity: {resource.get('config_severity', 0)}",
            f"Data sensitivity: {resource.get('data_sensitivity', 0)}",
            f"Days exposed: {resource.get('days_exposed', 0)}",
            f"CPU usage: {resource.get('cpu_usage', 0)}%",
            f"Monthly cost: ${resource.get('monthly_cost', 0)}",
        ]
        return "Cloud resource security analysis: " + "; ".join(parts)

    def _build_prompt(self, resource: dict[str, Any], context_docs: list[dict]) -> str:
        context_block = "\n\n---\n\n".join(
            [
                (
                    f"[{doc.get('category', 'general')}] {doc.get('title', 'Untitled')}"
                    f"\nSource: {doc.get('source', 'inline')}"
                    f"\n{doc.get('content', '')}"
                )
                for doc in context_docs
            ]
        )

        return f"""You are a cloud security expert copilot. Use the context and resource metadata to generate concise enterprise-ready JSON.

KNOWLEDGE BASE CONTEXT:
{context_block}

RESOURCE DETAILS:
- Resource ID: {resource.get('resource_id')}
- Resource Type: {resource.get('resource_type')}
- Cloud Provider: {resource.get('cloud_provider', 'N/A')}
- Region: {resource.get('region', 'N/A')}
- Publicly Exposed: {resource.get('exposed_to_public')}
- Open Security Group: {resource.get('open_security_group')}
- Storage Encrypted: {resource.get('storage_encrypted')}
- Config Severity: {resource.get('config_severity')}
- Data Sensitivity: {resource.get('data_sensitivity')}
- Days Exposed: {resource.get('days_exposed')}
- CPU Usage: {resource.get('cpu_usage')}%
- Monthly Cost: ${resource.get('monthly_cost')}
- Security Risk Score: {resource.get('security_risk_score', 'N/A')}
- Cost Risk Score: {resource.get('cost_risk_score', 'N/A')}
- Unified Priority Score: {resource.get('unified_priority_score', 'N/A')}

Return valid JSON only:
{{
  "risk_summary": "...",
  "exploitation_impact": "...",
  "remediation_steps": ["...", "..."],
  "business_impact": "..."
}}
"""

    def _template_explanation(self, resource: dict[str, Any], context_docs: list[dict]) -> dict:
        risks: list[str] = []
        impacts: list[str] = []
        remediation_steps: list[str] = []

        rtype = resource.get("resource_type", "Unknown")
        rid = resource.get("resource_id", "unknown")
        provider = resource.get("cloud_provider", "Unknown")

        if resource.get("exposed_to_public"):
            risks.append(f"{rtype} ({rid}) is publicly exposed")
            impacts.append("Unauthorized access and potential data exfiltration risk")
            remediation_steps.append("Remove public exposure and move service behind private networking controls")

        if resource.get("open_security_group"):
            risks.append("Network rules allow broad inbound access")
            impacts.append("Increased attack surface for scanning and exploitation")
            remediation_steps.append("Restrict inbound CIDR and ports to approved access paths")

        if not resource.get("storage_encrypted", True):
            risks.append("Storage is not encrypted at rest")
            impacts.append("Sensitive data may be exposed if storage is compromised")
            remediation_steps.append("Enable encryption at rest with managed encryption keys")

        severity = resource.get("config_severity", 0)
        if severity > 0.7:
            risks.append(f"High configuration severity ({severity:.2f})")
            impacts.append("Multiple baseline deviations can compound breach probability")
            remediation_steps.append("Run baseline compliance scan and remediate critical findings")

        days = resource.get("days_exposed", 0)
        if days > 90:
            risks.append(f"Exposure has persisted for {days} days")
            impacts.append("Long-lived exposure increases probability of successful compromise")
            remediation_steps.append("Set SLA-based remediation alerts for exposures older than 30 days")

        cpu = resource.get("cpu_usage", 100)
        cost = resource.get("monthly_cost", 0)
        if cpu < 10 and rtype in COMPUTE_TYPES:
            risks.append(f"Compute is idle ({cpu}% CPU utilization)")
            impacts.append(f"Potential avoidable waste of about ${cost * 0.9:.2f} per month")
            remediation_steps.append("Stop, schedule, or decommission idle compute resources")
        elif cpu < 40 and cost > 100 and rtype in COMPUTE_TYPES:
            risks.append(f"Compute appears oversized ({cpu}% CPU at ${cost:.2f}/month)")
            impacts.append(f"Potential avoidable waste of about ${cost * 0.4:.2f} per month")
            remediation_steps.append("Right-size instances using cloud recommendation tooling")

        if not risks:
            risks.append("Resource shows moderate risk profile based on current controls")
            impacts.append("No immediate critical exploit path detected")
            remediation_steps.append("Maintain baseline checks and periodic hardening reviews")

        sources = [f"{doc.get('category', 'general')}: {doc.get('title', 'Untitled')}" for doc in context_docs[:3]]
        risk_summary = "; ".join(risks)
        exploitation_impact = "; ".join(impacts)
        business_impact = (
            f"SRS {resource.get('security_risk_score', 'N/A')}/100, "
            f"CRS {resource.get('cost_risk_score', 'N/A')}/100, "
            f"UPS {resource.get('unified_priority_score', 'N/A')}/100. "
            "This finding can affect security posture, compliance outcomes, and cloud spend efficiency."
        )

        return {
            "resource_id": rid,
            "resource_type": rtype,
            "risk_summary": risk_summary,
            "exploitation_impact": exploitation_impact,
            "remediation_steps": remediation_steps,
            "business_impact": business_impact,
            "sources": sources,
            "risk": risk_summary,
            "impact": exploitation_impact,
            "recommendation": "; ".join(remediation_steps),
            "source": "template",
        }

    def _llm_openai(self, prompt: str) -> str:
        import openai

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _llm_gemini(self, prompt: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text

    def _parse_llm_response(self, text: str, resource: dict[str, Any], context_docs: list[dict]) -> dict:
        rid = resource.get("resource_id", "")
        rtype = resource.get("resource_type", "Unknown")

        try:
            raw = json.loads(text)
            risk_summary = raw.get("risk_summary", "See detailed analysis")
            exploitation_impact = raw.get("exploitation_impact", "Potential exploitation impact is elevated")
            remediation_steps = raw.get("remediation_steps", ["Review and apply recommended controls"])
            if not isinstance(remediation_steps, list) or not remediation_steps:
                remediation_steps = [str(remediation_steps)]
            business_impact = raw.get("business_impact", "Security and cost impacts require remediation")
        except Exception:
            return self._template_explanation(resource, context_docs)

        sources = [f"{doc.get('category', 'general')}: {doc.get('title', 'Untitled')}" for doc in context_docs[:3]]
        return {
            "resource_id": rid,
            "resource_type": rtype,
            "risk_summary": risk_summary,
            "exploitation_impact": exploitation_impact,
            "remediation_steps": remediation_steps,
            "business_impact": business_impact,
            "sources": sources,
            "risk": risk_summary,
            "impact": exploitation_impact,
            "recommendation": "; ".join(remediation_steps),
            "source": "llm",
        }

    def explain(self, resource: dict[str, Any]) -> dict:
        query = self._build_query(resource)
        context_docs = self.rag.retrieve_with_metadata(query, top_k=3)

        if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
            prompt = self._build_prompt(resource, context_docs)
            raw = self._llm_openai(prompt)
            return self._parse_llm_response(raw, resource, context_docs)

        if LLM_PROVIDER == "gemini" and GOOGLE_API_KEY:
            prompt = self._build_prompt(resource, context_docs)
            raw = self._llm_gemini(prompt)
            return self._parse_llm_response(raw, resource, context_docs)

        return self._template_explanation(resource, context_docs)
