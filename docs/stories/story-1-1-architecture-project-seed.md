# Story 1.1 — Architecture, LangChain project seed, and Open WebUI connection

Project path: repository root (no `docs/config.yaml` exists).

## Purpose

Record the classroom architecture, get instructor approval, then seed a small Python project for the **Learning Companion Chatbot** that answers in the already-installed Open WebUI through a LangChain prompt and a Grok model.

## What this story implements in plain English

- You can start a small local chatbot service on your own machine.
- You can pick the course's Grok model inside your existing Open WebUI.
- You can type a question in Open WebUI and get a helpful Learning Companion reply.
- Replies can appear all at once or word by word as they arrive.
- If your API key is missing, the service still starts and tells you clearly what to fix when you chat.

## Prerequisites

- Python 3.12 and UV installed.
- Open WebUI already installed and working. Do not reinstall, reconfigure, modify, or build it.
- A Grok API key (participant) and the Grok model name (supplied by the instructor).
- Existing repo files to preserve: `README.md` (title only, UTF-16), empty `.gitignore`, `CLAUDE.md`, `docs/`.

## Work to do

### Step 1 — Architecture (stop for approval)

Create `docs/architecture.md` (short) recording:

- Single flow: `Open WebUI → this local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`.
- Open WebUI is pre-installed and is the supplied chat client only; participants never change it.
- The capstone is a small Learning Companion Chatbot — no custom frontend, no second demo app.
- Boundaries: API keys only in untracked `.env`; application instructions kept separate from user messages.
- Out of scope: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.
- Planned layout: `src/learning_companion/` (settings, chain, API), `tests/`.

Then ask the instructor: "Please approve `docs/architecture.md` before I seed the project." **Stop.** Before approval, do not create seed files, install dependencies, or scaffold code. Resume this same story only after explicit approval.

### Step 2 — Project seed (after approval only)

Run:

```
uv init --package --python 3.12 --name learning-companion .
uv add fastapi uvicorn pydantic-settings langchain langchain-xai
uv add --dev ruff pytest
```

Create or change these files:

- `pyproject.toml` — Python 3.12, dependencies above, Ruff config.
- `uv.lock` — produced by UV.
- `.gitignore` — add `.env`, `.venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`.
- `.env.example` — exactly:
  ```
  APP_ENV=development
  GROK_API_KEY=
  GROK_API_BASE_URL=https://api.x.ai/v1
  GROK_MODEL_NAME=
  HOST=127.0.0.1
  PORT=8000
  ```
  No Claude, alternate-provider, database, or production settings.
- `README.md` — keep the title; rewrite as UTF-8. Add: copy `.env.example` to `.env`; put your real key only in `.env` (never commit it); the instructor supplies `GROK_MODEL_NAME`; run command; Open WebUI connection values (below).
- `src/learning_companion/__init__.py`
- `src/learning_companion/settings.py` — Pydantic settings reading `.env`; key and model name may be blank.
- `src/learning_companion/chain.py` — one LangChain flow: `ChatPromptTemplate` (fixed Learning Companion system instruction + latest user message) → `ChatXAI` (key, base URL, model from settings) → `StrOutputParser`. Build the model only when a call is made; if key or model name is blank, raise a clear configuration error.
- `src/learning_companion/api.py` — FastAPI app:
  - `GET /health` → `{"status": "ok"}`.
  - `GET /v1/models` → OpenAI-style list with one entry: the configured `GROK_MODEL_NAME`.
  - `POST /v1/chat/completions` → accepts `model`, `messages` (text content; roles `system`, `user`, `assistant`), `stream`. Pass only the latest user message to the chain.
    - `stream: false` → normal OpenAI `chat.completion` JSON.
    - `stream: true` → text-only `chat.completion.chunk` SSE events, then a chunk with `finish_reason: "stop"`, then `data: [DONE]`.
    - Missing key/model → honest configuration error (HTTP 500 JSON with a clear message), not a crash at startup.
  - No custom Open WebUI events, no second chat route, no browser UI.
- `src/learning_companion/__main__.py` — run Uvicorn with `HOST`/`PORT` from settings.
- `tests/test_health.py` — one test: `/health` returns ok (no API key needed).

Do not add conversation history, tool calls, LangGraph, agents, MCP, or advanced streaming.

## Completion checks

Run only these:

```
uv run ruff format src tests
uv run ruff check src tests
uv run pytest tests/test_health.py
uv run python -m learning_companion
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/v1/models
```

Open WebUI (application-side values only; do not change Open WebUI itself):

- OpenAI-compatible connection base URL: `http://127.0.0.1:8000/v1` (use `http://host.docker.internal:8000/v1` if Open WebUI runs in Docker); any non-empty API key value.
- Select the Grok model shown from `/v1/models`.
- Send one message with streaming on and one with streaming off.

Expected result: one Learning Companion reply from Grok visible in Open WebUI for each request. With a blank key, the service starts and the chat shows a clear configuration error.

## Handover

- Files created/changed: `docs/architecture.md`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`, `README.md`, `src/learning_companion/{__init__,settings,chain,api,__main__}.py`, `tests/test_health.py`.
- Later stories extend `chain.py` (prompt template 2.1, history 2.2, study helper 3.1), `api.py` (routing 3.2), and add `graph.py` (LangGraph 4.1) behind the same chat endpoint.
