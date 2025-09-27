# Dynamic Agent Platform Backend

This package exposes the core services for the dynamic agent platform and now ships with a FastAPI-powered HTTP surface for local development. It covers:

1. **Registry management** for agent templates, tools, functions, and deployed instances backed by SQLite.
2. **Dynamic generation stubs** that simulate GPT-driven component creation so the self-improvement loop can run offline.
3. **Orchestration workflows** that deploy agents, route requests using simple heuristics, and register self-improvement proposals.
4. **REST API** for the frontend experience with CORS enabled out of the box.

## Quickstart

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Run the API server

```bash
cd backend
python -m app.main
# or using uvicorn directly
uvicorn app.api:app --reload
```

The `python -m app.main` entry point seeds a small dataset, prints the created records, and then serves the API at <http://localhost:8000>.

## Example Requests

```bash
curl -X POST http://localhost:8000/templates \
  -H "Content-Type: application/json" \
  -d '{
        "name": "ResearchAssistant",
        "description": "Helps summarize papers",
        "required_tools": [],
        "model_config": {"temperature": 0.3}
      }'

curl http://localhost:8000/templates

curl -X POST http://localhost:8000/agents/deploy \
  -H "Content-Type: application/json" \
  -d '{
        "template_id": 1,
        "name": "Researcher",
        "owner_id": "demo"
      }'
```

## Running Tests

```bash
cd backend
pytest
```

## Module Overview

- `app/database.py` – SQLite connection manager and schema bootstrapper.
- `app/models.py` – Dataclasses describing registry records.
- `app/registry.py` – CRUD operations and query helpers built on the database module.
- `app/dynamic.py` – Offline dynamic component generator for tests and prototyping.
- `app/orchestration.py` – Deployment, routing, and self-improvement services.
- `app/api.py` – FastAPI application exposing registry, routing, and improvement endpoints.
- `app/main.py` – CLI launcher that seeds demo data and starts the API server.
- `tests/` – Unit tests covering registry flows, orchestration, dynamic generation, and HTTP endpoints.

See `../frontend/README.md` for details on the accompanying web interface.
