# Story 4.2 — Bounded answer review and improvement

## Purpose

Extend the existing LangGraph so each draft answer is checked once, improved once only if needed, and then returned. The router, endpoints, Open WebUI connection, Grok settings, history handling, and JSON/SSE shapes stay as they are.

## What this story implements in plain English

- Your question still goes in and an answer still comes back in Open WebUI, as before.
- The app now writes a draft answer first, then a reviewer checks it once against a short classroom rule.
- If the draft is fine, it is sent as is. If it needs work, an improver rewrites it once.
- After that one rewrite, the reviewer takes a final look and the answer is sent. It never goes round again, so there is at most one improvement.
- In development, a short trace shows the route, the review decision, the revision count, and the steps that ran.

## Prerequisites

- Stories 1.1–4.1 complete: `graph.py` has `GraphState`, `router`, `general_chat`, `study_helper`, and the compiled `GRAPH`; `chain.py` has both chains, `_build_model`, and `select_route`; `api.py` runs the graph for JSON and SSE.
- `.env` has valid `GROK_API_KEY` and `GROK_MODEL_NAME`. No `docs/config.yaml` exists.
- Open WebUI connected as before.

## Work to do

Preserve the endpoints, Open WebUI connection, request/response shapes, Grok settings, history conversion, and the `/study` routing path. No database, persistence, RAG, web search, tools, MCP, human approval, extra agents, planner, other loops or retries, or custom Open WebUI events.

Terms: the reviewer and improver are small LLM-powered specialist nodes (specialist agents for this classroom example). The router stays ordinary Python, not an agent. MCP could be a future node; it is not part of this story.

**New state fields (plain English)**

| Field | Meaning |
|-------|---------|
| `draft_answer` | The current answer text under review; written by an answer node, then replaced by the improver |
| `review_decision` | `approve` or `improve`, from the reviewer |
| `review_reason` | One short sentence from the reviewer explaining the decision |
| `revision_count` | How many improvements have happened (0 or 1); starts at 0 |
| `final_answer` | The answer sent to Open WebUI; set by the reviewer when the graph is about to end |

Existing fields (`question`, `messages`, `route`) are kept. `answer` is replaced by `draft_answer` and `final_answer`.

**Graph**

```
START → router ─(general)→ general_chat ─┐
              └(study)───→ study_helper ─┴→ reviewer ─(approve, or revision_count=1)→ END
                                              ↑   └(improve and revision_count=0)→ improver
                                              └──────────────────────────────────────┘
```

Edge rules: each answer node → `reviewer`; `reviewer` → `END` if the decision is `approve` or `revision_count` is 1; `reviewer` → `improver` only if the decision is `improve` and `revision_count` is 0; `improver` → `reviewer`. This one cycle gives a maximum of one improvement.

1. `src/learning_companion/chain.py`
   - Add `REVIEW_RULE` (short fixed classroom rule: clear, plain-language, beginner-appropriate, right role for the route; study answers have one next step; general answers are friendly and concise).
   - Add `ReviewResult` (Pydantic: `decision: Literal["approve", "improve"]`, `reason: str`) and `build_reviewer_chain()` = review prompt → `_build_model().with_structured_output(ReviewResult)`.
   - Add `build_improver_chain()` = improver prompt → `_build_model()` → `StrOutputParser()`; it rewrites the draft once using the reviewer reason. No tools, browsing, retrieval, planning, or routing.
   - Keep the instructions application-owned and separate from user content.
2. `src/learning_companion/graph.py`
   - Extend `GraphState` with the five fields above.
   - `general_chat` / `study_helper` write `draft_answer` (not `answer`) and set `revision_count` to 0.
   - `reviewer` node: calls the reviewer chain on the draft and route. If `revision_count` is 1, force `approve`. When ending (approve or count 1), set `final_answer = draft_answer`.
   - `improver` node: rewrites the draft once, writes `draft_answer`, sets `revision_count` to 1.
   - Wire the edges above with `add_edge` and one `add_conditional_edges` on `reviewer`. Update `ANSWER_NODES` handling accordingly.
   - Dev-only trace (`APP_ENV=development`), one line per run, e.g. `route=study decision=improve revisions=1 nodes=router,study_helper,reviewer,improver,reviewer`. No keys, prompts, or message text.
3. `src/learning_companion/api.py`
   - Normal mode: return `[route] final_answer`.
   - Streaming: the draft may be replaced, so do not stream draft tokens. After the graph finishes, send the `[route]` label and the `final_answer` as SSE content chunks (same chunk shape, then stop chunk and `data: [DONE]`).
   - Keep the configuration-error handling.
4. `docs/architecture.md`
   - Add the two nodes, new state fields, full graph diagram, edge rules, the one-revision limit, and the scope boundary (no tools, MCP, persistence, other loops).

## Completion checks

Run only:

```
uv run ruff format src tests
uv run ruff check src tests
uv run python -m learning_companion
```

In the existing Open WebUI chat:

1. Send an ordinary question, e.g. `Hello!`.
2. Send a `/study` question likely to benefit from clearer wording, e.g. `/study Explain recursion, middleware and idempotency in one go`.

Expected:
- Message 1: `[general]` reply shown in Open WebUI; trace `route=general decision=approve revisions=0 nodes=router,general_chat,reviewer`.
- Message 2: `[study]` reply shown in Open WebUI with a clear explanation and one next step; trace shows the path `router,study_helper,reviewer,improver,reviewer` with `revisions=1` if the reviewer asked for improvement. If the reviewer approves directly, the path is `router,study_helper,reviewer` (try a harder question to see the improve path).
- Never more than one `improver` in a trace.

Final capstone outcome: one Open WebUI chat, answered through one OpenAI-compatible endpoint by a LangGraph that routes to a general or study specialist, checks the draft once, improves it at most once, and returns the result.

## Handover

- Files changed: `src/learning_companion/chain.py`, `src/learning_companion/graph.py`, `src/learning_companion/api.py`, `docs/architecture.md`.
- Commands actually run: `uv run ruff format src tests`, `uv run ruff check src tests`, `uv run python -m learning_companion`, curl POSTs (`Hello!`, a hard `/study` question; stream on and off), and a one-off graph run with a stubbed reviewer returning `improve`.
- Results: both routes returned `[general]`/`[study]` replies in JSON and SSE; traces `route=general decision=approve revisions=0 nodes=router,general_chat,reviewer` and `route=study decision=approve revisions=0 nodes=router,study_helper,reviewer`. The stubbed run took reviewer → improver → reviewer and ended with `revision_count=1` (one improvement only). Open WebUI chat check not run.
- This is the last story: the capstone is complete.
