# Agentic Workflow Orchestration Platform

A small, independently implemented portfolio project demonstrating how deterministic software agents can plan and execute a text-processing workflow, validate results, and expose progress through a local dashboard. The default experience is fully offline after dependencies are installed; no API key is required.

> **Repository name:** `agentic-workflow-platform`

## Features

- Six logical, separately testable agents coordinated in a sequential workflow.
- Four runnable demo tasks: meeting notes, project planning, document extraction, and support analysis.
- Structured plans, per-step states, bounded retries, validation feedback, timestamps, and event history.
- Local in-memory history limited to the newest 100 workflows by default.
- Responsive HTML/CSS/vanilla JavaScript dashboard and typed FastAPI endpoints.
- Optional OpenAI-compatible LLM client abstraction; deterministic agents remain the default execution path.
- No arbitrary shell or Python execution, live research, or real-world actions.

## Screenshots

_Screenshot placeholder — add a desktop dashboard image here._

_Screenshot placeholder — add a narrow/mobile dashboard image here._

## Architecture

| Agent | Responsibility |
| --- | --- |
| Intake | Trims and validates the request and assigns a UUID. |
| Planning | Creates a fixed, bounded plan and step dependencies without claiming LLM planning. |
| Research | Uses only supplied task text and explicitly labels synthetic analysis and limitations. |
| Execution | Runs predefined meeting, project, extraction, support, or basic summary operations. |
| Validation | Checks required output structure and reports actionable feedback. |
| Summarization | Presents a concise result and distinguishes supplied evidence from suggestions. |

The orchestrator runs steps **sequentially**: research → execution → validation → summarization. Steps move from pending to running and then completed or failed; later steps are skipped after an unrecoverable failure. It retries failed steps up to the configured small limit. A validation failure triggers a bounded retry of execution. Execution is synchronous and local, not a distributed production orchestration service.

The history store is in memory and resets on application restart. Each stored workflow is copied on read/write, and the store drops the oldest records when its configured limit is exceeded.

## Project structure

```text
app/
  agents/        intake, planning, research, execution, validation, summarization
  frontend/      dashboard HTML, CSS, and vanilla JavaScript
  routes/        health and workflow API routes
  services/      registry, in-memory store, optional LLM client
  config.py      environment-backed settings
  main.py        FastAPI application factory
  models.py      Pydantic request and response schemas
  orchestrator.py
tests/
requirements.txt
run.py
```

## Setup on Windows PowerShell

Prerequisites: Python 3.12 and PowerShell.

```powershell
cd C:\path\to\agentic-workflow-platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this in the current terminal, then activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Start the app:

```powershell
python run.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The interactive API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API

All responses use the schemas in `app/models.py`.

| Method and route | Description |
| --- | --- |
| `GET /api/health` | Service status, demo-mode flag, and sequential execution mode. |
| `GET /api/agents` | Registered logical agents and supported operations. |
| `GET /api/workflows/examples` | Four demo tasks with scenario identifiers. |
| `POST /api/workflows` | Validate and synchronously execute a workflow. |
| `GET /api/workflows` | List recent workflow summaries, newest first. |
| `GET /api/workflows/{workflow_id}` | Get plan, state, events, outputs, validation, and final summary. |

Example:

```powershell
$body = @{
  task = "Process these notes.`nNotes:`nDecision: Ship on Friday."
  scenario = "meeting"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/workflows `
  -ContentType "application/json" -Body $body
```

The optional `scenario` is one of `meeting`, `project`, `document`, or `support`. Omit it for a short general text summary. Requests must include a non-empty task of at most 10,000 characters. Unknown workflow IDs return 404.

## Demo scenarios

- **Meeting notes processor:** summarizes provided notes and extracts lines explicitly marked as decisions or action items. Owners are included only when an `Owner:` or `Assigned to:` label is provided.
- **Project planner:** produces a small, prioritized starter checklist for the supplied goal.
- **Document information extractor:** extracts simple name, email, phone, organization, and date patterns; absent values remain null.
- **Support request analyzer:** classifies sample text and suggests safe next steps. This is not a live support integration.

Use the dashboard demo buttons or retrieve the examples endpoint and submit a task with its `scenario`.

## Optional LLM configuration

The default workflow uses deterministic local logic. If both `LLM_API_KEY` and `LLM_MODEL` are configured, the final report may be generated by the OpenAI-compatible backend client in `app/services/llm_service.py`. The request includes supplied task text and structured results, so configure a provider only if you consent to sending that content to it. Provider output is bounded and checked for non-empty text; a provider error or invalid/oversized result falls back to the deterministic report. The API labels a successful provider-assisted workflow `llm-assisted`; otherwise it is `demo`.

```powershell
Copy-Item .env.example .env
```

Set `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in the local `.env` only if you later connect the client. Never put credentials in frontend code or commit `.env`. API keys are not required for any built-in scenario.

## Tests

```powershell
pytest -q
```

The tests use synthetic inputs and FastAPI `TestClient`; they do not contact external services or need an API key.

## Limitations and safety

- This is a lightweight single-process demo, not durable or distributed orchestration.
- History is in memory and cleared on restart.
- Agents are logical Python components, not autonomous concurrent LLMs.
- Research is simulated from supplied text; no browsing or external retrieval occurs.
- Meeting and document extraction use simple deterministic text patterns and can miss nuanced or ambiguous content.
- Project priorities, classifications, and recommendations are suggestions, not verified decisions.
- The app will not execute arbitrary code or shell commands or take external actions.

## Troubleshooting

- **`python` is not found:** install Python 3.12 and reopen PowerShell; verify with `python --version`.
- **Activation is blocked:** use the process-scoped execution policy command above or invoke `.venv\Scripts\python.exe` directly.
- **Port 8000 is busy:** run `python -m uvicorn app.main:app --host 127.0.0.1 --port 8010` and open port 8010.
- **Dashboard cannot reach the API:** confirm the server is running and check `http://127.0.0.1:8000/api/health`.
- **Missing package errors:** activate this project's `.venv` and rerun `pip install -r requirements.txt`.

## GitHub preparation

The `.gitignore` excludes virtual environments, `.env`, test caches, Python bytecode, local editor settings, and generated databases/logs. Review files before publishing; do not commit secrets or local runtime artifacts.

```powershell
git init
git add .
git status
git commit -m "Build agentic workflow orchestration platform"
```

Review the staged file list before committing and configure the GitHub remote manually. This project does not initialize a repository or push automatically.
