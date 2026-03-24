"""Fix-first prioritization helpers for roadmap and recommendations."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_ups_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    """Compute UPS as 0.7*SRS + 0.3*CRS and return rows sorted by UPS desc."""
    out = df.copy()
    out["unified_priority_score"] = (0.7 * out["security_risk_score"] + 0.3 * out["cost_risk_score"]).round(2)
    return out.sort_values("unified_priority_score", ascending=False)


def short_reason(row: dict[str, Any]) -> str:
    reasons: list[str] = []
    if row.get("exposed_to_public"):
        reasons.append("publicly exposed")
    if row.get("open_security_group"):
        reasons.append("open ingress rules")
    if not row.get("storage_encrypted", True):
        reasons.append("unencrypted storage")
    if row.get("idle_resource"):
        reasons.append("idle spend")
    if row.get("oversized_resource"):
        reasons.append("oversized allocation")
    if row.get("orphaned_asset"):
        reasons.append("orphaned asset")
    if not reasons:
        return "Elevated composite risk score"
    return ", ".join(reasons)


def recommended_action(row: dict[str, Any]) -> str:
    actions: list[str] = []
    if row.get("exposed_to_public"):
        actions.append("Remove public exposure and place behind private networking controls")
    if row.get("open_security_group"):
        actions.append("Tighten security group/firewall CIDR and ports")
    if not row.get("storage_encrypted", True):
        actions.append("Enable encryption at rest with managed keys")
    if row.get("idle_resource"):
        actions.append("Stop or terminate idle resource")
    if row.get("oversized_resource"):
        actions.append("Right-size instance based on utilization")
    if row.get("orphaned_asset"):
        actions.append("Decommission unattached/orphaned storage")
    if not actions:
        actions.append("Review baseline controls and remediate highest deviation")
    return "; ".join(actions)
