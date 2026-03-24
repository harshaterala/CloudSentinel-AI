"""
Cost Risk Score (CRS) Engine
================================
Quantifies cost-inefficiency risk for each cloud resource.

Formula
-------
    CRS = 100 × normalize( U + O + R )

Components
----------
    U = Idle resource indicator     → 1 if CPU < 10 % on compute types
    O = Oversized resource indicator → 1 if CPU < 40 % and cost > median
    R = Cost impact factor          → monthly_cost normalised to [0, 1]

The CRS feeds into the Unified Priority Score together with the SRS.
"""

import numpy as np
import pandas as pd

from backend.config import COMPUTE_TYPES


def compute_cost_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'cost_risk_score' (CRS) and supporting columns to *df*."""
    df = df.copy()

    is_compute = df["resource_type"].isin(COMPUTE_TYPES)

    # U – idle resource indicator (compute resource with < 10 % CPU)
    U = (is_compute & (df["cpu_usage"] < 10)).astype(float)

    # O – oversized indicator (compute, < 40 % CPU, cost above median)
    median_cost = df["monthly_cost"].median()
    O = (is_compute & (df["cpu_usage"] < 40) & (df["monthly_cost"] > median_cost)).astype(float)

    # R – normalised cost impact
    R = df["monthly_cost_norm"]

    raw = U + O + R

    rmin, rmax = raw.min(), raw.max()
    normalised = (raw - rmin) / (rmax - rmin) if rmax > rmin else np.zeros(len(raw))

    df["cost_risk_score"] = np.round(normalised * 100, 2)
    df["idle_resource"] = U.astype(bool)
    df["oversized_resource"] = O.astype(bool)

    # Estimated monthly waste for idle / oversized resources
    df["estimated_waste"] = np.where(
        U.astype(bool), df["monthly_cost"] * 0.9,
        np.where(O.astype(bool), df["monthly_cost"] * 0.4, 0.0),
    ).round(2)

    return df
