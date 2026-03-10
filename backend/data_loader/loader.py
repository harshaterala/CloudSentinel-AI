"""
ETL and Normalization Layer
==============================
Loads multi-cloud resource logs from JSON, validates schema integrity,
normalises numeric fields to [0, 1], and produces a clean DataFrame
ready for the Risk Intelligence Engine.

Pipeline:  JSON file → load → validate → normalise → DataFrame
"""

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Fields that every record MUST contain, with expected Python type(s)
REQUIRED_FIELDS: dict[str, type | tuple] = {
    "resource_id": str,
    "resource_type": str,
    "cloud_provider": str,
    "cpu_usage": (int, float),
    "monthly_cost": (int, float),
    "exposed_to_public": bool,
    "data_sensitivity": (int, float),
    "days_exposed": (int, float),
    "config_severity": (int, float),
    "storage_encrypted": bool,
    "open_security_group": bool,
}


def load_json(path: Path) -> list[dict[str, Any]]:
    """Load raw records from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON array of objects.")
    logger.info("Loaded %d raw records from %s", len(data), path.name)
    return data


def validate_record(record: dict[str, Any], idx: int) -> list[str]:
    """Return validation error messages for a single record."""
    errors: list[str] = []
    for field, expected in REQUIRED_FIELDS.items():
        if field not in record:
            errors.append(f"Record {idx}: missing field '{field}'")
        elif not isinstance(record[field], expected):
            errors.append(
                f"Record {idx}: field '{field}' expected {expected}, got {type(record[field])}"
            )
    return errors


def validate_dataset(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate all records; return only valid ones."""
    valid: list[dict] = []
    skipped = 0
    for idx, rec in enumerate(data):
        errs = validate_record(rec, idx)
        if errs:
            for e in errs:
                logger.warning(e)
            skipped += 1
        else:
            valid.append(rec)
    if skipped:
        logger.warning("Skipped %d invalid records out of %d", skipped, len(data))
    logger.info("Validated %d records successfully", len(valid))
    return valid


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise numeric columns to [0, 1] range and add derived features."""
    df = df.copy()

    # Clip values to sensible bounds
    df["cpu_usage"] = df["cpu_usage"].clip(0, 100)
    df["data_sensitivity"] = df["data_sensitivity"].clip(0, 1)
    df["config_severity"] = df["config_severity"].clip(0, 1)

    # Normalise cost & days_exposed using min-max
    for col in ["monthly_cost", "days_exposed"]:
        cmin, cmax = df[col].min(), df[col].max()
        if cmax > cmin:
            df[f"{col}_norm"] = (df[col] - cmin) / (cmax - cmin)
        else:
            df[f"{col}_norm"] = 0.0

    # Normalise cpu to 0-1
    df["cpu_norm"] = df["cpu_usage"] / 100.0

    # Binary columns as int
    df["exposed_int"] = df["exposed_to_public"].astype(int)
    df["encrypted_int"] = df["storage_encrypted"].astype(int)
    df["open_sg_int"] = df["open_security_group"].astype(int)

    return df


def load_and_prepare(path: Path) -> pd.DataFrame:
    """Full ETL pipeline: load -> validate -> normalise."""
    raw = load_json(path)
    valid = validate_dataset(raw)
    df = pd.DataFrame(valid)
    df = normalize_dataframe(df)
    return df
