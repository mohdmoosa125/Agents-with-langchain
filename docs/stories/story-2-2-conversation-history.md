# Story 2.2 — Conversation history from Open WebUI

## Purpose

Let a follow-up question use earlier messages of the same chat. Open WebUI already sends the active chat's messages with each request; the app adds a short, recent slice of them to the existing prompt. Nothing is stored.

## What this story implements in plain English

- You can ask a first question, then a follow-up like "give another example", and the answer builds on the first.
- The app only looks at the most recent few messages Open WebUI sends; older ones are dropped.
- Close or switch chats and the app remembers nothing; it saves nothing between requests.
- The Learning Companion's guidance stays fixed; a "system" message in the chat cannot replace it.
- In development, the log shows message roles and count, never keys, hidden instructions, or message text.

## Prerequisites

- Story 2.1 complete: `chain.py` has `PROMPT` = `SystemMessage` + `HumanMessagePromptTemplate("{question}")`, `preview_messages`, and the dev log; `api.py` passes only the latest `user` message.
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.
- Open WebUI connected as in Story 1.1.

## Work to do

Preserve `GET /health`, `GET /v1/models`, `POST /v1/chat/completions`, request/response shapes, JSON and SSE behavior, Grok settings, and the Open WebUI connection. No database, persistent memory, RAG, tools, MCP, routing, LangGraph, new endpoint, or new UI.

1. `src/learning_companion/chain.py`
   - Add `MAX_HISTORY_MESSAGES = 6` (documented constant: most recent prior `user`/`assistant` messages kept).
   - Change `PROMPT` to: `SystemMessage(SYSTEM_INSTRUCTION)`, `MessagesPlaceholder("history")`, `HumanMessagePromptTemplate("{question}")`.
   - Add `to_history(messages) -> list[BaseMessage]`: keep only `user`/`assistant` messages with non-empty text content, in original order, map to `HumanMessage`/`AIMessage`, return the last `MAX_HISTORY_MESSAGES`. Ignore `system` and anything unsupported.
   - `answer` and `stream_answer` take `question` and `history`, invoking the same `PROMPT | ChatXAI | StrOutputParser()` chain with `{"history": history, "question": question}`.
   - Update `preview_messages(question, history=())` and the dev log (development only) to show count and role sequence, e.g. `prompt messages=4 roles=[system, human, ai, human]`. No text, keys, or system instruction.
2. `src/learning_companion/api.py`
   - Latest `user` message stays the question. History = messages before it, passed to `to_history`. Messages after it (if any) are ignored.
   - Response shapes unchanged. Request `system` messages stay ignored.
3. `docs/architecture.md`
   - Update message flow: `[SystemMessage, history (≤ 6 recent user/assistant messages from this request), latest HumanMessage] → Grok`.
   - State the limit and the boundary: request-provided only, nothing saved after the request, no cross-session memory. Story 2.1's "history arrives in Story 2.2" note becomes current behavior.

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion
```

In a new Open WebUI chat:

1. Send: "Explain what a variable is in one sentence."
2. Send: "Give me an example of that in Python."

Expected: the second answer is a Python variable example, so the earlier context was used. The dev log for the second request shows `prompt messages=4 roles=[system, human, ai, human]`; the first shows `messages=2 roles=[system, human]`. No keys, instruction text, or message bodies are logged. Starting a new chat gives no memory of the earlier one.

## Handover

- Files changed: `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`.
- Commands actually run: `uv run ruff format src tests`, `uv run ruff check src tests`, a one-line `to_history`/`preview_messages` check (roles `['system', 'human', 'ai', 'human']`).
- Two-turn Open WebUI result: not run in this session; follow the steps in Completion checks.
- Story 3.1 will extend this flow; it builds on the same prompt and request-provided messages, adding no storage in this story.
