# Story 3.2 — Visible Python routing between the two chains

## Purpose

Make both chains reachable from the same Open WebUI chat through one plain, visible Python rule: a latest user message starting with `/study` uses the study-helper chain; anything else uses the general-chat chain.

## What this story implements in plain English

- Type a normal message and you get the usual Learning Companion chat reply, as before.
- Start a message with `/study` (e.g. `/study Explain what an API is`) and you get a study-helper answer: a plain explanation and one next step.
- Both go through the same Open WebUI chat and the same earlier messages; only the app's instructions differ.
- Each reply starts with a short label, `[general]` or `[study]`, so you can see which path ran.
- This is a simple if/else the app checks itself, not an AI deciding. Session 4 will replace it with a more formal route.

## Prerequisites

- Stories 1.1–3.1 complete: `chain.py` has `build_chain`/`answer`/`stream_answer` (general), `build_study_helper_chain`/`study_answer` (study), `to_history`; `api.py` builds `question` and `history` and handles JSON and SSE.
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.
- Open WebUI connected as before.

## Work to do

Preserve the Open WebUI connection, endpoints, Grok settings, history handling (Story 2.2), and JSON/SSE response shapes. No LLM classification, LangGraph, extra specialists, review steps, loops, custom response fields, or Open WebUI plugins.

1. `src/learning_companion/chain.py`
   - Add `select_route(question) -> tuple[str, str]`: if `question.lstrip()` starts with `/study` (marker followed by whitespace or end), return `("study", question with only that leading marker removed, stripped)`; else `("general", question)`.
   - Add `stream_study_answer(question, history=())` mirroring `stream_answer` for the study-helper chain, so streaming works for both routes.
   - Generalise the dev log helper to include the route: `route=study prompt messages=N roles=[...]` (development only; no keys, instruction text, or message bodies).
2. `src/learning_companion/api.py`
   - After computing `question` and `history`, call `select_route`; dispatch to `answer`/`stream_answer` or `study_answer`/`stream_study_answer`.
   - Prefix the answer text with a short label (`[general] ` or `[study] `). In normal mode, prefix the full text; in streaming, emit the label as the first content chunk. The response shapes stay unchanged.
   - Edge case: a bare `/study` with no question falls through to the study chain with an empty question, which is acceptable here.
3. `docs/architecture.md`
   - Document the `/study` rule, the selected-chain path, the route label and dev log, and the boundary: deterministic application routing, not LLM classification, LangGraph, or multi-agent orchestration.

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion
```

In the existing Open WebUI chat:

1. Send `Hello!`
2. Send `/study Explain what an API is`

Inspect the server log (`%TEMP%\lc.err` if started in the background, otherwise the terminal).

Expected:
- Message 1: normal reply starting with `[general]`; log shows `route=general`.
- Message 2: reply starting with `[study]` with a clear plain explanation and one next step; log shows `route=study`. The `/study` marker is not in the question sent to the model.
- Both replies arrive through the same endpoint, in the same chat, with streaming on.

## Handover

- Files changed: `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`.
- Commands actually run: `uv run ruff format src tests`, `uv run ruff check src tests`, `select_route` check, `uv run python -m learning_companion`, curl POSTs (`Hello!`, `/study Explain what an API is`; stream on and off).
- Results: JSON replies started with `[general]` and `[study]`; log showed `route=general` and `route=study` for both stream modes. Open WebUI chat check not run.
- Story 4.1 will replace this Python if/else with an explicit LangGraph route inside the app, keeping the same endpoint and chains.
