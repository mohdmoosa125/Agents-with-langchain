# Story 2.1 — LangChain prompt template

## Purpose

Make the seed's LangChain flow reusable and easy to inspect: a stable application-owned Learning Companion instruction plus the current user message, built with LangChain chat-prompt abstractions. Same endpoints, settings, and Open WebUI connection as Story 1.1.

## What this story implements in plain English

- Chatting in Open WebUI looks and works the same as before.
- The Learning Companion's guidance is fixed by the app; nothing you type in the chat can replace it.
- Each reply is based on your latest message only; earlier turns are not remembered yet.
- If a chat sends its own "system" text, it is treated as part of what you said, not as the app's rules.
- In development, the app log shows which message roles went to the model (never keys or the hidden instruction).

## Prerequisites

- Story 1.1 complete: service starts, `/health` and `/v1/models` work, Open WebUI connected.
- Existing code reviewed: `chain.py` (already has `ChatPromptTemplate` with `{question}`), `api.py` (picks the latest `user` message; ignores `system`/`assistant`), `settings.py` (`GROK_*`).
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.

## Work to do

Preserve `GET /health`, `GET /v1/models`, `POST /v1/chat/completions`, JSON and SSE behavior, Grok settings, and the Open WebUI connection. No new dependencies, history, database, memory, RAG, tools, MCP, LangGraph, CLI chatbot, second chat path, or frontend.

1. `src/learning_companion/chain.py`
   - Keep `SYSTEM_INSTRUCTION` as the single application-owned constant.
   - Build the prompt with `ChatPromptTemplate.from_messages([SystemMessage(content=SYSTEM_INSTRUCTION), HumanMessagePromptTemplate.from_template("{question}")])`. The system part is a fixed `SystemMessage`, so braces or text in it are never templated, and no string concatenation.
   - Keep one chain `prompt | ChatXAI | StrOutputParser()`, used by both `answer` and `stream_answer`.
   - Add `preview_messages(question) -> list[BaseMessage]` using `PROMPT.format_messages(question=question)` (inspectable without calling Grok).
   - Add a dev-only log (when `APP_ENV=development`, via `logging`) from one helper, e.g. `describe_messages`: roles in order and count, e.g. `prompt messages=2 roles=[system, human]`. Never log keys, the system text, or full user text.
2. `src/learning_companion/api.py`
   - Keep selecting only the latest `user` message. A request `system` message stays ignored as an instruction: it is not passed as the application's system message. Optionally note in a comment that it is user-supplied content.
   - No history handling; leave the response shapes unchanged.
3. `docs/architecture.md`
   - Add the message flow: `Open WebUI request → latest user message → [SystemMessage(app instruction), HumanMessage(user)] → Grok → text → JSON/SSE`.
   - State the deliberate boundary: no persistence, history, or memory in this story; request `system` messages are not trusted as the app instruction.

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion
```

Then in the existing Open WebUI chat, send one ordinary question (e.g. "What is a variable?").

Expected: a normal Learning Companion answer renders in Open WebUI; the dev log shows two messages in order `system`, `human`; the log contains no key or instruction text. Optionally confirm order with `preview_messages("hi")` in a one-line `uv run python -c`.

## Handover

- Files changed: `src/learning_companion/chain.py`, `src/learning_companion/api.py` (comment/minimal only), `docs/architecture.md`.
- Commands actually run: `uv run ruff format src tests`, `uv run ruff check src tests`, `preview_messages` check (`['system', 'human']`), a POST to `/v1/chat/completions` (log showed `messages=2 roles=[system, human]`).
- Open WebUI result: not run in this session.
- Story 2.2 will extend the same prompt with a history placeholder and conversation-history handling from the incoming `messages` list.
