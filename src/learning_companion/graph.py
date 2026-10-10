"""LangGraph workflow: router -> answer node -> reviewer -> (improver -> reviewer) -> END.

At most one improvement: the reviewer ends the graph once revision_count is 1.
"""

import logging
from typing import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from learning_companion.chain import (
    answer,
    build_improver_chain,
    build_reviewer_chain,
    select_route,
    study_answer,
)
from learning_companion.settings import get_settings

logger = logging.getLogger("uvicorn.error")

ANSWER_NODES = {"general": "general_chat", "study": "study_helper"}


class GraphState(TypedDict, total=False):
    question: str  # current user message
    messages: list[BaseMessage]  # earlier user/assistant messages of this chat
    route: str  # "general" or "study", written by the router
    draft_answer: str  # answer under review; replaced once by the improver
    review_decision: str  # "approve" or "improve", from the reviewer
    review_reason: str  # one short sentence explaining the decision
    revision_count: int  # improvements done so far (0 or 1)
    final_answer: str  # answer sent to Open WebUI, set when the graph ends


def _trace(state: GraphState, decision: str) -> None:
    if get_settings().app_env == "development":
        revisions = state["revision_count"]
        nodes = ["router", ANSWER_NODES[state["route"]], "reviewer"]
        if revisions:
            nodes += ["improver", "reviewer"]
        logger.info(
            "route=%s decision=%s revisions=%d nodes=%s",
            state["route"],
            decision,
            revisions,
            ",".join(nodes),
        )


def router(state: GraphState) -> GraphState:
    """Ordinary Python (no model): the existing /study rule."""
    route, question = select_route(state["question"])
    return {"route": route, "question": question, "revision_count": 0}


async def general_chat(state: GraphState) -> GraphState:
    return {"draft_answer": await answer(state["question"], state["messages"])}


async def study_helper(state: GraphState) -> GraphState:
    return {"draft_answer": await study_answer(state["question"], state["messages"])}


async def reviewer(state: GraphState) -> GraphState:
    result = await build_reviewer_chain().ainvoke(
        {"route": state["route"], "question": state["question"], "draft": state["draft_answer"]}
    )
    decision = "approve" if state["revision_count"] >= 1 else result.decision
    update: GraphState = {"review_decision": decision, "review_reason": result.reason}
    if decision == "approve":
        update["final_answer"] = state["draft_answer"]
        _trace(state, decision)
    return update


async def improver(state: GraphState) -> GraphState:
    improved = await build_improver_chain().ainvoke(
        {
            "route": state["route"],
            "question": state["question"],
            "draft": state["draft_answer"],
            "reason": state["review_reason"],
        }
    )
    return {"draft_answer": improved, "revision_count": state["revision_count"] + 1}


def after_reviewer(state: GraphState) -> str:
    return "improver" if state["review_decision"] == "improve" else END


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("router", router)
    graph.add_node("general_chat", general_chat)
    graph.add_node("study_helper", study_helper)
    graph.add_node("reviewer", reviewer)
    graph.add_node("improver", improver)
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", lambda s: s["route"], ANSWER_NODES)
    graph.add_edge("general_chat", "reviewer")
    graph.add_edge("study_helper", "reviewer")
    graph.add_conditional_edges("reviewer", after_reviewer, {"improver": "improver", END: END})
    graph.add_edge("improver", "reviewer")
    return graph.compile()


GRAPH = build_graph()
