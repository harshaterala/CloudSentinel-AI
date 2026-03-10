# GenAI-Powered Cloud Security Copilot

> **Multi-cloud security & cost intelligence platform** that analyses cloud infrastructure, computes quantitative risk scores, and provides explainable AI-driven remediation guidance via Retrieval-Augmented Generation (RAG).

---

## Problem Statement

Modern organisations operate across **AWS, Azure, and GCP** simultaneously. Security teams struggle to:

- **Prioritise risks** across hundreds of heterogeneous resources
- **Quantify cost waste** from idle and oversized infrastructure
- **Explain findings** in business-friendly language for executives

This platform solves all three by combining **automated risk scoring** with **AI-generated explanations** in a single dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Cloud Resource Data                     │
│              (AWS · Azure · GCP — 350 resources)                │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
              ┌──────────────────────────┐
              │   ETL & Normalisation    │ ← data_loader/
              │   (Schema validation,    │
              │    cloud_provider check) │
              └────────────┬─────────────┘
                           ▼
         ┌─────────────────┴──────────────────┐
         ▼                                    ▼
┌──────────────────┐              ┌──────────────────────┐
│  Security Risk    │              │  Cost Risk            │
│  Engine (SRS)     │              │  Engine (CRS)         │
│  ─────────────    │              │  ──────────────       │
│  P × I × E × C   │              │  U + O + R            │
│  + MFA factor     │              │  + waste estimation   │
└────────┬─────────┘              └──────────┬───────────┘
         └─────────────────┬──────────────────┘
                           ▼
              ┌──────────────────────────┐
              │  Unified Priority Score  │ ← scoring/
              │  UPS = 0.7×SRS + 0.3×CRS│
              │  + priority_rank         │
              └────────────┬─────────────┘
                           ▼
              ┌──────────────────────────┐
              │  RAG Explanation Engine   │ ← ai_explainer/
              │  SentenceTransformers    │
              │  + FAISS Vector Store    │
              │  + 28 Knowledge Docs     │
              │  (OpenAI / Gemini / TPL) │
              └────────────┬─────────────┘
                           ▼
              ┌──────────────────────────┐
              │  FastAPI REST API         │ ← main.py
              │  7 endpoints + /docs     │
              └────────────┬─────────────┘
                           ▼
              ┌──────────────────────────┐
              │  React Dashboard         │ ← frontend/
              │  Tabs · Charts · Heatmap │
              │  Executive Summary       │
              │  AI Explanation Panel    │
              └──────────────────────────┘
```

---

## Features

| Category | Details |
|---|---|
| **Multi-Cloud Support** | AWS (EC2, S3, RDS, IAM, Lambda, EKS…), Azure (VM, Storage, SQL, AKS…), GCP (Compute, Cloud SQL, GKE…) |
| **Security Risk Scoring** | Config severity × data sensitivity × exposure level (public, open SG, unencrypted, no MFA) × duration |
| **Cost Risk Scoring** | Idle detection (CPU < 10%), oversized flagging, estimated monthly waste |
| **Unified Priority Score** | Weighted composite: 0.7 × Security + 0.3 × Cost, with priority ranking |
| **RAG AI Explanations** | 28-document knowledge base, FAISS similarity search, provider-aware template explanations |
| **LLM Integration** | OpenAI GPT-4, Google Gemini, or zero-API-key template fallback |
| **Executive Summary** | Leadership-ready metrics: critical risks, waste %, top security issue |
| **Interactive Dashboard** | Tab-based navigation, filterable resource table, risk heatmap, scatter plots |

---

## Quick Start

### Prerequisites

- **Python 3.10+**, **Node.js 18+**, **npm**

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# (Optional) Regenerate the simulated dataset
python data/generate_dataset.py

# Start API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: **http://localhost:8000/docs**

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: **http://localhost:5173**

### 3. (Optional) Enable LLM explanations

```bash
# OpenAI
set LLM_PROVIDER=openai
set OPENAI_API_KEY=sk-...

# OR Google Gemini
set LLM_PROVIDER=gemini
set GOOGLE_API_KEY=...
```

Without these, the system uses **template-based explanations** with RAG context — no API key needed.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health, uptime, and LLM provider status |
| `/analysis` | GET | All resources with SRS, CRS, UPS, priority rank |
| `/recommendations` | GET | Top 5 highest-priority risks with summaries |
| `/explain/{resource_id}` | GET | AI-generated explanation & remediation advice |
| `/stats` | GET | Aggregate dashboard statistics |
| `/heatmap` | GET | Risk heatmap data |
| `/executive-summary` | GET | Leadership metrics: risk counts, waste %, top issues |

### Example: `/executive-summary` response

```json
{
  "total_resources_analysed": 350,
  "critical_risks": 42,
  "high_risks": 68,
  "total_monthly_cost": 87432.50,
  "estimated_monthly_waste": 12650.80,
  "waste_percentage": 14.5,
  "top_security_issue": "Public Exposure",
  "providers_analysed": ["AWS", "Azure", "GCP"]
}
```

---

## Risk Scoring Models

### Security Risk Score (SRS)

$$SRS = 100 \times \text{normalize}(P \times I \times E \times C)$$

| Factor | Description |
|---|---|
| **P** | Configuration severity (0–1) |
| **I** | Data sensitivity (0–1) |
| **E** | Exposure level: public (0.45) + open SG (0.30) + unencrypted (0.15) + no MFA (0.10) |
| **C** | Duration of exposure (normalised days) |

### Cost Risk Score (CRS)

$$CRS = 100 \times \text{normalize}(U + O + R)$$

| Factor | Description |
|---|---|
| **U** | Idle resource indicator (CPU < 10%, compute types only) |
| **O** | Oversized indicator (CPU < 40% with above-median cost) |
| **R** | Normalised cost impact |

### Unified Priority Score (UPS)

$$UPS = 0.7 \times SRS + 0.3 \times CRS$$

Resources are ranked by UPS and classified as **Critical** (≥ 70), **High** (≥ 40), **Medium** (≥ 20), or **Low** (< 20).

---

## Project Structure

```
backend/
├── config.py                    # Central configuration
├── main.py                      # FastAPI app (7 endpoints)
├── requirements.txt
├── data/
│   ├── generate_dataset.py      # Multi-cloud dataset generator
│   └── cloud_resources.json     # 350 simulated resources
├── data_loader/
│   └── loader.py                # ETL pipeline with validation
├── risk_engine/
│   └── security_risk.py         # SRS with MFA factor + breakdown
├── cost_engine/
│   └── cost_risk.py             # CRS with waste estimation
├── scoring/
│   └── unified_scorer.py        # UPS with priority ranking
└── ai_explainer/
    ├── knowledge_base.py        # 28 curated knowledge documents
    ├── rag_engine.py            # FAISS vector store + retrieval
    └── explainer.py             # LLM/template explanation generator

frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── App.jsx                  # Tab-based dashboard layout
    ├── main.jsx
    ├── index.css                # Dark-theme styles
    ├── api/
    │   └── client.js            # Axios API client (8 functions)
    └── components/
        ├── Charts.jsx           # Risk distribution & type charts
        ├── CostSummary.jsx      # Cost optimisation with waste %
        ├── ExecutiveSummary.jsx  # Leadership executive summary
        ├── ExplanationPanel.jsx # AI explanation panel
        ├── ResourceTable.jsx    # Sortable/filterable resource table
        ├── RiskHeatmap.jsx      # Visual risk heatmap
        └── TopPriorities.jsx    # Top 5 priority remediations
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, FastAPI, Pandas, NumPy |
| **AI/ML** | SentenceTransformers (all-MiniLM-L6-v2), FAISS |
| **LLM** | OpenAI GPT-4 / Google Gemini / Template fallback |
| **Frontend** | React 18, Vite 5, Recharts |
| **API** | REST, Swagger/OpenAPI auto-docs |

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `none` | `openai`, `gemini`, or `none` (template) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GOOGLE_API_KEY` | — | Google Gemini API key |

All scoring weights and thresholds are configurable in `backend/config.py`.

---

## License

MIT
