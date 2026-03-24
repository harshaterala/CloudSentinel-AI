"""Provider-agnostic normalization for simulated multi-cloud telemetry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.config import COMPUTE_TYPES, DATASET_PATH


STORAGE_LIKE_TYPES = {
    "S3",
    "EBS",
    "Azure Storage",
    "GCP Storage",
    "CloudFront",
    "Azure CDN",
    "Cloud CDN",
}

CRITICAL_TAG_HINTS = {"critical", "production", "prod", "finance", "pci", "hipaa", "pii"}


def normalize_iam(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single IAM log event into a provider-agnostic shape."""
    return {
        "resource_id": event.get("resource_id", ""),
        "mfa_disabled": bool(event.get("mfa_disabled", False)),
        "over_permissive_policy": bool(event.get("over_permissive_policy", False)),
        "action": event.get("action", ""),
    }


def normalize_storage(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single storage-access log event."""
    return {
        "resource_id": event.get("resource_id", ""),
        "public_access": bool(event.get("public_access", False)),
        "encryption_enabled": event.get("encryption_enabled", True),
        "high_volume_download": bool(event.get("high_volume_download", False)),
    }


def normalize_security_group(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single security-group event."""
    return {
        "resource_id": event.get("resource_id", ""),
        "allows_0_0_0_0": bool(event.get("allows_0_0_0_0", False)),
        "open_ports": event.get("open_ports", []),
    }


def normalize_usage_metrics(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single usage/cost metrics event."""
    return {
        "resource_id": event.get("resource_id", ""),
        "cpu_usage": float(event.get("cpu_usage", 0.0)),
        "monthly_cost": float(event.get("monthly_cost", 0.0)),
    }


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _derive_compliance_criticality(resource: dict[str, Any]) -> float:
    tags = {str(t).lower() for t in resource.get("tags", [])}
    sensitivity = float(resource.get("data_sensitivity", 0.0))
    score = sensitivity * 0.7
    if tags & CRITICAL_TAG_HINTS:
        score += 0.2
    if str(resource.get("resource_type", "")).lower() in {
        "iam",
        "rds",
        "cloud sql",
        "azure sql",
        "azure cosmos db",
    }:
        score += 0.1
    return _clamp01(score)


def _derive_exposure(resource: dict[str, Any]) -> float:
    score = 0.0
    if resource.get("exposed_to_public", False):
        score += 0.5
    if resource.get("open_security_group", False):
        score += 0.3
    if not resource.get("storage_encrypted", True):
        score += 0.1
    if not resource.get("mfa_enabled", True):
        score += 0.1
    return _clamp01(score)


def _derive_probability(resource: dict[str, Any], exposure_level: float) -> float:
    config_severity = float(resource.get("config_severity", 0.0))
    score = (0.6 * config_severity) + (0.4 * exposure_level)
    return _clamp01(score)


def _derive_impact(resource: dict[str, Any], normalized_cost: float) -> float:
    sensitivity = float(resource.get("data_sensitivity", 0.0))
    compliance = _derive_compliance_criticality(resource)
    score = (0.6 * sensitivity) + (0.25 * compliance) + (0.15 * normalized_cost)
    return _clamp01(score)


def _is_orphaned(resource: dict[str, Any]) -> bool:
    tags = {str(t).lower() for t in resource.get("tags", [])}
    resource_type = resource.get("resource_type", "")
    cpu = float(resource.get("cpu_usage", 0.0))
    monthly_cost = float(resource.get("monthly_cost", 0.0))
    if "orphaned" in tags:
        return True
    return (
        resource_type in STORAGE_LIKE_TYPES
        and monthly_cost > 20
        and cpu <= 1
        and not resource.get("exposed_to_public", False)
    )


def _normalize_with_logs(
    base_resources: list[dict[str, Any]],
    iam_logs: list[dict[str, Any]],
    storage_logs: list[dict[str, Any]],
    sg_logs: list[dict[str, Any]],
    usage_logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {r["resource_id"]: dict(r) for r in base_resources}

    for ev in iam_logs:
        ev = normalize_iam(ev)
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("over_permissive_policy"):
            by_id[rid]["config_severity"] = min(1.0, float(by_id[rid].get("config_severity", 0.0)) + 0.15)
        if ev.get("mfa_disabled"):
            by_id[rid]["mfa_enabled"] = False

    for ev in storage_logs:
        ev = normalize_storage(ev)
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("public_access"):
            by_id[rid]["exposed_to_public"] = True
        if ev.get("encryption_enabled") is False:
            by_id[rid]["storage_encrypted"] = False

    for ev in sg_logs:
        ev = normalize_security_group(ev)
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if ev.get("allows_0_0_0_0"):
            by_id[rid]["open_security_group"] = True
            by_id[rid]["exposed_to_public"] = True
        by_id[rid]["open_ports"] = ev.get("open_ports", [])

    for ev in usage_logs:
        ev = normalize_usage_metrics(ev)
        rid = ev.get("resource_id")
        if rid not in by_id:
            continue
        if "cpu_usage" in ev:
            by_id[rid]["cpu_usage"] = float(ev["cpu_usage"])
        if "monthly_cost" in ev:
            by_id[rid]["monthly_cost"] = float(ev["monthly_cost"])

    records = list(by_id.values())
    if not records:
        return []

    max_cost = max(float(r.get("monthly_cost", 0.0)) for r in records) or 1.0

    for rec in records:
        rec.setdefault("mfa_enabled", True)
        rec.setdefault("backup_enabled", True)
        rec.setdefault("open_security_group", False)
        rec.setdefault("storage_encrypted", True)
        rec.setdefault("exposed_to_public", False)
        rec.setdefault("tags", [])
        rec.setdefault("open_ports", [])
        rec.setdefault("region", "unknown")

        rec["cpu_usage"] = float(rec.get("cpu_usage", 0.0))
        rec["cpu_utilization"] = rec["cpu_usage"]
        rec["monthly_cost"] = float(rec.get("monthly_cost", 0.0))
        rec["normalized_monthly_cost"] = _clamp01(rec["monthly_cost"] / max_cost)
        rec["mfa_status"] = bool(rec.get("mfa_enabled", True))
        rec["idle_state"] = bool(rec["resource_type"] in COMPUTE_TYPES and rec["cpu_usage"] < 10)
        rec["orphaned_flag"] = _is_orphaned(rec)

        exposure = _derive_exposure(rec)
        compliance = _derive_compliance_criticality(rec)
        rec["exposure_level"] = exposure
        rec["compliance_criticality"] = compliance
        rec["probability_of_exploitation"] = _derive_probability(rec, exposure)
        rec["impact_score"] = _derive_impact(rec, rec["normalized_monthly_cost"])

        # Cost-risk specific components in [0, 1].
        cpu = rec["cpu_usage"]
        is_compute = rec["resource_type"] in COMPUTE_TYPES
        rec["underutilization_waste"] = _clamp01((20 - cpu) / 20.0) if is_compute and cpu < 20 else 0.0
        rec["oversized_waste"] = _clamp01((40 - cpu) / 40.0) if is_compute and cpu < 40 and rec["monthly_cost"] > 100 else 0.0
        rec["orphaned_waste"] = 1.0 if rec["orphaned_flag"] else (0.6 if rec["idle_state"] else 0.0)

    return records


def normalize_cloud_telemetry(
    base_dataset_path: Path | None = None,
    logs_dir: Path | None = None,
) -> list[dict[str, Any]]:
    base_dataset_path = base_dataset_path or DATASET_PATH
    logs_dir = logs_dir or (base_dataset_path.parent / "logs")

    with open(base_dataset_path, "r", encoding="utf-8") as f:
        base_resources = json.load(f)

    iam_logs = _load_json(logs_dir / "iam_logs.json")
    storage_logs = _load_json(logs_dir / "storage_access_logs.json")
    sg_logs = _load_json(logs_dir / "security_groups.json")
    usage_logs = _load_json(logs_dir / "usage_metrics.json")

    return _normalize_with_logs(base_resources, iam_logs, storage_logs, sg_logs, usage_logs)


def normalize_cloud_telemetry_from_payload(
    payload: dict[str, list[dict[str, Any]]],
    base_dataset_path: Path | None = None,
) -> list[dict[str, Any]]:
    base_dataset_path = base_dataset_path or DATASET_PATH
    with open(base_dataset_path, "r", encoding="utf-8") as f:
        base_resources = json.load(f)

    return _normalize_with_logs(
        base_resources,
        payload.get("iam_logs", []),
        payload.get("storage_access_logs", []),
        payload.get("security_groups", []),
        payload.get("usage_metrics", []),
    )