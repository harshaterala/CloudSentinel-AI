import pandas as pd
from fastapi.testclient import TestClient

import main
from ai_explainer.explainer import AIExplainer


class _RagRecorder:
    def __init__(self):
        self.called = 0

    def retrieve_with_metadata(self, query: str, top_k: int = 3):
        self.called += 1
        return [
            {
                "title": "NIST Incident Response",
                "category": "nist",
                "source": "kb",
                "score": 0.8,
                "content": "Prioritize high-risk internet-facing assets and enforce least privilege.",
            }
        ]


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
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
            },
            {
                "resource_id": "r2",
                "resource_type": "Azure VM",
                "cloud_provider": "Azure",
                "region": "eastus",
                "cpu_usage": 6,
                "monthly_cost": 300,
                "exposed_to_public": False,
                "data_sensitivity": 0.6,
                "days_exposed": 3,
                "config_severity": 0.6,
                "probability_of_exploitation": 0.5,
                "impact_score": 0.6,
                "exposure_level": 0.5,
                "compliance_criticality": 0.6,
                "underutilization_waste": 0.7,
                "oversized_waste": 0.7,
                "orphaned_waste": 0.0,
                "storage_encrypted": True,
                "open_security_group": False,
                "tags": [],
                "security_risk_score": 50,
                "cost_risk_score": 55,
                "unified_priority_score": 51.5,
                "risk_level": "High",
                "priority_rank": 2,
                "idle_resource": True,
                "oversized_resource": True,
                "orphaned_asset": False,
                "estimated_waste": 80,
                "avoidable_waste": 80,
                "projected_optimized_cost": 220,
                "savings_percentage": 26.67,
            },
        ]
    )


def test_answer_query_always_uses_rag():
    explainer = AIExplainer.__new__(AIExplainer)
    recorder = _RagRecorder()
    explainer.rag = recorder

    result = explainer.answer_query("What is my top risk?", [{"resource_id": "r1", "unified_priority_score": 80}], top_k=3)
    assert recorder.called == 1
    assert "answer" in result
    assert isinstance(result.get("sources"), list)


def test_copilot_endpoint_no_canned(monkeypatch):
    call_counter = {"n": 0}

    class _DummyExplainer:
        def answer_query(self, query, resources, top_k=5):
            call_counter["n"] += 1
            return {
                "answer": f"generated for: {query}",
                "sources": ["cis: sample"],
                "related_resources": resources,
            }

    monkeypatch.setattr(main, "_get_df", _sample_df)
    monkeypatch.setattr(main, "_get_explainer", lambda: _DummyExplainer())

    client = TestClient(main.app)

    r1 = client.post("/copilot/query", json={"query": "What are top risks?", "top_k": 2})
    r2 = client.post("/copilot/query", json={"query": "Where is waste?", "top_k": 2})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert "What are top risks?" in r1.json()["answer"]
    assert "Where is waste?" in r2.json()["answer"]
    assert call_counter["n"] == 2
