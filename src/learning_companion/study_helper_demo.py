"""Development-only: run the study-helper chain locally. Not wired to any route."""

import asyncio
import json
import sys

from langchain_core.messages import convert_to_openai_messages

from learning_companion.chain import STUDY_HELPER_PROMPT, ConfigurationError, study_answer


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        sys.exit('Usage: python -m learning_companion.study_helper_demo "<question>"')
    messages = STUDY_HELPER_PROMPT.format_messages(question=question, history=[])
    payload = {"messages": convert_to_openai_messages(messages)}
    print("--- payload sent to LLM ---")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("--- answer ---")
    try:
        print(asyncio.run(study_answer(question)))
    except ConfigurationError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
