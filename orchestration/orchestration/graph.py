"""Grafo LangGraph del pipeline PQRS."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from orchestration.deps import OrchestrationDeps, default_deps
from orchestration.nodes import (
    _after_classify,
    ingest_node,
    make_classify_node,
    make_prioritize_node,
    make_route_node,
    reject_node,
    warehouse_node,
)
from orchestration.state import AgentState


def build_graph(deps: OrchestrationDeps | None = None):
    """Compila ingest → classify → reject | (prioritize → route → warehouse)."""
    d = deps if deps is not None else default_deps()
    g = StateGraph(AgentState)
    g.add_node("ingest", ingest_node)
    g.add_node("classify", make_classify_node(d))
    g.add_node("reject", reject_node)
    g.add_node("prioritize", make_prioritize_node(d))
    g.add_node("route", make_route_node(d))
    g.add_node("warehouse", warehouse_node)
    g.set_entry_point("ingest")
    g.add_edge("ingest", "classify")
    g.add_conditional_edges(
        "classify",
        _after_classify,
        {"reject": "reject", "continue": "prioritize"},
    )
    g.add_edge("prioritize", "route")
    g.add_edge("route", "warehouse")
    g.add_edge("reject", END)
    g.add_edge("warehouse", END)
    return g.compile()


__all__ = ["build_graph", "AgentState"]
