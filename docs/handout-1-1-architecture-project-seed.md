# Handout 1.1 — Architecture, LangChain project seed, and Open WebUI connection

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-1-1-architecture-project-seed.md`. This is a story for a later coding assistant to implement. Do **not** implement the project, install dependencies, or change application code now. Create only this story file and preserve existing work.

Read `docs/config.yaml` if it exists, `docs/architecture.md` if present, the repository layout, and existing stories first. Resolve a configured project path when one exists; otherwise use the repository root. This is the first story in a short, beginner LangChain and LangGraph classroom course. Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets what a participant will be able to do after this story, without framework jargon.

The story must first create or update `docs/architecture.md` and ask the instructor to approve it before creating the project seed. Before approval, do not create seed files, install dependencies, or scaffold code. Resume the same story only after explicit approval. The architecture must record this single classroom flow:

`Open WebUI → this local application’s OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`.

Record that Open WebUI is already installed and working for participants. It is the supplied chat client only. Participants must not reinstall, reconfigure, modify, or build Open WebUI. The capstone is a small **Learning Companion Chatbot**, not a custom frontend or a second demonstration application. Keep boundaries light: API keys stay in an untracked `.env`; application instructions stay separate from user messages; and this course does not cover authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, or extensive tests.

After approval, seed a Python 3.12 and UV project with FastAPI, Pydantic settings, `langchain`, the Grok-compatible LangChain provider integration, Uvicorn, Ruff, and a minimal test runner. Create a `src/learning_companion/` application package, `tests/`, `.env.example`, `.gitignore`, `pyproject.toml`, `uv.lock`, and `README.md`. The application must start without a real API key and return an honest configuration error only when a model call is attempted.

Create the project’s canonical `.env.example` with these exact setting names: `APP_ENV=development`; blank `GROK_API_KEY`; `GROK_API_BASE_URL=https://api.x.ai/v1`; blank `GROK_MODEL_NAME`; `HOST=127.0.0.1`; and `PORT=8000`. Document that the instructor supplies the model name and participants place their real key only in untracked `.env`. Do not add Claude, alternate-provider, database, or production configuration.

Require a minimal FastAPI application with `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions`. The chat route must accept the normal OpenAI-compatible chat-completions request shape needed by the existing Open WebUI connection: `model`, a list of text messages using `system`, `user`, or `assistant` roles, and `stream`. It must return normal OpenAI-compatible JSON when `stream` is false and normal text-only OpenAI-compatible SSE chunks followed by a stop chunk and `[DONE]` when `stream` is true. Do not create custom Open WebUI events, a second chat route, or a custom browser UI.

For this seed only, create one small LangChain prompt → Grok chat model → text-output flow with a fixed Learning Companion instruction and the latest user message. Use it behind the same chat endpoint for both normal and streaming requests. `GET /v1/models` must expose the configured Grok model as the model Open WebUI can select. Keep the implementation deliberately small; full prompt construction and conversation history are Story 2.1.

The story must instruct the implementer to run only lightweight checks: format/lint the changed code, start the API, verify `/health`, verify model discovery, and make one normal and one streaming request through the existing Open WebUI setup. The expected classroom result is one Grok reply visible in Open WebUI. If the participant’s existing Open WebUI connection needs a local base URL or model selection change, document only that application-side connection value; do not alter Open WebUI itself. Do not add a broad test suite, tool calls, LangGraph, agents, MCP, or advanced streaming features.

The story must name the files it creates or changes, the commands the implementer actually runs, the expected Open WebUI result, and what Story 2.1 will extend. After creating the story, report its path only.
