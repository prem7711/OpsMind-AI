# Sentinel AI — Project Guide (Interview Prep)

Multi-agent AI system that investigates production incidents automatically.
You upload logs/metrics for an incident, seven AI agents each investigate a
different angle (logs, metrics, k8s, dependencies, root cause, fixes,
postmortem), and you get a full incident report — without an engineer
manually digging through dashboards at 3am.

---

## 1. One-sentence pitch

"An agentic incident-response platform where seven LangGraph ReAct agents —
each with its own tools — investigate a production incident in sequence and
produce a root cause, remediation recommendations, and a postmortem, backed
by a RAG knowledge base over infra docs."

---

## 2. The architectural decision that matters most (lead with this)

**Every agent is a genuine tool-using ReAct agent, not a hardcoded pipeline.**

The naive way to build this: `if error_rate > threshold: check_cpu()`. That's
not AI, it's a flowchart. Instead:

- Each agent = `langgraph.prebuilt.create_react_agent(llm, tools=[...], prompt=...)`.
- The agent gets a **system prompt describing its goal** and a **list of
  tools with docstrings** — nothing else.
- The LLM itself decides: which tool to call, in what order, how many times,
  when it has enough evidence to stop.
- Example: `log_agent` isn't told "call `grep_pattern` for ERROR lines." It's
  told "find recurring error patterns." It has `grep_pattern`, `search_logs`,
  `summarize_log_levels` available and picks based on what it's seeing.

**Why this matters (interview answer):** it's the difference between a
scripted workflow wearing an "AI" label and actual agentic behavior. It also
means adding a new capability = adding a new tool with a good docstring, not
rewriting branching logic.

**If asked "how do you know it's really using the tools and not hallucinating?"**
Point to `AgentResult.tools_used` — every agent run persists exactly which
tools got called (see `app/agents/base.py` — pulled from the LLM's actual
`tool_calls` on each message). It's queryable, not a claim.

---

## 3. Tech stack (and why)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python + FastAPI | async-friendly, natural fit for LangChain/LangGraph ecosystem |
| Agent orchestration | LangGraph (`create_react_agent` + `StateGraph`) | gives ReAct tool-loop per agent for free, plus a graph to sequence the 7 agents with shared state |
| LLM | Ollama (local) via `langchain-ollama` | free, local, swappable — `app/llm.py` is the one seam to change providers |
| Vector DB / RAG | Chroma (embedded, `PersistentClient`) | zero extra infra — no separate server needed for local dev |
| Database | PostgreSQL (Neon in prod) via SQLAlchemy | relational data (incidents, investigations, results) fits SQL better than a document store |
| Frontend | React + Vite + TypeScript + Tailwind v4 | fast dev loop, type safety on API contracts, utility CSS for a real design system fast |
| Testing | pytest (backend), Playwright (manual verification pass) | unit tests mock the LLM; Playwright was used to catch real console/render errors, not committed as a dependency |

---

## 4. The AI flow (what actually happens)

```
User uploads incident (title, description, log files, metric files)
        │
        ▼
POST /incident/upload  →  creates Incident + Logs + Metrics rows
        │
POST /incident/analyze →  creates Investigation row, kicks off orchestrator
        │                  as a FastAPI BackgroundTask (non-blocking)
        ▼
┌─────────────────────────────────────────────────────────────┐
│  LangGraph StateGraph (app/agents/orchestrator.py)           │
│                                                               │
│  log_agent → metrics_agent → k8s_agent → dependency_agent    │
│       → root_cause_agent → recommendation_agent               │
│       → postmortem_agent → END                                │
│                                                               │
│  Each node:                                                   │
│   1. builds that agent's tool set (registry.py)               │
│   2. runs its ReAct loop (agent.run(task))                     │
│   3. persists an AgentResult row (agent_name, tools_used,      │
│      structured output, timestamp)                             │
│   4. folds its findings into shared state for the next agent   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
Investigation marked completed/failed, Recommendations +
Postmortem persisted, frontend polling picks up the result
```

State passed between agents is a plain `TypedDict` (`IncidentState`) —
each agent's structured output dict gets appended and handed to the next
agent's prompt as context. So `root_cause_agent` sees the log/metrics/k8s/
dependency findings; `postmortem_agent` sees everything.

---

## 5. The seven agents

| # | Agent | Job | Tools it can choose from | Output schema |
|---|---|---|---|---|
| 1 | `log_agent` | find recurring error patterns in uploaded logs | `grep_pattern`, `search_logs`, `summarize_log_levels`, `search_knowledge_base` | summary, error_patterns[], suspected_components[], severity |
| 2 | `metrics_agent` | find anomalous metric readings | `query_metrics`, `detect_anomaly`, `search_knowledge_base` | summary, anomalies[], suspected_components[], severity |
| 3 | `k8s_agent` | check cluster health | `get_pod_status`, `get_deployment_status`, `get_events`, `search_knowledge_base` | summary, unhealthy_resources[], suspected_components[], severity |
| 4 | `dependency_agent` | trace downstream service health | `get_service_dependency_graph`, `check_service_health`, `search_knowledge_base` | summary, unhealthy_services[], dependency_chain[], severity |
| 5 | `root_cause_agent` | synthesize a single root cause | **all of the above tools** (can re-verify any prior agent's claim itself) | root_cause, contributing_factors[], affected_components[], confidence |
| 6 | `recommendation_agent` | propose fixes | `run_diagnostic_query`, `explain_query` (SQL), `search_knowledge_base` | recommendations[] (action, category, rationale, confidence) |
| 7 | `postmortem_agent` | write the full report | `search_knowledge_base` | executive_summary, timeline[], root_cause, impact, fix_applied, preventive_actions[], lessons_learned[] |

**Why root_cause_agent gets every tool:** it's the one agent whose entire
job is cross-checking — if the log and metrics agents disagree, it needs to
be able to go re-run `detect_anomaly` or `grep_pattern` itself rather than
blindly trusting either. That's a deliberate design choice worth mentioning
if asked "why doesn't every agent just get every tool" — scoping tools per
agent keeps each one focused and its tool-choice space small and relevant;
root_cause is the deliberate exception because arbitration is its actual job.

---

## 6. Tools — how they're built (`app/agents/tools/`)

Each tool module exports a **factory function**, not a bare tool:

```python
def make_log_tools(log_content: str) -> list:
    def grep_pattern(pattern: str) -> str:
        ...
    return [StructuredTool.from_function(grep_pattern, ...), ...]
```

**Why a factory, not a global tool:** each tool needs to be bound to *this
incident's* log content, without the LLM having to pass the entire log file
as an argument on every call. The factory closes over `log_content`; the LLM
only ever supplies the small decision — *which* pattern to grep, *which*
metric to check — not the whole haystack. This keeps tool-call payloads
small and keeps the tool interface (what the LLM sees) clean.

**Mockable by design:** `k8s_tools.py` and `metrics_tools.py` hit a real
Kubernetes cluster / Prometheus if configured (`KUBECONFIG_PATH`,
`PROMETHEUS_URL` env vars), and fall back to realistic mock fixtures
otherwise. This is what makes the whole pipeline runnable and demoable
without a real cluster — a deliberate choice for a project meant to be run
locally / demoed, not a production shortcut.

`sql_tools.py` rejects anything that isn't a `SELECT` — a small but real
safety boundary worth mentioning if asked about security: agents that can
run arbitrary tools need guardrails on the ones with side effects.

---

## 7. Structured output — how "the AI returns JSON, not prose" actually works

`app/agents/base.py`'s `ToolUsingAgent` passes `response_format=<pydantic model>`
into `create_react_agent`. LangGraph runs the normal ReAct tool loop, then
does one more LLM call constrained to that schema, and returns it as
`state["structured_response"]`. That's why `AgentResult.output` in the
database is a real JSON object with named fields, not something we regex
out of free text.

```python
class LogFindings(BaseModel):
    summary: str
    error_patterns: list[str]
    suspected_components: list[str]
    severity_assessment: str
```

If asked "why pydantic / why not just ask the model to output JSON in the
prompt": schema-constrained output is enforced by the framework (it retries
the coercion call), not hoped-for by prompt-engineering — much more reliable
for something you're persisting to a database and building a UI on top of.

---

## 8. Database schema (9 tables, `app/db/models.py`)

```
User ──< Incident ──< LogArtifact
                  ├─< MetricArtifact
                  ├─< Investigation ──< AgentResult
                  │                 ├─< Recommendation
                  │                 └── Postmortem (1:1)
                  └─< Feedback
KnowledgeBaseDoc   (RAG chunk metadata — vectors live in Chroma, not here)
```

- `Investigation.status`: `pending → running → completed | failed`, plus
  `current_agent` (which of the 7 it's on) and `error` (if it failed).
- `AgentResult`: one row per agent per investigation — `agent_name`,
  `tools_used` (JSON list), `output` (JSON, the structured pydantic dump).
- Why `AgentResult` and `Recommendation`/`Postmortem` are separate tables
  instead of one blob: recommendations and the postmortem are the two
  things the *user* actually reads and acts on, so they get first-class
  columns and a dedicated frontend view; the other five agents' outputs are
  intermediate reasoning, so they're stored generically.

---

## 9. RAG / knowledge base

`app/rag/ingest.py` seeds Chroma with ~18 short, hand-written operational
notes across Kubernetes, Docker, PostgreSQL, Redis, Kafka, Spring Boot, Go,
Prometheus (e.g. "CrashLoopBackOff usually means OOMKilled or a failing
probe — check `kubectl describe pod`"). `search_knowledge_base` is a real
tool every agent can call, backed by a real embedding-based retriever
(`OllamaEmbeddings` + Chroma).

**Be upfront about scope if asked:** this is a representative seed set, not
the full official documentation corpus — ingesting the entire K8s/Postgres
docs was explicitly deferred as a follow-up, not something that silently
didn't happen. Good answer if asked "is this production ready" — no, and
here's specifically what's stubbed vs real.

---

## 10. REST API (`app/api/`)

| Endpoint | Purpose |
|---|---|
| `POST /incident/upload` | multipart: title, description, severity, log files, metric files → creates Incident |
| `POST /incident/analyze` | `{incident_id}` → creates Investigation, runs the 7-agent pipeline as a `BackgroundTask` (non-blocking) |
| `GET /incident/{id}` | full incident + investigation + all agent results + recommendations + postmortem |
| `GET /incident/history` | paginated incident list |
| `GET /dashboard` | aggregate stats (by severity/status, avg resolution time, recent investigations) |
| `GET /health` | checks DB, Chroma, and Ollama reachability independently |
| `POST /feedback` | user rates an investigation (1-5 + comment) |

**Why `analyze` is a BackgroundTask and not synchronous:** the pipeline can
take anywhere from ~40s (tiny model) to minutes (full model, more tool
calls). Blocking an HTTP request for that long is a bad API; the frontend
polls `GET /incident/{id}` instead.

---

## 11. Frontend (`frontend/src/`)

React + Vite + TS + Tailwind v4. Four pages:

- **Upload** — incident form + file drop, kicks off upload → analyze, redirects to the investigation page.
- **Investigation** (`/incident/:id`) — polls every 3s while `status` is `pending`/`running`. Shows an `AgentTimeline` (which of the 7 agents are done/active/pending), a card per completed agent with its structured output and which tools it used, the recommendation list with confidence bars, the full postmortem, and a feedback form once completed.
- **History** — list of past incidents.
- **Dashboard** — stat tiles, severity/status breakdown, recent investigations.

Dev setup uses a Vite proxy (`/api` → `localhost:8000`) so there's no CORS
juggling locally; `CORSMiddleware` is also on the backend for direct calls.

**A UI decision worth mentioning:** `recommendation_agent` and
`postmortem_agent`'s raw structured output is intentionally **not** shown as
a generic card — their data is fully covered by the dedicated
`RecommendationList` / `PostmortemView` components, so showing both would be
duplicate, and for the recommendation agent, ugly (stringified JSON). This
was actually a real bug I found and fixed while testing — good story if
asked "tell me about a bug you caught."

---

## 12. Real bugs found while building this (good interview stories)

1. **Dependency version mismatch**: pinned `langgraph==0.2.34`, but that
   version's `create_react_agent` doesn't accept `prompt=` or
   `response_format=` — those were added in later 0.2.x releases. Found by
   actually running the pipeline (not just unit tests, which mocked the
   agents), not by reading changelogs. Fixed by upgrading to a verified
   mutually-compatible set (`langchain==0.3.27`, `langgraph==0.2.74`, etc.)
   — jumping straight to the latest majors (`langgraph 1.x`) broke
   differently (the whole `prebuilt` module reorganized), so the fix was
   pinning to the last coherent pre-1.0 snapshot, not "just upgrade
   everything."

2. **Small local model reveals a real robustness gap**: end-to-end tested
   with a genuinely tiny model (`qwen2.5:0.5b`, chosen because bandwidth in
   the dev sandbox couldn't pull `llama3.1` in reasonable time). The
   `postmortem_agent` called `search_knowledge_base`, got back a Chroma
   internal error string, and — because the model was too weak to recognize
   "this is a tool failure, not incident data" — wrote a postmortem *about
   the Chroma error* instead of the incident. Two lessons: (a) small models
   don't reliably distinguish tool errors from tool data, so production use
   needs either a bigger model or an explicit error-shape check before
   handing tool output back to the LLM; (b) this is exactly why
   `tools_used` and raw `output` are persisted per agent — you can debug
   *why* an agent said something wrong.

3. **Duplicate UI rendering**: the generic per-agent result card and the
   dedicated recommendation/postmortem views both rendered the same data —
   caught visually (via a headless Playwright pass + screenshots), not by
   type-checking, since TypeScript has no opinion on "this looks redundant."

---

## 13. Likely interview questions + how to answer them

**"Why LangGraph instead of just calling the OpenAI/Ollama function-calling
API yourself in a loop?"**
Could build a ReAct loop by hand, but LangGraph's `create_react_agent` gives
you the loop, message history management, and `response_format` structured
output for free — and `StateGraph` gives sequencing between agents with
shared, typed state. Rebuilding that is undifferentiated work.

**"Why seven separate agents instead of one agent with all the tools?"**
Two reasons: (1) focus — an agent with 20 tools has a much harder tool-choice
problem than one with 3-4 scoped to its domain; (2) it maps directly to how
a human incident-response team actually works — different specialists look
at different signals, then someone synthesizes. `root_cause_agent` is
literally that synthesis step, which is why it's the one exception that
gets every tool.

**"How would you make this production-ready?"**
Swap the mock K8s/metrics tools for real cluster/Prometheus calls (the
seam's already there via env vars), ingest the full doc corpus instead of
the seed set, add auth (there's a `User` table but no auth wired), move off
`BackgroundTasks` to a real task queue (Celery/RQ) so a server restart
doesn't lose an in-flight investigation, and use a real model (7B+) — the
0.5B test model proved the wiring but not the answer quality.

**"What happens if an agent's tool call fails?"**
Right now LangGraph's default tool-error handling turns it into a tool
message the LLM sees and reacts to — which works fine with a capable model,
but I found (see bug #2 above) a small model can misinterpret that as data.
Worth adding an explicit check: if a tool result looks like an error/traceback,
short-circuit rather than handing it to the LLM as evidence.

**"How do you know the agents aren't just hardcoded to look like they use tools?"**
`AgentResult.tools_used` is populated by reading the LLM's actual
`tool_calls` off its response messages (`app/agents/base.py`) — it's not
something we set ourselves. If the model calls zero tools for a task, that's
exactly what gets recorded (and did happen with the small test model on
`log_agent` — it skipped tools and just guessed, which is visible in the
data, not hidden).

**"Why sqlite fallback if Postgres is the 'real' database?"**
Same SQLAlchemy models, same code path — sqlite is just for local dev
convenience when Docker/Postgres isn't handy. Neon Postgres is the
documented production target (per the original TRD's deployment section).

**"What's NOT done?"** (be ready to just list this plainly)
- No deploy configs yet (Vercel/Render/Neon wiring from the TRD).
- No auth despite having a `User` table.
- RAG knowledge base is a small seed set, not the full doc corpus.
- No retry/dead-letter handling if a background investigation crashes mid-way (it's marked `failed` with an error message, but nothing auto-retries).
- Real-model, real-cluster end-to-end run — verified with a tiny local model and mock K8s/metrics; not yet verified with production-scale infra behind it.

---

## 14. How to run it

```bash
# Backend
cd backend
pip3 install -r requirements.txt   # or use a venv if available
export DATABASE_URL="sqlite:///./sentinel.db"   # or run docker compose up -d for real Postgres
export OLLAMA_MODEL="llama3.1"                   # whatever model you've pulled
python3 -m app.rag.ingest
uvicorn app.main:app --reload --port 8000

# Ollama (separate terminal)
ollama serve
ollama pull llama3.1
ollama pull nomic-embed-text

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

`GET /health` tells you at a glance whether DB / Chroma / Ollama are all
reachable — first thing to check if something's not working.

---

## 15. Testing

- `pytest` in `backend/` — 11 tests: tool unit tests (no external deps),
  an orchestrator flow test (agents mocked via `monkeypatch`, so it tests
  the *wiring* — state passing, DB persistence, status transitions — not
  the LLM), and API tests (FastAPI `TestClient` against sqlite, orchestrator
  stubbed).
- Deliberately **not** tested by pytest: actual LLM reasoning quality —
  that's not a unit-testable property. It was verified manually, once, with
  a real local model end-to-end (see bug #2) — worth being honest that
  "tests pass" and "the AI gives good answers" are different claims.
