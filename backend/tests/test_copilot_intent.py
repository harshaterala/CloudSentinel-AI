from main import _infer_intent


def test_intent_routing_keywords():
    assert _infer_intent("What should we fix first?") == "top_priorities"
    assert _infer_intent("Where is the highest cost waste?") == "cost_waste"
    assert _infer_intent("Explain why rds-0150 is risky") == "risk_explanation"
    assert _infer_intent("Show CIS benchmark alignment") == "compliance"
