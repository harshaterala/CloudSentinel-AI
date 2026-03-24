# GenAI-Powered Cloud Security Copilot

Hackathon-ready MVP for simulated multi-cloud security risk and cloud cost optimization analysis.

Important honesty note: this project uses simulated telemetry and synthetic resource data for demo purposes. It does not claim direct production cloud API integration.

## What This Version Adds

- Rich structured RAG explanations with four mandatory sections.
- Natural language copilot query API (`/copilot/query`) and UI panel.
- Full ranked fix-first remediation roadmap endpoint (`/roadmap`) + UI table.
- Expanded benchmark-oriented knowledge base (CIS, NIST, cloud baselines, remediation, cost optimization).
- Simulated cloud-native log ingestion pipeline (`/ingestion/normalize`).
- Docker + Docker Compose setup for fast demo startup.
- Explicit cost-savings methodology with annual savings projections.

## Architecture (Updated)

```text
Simulated Cloud Inputs
  - data/cloud_resources.json
  - data/logs/iam_logs.json
  - data/logs/storage_access_logs.json
  - data/logs/security_groups.json
  - data/logs/usage_metrics.json
             |
             v
Ingestion + Normalization (services/ingestion.py + data_loader)
             |
             v
Security Risk Engine (SRS) + Cost Risk Engine (CRS)
             |
             v
Unified Priority Score (UPS) + Fix-First Ranking
             |
             +--> Cost Savings Methodology (avoidable waste, optimized cost)
             |
             +--> RAG Explanation Layer (FAISS-backed retrieval)
                         |
                         v
FastAPI Endpoints (analysis, roadmap, copilot, executive summary)
                         |
                         v
React Dashboard (roadmap table, copilot panel, executive metrics)
```

## Scoring Formulas

Security Risk Score (SRS):

```
SRS = 100 × normalize(P × I × E × C)
```

- `P`: probability of exploitation (`probability_of_exploitation`)
- `I`: impact if exploited (`impact_score`)
- `E`: exposure level (`exposure_level`)
- `C`: compliance/business criticality (`compliance_criticality`, derived from metadata/tags/sensitivity)

Cost Risk Score (CRS):

```
CRS = 100 × normalize(U + O + R)
```

- `U`: underutilization waste (`underutilization_waste`)
- `O`: oversized waste (`oversized_waste`)
- `R`: orphaned/idle waste (`orphaned_waste`)

Unified Priority Score (UPS):

```
UPS = 0.7 × SRS + 0.3 × CRS
```

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service health and runtime settings |
| `/analysis` | GET | Full scored resources |
| `/recommendations` | GET | Top recommendations, configurable `limit` |
| `/roadmap` | GET | Full ranked fix-first roadmap with filters |
| `/explain/{resource_id}` | GET | Structured RAG explanation for a resource |
| `/copilot/query` | POST | Free-form natural language copilot query |
| `/copilot-query` | POST | Backward-compatible legacy copilot route |
| `/stats` | GET | Dashboard metrics including cost-savings summary |
| `/heatmap` | GET | Risk heatmap data |
| `/executive-summary` | GET | Leadership-level summary + savings metrics |
| `/ingestion/normalize` | POST | Normalize optional user-supplied simulated telemetry |

### `/copilot/query` request/response

Request:

```json
{
  "query": "What should we fix first?",
  "top_k": 5
}
```

Response:

```json
{
  "query": "What should we fix first?",
  "answer": "Top fix-first resources are ranked by Unified Priority Score...",
  "related_resources": [{"resource_id": "rds-0150", "risk_level": "Critical"}],
  "sources": ["cis: CIS Network Exposure Baseline", "remediation: Remediation Playbook: Public Exposure"]
}
```

### `/roadmap` query params

- `limit` (default 100)
- `severity` (e.g. `Critical`, `High`)
- `resource_type` (exact match)
- `include_remediation` (`true/false`)

## Structured Explanation Contract

`/explain/{resource_id}` returns explanation JSON that always includes:

- `root_cause`
- `business_impact`
- `remediation_steps`
- `executive_summary`

All responses are generated from resource context plus retrieved documents from the vector store (RAG).

## Simulated Ingestion Inputs

Sample files are under `backend/data/logs/`:

- `iam_logs.json`
- `storage_access_logs.json`
- `security_groups.json`
- `usage_metrics.json`

These are normalized and merged with base inventory by `backend/services/ingestion.py`.

## Knowledge Base and RAG

Knowledge files are organized under `backend/knowledge_base/`:

- `cis/`
- `nist/`
- `cloud_baselines/`
- `remediation/`
- `cost_optimization/`

Retrieval metadata includes category, title, and source path so UI/API can cite documents clearly.

Rebuild vector index:

```bash
python scripts/rebuild_index.py
```

## Cost Savings Methodology (Explicit)

Implemented in `backend/services/cost_savings.py`.

Simulated assumptions:

- Idle compute: 90% of monthly cost avoidable
- Oversized compute: 40% avoidable
- Orphaned storage-like assets: 70% avoidable

Per resource metrics:

- `monthly_cost`
- `avoidable_waste`
- `projected_optimized_cost`
- `savings_percentage`

Executive metrics:

- `total_monthly_cost`
- `total_avoidable_waste`
- `projected_annual_savings`
- `overall_savings_percentage`

The commonly referenced 15-30% savings figure is documented as a simulated potential range, not a guaranteed production outcome.

## Local Run Instructions

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://localhost:5173`

## Docker Instructions

### Build and run backend only

```bash
docker build -t cloud-copilot-backend ./backend
docker run --rm -p 8000:8000 cloud-copilot-backend
```

### Build and run frontend only

```bash
docker build -t cloud-copilot-frontend ./frontend
docker run --rm -p 5173:5173 cloud-copilot-frontend
```

### Run full stack with one command

```bash
docker compose up --build
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` or `none` |
| `GOOGLE_API_KEY` | empty | Gemini key |
| `USE_SIMULATED_INGESTION` | `true` | Use local simulated logs from `data/logs/` |

## Demo Flow

1. Start backend (`python -m uvicorn main:app --host 127.0.0.1 --port 8000`).
2. Start frontend (`npm run dev`).
3. Open dashboard and confirm heatmap, cost summary, and roadmap are populated.
4. Use ingestion panel to upload or apply simulated telemetry.
5. Click a resource to open explanation panel with root cause, business impact, remediation steps, and executive summary.
6. Use copilot chat to ask natural-language questions and review RAG-grounded answers and references.
7. Show `/roadmap` ordering by UPS and `/copilot/query` behavior in API docs.

## Lightweight Tests

```bash
cd backend
pytest -q
```

Current lightweight tests cover:

- SRS formula correctness with compliance criticality (`test_risk.py`)
- CRS formula correctness with orphaned/idle waste (`test_cost.py`)
- explanation contract and RAG usage (`test_explanation_contract.py`)
- copilot no-canned generation path (`test_copilot.py`)

## License

MIT
