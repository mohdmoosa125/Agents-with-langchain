# Handout 2.1 — LangChain prompt template

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-2-1-langchain-prompt-template.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Story 1.1, existing code, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve existing work, routes, settings, and the working Open WebUI connection.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets what changes for a participant using the chatbot, without framework jargon.

This story follows the seed and makes its LangChain flow reusable and understandable. It must preserve the same `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions` endpoints, the same normal JSON and SSE response behavior, the same Grok settings, and the same Open WebUI connection. Do not create a command-line-only chatbot, a second chat path, conversation history, a database, persistent memory, RAG, tools, MCP, LangGraph, or a new frontend.

Require the implementer to replace the seed’s fixed latest-message prompt with a small LangChain chat prompt that has two clearly separate parts: a stable Learning Companion system instruction owned by the application and the current user message. Use suitable LangChain message and prompt-template abstractions. Do not concatenate a large ad-hoc string.

For this story, use only the latest supported user message from the OpenAI-compatible request. Treat a request-supplied `system` message as user-provided content, not as a replacement for the application’s stable instruction. Do not introduce history handling yet; Story 2.2 adds it.

Require the existing prompt → Grok model → text-output chain to be used for both the normal and streaming paths. Keep the request and response OpenAI-compatible; do not add custom message formats or Open WebUI plugins. Add a compact development-only log or inspectable helper that shows message roles and counts, never API keys or full hidden instructions. Update `docs/architecture.md` with the message flow and the deliberate no-persistence boundary.

Keep verification small: format/lint and one ordinary question through the existing Open WebUI chat. Confirm that the fixed application instruction and latest user message reach the LangChain prompt in the expected order and that Open WebUI still renders the answer. Do not add an evaluation harness, broad test suite, production memory, or security programme.

The story must name the files it changes, commands actually run, the expected Open WebUI result, and what Story 2.2 will extend. After creating the story, report its path only.
