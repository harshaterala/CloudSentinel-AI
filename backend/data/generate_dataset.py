"""
Generate a simulated multi-cloud dataset of ~350 cloud resources.
Each resource is assigned a cloud provider (AWS / Azure / GCP) and a
provider-appropriate resource type and region.

Run:  python generate_dataset.py
"""

import json
import random
import os

random.seed(42)

# ── Provider-specific resource types and regions ──────────────────────────

PROVIDER_CONFIG = {
    "AWS": {
        "resource_types": [
            "EC2", "S3", "RDS", "IAM", "Lambda",
            "EKS", "DynamoDB", "CloudFront", "EBS", "ElastiCache",
        ],
        "regions": [
            "us-east-1", "us-west-2", "eu-west-1",
            "ap-southeast-1", "eu-central-1", "ap-northeast-1",
        ],
    },
    "Azure": {
        "resource_types": [
            "Azure VM", "Azure Storage", "Azure SQL",
            "Azure AD", "Azure Functions", "Azure AKS",
            "Azure Cosmos DB", "Azure CDN",
        ],
        "regions": [
            "eastus", "westus2", "westeurope",
            "northeurope", "southeastasia", "japaneast",
        ],
    },
    "GCP": {
        "resource_types": [
            "GCP Compute", "GCP Storage", "Cloud SQL",
            "GCP IAM", "Cloud Functions", "GKE",
            "Firestore", "Cloud CDN",
        ],
        "regions": [
            "us-central1", "us-east4", "europe-west1",
            "asia-southeast1", "europe-west3", "asia-northeast1",
        ],
    },
}

# Resource types that have CPU utilisation metrics
COMPUTE_TYPES = {
    "EC2", "EKS", "RDS", "ElastiCache", "Lambda",
    "Azure VM", "Azure AKS", "Azure SQL", "Azure Functions",
    "GCP Compute", "GKE", "Cloud SQL", "Cloud Functions",
}

COST_RANGES = {
    "EC2": (20, 500), "S3": (1, 80), "RDS": (50, 600),
    "IAM": (0, 0), "Lambda": (0.5, 50), "EKS": (100, 800),
    "DynamoDB": (5, 200), "CloudFront": (2, 150),
    "EBS": (5, 100), "ElastiCache": (30, 300),
    # Azure
    "Azure VM": (25, 550), "Azure Storage": (2, 90),
    "Azure SQL": (55, 620), "Azure AD": (0, 0),
    "Azure Functions": (0.5, 55), "Azure AKS": (110, 850),
    "Azure Cosmos DB": (10, 250), "Azure CDN": (3, 130),
    # GCP
    "GCP Compute": (22, 520), "GCP Storage": (1.5, 85),
    "Cloud SQL": (48, 580), "GCP IAM": (0, 0),
    "Cloud Functions": (0.5, 48), "GKE": (95, 780),
    "Firestore": (4, 180), "Cloud CDN": (2, 140),
}

TAG_POOL = ["production", "staging", "dev", "critical", "internal", "public",
            "finance", "healthcare", "ml-pipeline", "shared-services"]


def generate_resource(idx: int) -> dict:
    provider = random.choice(["AWS", "Azure", "GCP"])
    cfg = PROVIDER_CONFIG[provider]
    rtype = random.choice(cfg["resource_types"])
    region = random.choice(cfg["regions"])

    tag = rtype.lower().replace(" ", "-")
    resource_id = f"{tag}-{idx:04d}"

    cpu_usage = round(random.uniform(1, 100), 2) if rtype in COMPUTE_TYPES else 0.0

    lo, hi = COST_RANGES.get(rtype, (1, 100))
    monthly_cost = round(random.uniform(lo, hi), 2)

    exposed_to_public = random.random() < 0.3
    data_sensitivity = round(random.uniform(0, 1), 2)
    days_exposed = random.randint(0, 365) if exposed_to_public else 0
    config_severity = round(random.uniform(0, 1), 2)
    storage_encrypted = random.random() > 0.25
    open_security_group = random.random() < 0.2
    mfa_enabled = random.random() > 0.3
    backup_enabled = random.random() > 0.2
    last_patched_days_ago = random.randint(0, 180)

    tags = random.sample(TAG_POOL, k=random.randint(1, 3))

    return {
        "resource_id": resource_id,
        "resource_type": rtype,
        "cloud_provider": provider,
        "region": region,
        "cpu_usage": cpu_usage,
        "monthly_cost": monthly_cost,
        "exposed_to_public": exposed_to_public,
        "data_sensitivity": data_sensitivity,
        "days_exposed": days_exposed,
        "config_severity": config_severity,
        "storage_encrypted": storage_encrypted,
        "open_security_group": open_security_group,
        "mfa_enabled": mfa_enabled,
        "backup_enabled": backup_enabled,
        "last_patched_days_ago": last_patched_days_ago,
        "tags": tags,
    }


def main():
    resources = [generate_resource(i) for i in range(1, 351)]
    out_path = os.path.join(os.path.dirname(__file__), "cloud_resources.json")
    with open(out_path, "w") as f:
        json.dump(resources, f, indent=2)
    print(f"Generated {len(resources)} resources -> {out_path}")


if __name__ == "__main__":
    main()
