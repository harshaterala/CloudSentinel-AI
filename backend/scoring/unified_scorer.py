"""
Unified Priority Scoring
============================
Combines security and cost risk into a single actionable priority.

Formula
-------
    UPS = 0.7 × SRS + 0.3 × CRS

Risk levels (based on UPS):
    Critical  ≥ 70
    High      ≥ 40
    Medium    ≥ 20
    Low       <  20
"""

import numpy as np
import pandas as pd

from backend.config import SECURITY_WEIGHT, COST_WEIGHT


def compute_unified_priority(df: pd.DataFrame) -> pd.DataFrame:
    """Add Unified Priority Score (UPS), risk level, and rank."""
    df = df.copy()

    df["unified_priority_score"] = np.round(
        SECURITY_WEIGHT * df["security_risk_score"]
        + COST_WEIGHT * df["cost_risk_score"],
        2,
    )

    # Qualitative risk level
    conditions = [
        df["unified_priority_score"] >= 70,
        df["unified_priority_score"] >= 40,
        df["unified_priority_score"] >= 20,
    ]
    choices = ["Critical", "High", "Medium"]
    df["risk_level"] = np.select(conditions, choices, default="Low")

    # Global rank (1 = most urgent)
    df["priority_rank"] = df["unified_priority_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    return df
