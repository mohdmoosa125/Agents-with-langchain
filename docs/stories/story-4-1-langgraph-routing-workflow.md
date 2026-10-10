# Story 4.1 — LangGraph routing workflow

## Purpose

Replace only the internal Python if/else from Story 3.2 with one small LangGraph workflow that makes the route, state, nodes, and edges visible. The existing general-chat and study-helper chains, endpoints, Grok settings, history handling, and JSON/SSE behavior stay as they are.

## What this story implements in plain English

- You ask a question in Open WebUI exactly as before; nothing changes on screen.
- Inside the app, your question now enters a small workflow with a written-down shape: a first step picks the path, then one of two answer steps runs.
- A question starting with `/study` takes the study path; anything else takes the general-chat path. The rule is the same as before.
- The chosen answer step writes the final reply, which is sent back to Open WebUI.
- In development, a short trace shows the route and the steps that ran, in order.

## Prerequisites

- Stories 1.1–3.2 complete: `chain.py` has `select_route`, `build_chain`, `build_study_helper_chain`, `to_history`; `api.py` dispatches on the route and adds `[general]`/`[study]` labels for JSON and SSE.
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.
- Open WebUI connected as before.

## Work to do

Preserve the endpoints, Open WebUI connection, request/response shapes, Grok settings, history conversion (`to_history`, Story 2.2), and the `/study` behavior. No second app or route, review step, loop, retry, extra agent, database, persistence, RAG, web search, tool execution, MCP, or human approval.

Terms: a **node** is a focused piece of work, not automatically an agent. The router is ordinary application logic. The two Grok-powered nodes are small specialist behaviours. An MCP tool call could sit inside a future node; MCP is not implemented in this course story.

**State fields (plain English)**

| Field | Meaning |
|-------|---------|
| `question` | The current user message, as typed |
| `messages` | Earlier user/assistant messages of this chat, already converted by `to_history` |
| `route` | `general` or `study`, written by the router |
| `answer` | The final reply text, written by an answer node |

**Nodes and edges**

```
START → router ─(route=general)→ general_chat → END
              └(route=study)───→ study_helper → END
```

1. Add dependency: `uv add langgraph`.
2. `src/learning_companion/graph.py` (new)
   - `GraphState` as a `TypedDict` with `question: str`, `messages: list[BaseMessage]`, `route: str`, `answer: str`.
   - `router` node: ordinary Python; calls `select_route` (the existing `/study` rule) and writes `route` and the stripped `question`. No model call.
   - `general_chat` node: invokes the existing general-chat chain with `question` and `messages`; writes `answer`.
   - `study_helper` node: invokes the existing study-helper chain the same way; writes `answer`.
   - Build with `StateGraph(GraphState)`: `add_edge(START, "router")`, `add_conditional_edges("router", lambda s: s["route"], {"general": "general_chat", "study": "study_helper"})`, `add_edge("general_chat", END)`, `add_edge("study_helper", END)`. Export a compiled `GRAPH`.
   - Dev-only trace (`APP_ENV=development`): log `route=<r> nodes=router,<answer node>` once per run. No keys, prompts, or message text.
3. `src/learning_companion/api.py`
   - Replace the `select_route` dispatch with the graph. Normal mode: `await GRAPH.ainvoke(...)` and return `[route] answer`. Streaming mode: `GRAPH.astream(..., stream_mode="messages")` forwarding model text tokens as SSE content chunks, after the `[route]` label chunk. If token streaming from nodes is not practical, emit the final answer as one content chunk; the SSE shape stays valid either way.
   - Keep configuration-error handling (HTTP 500 JSON on missing key/model).
4. `docs/architecture.md`
   - Add the graph diagram, state fields, node responsibilities, edge rules, and out-of-scope list (review/loops are Story 4.2; no MCP, tools, persistence).

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion
```

In the existing Open WebUI chat, send:

1. `Hello!`
2. `/study Explain what an API is`

Expected:
- Message 1: normal reply starting `[general]`; trace `route=general nodes=router,general_chat`.
- Message 2: reply starting `[study]` with a clear explanation and one next step; trace `route=study nodes=router,study_helper`.
- Both replies appear in Open WebUI through the same endpoint, same as Story 3.2.

## Handover

- Files changed: `pyproject.toml`, `uv.lock`, `src/learning_companion/graph.py` (new), `src/learning_companion/api.py`, `docs/architecture.md`.
- Commands actually run: `uv add langgraph`, `uv run ruff format src tests`, `uv run ruff check src tests`, `uv run python -m learning_companion`, curl POSTs (`Hello!`, `/study Explain what an API is`; stream on and off).
- Results: JSON and SSE (token-streamed, ends `data: [DONE]`) worked for both paths; traces `route=general nodes=router,general_chat` and `route=study nodes=router,study_helper`. Open WebUI chat check not run.
- Story 4.2 will add a bounded review path to this graph (no unbounded loops), reusing the same state, nodes, and endpoint.
