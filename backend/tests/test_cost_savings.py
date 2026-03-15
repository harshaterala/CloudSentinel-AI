import pandas as pd

from services.cost_savings import apply_cost_savings_methodology, summarize_cost_savings


def test_cost_savings_fields_present():
    df = pd.DataFrame(
        [
            {
                "resource_type": "EC2",
                "monthly_cost": 100.0,
                "cpu_usage": 5.0,
                "exposed_to_public": False,
                "idle_resource": True,
                "oversized_resource": False,
                "estimated_waste": 0.0,
            }
        ]
    )

    out = apply_cost_savings_methodology(df)
    assert "avoidable_waste" in out.columns
    assert "projected_optimized_cost" in out.columns
    assert "savings_percentage" in out.columns
    assert out.loc[0, "avoidable_waste"] > 0


def test_cost_savings_summary_has_annual_metric():
    df = pd.DataFrame(
        [
            {
                "monthly_cost": 100.0,
                "avoidable_waste": 20.0,
                "projected_optimized_cost": 80.0,
            }
        ]
    )
    summary = summarize_cost_savings(df)
    assert summary["projected_annual_savings"] == 240.0
