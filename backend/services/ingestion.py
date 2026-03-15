"""Simulated cloud telemetry ingestion and normalization.

This module ingests simulated cloud-native logs (IAM, storage access,
security groups, usage metrics) and maps them into the internal resource model.
It does not call cloud provider APIs; data is local and simulated for demos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.config import DATASET_PATH


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, list) else []


def normalize_cloud_inputs(
    base_dataset_path: Path | None = None,
    logs_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Merge base resource inventory with simulated telemetry logs."""
    base_dataset_path = base_dataset_path or DATASET_PATH
    logs_dir = logs_dir or (base_dataset_path.parent / "logs")

    with open(base_dataset_path, "r", encoding="utf-8") as f:
        base_resources = json.load(f)

    iam_logs = _load_json(logs_dir / "iam_logs.json")
    storage_logs = _load_json(logs_dir / "storage_access_logs.json")
    sg_logs = _load_json(logs_dir / "security_groups.json")
    usage_logs = _load_json(logs_dir / "usage_metrics.json")

    by_id = {r["resource_id"]: dict(r) for r in base_resources}

    for ev in iam_logs:
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("over_permissive_policy"):
            by_id[rid]["config_severity"] = min(1.0, float(by_id[rid].get("config_severity", 0)) + 0.15)
        if ev.get("mfa_disabled"):
            by_id[rid]["mfa_enabled"] = False

    for ev in storage_logs:
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("public_access"):
            by_id[rid]["exposed_to_public"] = True
        if ev.get("encryption_enabled") is False:
            by_id[rid]["storage_encrypted"] = False

    for ev in sg_logs:
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("allows_0_0_0_0"):
            by_id[rid]["open_security_group"] = True
            by_id[rid]["exposed_to_public"] = True

    for ev in usage_logs:
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if "cpu_usage" in ev:
            by_id[rid]["cpu_usage"] = float(ev["cpu_usage"])
        if "monthly_cost" in ev:
            by_id[rid]["monthly_cost"] = float(ev["monthly_cost"])

    # Ensure required fields always exist after merge.
    for rid, rec in by_id.items():
        rec.setdefault("mfa_enabled", True)
        rec.setdefault("backup_enabled", True)
        rec.setdefault("open_security_group", False)
        rec.setdefault("storage_encrypted", True)
        rec.setdefault("exposed_to_public", False)
        rec.setdefault("tags", [])

    return list(by_id.values())


def normalize_cloud_inputs_from_payload(
    payload: dict[str, list[dict[str, Any]]],
    base_dataset_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Normalize user-provided simulated log payloads into the resource model.

    Expected payload keys:
    - iam_logs
    - storage_access_logs
    - security_groups
    - usage_metrics
    """
    base_dataset_path = base_dataset_path or DATASET_PATH
    with open(base_dataset_path, "r", encoding="utf-8") as f:
        base_resources = json.load(f)

    by_id = {r["resource_id"]: dict(r) for r in base_resources}

    iam_logs = payload.get("iam_logs", [])
    storage_logs = payload.get("storage_access_logs", [])
    sg_logs = payload.get("security_groups", [])
    usage_logs = payload.get("usage_metrics", [])

    for ev in iam_logs:
        rid = ev.get("resource_id")
        if rid in by_id and ev.get("over_permissive_policy"):
            by_id[rid]["config_severity"] = min(1.0, float(by_id[rid].get("config_severity", 0)) + 0.15)
        if rid in by_id and ev.get("mfa_disabled"):
            by_id[rid]["mfa_enabled"] = False

    for ev in storage_logs:
        rid = ev.get("resource_id")
        if rid in by_id and ev.get("public_access"):
            by_id[rid]["exposed_to_public"] = True
        if rid in by_id and ev.get("encryption_enabled") is False:
            by_id[rid]["storage_encrypted"] = False

    for ev in sg_logs:
        rid = ev.get("resource_id")
        if rid in by_id and ev.get("allows_0_0_0_0"):
            by_id[rid]["open_security_group"] = True
            by_id[rid]["exposed_to_public"] = True

    for ev in usage_logs:
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if "cpu_usage" in ev:
            by_id[rid]["cpu_usage"] = float(ev["cpu_usage"])
        if "monthly_cost" in ev:
            by_id[rid]["monthly_cost"] = float(ev["monthly_cost"])

    for rec in by_id.values():
        rec.setdefault("mfa_enabled", True)
        rec.setdefault("backup_enabled", True)
        rec.setdefault("open_security_group", False)
        rec.setdefault("storage_encrypted", True)
        rec.setdefault("exposed_to_public", False)
        rec.setdefault("tags", [])

    return list(by_id.values())
