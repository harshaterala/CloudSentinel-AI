"""GenAI Cloud Security Copilot FastAPI backend."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is on sys.path so that `backend.*` imports resolve.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_explainer.rag_engine import RAGEngine
from backend.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    COST_WEIGHT,
    DATASET_PATH,
    LLM_PROVIDER,
    LOGS_DIR,
    SECURITY_WEIGHT,
    USE_SIMULATED_INGESTION,
)
from backend.scoring.unified_scorer import compute_unified_priority
from backend.services.cost_engine import compute_crs
from backend.services.cost_savings import apply_cost_savings_methodology, summarize_cost_savings
from backend.services.ingestion import normalize_cloud_inputs, normalize_cloud_inputs_from_payload
from backend.services.prioritization import recommended_action, short_reason
from backend.services.risk_engine import compute_srs
from backend.routes.copilot import generate_copilot_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_df: pd.DataFrame | None = None
_explainer = None
_rag: RAGEngine | None = None
_startup_time = time.time()


PUBLIC_COLUMNS = [
    "resource_id",
    "resource_type",
    "cloud_provider",
    "region",
    "cpu_usage",
    "monthly_cost",
    "exposed_to_public",
    "data_sensitivity",
    "days_exposed",
    "config_severity",
    "probability_of_exploitation",
    "impact_score",
    "exposure_level",
    "compliance_criticality",
    "underutilization_waste",
    "oversized_waste",
    "orphaned_waste",
    "idle_state",
    "orphaned_flag",
    "storage_encrypted",
    "open_security_group",
    "tags",
    "security_risk_score",
    "cost_risk_score",
    "unified_priority_score",
    "risk_level",
    "exposure_level",
    "priority_rank",
    "idle_resource",
    "oversized_resource",
    "orphaned_asset",
    "estimated_waste",
    "avoidable_waste",
    "projected_optimized_cost",
    "savings_percentage",
]


class CopilotQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)


class IngestionPayloadRequest(BaseModel):
    iam_logs: list[dict[str, Any]] = Field(default_factory=list)
    storage_access_logs: list[dict[str, Any]] = Field(default_factory=list)
    security_groups: list[dict[str, Any]] = Field(default_factory=list)
    usage_metrics: list[dict[str, Any]] = Field(default_factory=list)
    apply_to_runtime: bool = False


def _run_pipeline(records: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    if records is None:
        if USE_SIMULATED_INGESTION and LOGS_DIR.exists():
            logger.info("Using simulated cloud telemetry ingestion from %s", LOGS_DIR)
            records = normalize_cloud_inputs(DATASET_PATH, LOGS_DIR)
        else:
            records = normalize_cloud_inputs(DATASET_PATH, LOGS_DIR)

    df = pd.DataFrame(records)
    df = compute_srs(df)
    df = compute_crs(df)
    df = compute_unified_priority(df)
    df = apply_cost_savings_methodology(df)
    return df


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        logger.info("Running analysis pipeline...")
        _df = _run_pipeline()
        logger.info("Pipeline complete — %d resources analysed.", len(_df))
    return _df


def _get_explainer():
    global _explainer
    if _explainer is None:
        from backend.ai_explainer.explainer import AIExplainer

        _explainer = AIExplainer()
        logger.info("AI Explainer initialised (mode=%s).", LLM_PROVIDER)
    return _explainer


def _get_rag() -> RAGEngine:
    global _rag
    if _rag is None:
        _rag = RAGEngine()
    return _rag


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in PUBLIC_COLUMNS:
        value = row.get(col)
        if value is None:
            continue
        if hasattr(value, "item"):
            value = value.item()
        out[col] = value
    return out


@app.get("/health", tags=["System"])
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "llm_provider": LLM_PROVIDER,
        "simulated_ingestion": USE_SIMULATED_INGESTION,
    }


@app.get("/analysis", tags=["Analysis"])
def get_analysis(
    sort_by: str = Query("unified_priority_score"),
    ascending: bool = Query(False),
    limit: int = Query(0, ge=0),
):
    df = _get_df()
    if sort_by not in df.columns:
        sort_by = "unified_priority_score"
    view = df.sort_values(sort_by, ascending=ascending)
    if limit > 0:
        view = view.head(limit)
    return {"count": len(view), "resources": [_row_to_dict(row) for _, row in view.iterrows()]}


@app.get("/recommendations", tags=["Analysis"])
def get_recommendations(limit: int = Query(5, ge=1, le=50)):
    df = _get_df()
    top = df.nlargest(limit, "unified_priority_score")
    recommendations = []
    for _, row in top.iterrows():
        item = _row_to_dict(row)
        item["summary"] = short_reason(item)
        item["recommended_action"] = recommended_action(item)
        recommendations.append(item)
    return {"count": len(recommendations), "recommendations": recommendations}


@app.get("/roadmap", tags=["Analysis"])
def get_roadmap(
    limit: int = Query(100, ge=1, le=500),
    severity: str | None = Query(None),
    resource_type: str | None = Query(None),
    include_remediation: bool = Query(True),
):
    """Full fix-first prioritization roadmap sorted by UPS descending."""
    df = _get_df().sort_values("unified_priority_score", ascending=False)
    if severity:
        df = df[df["risk_level"].str.lower() == severity.lower()]
    if resource_type:
        df = df[df["resource_type"].str.lower() == resource_type.lower()]

    df = df.head(limit).copy()
    results = []
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        r = _row_to_dict(row)
        item = {
            "rank": i,
            "resource_id": r.get("resource_id"),
            "resource_type": r.get("resource_type"),
            "srs": r.get("security_risk_score"),
            "crs": r.get("cost_risk_score"),
            "ups": r.get("unified_priority_score"),
            "severity": r.get("risk_level"),
            "estimated_monthly_waste": r.get("estimated_waste", 0),
            "short_reason": short_reason(r),
        }
        if include_remediation:
            item["recommended_action"] = recommended_action(r)
        results.append(item)

    return {"count": len(results), "roadmap": results}


@app.get("/explain/{resource_id}", tags=["AI Copilot"])
def explain_resource(resource_id: str):
    df = _get_df()
    match = df[df["resource_id"] == resource_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_id}' not found")
    resource = _row_to_dict(match.iloc[0])
    explanation = _get_explainer().explain(resource)
    return explanation


@app.post("/copilot/query", tags=["AI Copilot"])
def copilot_query_v2(body: CopilotQueryRequest):
    """Natural language copilot endpoint that always goes through RAG + generator."""
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    df = _get_df()
    top_resources = [_row_to_dict(row) for _, row in df.nlargest(body.top_k, "unified_priority_score").iterrows()]
    generated = generate_copilot_response(
        explainer=_get_explainer(),
        query=query,
        resources=top_resources,
        top_k=body.top_k,
    )

    return {
        "query": query,
        "answer": generated.get("answer", ""),
        "related_resources": generated.get("related_resources", []),
        "sources": generated.get("sources", []),
    }


@app.post("/copilot-query", tags=["AI Copilot"])
def copilot_query_legacy(body: CopilotQueryRequest):
    """Backward-compatible endpoint used by earlier UI revisions."""
    result = copilot_query_v2(body)
    return {
        "query": result["query"],
        "category": "generated",
        "message": result["answer"],
        "results": result["related_resources"],
        "sources": result["sources"],
    }


@app.post("/ingestion/normalize", tags=["Ingestion"])
def ingestion_normalize(payload: IngestionPayloadRequest):
    """Normalize optional user-supplied simulated cloud telemetry payloads."""
    records = normalize_cloud_inputs_from_payload(payload.model_dump(), DATASET_PATH)
    normalized_df = _run_pipeline(records)

    if payload.apply_to_runtime:
        global _df
        _df = normalized_df

    preview = normalized_df.nlargest(10, "unified_priority_score")
    return {
        "simulated": True,
        "normalized_records": len(normalized_df),
        "applied_to_runtime": payload.apply_to_runtime,
        "top_preview": [_row_to_dict(row) for _, row in preview.iterrows()],
    }


@app.get("/stats", tags=["Dashboard"])
def get_stats():
    df = _get_df()
    savings = summarize_cost_savings(df)
    return {
        "total_resources": len(df),
        "critical_count": int((df["risk_level"] == "Critical").sum()),
        "high_count": int((df["risk_level"] == "High").sum()),
        "medium_count": int((df["risk_level"] == "Medium").sum()),
        "low_count": int((df["risk_level"] == "Low").sum()),
        "avg_security_score": round(float(df["security_risk_score"].mean()), 2),
        "avg_cost_score": round(float(df["cost_risk_score"].mean()), 2),
        "avg_priority_score": round(float(df["unified_priority_score"].mean()), 2),
        "total_monthly_cost": savings["total_monthly_cost"],
        "estimated_monthly_waste": round(float(df["estimated_waste"].sum()), 2),
        "total_avoidable_waste": savings["total_avoidable_waste"],
        "projected_annual_savings": savings["projected_annual_savings"],
        "overall_savings_percentage": savings["overall_savings_percentage"],
        "methodology_note": savings["methodology_note"],
        "publicly_exposed_count": int(df["exposed_to_public"].sum()),
        "unencrypted_count": int((~df["storage_encrypted"]).sum()),
        "idle_count": int(df["idle_resource"].sum()),
        "oversized_count": int(df["oversized_resource"].sum()),
        "orphaned_asset_count": int(df["orphaned_asset"].sum()),
        "risk_distribution": {
            "Critical": int((df["risk_level"] == "Critical").sum()),
            "High": int((df["risk_level"] == "High").sum()),
            "Medium": int((df["risk_level"] == "Medium").sum()),
            "Low": int((df["risk_level"] == "Low").sum()),
        },
        "resource_type_counts": df["resource_type"].value_counts().to_dict(),
        "provider_counts": df["cloud_provider"].value_counts().to_dict() if "cloud_provider" in df.columns else {},
    }


@app.get("/heatmap", tags=["Dashboard"])
def get_heatmap():
    df = _get_df()
    return {
        "heatmap": [
            {
                "resource_id": row["resource_id"],
                "resource_type": row["resource_type"],
                "cloud_provider": row.get("cloud_provider", ""),
                "security_risk_score": round(float(row["security_risk_score"]), 2),
                "cost_risk_score": round(float(row["cost_risk_score"]), 2),
                "unified_priority_score": round(float(row["unified_priority_score"]), 2),
                "risk_level": row["risk_level"],
            }
            for _, row in df.iterrows()
        ]
    }


@app.get("/executive-summary", tags=["Dashboard"])
def executive_summary():
    df = _get_df()
    savings = summarize_cost_savings(df)
    critical = df[df["risk_level"] == "Critical"]
    high = df[df["risk_level"] == "High"]
    top_risk = df.nlargest(1, "unified_priority_score").iloc[0] if len(df) > 0 else None

    issue_counts: dict[str, int] = {}
    if df["exposed_to_public"].sum() > 0:
        issue_counts["Public Exposure"] = int(df["exposed_to_public"].sum())
    if (~df["storage_encrypted"]).sum() > 0:
        issue_counts["Unencrypted Storage"] = int((~df["storage_encrypted"]).sum())
    if df["open_security_group"].sum() > 0:
        issue_counts["Open Security Groups"] = int(df["open_security_group"].sum())
    if df["idle_resource"].sum() > 0:
        issue_counts["Idle Resources"] = int(df["idle_resource"].sum())

    top_issue = max(issue_counts, key=issue_counts.get) if issue_counts else "None"

    return {
        "total_resources_analysed": len(df),
        "critical_risks": len(critical),
        "high_risks": len(high),
        "total_monthly_cost": savings["total_monthly_cost"],
        "estimated_monthly_waste": round(float(df["estimated_waste"].sum()), 2),
        "total_avoidable_waste": savings["total_avoidable_waste"],
        "projected_annual_savings": savings["projected_annual_savings"],
        "overall_savings_percentage": savings["overall_savings_percentage"],
        "waste_percentage": round(
            (savings["total_avoidable_waste"] / savings["total_monthly_cost"] * 100)
            if savings["total_monthly_cost"]
            else 0,
            1,
        ),
        "methodology_note": savings["methodology_note"],
        "top_security_issue": top_issue,
        "issue_breakdown": issue_counts,
        "top_risk_resource": {
            "resource_id": top_risk["resource_id"] if top_risk is not None else "N/A",
            "resource_type": top_risk["resource_type"] if top_risk is not None else "N/A",
            "cloud_provider": top_risk.get("cloud_provider", "N/A") if top_risk is not None else "N/A",
            "unified_priority_score": round(float(top_risk["unified_priority_score"]), 2)
            if top_risk is not None
            else 0,
        },
        "scoring_methodology": {
            "security_weight": SECURITY_WEIGHT,
            "cost_weight": COST_WEIGHT,
            "formula": "UPS = 0.7 x SRS + 0.3 x CRS",
        },
        "providers_analysed": sorted(df["cloud_provider"].unique().tolist()) if "cloud_provider" in df.columns else [],
    }
