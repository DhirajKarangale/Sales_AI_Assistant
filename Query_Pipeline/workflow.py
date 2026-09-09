import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langgraph.graph import StateGraph, START, END
from Query_Pipeline.state import PipelineState
from Query_Pipeline.query_optimizer import (
    node_fetch_salesperson_info,
    node_normalize_query,
    node_extract_questions,
)
from Query_Pipeline.db_dependency import node_detect_db_dependencies
from Query_Pipeline.db_agent import node_db_agent_process
from Query_Pipeline.response_generator import node_generate_response


def route_after_fetch(state: PipelineState) -> str:
    """Route after fetching salesperson info.
    
    If error is set (salesperson not found), go to END.
    Otherwise, proceed to query normalization.
    """
    if state.get("error"):
        return "end"
    return "normalize_query"


def route_after_dependencies(state: PipelineState) -> str:
    """Route after DB dependency detection.
    
    If any question needs DB data, go to db_agent_process.
    Otherwise, skip directly to response generation.
    """
    questions = state.get("questions", [])
    if any(q.get("needs_db") for q in questions):
        return "db_agent_process"
    return "generate_response"


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow for the query-response pipeline."""
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("fetch_salesperson_info", node_fetch_salesperson_info)
    workflow.add_node("normalize_query", node_normalize_query)
    workflow.add_node("extract_questions", node_extract_questions)
    workflow.add_node("detect_db_dependencies", node_detect_db_dependencies)
    workflow.add_node("db_agent_process", node_db_agent_process)
    workflow.add_node("generate_response", node_generate_response)

    # Entry edge
    workflow.add_edge(START, "fetch_salesperson_info")

    # Conditional edge: check if salesperson was found
    workflow.add_conditional_edges(
        "fetch_salesperson_info",
        route_after_fetch,
        {
            "normalize_query": "normalize_query",
            "end": END,
        }
    )

    # Linear edges through query optimization
    workflow.add_edge("normalize_query", "extract_questions")
    workflow.add_edge("extract_questions", "detect_db_dependencies")

    # Conditional edge: DB dependency routing
    workflow.add_conditional_edges(
        "detect_db_dependencies",
        route_after_dependencies,
        {
            "db_agent_process": "db_agent_process",
            "generate_response": "generate_response",
        }
    )

    # DB agent always flows to response generation
    workflow.add_edge("db_agent_process", "generate_response")

    # Response generation completes the pipeline
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# Singleton compiled graph
_compiled_workflow = None


def get_workflow():
    """Get or build the compiled workflow (singleton)."""
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = build_workflow()
    return _compiled_workflow


def run_pipeline(salesperson_id: str, query: str) -> str:
    """Execute the complete query-response pipeline.
    
    Args:
        salesperson_id: UUID string of the salesperson.
        query: Natural language query from the salesperson.
    
    Returns:
        The final response string, or an error message.
    """

    app = get_workflow()

    initial_state = {
        "salesperson_id": salesperson_id,
        "raw_query": query,
    }

    final_state = app.invoke(initial_state)

    if final_state.get("error"):
        print(f"\n[Pipeline] ERROR: {final_state['error']}")
        return f"Error: {final_state['error']}"

    response = final_state.get("final_response", "No response generated.")

    print("\n" + "=" * 70)
    print("QUERY PIPELINE — COMPLETE")
    print("=" * 70)

    return response
