from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents import extractor_agent, validator_agent, normalizer_agent

class EventState(TypedDict):
    raw_event: dict
    cleaned_data: str
    extracted_entities: dict
    validation_status: str
    validation_feedback: str
    retry_count: int
    normalized_event: dict

def extractor_node(state: EventState) -> dict:
    feedback = state.get("validation_feedback")
    extracted = extractor_agent(state["raw_event"], state["cleaned_data"], feedback)
    return {
        "extracted_entities": extracted,
        "retry_count": state.get("retry_count", 0) + 1
    }

def validator_node(state: EventState) -> dict:
    res = validator_agent(state["cleaned_data"], state["extracted_entities"])
    if res.get("valid"):
        return {
            "validation_status": "PASS",
            "validation_feedback": ""
        }
    else:
        return {
            "validation_status": "FAIL",
            "validation_feedback": res.get("feedback", "Unknown hallucination")
        }

def normalizer_node(state: EventState) -> dict:
    normalized = normalizer_agent(state["extracted_entities"], state["cleaned_data"])
    normalized["source_id"] = state["raw_event"].get("source_id")
    return {"normalized_event": normalized}

def fallback_node(state: EventState) -> dict:
    fallback_entities = {
        "event_type": state["raw_event"].get("event_type"),
        "participants": state["raw_event"].get("participants", []),
        "customer": None,
        "project": None,
        "salesperson": None,
        "summary": state["raw_event"].get("subject", ""),
        "complete_cleaned_data": state["cleaned_data"]
    }
    return {"extracted_entities": fallback_entities}

def route_validation(state: EventState) -> str:
    if state.get("validation_status") == "PASS":
        return "normalizer"
    
    if state.get("retry_count", 0) >= 2:
        return "fallback"
        
    return "extractor"

def build_workflow():
    workflow = StateGraph(EventState)
    
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("normalizer", normalizer_node)
    
    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "validator")
    
    workflow.add_conditional_edges(
        "validator",
        route_validation,
        {
            "normalizer": "normalizer",
            "fallback": "fallback",
            "extractor": "extractor"
        }
    )
    
    workflow.add_edge("fallback", "normalizer")
    workflow.add_edge("normalizer", END)
    
    return workflow.compile()

app_workflow = build_workflow()

def process_event(raw_event: dict) -> dict:
    initial_state = {
        "raw_event": raw_event,
        "cleaned_data": raw_event.get("cleaned_data", ""),
        "extracted_entities": {},
        "validation_status": "",
        "validation_feedback": "",
        "retry_count": 0,
        "normalized_event": {}
    }
    
    final_state = app_workflow.invoke(initial_state)
    return final_state["normalized_event"]
