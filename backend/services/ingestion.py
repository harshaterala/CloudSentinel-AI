"""Simulated cloud telemetry ingestion and normalization.

This module ingests simulated cloud-native logs (IAM, storage access,
security groups, usage metrics) and maps them into the internal resource model.
It does not call cloud provider APIs; data is local and simulated for demos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.services.normalization import (
    normalize_cloud_telemetry,
    normalize_cloud_telemetry_from_payload,
)


def normalize_cloud_inputs(
    base_dataset_path: Path | None = None,
    logs_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Merge and normalize base inventory with simulated telemetry logs."""
    return normalize_cloud_telemetry(base_dataset_path=base_dataset_path, logs_dir=logs_dir)


def normalize_cloud_inputs_from_payload(
    payload: dict[str, list[dict[str, Any]]],
    base_dataset_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Normalize user-provided simulated log payloads into unified telemetry records."""
    return normalize_cloud_telemetry_from_payload(payload=payload, base_dataset_path=base_dataset_path)
