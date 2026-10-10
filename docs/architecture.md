# Architecture — Learning Companion Chatbot

## Flow

`Open WebUI → this local application's OpenAI-compatible chat endpoint → LangGraph router → LangChain chain and Grok model → answer in Open WebUI`

## Components

- **Open WebUI** — already installed and working for participants. It is the supplied chat client only. Participants do not reinstall, reconfigure, modify, or build it.
- **Local application** — a small FastAPI service exposing `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions` (OpenAI-compatible JSON and SSE streaming).
- **LangChain chains** — general chat and study helper, each prompt → Grok chat model → text output.
- **LangGraph workflow** — routes each request to one of the two chains.
- **Grok** — the only model provider, reached with the participant's API key.

The capstone is a small Learning Companion Chatbot, not a custom frontend or a second demonstration application.

## Message flow

`Open WebUI request → [SystemMessage(app instruction), history, HumanMessage(latest user)] → Grok → text → JSON/SSE`

History = the last 6 (`MAX_HISTORY_MESSAGES`) prior `user`/`assistant` messages in the current request, in order, via a LangChain `MessagesPlaceholder`. Request `system` messages and empty/unsupported content are ignored. Boundary: request-provided only; nothing is saved after the request, no cross-session memory.

## Chain behaviours

- **General chat** — greetings and ordinary conversation (default route).
- **Study helper** — explains beginner technical concepts, with a small example and one next step. Selected by `/study`; also runnable via `python -m learning_companion.study_helper_demo "<question>"`, which prints the payload sent to the LLM, then the answer.

Both use the same Grok model and request history.

## Workflow (LangGraph, `graph.py`)

```
START → router ─(general)→ general_chat ─┐
              └(study)───→ study_helper ─┴→ reviewer ─(approve, or revision_count=1)→ END
                                              ↑   └(improve and revision_count=0)→ improver
                                              └──────────────────────────────────────┘
```

State: `question`, `messages` (earlier user/assistant messages via `to_history`), `route` (`general`|`study`), `draft_answer` (answer under review), `review_decision` (`approve`|`improve`), `review_reason` (one sentence), `revision_count` (0 or 1), `final_answer` (sent to Open WebUI).

- **router** — ordinary Python, no model; applies the `/study` rule (`select_route`).
- **general_chat** / **study_helper** — existing LangChain chains; write `draft_answer`.
- **reviewer** — Grok specialist; checks the draft once against a fixed classroom rule (structured `approve`/`improve` plus a short reason). Forced to approve once `revision_count` is 1.
- **improver** — Grok specialist; rewrites the draft once using the reviewer's reason, sets `revision_count` to 1. No tools, browsing, retrieval, planning, or routing.

Edge rules: answer nodes → reviewer; reviewer → END on `approve` or `revision_count=1`; reviewer → improver only on `improve` with `revision_count=0`; improver → reviewer. Maximum one improvement; no other loops or retries.

The endpoint runs the graph and returns `final_answer` in the same JSON/SSE shapes (SSE sends the final text only, after review). Replies start with `[general]` or `[study]`; the dev log shows `route=<r> decision=<d> revisions=<n> nodes=<sequence>`.

Out of scope: MCP, tools, retrieval, persistence, human approval, extra agents, other loops.

## Boundaries

- API keys stay in an untracked `.env`; `.env.example` holds blank placeholders.
- Application instructions (system prompt) stay separate from user messages.
- Out of scope: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.

## Layout

- `src/learning_companion/` — `settings.py`, `chain.py` (prompts, chains, `/study` rule, history), `graph.py` (LangGraph router workflow), `api.py` (OpenAI-compatible endpoints), `main.py` (entry point, exposes `app`), `__main__.py`, `study_helper_demo.py` (dev-only)
- `tests/` — minimal checks
