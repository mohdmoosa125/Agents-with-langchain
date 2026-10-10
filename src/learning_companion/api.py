import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from learning_companion.chain import ConfigurationError, build_chain, to_history
from learning_companion.graph import GRAPH
from learning_companion.settings import get_settings

app = FastAPI(title="Learning Companion Chatbot")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False


def _model_name(request_model: str) -> str:
    return get_settings().grok_model_name or request_model


def _config_error(exc: ConfigurationError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"message": str(exc), "type": "configuration_error"}},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    name = get_settings().grok_model_name
    data = [{"id": name, "object": "model", "created": 0, "owned_by": "xai"}] if name else []
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # Latest user message + recent prior user/assistant messages; request "system" is ignored.
    last = next(
        (i for i in range(len(request.messages) - 1, -1, -1) if request.messages[i].role == "user"),
        None,
    )
    question = request.messages[last].content if last is not None else ""
    history = to_history(request.messages[:last]) if last is not None else []
    state = {"question": question, "messages": history}
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    model = _model_name(request.model)

    try:
        if not request.stream:
            result = await GRAPH.ainvoke(state)
            text = f"[{result['route']}] {result['final_answer']}"
            return {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            }
        build_chain()  # fail fast on missing configuration before streaming starts
    except ConfigurationError as exc:
        return _config_error(exc)

    def chunk(delta: dict, finish_reason: str | None = None) -> str:
        payload = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        return f"data: {json.dumps(payload)}\n\n"

    async def events() -> AsyncIterator[str]:
        yield chunk({"role": "assistant"})
        # The draft may be replaced by the improver, so send only the final answer.
        result = await GRAPH.ainvoke(state)
        yield chunk({"content": f"[{result['route']}] "})
        for i in range(0, len(result["final_answer"]), 40):
            yield chunk({"content": result["final_answer"][i : i + 40]})
        yield chunk({}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
