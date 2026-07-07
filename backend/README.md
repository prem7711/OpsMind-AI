# Sentinel AI — Core Pipeline

Multi-agent incident analysis backend. Seven tool-using LangGraph ReAct agents
(Log → Metrics → K8s → Dependency → RootCause → Recommendation → Postmortem)
investigate an uploaded incident and produce a postmortem. No hardcoded
"if X then call tool Y" branching — each agent's LLM decides which of its
bound tools to call, in what order, and how many times.

A React frontend lives in `../frontend` (see its quickstart below). No deploy
configs yet — see the TRD's `14. Deployment` section for the intended
Vercel/Render/Neon/Chroma targets.

## Prerequisites

- Python 3.10+
- Docker (for local Postgres)
- [Ollama](https://ollama.com) running locally with a chat model and an embedding model pulled:
  ```
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```

## Quickstart

```bash
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d          # starts Postgres
python -m app.rag.ingest      # seeds the Chroma knowledge base
uvicorn app.main:app --reload
```

## Try it end-to-end

```bash
# 1. Upload an incident with a log file
curl -s -X POST http://localhost:8000/incident/upload \
  -F title="API 500 spike" \
  -F description="Checkout service returning 500s since 10:00" \
  -F severity=high \
  -F log_files=@sample_incident.log | tee /tmp/upload.json

INCIDENT_ID=$(python -c "import json;print(json.load(open('/tmp/upload.json'))['incident_id'])")

# 2. Kick off analysis (runs the 7-agent pipeline as a background task)
curl -s -X POST http://localhost:8000/incident/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"incident_id\": $INCIDENT_ID}"

# 3. Poll until status is "completed"
curl -s http://localhost:8000/incident/$INCIDENT_ID | python -m json.tool

# Also: GET /incident/history, GET /dashboard, GET /health, POST /feedback
```

## Tests

```bash
pytest
```

Tool unit tests run with no external dependencies. The orchestrator and API
tests stub out the LLM-backed agents (via monkeypatch) so the full
upload → analyze → fetch flow is verified without needing Ollama running.

## Frontend

```bash
cd ../frontend
npm install
npm run dev   # http://localhost:5173, proxies /api/* to the backend on :8000
```

Upload an incident from the UI, watch the 7-agent pipeline progress live, and
view recommendations/postmortem once it completes.

## Architecture

See `app/agents/` — `base.py` has the generic `ToolUsingAgent` wrapper;
each `*_agent.py` defines a system prompt, an output schema, and pulls its
tool set from `app/agents/tools/registry.py`. `orchestrator.py` wires the
seven agents into a LangGraph `StateGraph` matching the TRD's AI Flow, and
persists each agent's structured output as it completes.

## Exact commands to start everything (3 terminals)

**Terminal 1 — Ollama:**
```bash
export PATH="$HOME/.local/ollama/bin:$PATH"   # only needed if installed user-local, not system-wide
ollama serve
```

**Terminal 2 — Backend:**
```bash
cd backend
pip3 install -r requirements.txt
export DATABASE_URL="sqlite:///./sentinel.db"   # or: docker compose up -d  →  use the postgresql URL in .env.example
export OLLAMA_MODEL="llama3.1"                   # must match a model you've pulled: ollama pull llama3.1
export OLLAMA_EMBED_MODEL="nomic-embed-text"     # ollama pull nomic-embed-text
python3 -m app.rag.ingest
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173**. Check `curl http://localhost:8000/health`
first if anything seems broken — it reports DB/Chroma/Ollama reachability
independently.
