import pandas as pd
from fastapi.testclient import TestClient

import main
from ai_explainer.explainer import AIExplainer


class _StubRag:
    def __init__(self):
        self.calls = 0

    def retrieve_with_metadata(self, query: str, top_k: int = 3):
        self.calls += 1
        return [
            {
                "title": "CIS Network Exposure Baseline",
                "category": "cis",
                "source": "kb",
                "score": 0.9,
                "content": "Restrict public exposure and tighten network ingress.",
            }
        ]


def test_explainer_returns_exact_four_fields_and_uses_rag():
    explainer = AIExplainer.__new__(AIExplainer)
    explainer.rag = _StubRag()

    resource = {
        "resource_id": "r1",
        "resource_type": "EC2",
        "cloud_provider": "AWS",
        "config_severity": 0.9,
        "exposure_level": 0.8,
        "security_risk_score": 80,
        "cost_risk_score": 40,
        "unified_priority_score": 68,
        "storage_encrypted": False,
        "mfa_enabled": False,
        "exposed_to_public": True,
    }

    out = explainer.explain(resource)
    assert set(out.keys()) == {"root_cause", "business_impact", "remediation_steps", "executive_summary"}
    assert explainer.rag.calls == 1
    assert "r1" in out["root_cause"]


def test_explain_endpoint_contract(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "resource_id": "r1",
                "resource_type": "EC2",
                "cloud_provider": "AWS",
                "region": "us-east-1",
                "cpu_usage": 10,
                "monthly_cost": 100,
                "exposed_to_public": True,
                "data_sensitivity": 0.7,
                "days_exposed": 5,
                "config_severity": 0.8,
                "probability_of_exploitation": 0.8,
                "impact_score": 0.8,
                "exposure_level": 0.9,
                "compliance_criticality": 0.9,
                "underutilization_waste": 0.2,
                "oversized_waste": 0.2,
                "orphaned_waste": 0.0,
                "storage_encrypted": False,
                "open_security_group": True,
                "tags": [],
                "security_risk_score": 90,
                "cost_risk_score": 30,
                "unified_priority_score": 72,
                "risk_level": "Critical",
                "priority_rank": 1,
                "idle_resource": False,
                "oversized_resource": True,
                "orphaned_asset": False,
                "estimated_waste": 20,
                "avoidable_waste": 20,
                "projected_optimized_cost": 80,
                "savings_percentage": 20,
            }
        ]
    )

    class _DummyExplainer:
        def explain(self, resource):
            return {
                "root_cause": "root",
                "business_impact": "impact",
                "remediation_steps": "steps",
                "executive_summary": "summary",
            }

    monkeypatch.setattr(main, "_get_df", lambda: df)
    monkeypatch.setattr(main, "_get_explainer", lambda: _DummyExplainer())

    client = TestClient(main.app)
    response = client.get("/explain/r1")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"root_cause", "business_impact", "remediation_steps", "executive_summary"}
