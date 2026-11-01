from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.discovery_agent import discover_products
from app.agents.explanation_agent import explain_recommendations
from app.agents.intent_agent import understand_intent
from app.agents.ranking_agent import rank_candidates
from app.agents.review_agent import analyze_reviews
from app.agents.verification_agent import verify_recommendations
from app.services.normalization import deduplicate_products


class WorkflowState(TypedDict):
    query: str
    parsed_requirements: dict
    provider_results: list
    normalized_products: list
    review_analysis: list
    candidate_rankings: list
    verification_results: list
    final_recommendations: list
    errors: list
    status: str


def _intent_node(state: WorkflowState) -> WorkflowState:
    state["parsed_requirements"] = understand_intent(state["query"])
    return state


def _discovery_node(state: WorkflowState) -> WorkflowState:
    candidates = discover_products(state["parsed_requirements"])
    state["provider_results"] = candidates
    state["normalized_products"] = deduplicate_products(candidates)
    return state


def _review_node(state: WorkflowState) -> WorkflowState:
    state["review_analysis"] = analyze_reviews(state["normalized_products"])
    return state


def _ranking_node(state: WorkflowState) -> WorkflowState:
    state["candidate_rankings"] = rank_candidates(state["normalized_products"], state["parsed_requirements"])
    return state


def _verification_node(state: WorkflowState) -> WorkflowState:
    state["verification_results"] = verify_recommendations(state["candidate_rankings"], state["normalized_products"])
    state["status"] = "demo_data"
    return state


def _explanation_node(state: WorkflowState) -> WorkflowState:
    state["final_recommendations"] = explain_recommendations(
        state["verification_results"], state["parsed_requirements"]
    )
    return state


builder = StateGraph(WorkflowState)
builder.add_node("intent_understanding", _intent_node)
builder.add_node("product_discovery", _discovery_node)
builder.add_node("review_analysis", _review_node)
builder.add_node("recommendation_ranking", _ranking_node)
builder.add_node("verification", _verification_node)
builder.add_node("explanation_generation", _explanation_node)

builder.set_entry_point("intent_understanding")
builder.add_edge("intent_understanding", "product_discovery")
builder.add_edge("product_discovery", "review_analysis")
builder.add_edge("review_analysis", "recommendation_ranking")
builder.add_edge("recommendation_ranking", "verification")
builder.add_edge("verification", "explanation_generation")
builder.add_edge("explanation_generation", END)

WORKFLOW = builder.compile()


def run_workflow(query: str):
    initial_state: WorkflowState = {
        "query": query,
        "parsed_requirements": {},
        "provider_results": [],
        "normalized_products": [],
        "review_analysis": [],
        "candidate_rankings": [],
        "verification_results": [],
        "final_recommendations": [],
        "errors": [],
        "status": "demo_data",
    }
    result = WORKFLOW.invoke(initial_state)
    return {
        "query": query,
        "parsed_requirements": result.get("parsed_requirements", {}),
        "products": result.get("normalized_products", []),
        "review_analysis": result.get("review_analysis", []),
        "recommendations": result.get("final_recommendations") or result.get("verification_results") or [],
        "status": "live_web",
    }
