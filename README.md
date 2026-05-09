# SHL Assessment Recommender

Minimal RAG-style recommender for SHL product catalog.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python run.py
# or
uvicorn app.main:app --reload --port 8000
```

## Data

- Raw catalog at `data/raw/shl_product_catalog.json`
- Processed outputs in `data/processed/`

## Scripts

- `scripts/inspect_catalog.py` - Quick inspect of catalog
- `scripts/clean_catalog.py` - Write cleaned JSON and CSV
- `scripts/build_index.py` - Build inverted index

## Tests

```bash
pytest -q
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /chat` - Recommendation endpoint

```json
{
  "query": "Which assessment for data entry skills?"
}
```
