"""Security Risk Score (SRS) service.

SRS = 100 x normalize(P * I * E * C)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_srs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    P = out["probability_of_exploitation"].clip(0, 1)
    I = out["impact_score"].clip(0, 1)
    E = out["exposure_level"].clip(0, 1)
    C = out["compliance_criticality"].clip(0, 1)

    raw = P * I * E * C
    rmin, rmax = raw.min(), raw.max()
    norm = (raw - rmin) / (rmax - rmin) if rmax > rmin else np.zeros(len(raw))

    out["security_risk_score"] = np.round(norm * 100, 2)
    return out