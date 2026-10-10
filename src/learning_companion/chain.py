import logging
from collections.abc import AsyncIterator, Sequence
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables import Runnable
from langchain_xai import ChatXAI
from pydantic import BaseModel

from learning_companion.settings import get_settings

logger = logging.getLogger("uvicorn.error")

SYSTEM_INSTRUCTION = (
    "You are the Learning Companion, a friendly study helper. "
    "Explain ideas clearly in plain language, use short examples, "
    "and check the learner's understanding with a brief follow-up question."
)

# Most recent prior user/assistant messages from the current request that are kept.
MAX_HISTORY_MESSAGES = 6

PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=SYSTEM_INSTRUCTION),
        MessagesPlaceholder("history"),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)

STUDY_HELPER_INSTRUCTION = (
    "You are the Learning Companion's study helper for beginner technical concepts. "
    "Give a concise explanation in plain language, add a small example where useful, "
    "and end with exactly one suggested next learning step. "
    "Do not claim to research, browse, or use course data, and do not guarantee "
    "your answer is correct."
)

STUDY_HELPER_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=STUDY_HELPER_INSTRUCTION),
        MessagesPlaceholder("history"),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)


def to_history(messages: Sequence) -> list[BaseMessage]:
    """Convert request messages (role, content) to the last few user/assistant messages."""
    history: list[BaseMessage] = []
    for m in messages:
        if not isinstance(m.content, str) or not m.content.strip():
            continue
        if m.role == "user":
            history.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            history.append(AIMessage(content=m.content))
    return history[-MAX_HISTORY_MESSAGES:]


def preview_messages(question: str, history: Sequence[BaseMessage] = ()) -> list[BaseMessage]:
    """Return the messages the prompt would send, without calling Grok."""
    return PROMPT.format_messages(question=question, history=list(history))


def select_route(question: str) -> tuple[str, str]:
    """Visible routing rule: a leading /study selects the study helper, else general chat."""
    text = question.lstrip()
    marker = "/study"
    if text.startswith(marker) and (len(text) == len(marker) or text[len(marker)].isspace()):
        return "study", text[len(marker) :].strip()
    return "general", question


def _log_messages(
    question: str, history: Sequence[BaseMessage], route: str = "general", prompt=PROMPT
) -> None:
    if get_settings().app_env == "development":
        messages = prompt.format_messages(question=question, history=list(history))
        roles = ", ".join(m.type for m in messages)
        logger.info("route=%s prompt messages=%d roles=[%s]", route, len(messages), roles)


class ConfigurationError(RuntimeError):
    """Raised when required model settings are missing."""


def _build_model() -> ChatXAI:
    settings = get_settings()
    missing = [
        name
        for name, value in (
            ("GROK_API_KEY", settings.grok_api_key),
            ("GROK_MODEL_NAME", settings.grok_model_name),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(f"Missing setting(s) in .env: {', '.join(missing)}")
    return ChatXAI(
        model=settings.grok_model_name,
        xai_api_key=settings.grok_api_key,
        xai_api_base=settings.grok_api_base_url,
    )


def build_chain() -> Runnable:
    return PROMPT | _build_model() | StrOutputParser()


def build_study_helper_chain() -> Runnable:
    return STUDY_HELPER_PROMPT | _build_model() | StrOutputParser()


async def study_answer(question: str, history: Sequence[BaseMessage] = ()) -> str:
    chain = build_study_helper_chain()
    _log_messages(question, history, "study", STUDY_HELPER_PROMPT)
    return await chain.ainvoke({"question": question, "history": list(history)})


async def stream_study_answer(
    question: str, history: Sequence[BaseMessage] = ()
) -> AsyncIterator[str]:
    chain = build_study_helper_chain()
    _log_messages(question, history, "study", STUDY_HELPER_PROMPT)
    async for text in chain.astream({"question": question, "history": list(history)}):
        if text:
            yield text


async def answer(question: str, history: Sequence[BaseMessage] = ()) -> str:
    chain = build_chain()
    _log_messages(question, history)
    return await chain.ainvoke({"question": question, "history": list(history)})


async def stream_answer(question: str, history: Sequence[BaseMessage] = ()) -> AsyncIterator[str]:
    chain = build_chain()
    _log_messages(question, history)
    async for text in chain.astream({"question": question, "history": list(history)}):
        if text:
            yield text


REVIEW_RULE = (
    "Approve the draft if it is clear, in plain language, and suitable for a beginner. "
    "General-chat drafts should be friendly and concise. Study-helper drafts should give a "
    "short explanation and end with exactly one suggested next learning step. "
    "Otherwise choose improve."
)

REVIEWER_INSTRUCTION = (
    "You review a draft answer once against this rule: "
    + REVIEW_RULE
    + " Reply with a decision (approve or improve) and one short plain-English reason."
)

IMPROVER_INSTRUCTION = (
    "You rewrite a draft answer once to fix the reviewer's reason. Keep it clear, in plain "
    "language, and in the same role. Do not research, browse, plan, or add new claims. "
    "Return only the improved answer."
)


class ReviewResult(BaseModel):
    decision: Literal["approve", "improve"]
    reason: str


REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=REVIEWER_INSTRUCTION),
        HumanMessagePromptTemplate.from_template(
            "Role: {route}\nQuestion: {question}\nDraft answer:\n{draft}"
        ),
    ]
)

IMPROVER_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=IMPROVER_INSTRUCTION),
        HumanMessagePromptTemplate.from_template(
            "Role: {route}\nQuestion: {question}\nDraft answer:\n{draft}\nReviewer reason: {reason}"
        ),
    ]
)


def build_reviewer_chain() -> Runnable:
    return REVIEW_PROMPT | _build_model().with_structured_output(ReviewResult)


def build_improver_chain() -> Runnable:
    return IMPROVER_PROMPT | _build_model() | StrOutputParser()
