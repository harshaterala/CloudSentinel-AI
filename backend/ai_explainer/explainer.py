"""
AI Explainer – generates natural language explanations for detected risks.
Supports three modes:
  1. OpenAI  (LLM_PROVIDER=openai + OPENAI_API_KEY)
  2. Gemini  (LLM_PROVIDER=gemini + GOOGLE_API_KEY)
  3. Template fallback with RAG context (default, no API key needed)
"""

from __future__ import annotations

from typing import Any

from backend.ai_explainer.rag_engine import RAGEngine
from backend.config import LLM_PROVIDER, OPENAI_API_KEY, GOOGLE_API_KEY, COMPUTE_TYPES


class AIExplainer:
    """Generates risk explanations using RAG + LLM (or template fallback)."""

    def __init__(self):
        self.rag = RAGEngine()

    def _build_query(self, resource: dict[str, Any]) -> str:
        """Construct a natural-language query from resource attributes."""
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

    def _build_prompt(self, resource: dict[str, Any], context_docs: list[str]) -> str:
        """Build the LLM prompt with retrieved context."""
        context_block = "\n\n---\n\n".join(context_docs)
        return f"""You are a cloud security expert copilot. Based on the following knowledge base context and resource details, provide a concise security and cost analysis.

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

Provide your analysis in this exact format:
Risk: <one-line risk summary>
Impact: <potential business impact>
Recommendation: <specific remediation steps>
Business Impact: <cost and compliance implications>"""

    def _template_explanation(self, resource: dict[str, Any], context_docs: list[str]) -> dict:
        """Generate explanation using templates when no LLM is available."""
        risks = []
        impacts = []
        recommendations = []

        rtype = resource.get("resource_type", "Unknown")
        rid = resource.get("resource_id", "unknown")
        provider = resource.get("cloud_provider", "Unknown")

        # --- Security findings ---
        if resource.get("exposed_to_public"):
            risks.append(f"Publicly exposed {rtype} resource ({rid}) on {provider}")
            impacts.append("Potential unauthorized access, data leakage, and regulatory violations")
            if provider == "AWS":
                recommendations.append("Disable public access; move to private subnet behind ALB/NLB; use VPC endpoints")
            elif provider == "Azure":
                recommendations.append("Remove public IP; use Azure Bastion for access; configure NSG deny-all default")
            elif provider == "GCP":
                recommendations.append("Remove external IP; use Identity-Aware Proxy (IAP); restrict VPC firewall rules")
            else:
                recommendations.append("Disable public access and move to private subnet")

        if resource.get("open_security_group"):
            risks.append("Open security group / firewall allowing unrestricted inbound traffic (0.0.0.0/0)")
            impacts.append("Dramatically increased attack surface for brute-force, port scanning, and exploitation")
            recommendations.append(
                "Restrict rules to specific CIDR ranges and required ports only; "
                "enable flow logs for traffic monitoring"
            )

        if not resource.get("storage_encrypted", True):
            risks.append("Storage is NOT encrypted at rest")
            impacts.append(
                "Data exposure if media is compromised; violates PCI DSS, HIPAA, "
                "SOC 2 compliance requirements"
            )
            if provider == "Azure":
                recommendations.append("Enable Azure Storage Service Encryption with customer-managed keys")
            elif provider == "GCP":
                recommendations.append("Enable Customer-Managed Encryption Keys (CMEK) for Cloud Storage")
            else:
                recommendations.append("Enable default EBS/S3 encryption using KMS-managed keys")

        severity = resource.get("config_severity", 0)
        if severity > 0.7:
            risks.append(f"High configuration severity ({severity:.2f}) — multiple deviations from security baselines")
            impacts.append("Compounding misconfigurations significantly amplify overall breach probability")
            recommendations.append(
                "Run compliance scan with AWS Config / Azure Policy / GCP Security Command Center; "
                "remediate all critical findings"
            )

        sensitivity = resource.get("data_sensitivity", 0)
        if sensitivity > 0.7:
            impacts.append(
                f"High data sensitivity ({sensitivity:.2f}) — breach impact is amplified; "
                "potential PII / PHI / financial data exposure"
            )
            recommendations.append(
                "Classify data; apply DLP policies; ensure encryption and access controls "
                "proportional to sensitivity level"
            )

        days = resource.get("days_exposed", 0)
        if days > 90:
            risks.append(f"Resource has been exposed for {days} days without remediation")
            impacts.append("Prolonged exposure dramatically increases probability of discovery and exploitation")
            recommendations.append("Implement SLA-based remediation; set up automated alerting for exposure > 30 days")

        # --- Cost findings ---
        cpu = resource.get("cpu_usage", 100)
        cost = resource.get("monthly_cost", 0)
        if cpu < 10 and rtype in COMPUTE_TYPES:
            risks.append(f"Idle {rtype} resource with only {cpu}% CPU utilization")
            waste = cost * 0.9
            impacts.append(f"Estimated waste of ~${waste:.2f}/month on an underutilized resource")
            recommendations.append(
                "Terminate if unused; schedule stop outside business hours; "
                "or right-size to a smaller instance type"
            )
        elif cpu < 40 and cost > 100 and rtype in COMPUTE_TYPES:
            risks.append(f"Oversized {rtype} resource ({cpu}% CPU at ${cost:.2f}/month)")
            waste = cost * 0.4
            impacts.append(f"Estimated ~${waste:.2f}/month in unnecessary spend from over-provisioning")
            recommendations.append(
                "Right-size using Compute Optimizer (AWS) / Azure Advisor / GCP Recommender; "
                "consider reserved/committed pricing"
            )

        if not risks:
            risks.append(f"{rtype} resource {rid} on {provider} has a moderate risk profile")
            impacts.append("Standard operational risk — continue periodic review and compliance checks")
            recommendations.append("Maintain current security baselines; schedule quarterly configuration audit")

        # Incorporate RAG context
        context_titles = []
        if context_docs:
            for doc in context_docs[:2]:
                title = doc.split("\n")[0]
                context_titles.append(title)

        srs = resource.get("security_risk_score", "N/A")
        crs = resource.get("cost_risk_score", "N/A")
        ups = resource.get("unified_priority_score", "N/A")

        return {
            "resource_id": rid,
            "risk": "; ".join(risks),
            "impact": "; ".join(impacts) if impacts else "Standard operational risk.",
            "recommendation": "; ".join(recommendations),
            "business_impact": (
                f"Security Risk Score: {srs}/100 | "
                f"Cost Risk Score: {crs}/100 | "
                f"Unified Priority Score: {ups}/100. "
                f"Related best practices: {', '.join(context_titles) if context_titles else 'N/A'}"
            ),
            "source": "template",
        }

    def _llm_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
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
        """Call Google Gemini API."""
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text

    def _parse_llm_response(self, text: str, resource_id: str) -> dict:
        """Parse structured LLM response into a dict."""
        result = {"resource_id": resource_id, "source": "llm"}
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.lower().startswith("risk:"):
                result["risk"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("impact:"):
                result["impact"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("recommendation:"):
                result["recommendation"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("business impact:"):
                result["business_impact"] = line.split(":", 1)[1].strip()

        # Fallback for missing fields
        for key in ("risk", "impact", "recommendation", "business_impact"):
            if key not in result:
                result[key] = text[:200] if key == "risk" else "See full analysis."

        return result

    def explain(self, resource: dict[str, Any]) -> dict:
        """Generate an explanation for a resource's risk profile."""
        query = self._build_query(resource)
        context_docs = self.rag.retrieve(query, top_k=3)

        if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
            prompt = self._build_prompt(resource, context_docs)
            raw = self._llm_openai(prompt)
            return self._parse_llm_response(raw, resource.get("resource_id", ""))
        elif LLM_PROVIDER == "gemini" and GOOGLE_API_KEY:
            prompt = self._build_prompt(resource, context_docs)
            raw = self._llm_gemini(prompt)
            return self._parse_llm_response(raw, resource.get("resource_id", ""))
        else:
            return self._template_explanation(resource, context_docs)
