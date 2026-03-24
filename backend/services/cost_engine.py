"""Cost Risk Score (CRS) service.

CRS = 100 x normalize(U + O + R)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_crs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    U = out["underutilization_waste"].clip(0, 1)
    O = out["oversized_waste"].clip(0, 1)
    R = out["orphaned_waste"].clip(0, 1)

    raw = U + O + R
    rmin, rmax = raw.min(), raw.max()
    norm = (raw - rmin) / (rmax - rmin) if rmax > rmin else np.zeros(len(raw))

    out["cost_risk_score"] = np.round(norm * 100, 2)
    out["idle_resource"] = out.get("idle_state", False)
    out["oversized_resource"] = O > 0
    out["orphaned_asset"] = out.get("orphaned_flag", False)
    out["estimated_waste"] = np.round(out["monthly_cost"] * (0.5 * U + 0.4 * O + 0.7 * R), 2)

    return out