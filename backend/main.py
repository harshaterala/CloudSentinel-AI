"""
GenAI-Powered Cloud Security Copilot — FastAPI Backend
======================================================
Exposes a REST API that runs the complete analysis pipeline
(ETL → SRS → CRS → UPS) and serves results + AI explanations.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so that `backend.*` imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import (
    DATASET_PATH, APP_TITLE, APP_VERSION, APP_DESCRIPTION,
    SECURITY_WEIGHT, COST_WEIGHT, LLM_PROVIDER,
)
from backend.data_loader.loader import load_and_prepare
from backend.risk_engine.security_risk import compute_security_risk
from backend.cost_engine.cost_risk import compute_cost_risk
from backend.scoring.unified_scorer import compute_unified_priority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ───────────────────────────────────────────────────────────

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

# ── Lazy globals — populated on first request ─────────────────────────────

_df = None
_explainer = None
_startup_time = time.time()


def _get_df():
    global _df
    if _df is None:
        logger.info("Running analysis pipeline...")
        df = load_and_prepare(DATASET_PATH)
        df = compute_security_risk(df)
        df = compute_cost_risk(df)
        df = compute_unified_priority(df)
        _df = df
        logger.info("Pipeline complete — %d resources analysed.", len(df))
    return _df


def _get_explainer():
    global _explainer
    if _explainer is None:
        from backend.ai_explainer.explainer import AIExplainer
        _explainer = AIExplainer()
        logger.info("AI Explainer initialised (mode=%s).", LLM_PROVIDER)
    return _explainer


# ── Columns exposed in API responses ──────────────────────────────────────

PUBLIC_COLUMNS = [
    "resource_id", "resource_type", "cloud_provider", "region",
    "cpu_usage", "monthly_cost",
    "exposed_to_public", "data_sensitivity", "days_exposed",
    "config_severity", "storage_encrypted", "open_security_group",
    "tags",
    "security_risk_score", "cost_risk_score", "unified_priority_score",
    "risk_level", "exposure_level", "priority_rank",
    "idle_resource", "oversized_resource", "estimated_waste",
]


def _row_to_dict(row) -> dict:
    d = {}
    for col in PUBLIC_COLUMNS:
        val = row.get(col)
        if val is None:
            continue
        if hasattr(val, "item"):
            val = val.item()
        d[col] = val
    return d


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    """Lightweight health check for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "llm_provider": LLM_PROVIDER,
    }


# ── Analysis ──────────────────────────────────────────────────────────────

@app.get("/analysis", tags=["Analysis"])
def get_analysis(
    sort_by: str = Query("unified_priority_score", description="Column to sort by"),
    ascending: bool = Query(False, description="Sort order"),
    limit: int = Query(0, description="Limit results (0 = all)"),
):
    """Return all analysed resources with SRS, CRS, and UPS."""
    df = _get_df()
    if sort_by not in df.columns:
        sort_by = "unified_priority_score"
    sorted_df = df.sort_values(sort_by, ascending=ascending)
    if limit > 0:
        sorted_df = sorted_df.head(limit)
    return {
        "count": len(sorted_df),
        "resources": [_row_to_dict(row) for _, row in sorted_df.iterrows()],
    }


# ── Recommendations ──────────────────────────────────────────────────────

@app.get("/recommendations", tags=["Analysis"])
def get_recommendations():
    """Return the top 5 highest-priority risks with brief descriptions."""
    df = _get_df()
    top = df.nlargest(5, "unified_priority_score")
    results = []
    for _, row in top.iterrows():
        rec = _row_to_dict(row)
        issues = []
        if row.get("exposed_to_public"):
            issues.append("publicly exposed")
        if row.get("open_security_group"):
            issues.append("open security group")
        if not row.get("storage_encrypted", True):
            issues.append("unencrypted storage")
        if row.get("idle_resource"):
            issues.append("idle resource")
        if row.get("oversized_resource"):
            issues.append("oversized resource")
        rec["summary"] = ", ".join(issues) if issues else "elevated risk profile"
        results.append(rec)
    return {"recommendations": results}


# ── Explain ──────────────────────────────────────────────────────────────

@app.get("/explain/{resource_id}", tags=["AI Copilot"])
def explain_resource(resource_id: str):
    """Return an AI-generated explanation and remediation advice."""
    df = _get_df()
    match = df[df["resource_id"] == resource_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_id}' not found")
    row = match.iloc[0]
    resource_dict = _row_to_dict(row)
    explainer = _get_explainer()
    explanation = explainer.explain(resource_dict)
    return {"resource": resource_dict, "explanation": explanation}


# ── Stats ────────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Dashboard"])
def get_stats():
    """Aggregate statistics powering the dashboard widgets."""
    df = _get_df()

    total_waste = round(float(df["estimated_waste"].sum()), 2)

    return {
        "total_resources": len(df),
        "critical_count": int((df["risk_level"] == "Critical").sum()),
        "high_count": int((df["risk_level"] == "High").sum()),
        "medium_count": int((df["risk_level"] == "Medium").sum()),
        "low_count": int((df["risk_level"] == "Low").sum()),
        "avg_security_score": round(float(df["security_risk_score"].mean()), 2),
        "avg_cost_score": round(float(df["cost_risk_score"].mean()), 2),
        "avg_priority_score": round(float(df["unified_priority_score"].mean()), 2),
        "total_monthly_cost": round(float(df["monthly_cost"].sum()), 2),
        "estimated_monthly_waste": total_waste,
        "publicly_exposed_count": int(df["exposed_to_public"].sum()),
        "unencrypted_count": int((~df["storage_encrypted"]).sum()),
        "idle_count": int(df["idle_resource"].sum()),
        "oversized_count": int(df["oversized_resource"].sum()),
        "risk_distribution": {
            "Critical": int((df["risk_level"] == "Critical").sum()),
            "High": int((df["risk_level"] == "High").sum()),
            "Medium": int((df["risk_level"] == "Medium").sum()),
            "Low": int((df["risk_level"] == "Low").sum()),
        },
        "resource_type_counts": df["resource_type"].value_counts().to_dict(),
        "provider_counts": (
            df["cloud_provider"].value_counts().to_dict()
            if "cloud_provider" in df.columns else {}
        ),
    }


# ── Heatmap ──────────────────────────────────────────────────────────────

@app.get("/heatmap", tags=["Dashboard"])
def get_heatmap():
    """Return data optimised for rendering a risk heatmap."""
    df = _get_df()
    heatmap_data = []
    for _, row in df.iterrows():
        heatmap_data.append({
            "resource_id": row["resource_id"],
            "resource_type": row["resource_type"],
            "cloud_provider": row.get("cloud_provider", ""),
            "security_risk_score": round(float(row["security_risk_score"]), 2),
            "cost_risk_score": round(float(row["cost_risk_score"]), 2),
            "unified_priority_score": round(float(row["unified_priority_score"]), 2),
            "risk_level": row["risk_level"],
        })
    return {"heatmap": heatmap_data}


# ── Executive Summary ────────────────────────────────────────────────────

@app.get("/executive-summary", tags=["Dashboard"])
def executive_summary():
    """High-level executive summary for leadership reporting."""
    df = _get_df()

    critical = df[df["risk_level"] == "Critical"]
    high = df[df["risk_level"] == "High"]
    top_risk = df.nlargest(1, "unified_priority_score").iloc[0] if len(df) > 0 else None

    total_waste = round(float(df["estimated_waste"].sum()), 2)
    total_cost = round(float(df["monthly_cost"].sum()), 2)

    # Find the most common security issue
    issue_counts = {}
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
        "total_monthly_cost": total_cost,
        "estimated_monthly_waste": total_waste,
        "waste_percentage": round((total_waste / total_cost * 100) if total_cost else 0, 1),
        "top_security_issue": top_issue,
        "issue_breakdown": issue_counts,
        "top_risk_resource": {
            "resource_id": top_risk["resource_id"] if top_risk is not None else "N/A",
            "resource_type": top_risk["resource_type"] if top_risk is not None else "N/A",
            "cloud_provider": top_risk.get("cloud_provider", "N/A") if top_risk is not None else "N/A",
            "unified_priority_score": round(float(top_risk["unified_priority_score"]), 2) if top_risk is not None else 0,
        },
        "scoring_methodology": {
            "security_weight": SECURITY_WEIGHT,
            "cost_weight": COST_WEIGHT,
            "formula": "UPS = 0.7 × SRS + 0.3 × CRS",
        },
        "providers_analysed": sorted(df["cloud_provider"].unique().tolist()) if "cloud_provider" in df.columns else [],
    }


# ── Copilot Natural Language Query ───────────────────────────────────────

class CopilotQueryRequest(BaseModel):
    query: str


_CATEGORY_KEYWORDS = {
    "risk":     ["risk", "dangerous", "vulnerable", "threat", "risky", "security"],
    "cost":     ["cost", "waste", "expensive", "spend", "money", "saving"],
    "exposure": ["public", "exposed", "open", "internet", "accessible"],
    "priority": ["fix", "priority", "urgent", "first", "remediate", "action"],
    "explain":  ["why", "explain", "reason", "detail", "tell me about"],
}


def _classify_query(query: str) -> str:
    q = query.lower()
    # "explain" intent takes priority when explicit question words appear
    explain_signals = ["why", "explain", "reason", "tell me about"]
    if any(sig in q for sig in explain_signals):
        return "explain"
    scores = {cat: sum(kw in q for kw in kws) for cat, kws in _CATEGORY_KEYWORDS.items()
              if cat != "explain"}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "risk"


@app.post("/copilot-query", tags=["AI Copilot"])
def copilot_query(body: CopilotQueryRequest):
    """Natural language query interface for the cloud security copilot."""
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    df = _get_df()
    category = _classify_query(query)

    if category == "exposure":
        subset = df[df["exposed_to_public"] == True]
        message = f"Found {len(subset)} publicly exposed resources."
        results = [_row_to_dict(row) for _, row in subset.nlargest(10, "unified_priority_score").iterrows()]

    elif category == "cost":
        top = df.nlargest(5, "estimated_waste")
        total_waste = round(float(top["estimated_waste"].sum()), 2)
        message = f"Top 5 resources by estimated monthly waste (${total_waste} combined)."
        results = [_row_to_dict(row) for _, row in top.iterrows()]

    elif category == "priority":
        top = df.nsmallest(5, "priority_rank")
        message = "Top 5 resources that should be fixed first, ranked by priority."
        results = [_row_to_dict(row) for _, row in top.iterrows()]

    elif category == "explain":
        # Try to extract a resource_id from the query, otherwise explain the top risk
        target_id = None
        for rid in df["resource_id"].values:
            if rid.lower() in query.lower():
                target_id = rid
                break
        if target_id is None:
            target_id = df.nlargest(1, "unified_priority_score").iloc[0]["resource_id"]
        row = df[df["resource_id"] == target_id].iloc[0]
        resource_dict = _row_to_dict(row)
        explainer = _get_explainer()
        explanation = explainer.explain(resource_dict)
        message = f"AI explanation for {target_id}."
        results = [{"resource": resource_dict, "explanation": explanation}]

    else:  # risk (default)
        top = df.nlargest(5, "unified_priority_score")
        message = "Top 5 most dangerous resources ranked by Unified Priority Score."
        results = [_row_to_dict(row) for _, row in top.iterrows()]

    return {
        "query": query,
        "category": category,
        "message": message,
        "results": results,
    }
