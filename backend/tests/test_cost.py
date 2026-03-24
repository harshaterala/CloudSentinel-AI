import pandas as pd

from services.cost_engine import compute_crs


def test_crs_uses_u_o_r_components():
    df = pd.DataFrame(
        [
            {
                "resource_id": "a",
                "monthly_cost": 100,
                "underutilization_waste": 1.0,
                "oversized_waste": 0.5,
                "orphaned_waste": 1.0,
                "idle_state": True,
                "orphaned_flag": True,
            },
            {
                "resource_id": "b",
                "monthly_cost": 100,
                "underutilization_waste": 0.0,
                "oversized_waste": 0.0,
                "orphaned_waste": 0.0,
                "idle_state": False,
                "orphaned_flag": False,
            },
        ]
    )

    out = compute_crs(df)
    assert "cost_risk_score" in out.columns
    assert out.loc[0, "cost_risk_score"] > out.loc[1, "cost_risk_score"]


def test_crs_orphaned_waste_drives_r_component():
    df = pd.DataFrame(
        [
            {
                "resource_id": "x1",
                "monthly_cost": 50,
                "underutilization_waste": 0.0,
                "oversized_waste": 0.0,
                "orphaned_waste": 1.0,
                "idle_state": False,
                "orphaned_flag": True,
            },
            {
                "resource_id": "x2",
                "monthly_cost": 50,
                "underutilization_waste": 0.0,
                "oversized_waste": 0.0,
                "orphaned_waste": 0.0,
                "idle_state": False,
                "orphaned_flag": False,
            },
        ]
    )

    out = compute_crs(df)
    assert out.loc[0, "cost_risk_score"] > out.loc[1, "cost_risk_score"]
    assert bool(out.loc[0, "orphaned_asset"]) is True
