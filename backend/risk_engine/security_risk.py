"""
Security Risk Score (SRS) Engine
====================================
Quantifies security risk for each cloud resource.

Formula
-------
    SRS = 100 × normalize( P × I × E × C )

Components
----------
    P = Configuration severity     (0–1)  config_severity
    I = Data sensitivity          (0–1)  data_sensitivity
    E = Exposure level            (0–1)  composite of public access, open SG, encryption
    C = Duration of exposure      (0–1)  days_exposed normalised

A higher SRS means the resource has a more dangerous combination of
misconfiguration, sensitivity, and exposure duration.
"""

import numpy as np
import pandas as pd

from backend.config import COMPUTE_TYPES


def _exposure_level(row: pd.Series) -> float:
    """Compute composite exposure level E in [0, 1].

    Weighting:
      - Publicly exposed    → +0.45
      - Open security group → +0.30
      - Unencrypted storage → +0.15
      - MFA disabled        → +0.10
    """
    score = 0.0
    if row.get("exposed_to_public", False):
        score += 0.45
    if row.get("open_security_group", False):
        score += 0.30
    if not row.get("storage_encrypted", True):
        score += 0.15
    if not row.get("mfa_enabled", True):
        score += 0.10
    return min(score, 1.0)


def compute_security_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Add Security Risk Score (SRS) and per-component columns."""
    df = df.copy()

    P = df["config_severity"]
    I = df["data_sensitivity"]
    E = df.apply(_exposure_level, axis=1)
    C = df["days_exposed_norm"]

    raw = P * I * E * C

    rmin, rmax = raw.min(), raw.max()
    normalised = (raw - rmin) / (rmax - rmin) if rmax > rmin else np.zeros(len(raw))

    df["security_risk_score"] = np.round(normalised * 100, 2)
    df["exposure_level"] = E

    # Per-component breakdown (useful for explanations)
    df["srs_config"] = np.round(P * 100, 2)
    df["srs_sensitivity"] = np.round(I * 100, 2)
    df["srs_exposure"] = np.round(E * 100, 2)
    df["srs_duration"] = np.round(C * 100, 2)

    return df
