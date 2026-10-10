# Story 3.1 — Study-helper LangChain chain

## Purpose

Add a second, separately named chain, the study helper, that explains beginner technical concepts and ends with one next learning step. The existing general-chat chain and endpoint behavior stay unchanged. Choosing between the chains is Story 3.2.

## What this story implements in plain English

- Normal chatting in Open WebUI works exactly as before; greetings and ordinary conversation are unchanged.
- The app gains a study-helper mode that explains a beginner technical idea in plain language, with a small example when useful.
- Every study-helper answer ends with one small suggested next step to learn.
- It uses the same Grok model and the earlier messages of the same chat.
- You can't pick study mode in Open WebUI yet; for now a developer tries it from a local command.

## Prerequisites

- Stories 1.1–2.2 complete: `chain.py` has `SYSTEM_INSTRUCTION`, `PROMPT` (system + `history` placeholder + `{question}`), `to_history`, `build_chain`, `answer`, `stream_answer`; `api.py` calls them for the one chat endpoint.
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.
- Open WebUI connected as before.

## Work to do

Do not change the active route, endpoints, Grok settings, request/response shapes, or history handling. No second app/endpoint/provider/UI, database, retrieval, MCP, tools, LangGraph, or agent. No routing or classification.

1. `src/learning_companion/chain.py`
   - Leave the general-chat `SYSTEM_INSTRUCTION`, `PROMPT`, `build_chain`, `answer`, and `stream_answer` untouched.
   - Add `STUDY_HELPER_INSTRUCTION` (application-owned, separate from user content): give a concise plain-language explanation of the beginner concept, a small example where useful, and end with exactly one suggested next learning step. It must not claim to research, browse, retrieve course data, or guarantee correctness.
   - Add `STUDY_HELPER_PROMPT` with the same shape as `PROMPT` (`SystemMessage`, `MessagesPlaceholder("history")`, `HumanMessagePromptTemplate("{question}")`).
   - Add `build_study_helper_chain()` returning `STUDY_HELPER_PROMPT | model | StrOutputParser()`. Reuse the existing model/config check (extract a small shared helper, e.g. `_build_model()`, so the general chain's behavior doesn't change).
   - Add `async def study_answer(question, history=()) -> str` that invokes the study-helper chain.
2. `src/learning_companion/study_helper_demo.py` (new, development-only)
   - Tiny `python -m learning_companion.study_helper_demo "<question>"` entry point. It prints the payload sent to the LLM (OpenAI-style `messages` JSON with roles and content), then calls `study_answer` and prints the answer. Not wired to any route.
3. `docs/architecture.md`
   - List two chain behaviors: general chat (greetings, ordinary conversation; active) and study helper (beginner concept explanation plus one next step; available, not yet selected). State that selection between them arrives in Story 3.2.

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion.study_helper_demo "What is an API?"
```

Then send one ordinary message (e.g. "Hello!") in the existing Open WebUI chat.

Expected:
- Demo first prints the payload (`system` then `user` message), then a plain explanation of an API and ends with one suggested next step.
- Open WebUI still shows a normal general-chat reply, unchanged from Story 2.2.

## Handover

- Files changed: `src/learning_companion/chain.py`, `src/learning_companion/study_helper_demo.py` (new), `docs/architecture.md`.
- Commands actually run: `uv run ruff format src tests`, `uv run ruff check src tests`, `uv run python -m learning_companion.study_helper_demo "What is an API?"`.
- Results: format/lint pass; demo printed the payload, then an explanation, example and one next step. Open WebUI "Hello!" check not run.
- Story 3.2 will add the visible `/study` route rule in the chat endpoint to select the study-helper chain; no other routing here.
