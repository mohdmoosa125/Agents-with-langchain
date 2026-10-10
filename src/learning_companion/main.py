"""Entry point: exposes the FastAPI `app` and starts the service.

Flow: Open WebUI -> POST /v1/chat/completions (api.py) -> LangGraph router (graph.py)
-> general_chat | study_helper LangChain chain (chain.py) -> Grok.
"""

import uvicorn

from learning_companion.api import app
from learning_companion.settings import get_settings

__all__ = ["app", "main"]


def main() -> None:
    settings = get_settings()
    uvicorn.run("learning_companion.main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
