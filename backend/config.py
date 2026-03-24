"""Configuration constants for the Cloud Security Copilot backend."""

import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "cloud_resources.json"
LOGS_DIR = DATA_DIR / "logs"
USE_SIMULATED_INGESTION = os.getenv("USE_SIMULATED_INGESTION", "true").lower() == "true"

# ── Scoring weights (UPS = SECURITY_WEIGHT × SRS + COST_WEIGHT × CRS) ────
SECURITY_WEIGHT = 0.7
COST_WEIGHT = 0.3

# ── RAG / Vector store ────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DB_DIR = BASE_DIR / "vector_store"

# ── LLM configuration ────────────────────────────────────────────────────
# Set these via environment variables; fallback to template-based explanations
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")   # "gemini" | "none"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── Multi-cloud compute types (used by cost engine) ──────────────────────
COMPUTE_TYPES = {
    # AWS
    "EC2", "EKS", "RDS", "ElastiCache", "Lambda",
    # Azure
    "Azure VM", "Azure AKS", "Azure SQL", "Azure Functions",
    # GCP
    "GCP Compute", "GKE", "Cloud SQL", "Cloud Functions",
}

# ── App metadata ──────────────────────────────────────────────────────────
APP_TITLE = "Cloud Security Copilot"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = (
    "GenAI-powered multi-cloud security & cost intelligence platform. "
    "Analyses infrastructure logs, computes risk scores, and provides "
    "explainable AI-driven remediation guidance via RAG."
)
