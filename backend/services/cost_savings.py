"""Cost savings methodology for simulated cloud optimization analysis.

This module is intentionally transparent and deterministic for hackathon demos.
It estimates avoidable cloud waste using common optimization heuristics:
- Idle compute: 90% of monthly cost avoidable
- Oversized compute: 40% of monthly cost avoidable
- Unattached/orphaned storage-like assets: 70% avoidable

Important: these are simulated assumptions, not production billing forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


STORAGE_LIKE_TYPES = {
    "S3", "EBS", "Azure Storage", "GCP Storage", "CloudFront", "Azure CDN", "Cloud CDN"
}


@dataclass(frozen=True)
class SavingsAssumptions:
    idle_compute_ratio: float = 0.90
    oversized_ratio: float = 0.40
    orphaned_storage_ratio: float = 0.70


def _detect_orphaned_storage(df: pd.DataFrame) -> pd.Series:
    """Heuristic to detect storage-like assets likely to be orphaned.

    We mark a storage-like asset as orphaned when:
    - monthly_cost is meaningful (> $20)
    - CPU usage is near zero (or unavailable and treated as 0)
    - not publicly exposed (often stale internal assets)
    """
    cpu = df.get("cpu_usage", pd.Series([0] * len(df))).fillna(0)
    storage_like = df["resource_type"].isin(STORAGE_LIKE_TYPES)
    return storage_like & (df["monthly_cost"] > 20) & (cpu <= 1) & (~df["exposed_to_public"])


def apply_cost_savings_methodology(
    df: pd.DataFrame,
    assumptions: SavingsAssumptions | None = None,
) -> pd.DataFrame:
    """Add transparent cost-optimization projections to a scored dataframe."""
    assumptions = assumptions or SavingsAssumptions()
    out = df.copy()

    orphaned_asset = _detect_orphaned_storage(out)
    idle = out.get("idle_resource", pd.Series([False] * len(out))).astype(bool)
    oversized = out.get("oversized_resource", pd.Series([False] * len(out))).astype(bool)

    avoidable_waste = np.where(
        idle,
        out["monthly_cost"] * assumptions.idle_compute_ratio,
        np.where(
            oversized,
            out["monthly_cost"] * assumptions.oversized_ratio,
            np.where(orphaned_asset, out["monthly_cost"] * assumptions.orphaned_storage_ratio, 0.0),
        ),
    )

    out["orphaned_asset"] = orphaned_asset
    out["avoidable_waste"] = np.round(avoidable_waste, 2)
    out["projected_optimized_cost"] = np.round(out["monthly_cost"] - out["avoidable_waste"], 2)

    out["savings_percentage"] = np.where(
        out["monthly_cost"] > 0,
        np.round((out["avoidable_waste"] / out["monthly_cost"]) * 100, 2),
        0.0,
    )

    # Keep existing field consistent and populated.
    if "estimated_waste" in out.columns:
        out["estimated_waste"] = out[["estimated_waste", "avoidable_waste"]].max(axis=1).round(2)
    else:
        out["estimated_waste"] = out["avoidable_waste"]

    return out


def summarize_cost_savings(df: pd.DataFrame) -> dict:
    """Return aggregate cost-savings KPIs for dashboard and executive reports."""
    total_monthly_cost = round(float(df["monthly_cost"].sum()), 2)
    total_avoidable_waste = round(float(df["avoidable_waste"].sum()), 2)
    projected_monthly_optimized_cost = round(float(df["projected_optimized_cost"].sum()), 2)

    overall_savings_percentage = round(
        (total_avoidable_waste / total_monthly_cost * 100) if total_monthly_cost else 0,
        2,
    )
    projected_annual_savings = round(total_avoidable_waste * 12, 2)

    return {
        "methodology_note": (
            "Estimated 15-30% potential savings is derived from simulated workloads and "
            "common optimization assumptions for idle, oversized, and orphaned assets."
        ),
        "total_monthly_cost": total_monthly_cost,
        "total_avoidable_waste": total_avoidable_waste,
        "projected_monthly_optimized_cost": projected_monthly_optimized_cost,
        "projected_annual_savings": projected_annual_savings,
        "overall_savings_percentage": overall_savings_percentage,
    }
