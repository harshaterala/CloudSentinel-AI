import pandas as pd

from services.risk_engine import compute_srs


def test_srs_uses_probability_impact_exposure_compliance():
    df = pd.DataFrame(
        [
            {
                "resource_id": "r1",
                "probability_of_exploitation": 0.9,
                "impact_score": 0.8,
                "exposure_level": 0.9,
                "compliance_criticality": 0.95,
                "days_exposed": 365,
            },
            {
                "resource_id": "r2",
                "probability_of_exploitation": 0.3,
                "impact_score": 0.3,
                "exposure_level": 0.3,
                "compliance_criticality": 0.1,
                "days_exposed": 365,
            },
        ]
    )

    out = compute_srs(df)
    assert "security_risk_score" in out.columns
    assert out.loc[0, "security_risk_score"] > out.loc[1, "security_risk_score"]


def test_srs_changes_with_compliance_criticality_not_time():
    base = {
        "resource_id": "ra",
        "probability_of_exploitation": 0.6,
        "impact_score": 0.6,
        "exposure_level": 0.6,
    }
    df = pd.DataFrame(
        [
            {**base, "compliance_criticality": 0.9, "days_exposed": 1},
            {**base, "compliance_criticality": 0.2, "days_exposed": 999},
        ]
    )

    out = compute_srs(df)
    assert out.loc[0, "security_risk_score"] > out.loc[1, "security_risk_score"]
