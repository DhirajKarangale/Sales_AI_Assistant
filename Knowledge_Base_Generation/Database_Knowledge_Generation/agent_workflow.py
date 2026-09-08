import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing import TypedDict, Dict
from langgraph.graph import StateGraph, START, END

from db_extractor import extract_schema
from llm_generator import (
    generate_root_wiki, 
    generate_table_wiki, 
    generate_knowledge_graph, 
    validate_knowledge,
    clean_markdown
)

class GraphState(TypedDict):
    raw_schema: dict
    root_wiki: str
    table_wikis: Dict[str, str]
    knowledge_graph: str
    validation_feedback: Dict[str, str]
    generation_attempts: int

def node_extract_schema(state: GraphState):
    print("Extracting DB schema...")
    schema = extract_schema()
    return {"raw_schema": schema, "generation_attempts": 0, "validation_feedback": {}}

def node_generate_knowledge(state: GraphState):
    print(f"Generating knowledge (Attempt {state.get('generation_attempts', 0) + 1})...")
    raw_schema = state["raw_schema"]
    feedback = state.get("validation_feedback", {})
    
    root_wiki = generate_root_wiki(raw_schema, feedback.get("root_wiki"))
    
    table_wikis = state.get("table_wikis", {})
    for table, info in raw_schema.items():
        table_feedback = feedback.get(f"table_{table}")
        if not table_wikis.get(table) or table_feedback:
            print(f" -> Generating Table Wiki: {table}")
            table_wikis[table] = generate_table_wiki(table, info, table_feedback)
            
    knowledge_graph = generate_knowledge_graph(raw_schema, feedback.get("knowledge_graph"))
    
    return {
        "root_wiki": clean_markdown(root_wiki),
        "table_wikis": {k: clean_markdown(v) for k, v in table_wikis.items()},
        "knowledge_graph": clean_markdown(knowledge_graph),
        "generation_attempts": state.get("generation_attempts", 0) + 1
    }

def node_validate_knowledge(state: GraphState):
    print("Validating knowledge against raw schema...")
    raw_schema = state["raw_schema"]
    feedback = {}
    
    print(" -> Validating Root Wiki")
    root_res = validate_knowledge(raw_schema, state["root_wiki"], scope="Root Wiki")
    if "PASS" not in root_res.upper() and len(root_res) > 20:
        print(f"    Failed: {root_res}")
        feedback["root_wiki"] = root_res

    for table, wiki_md in state["table_wikis"].items():
        print(f" -> Validating Table Wiki: {table}")
        res = validate_knowledge(raw_schema[table], wiki_md, scope=f"Table: {table}")
        if "PASS" not in res.upper() and len(res) > 20:
            print(f"    Failed: {res}")
            feedback[f"table_{table}"] = res

    print(" -> Validating Knowledge Graph")
    kg_res = validate_knowledge(raw_schema, state["knowledge_graph"], scope="Knowledge Graph")
    if "PASS" not in kg_res.upper() and len(kg_res) > 20:
        print(f"    Failed: {kg_res}")
        feedback["knowledge_graph"] = kg_res

    return {"validation_feedback": feedback}

def conditional_edge(state: GraphState):
    feedback = state.get("validation_feedback", {})
    if not feedback:
        print("Validation Passed!")
        return "save_files"
    if state["generation_attempts"] >= 3:
        print("Max attempts reached. Proceeding with warnings.")
        return "save_files"
    print("Validation Failed. Retrying generation with feedback...")
    return "generate_knowledge"

def node_save_files(state: GraphState):
    import shutil
    print("Saving files...")
    kb_dir = os.path.join(project_root, "Knowledge_Bases", "Database")
    
    if os.path.exists(kb_dir):
        shutil.rmtree(kb_dir)
        
    tables_dir = os.path.join(kb_dir, "Tables")
    os.makedirs(tables_dir, exist_ok=True)
    
    with open(os.path.join(kb_dir, "Root_Wiki.md"), "w", encoding="utf-8") as f:
        f.write(state["root_wiki"])
        
    with open(os.path.join(kb_dir, "Knowledge_Graph.md"), "w", encoding="utf-8") as f:
        f.write(state["knowledge_graph"])
        
    for table, md in state["table_wikis"].items():
        with open(os.path.join(tables_dir, f"{table}_Wiki.md"), "w", encoding="utf-8") as f:
            f.write(md)
            
    print("Files saved successfully.")
    return {}

def run_agent():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("extract_schema", node_extract_schema)
    workflow.add_node("generate_knowledge", node_generate_knowledge)
    workflow.add_node("validate_knowledge", node_validate_knowledge)
    workflow.add_node("save_files", node_save_files)
    
    workflow.add_edge(START, "extract_schema")
    workflow.add_edge("extract_schema", "generate_knowledge")
    workflow.add_edge("generate_knowledge", "validate_knowledge")
    
    workflow.add_conditional_edges(
        "validate_knowledge",
        conditional_edge,
        {
            "save_files": "save_files",
            "generate_knowledge": "generate_knowledge"
        }
    )
    workflow.add_edge("save_files", END)
    
    app = workflow.compile()
    print("Starting LangGraph Orchestration...")
    app.invoke({"generation_attempts": 0})

if __name__ == "__main__":
    run_agent()
