# SHL Assessment Recommender (FastAPI)

Production-ready, stateless conversational recommender for SHL assessments.

## API Contract

### `GET /health`

Returns:

```json
{"status":"ok"}
```

### `POST /chat`

Request schema:

```json
{
  "messages": [
    {"role":"user","content":"..."},
    {"role":"assistant","content":"..."}
  ]
}
```

Response schema:

```json
{
  "reply":"string",
  "recommendations":[],
  "end_of_conversation":false
}
```

or

```json
{
  "reply":"string",
  "recommendations":[
    {"name":"...", "url":"https://www.shl.com/...", "test_type":"..."}
  ],
  "end_of_conversation":false
}
```

The service is stateless: every `/chat` call must include full message history.

## What Is Enforced

- Clarification/refusal/compare returns `recommendations: []`.
- Recommendation responses return 1 to 10 items.
- Only SHL catalog URLs are returned (`https://www.shl.com/...`).
- Duplicate recommendation URLs are removed.
- `end_of_conversation` is only `true` on clear user confirmation.

## Local Setup

1. Create and activate virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Run the API.

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

4. Health check.

```bash
curl http://127.0.0.1:8000/health
```

## Testing

Run all tests:

```bash
pytest -q
```

Run replay tests only:

```bash
pytest -q tests/test_trace_replay_turn_cap.py
```

## Data

- Raw catalog: `data/raw/shl_product_catalog.json`
- Processed catalog used at runtime: `data/processed/shl_catalog_clean.json`

## Deployment (Render)

This repo includes:

- `.python-version` (Python pin)
- `runtime.txt` (extra Python runtime compatibility)
- `render.yaml` (build/start/health settings)

### Option A: Blueprint deploy (recommended)

1. Push this repo to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select the repository.
4. Render reads `render.yaml` and creates the service.

### Option B: Manual web service

Use these settings:

- Runtime: `Python`
- Root Directory: `shl-assessment-recommender` (only if your Git repo root is the parent folder)
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

## Useful Scripts

- `python scripts/inspect_catalog.py`
- `python scripts/clean_catalog.py`
- `python scripts/replay_traces.py`
- `python scripts/evaluate_recall.py`
