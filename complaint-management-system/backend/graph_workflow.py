"""
LangGraph workflow assembly.

Linear pipeline (see graph_nodes.py for what each node does):

  classify_input -> extract -> merge_state -> completeness_check
  -> duplicate_check -> risk_assessment -> END

Kept linear rather than branching on error, because every node already checks
`state.get("error")` at its start and no-ops if a prior node failed — this
keeps the graph definition simple while still short-circuiting expensive work
(e.g. no point running risk assessment if extraction already failed).
"""

from langgraph.graph import StateGraph, END

from graph_state import GraphState
from graph_nodes import (
    classify_input_node,
    extract_node,
    merge_state_node,
    completeness_check_node,
    duplicate_check_node,
    risk_assessment_node,
)


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_input", classify_input_node)
    graph.add_node("extract", extract_node)
    graph.add_node("merge_state", merge_state_node)
    graph.add_node("completeness_check", completeness_check_node)
    graph.add_node("duplicate_check", duplicate_check_node)
    graph.add_node("risk_assessment", risk_assessment_node)

    graph.set_entry_point("classify_input")
    graph.add_edge("classify_input", "extract")
    graph.add_edge("extract", "merge_state")
    graph.add_edge("merge_state", "completeness_check")
    graph.add_edge("completeness_check", "duplicate_check")
    graph.add_edge("duplicate_check", "risk_assessment")
    graph.add_edge("risk_assessment", END)

    return graph.compile()


# Compiled once at import time — reused across requests.
complaint_workflow = build_graph()