import sys
import os
import json
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.huggingface import invoke_llm
from Query_Pipeline.kb_loader import (
    load_business_knowledge_graph,
    load_business_wiki,
    list_business_wikis,
    parse_wiki,
)

# Response generation models (long-form, grounded answer synthesis)
RESPONSE_MODELS = ["deepseek_v3", "qwen2_5_72b", "llama3_3_70b"]

# Knowledge graph traversal limits
MAX_GRAPH_DEPTH = 2
MAX_GRAPH_BREADTH = 10


def _build_context_subgraph(knowledge_graph: dict, salesperson_info: dict) -> set:
    """Traverse the Business Knowledge Graph from the salesperson's context.
    
    Performs BFS from salesperson-related nodes with depth and breadth limits.
    Returns a set of node IDs that form the relevant subgraph.
    """
    nodes_by_id = {n["id"]: n for n in knowledge_graph.get("nodes", [])}
    edges = knowledge_graph.get("edges", [])

    # Build adjacency list
    adjacency = {}
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src not in adjacency:
            adjacency[src] = []
        adjacency[src].append(tgt)
        if tgt not in adjacency:
            adjacency[tgt] = []
        adjacency[tgt].append(src)

    # Seed nodes: salesperson name, their projects, and their customers
    seed_nodes = set()
    sp_name = salesperson_info.get("name", "")
    if sp_name and sp_name in nodes_by_id:
        seed_nodes.add(sp_name)

    for proj in salesperson_info.get("projects", []):
        proj_name = proj.get("project_name", "")
        cust_name = proj.get("customer_name", "")
        if proj_name and proj_name in nodes_by_id:
            seed_nodes.add(proj_name)
        if cust_name and cust_name in nodes_by_id:
            seed_nodes.add(cust_name)

    if not seed_nodes:
        # If no seeds found by exact name, return empty
        return set()

    # BFS traversal with depth and breadth limits
    visited = set()
    queue = [(node_id, 0) for node_id in seed_nodes]

    while queue and len(visited) < MAX_GRAPH_BREADTH:
        node_id, depth = queue.pop(0)

        if node_id in visited:
            continue
        if depth > MAX_GRAPH_DEPTH:
            continue

        visited.add(node_id)

        if len(visited) >= MAX_GRAPH_BREADTH:
            break

        # Add neighbors
        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))

    return visited


def _select_relevant_wikis(subgraph_nodes: set, salesperson_info: dict) -> list[dict]:
    """Map subgraph nodes to Business wiki files and load their content.
    
    Scans all wiki categories for wikis whose metadata 'name' matches a subgraph node.
    Returns a list of {"category", "name", "metadata", "content"} dicts.
    """
    categories = ["Salespersons", "Customers", "Projects", "People", "Events"]
    relevant_wikis = []

    for category in categories:
        wiki_names = list_business_wikis(category)
        for wiki_name in wiki_names:
            wiki = load_business_wiki(category, wiki_name)
            wiki_entity_name = wiki.get("metadata", {}).get("name", "")

            # Check if this wiki's entity is in the subgraph
            if wiki_entity_name in subgraph_nodes:
                relevant_wikis.append({
                    "category": category,
                    "name": wiki_name,
                    "metadata": wiki.get("metadata", {}),
                    "content": wiki.get("content", ""),
                })

    # Also include salesperson-related wikis by checking projects/customers
    sp_name = salesperson_info.get("name", "")
    for category in categories:
        wiki_names = list_business_wikis(category)
        for wiki_name in wiki_names:
            # Skip already included
            if any(w["name"] == wiki_name and w["category"] == category for w in relevant_wikis):
                continue

            wiki = load_business_wiki(category, wiki_name)
            meta = wiki.get("metadata", {})

            # Check if this wiki references the salesperson
            if sp_name and (
                meta.get("salesperson") == sp_name
                or sp_name in meta.get("salespersons", [])
            ):
                relevant_wikis.append({
                    "category": category,
                    "name": wiki_name,
                    "metadata": meta,
                    "content": wiki.get("content", ""),
                })

    return relevant_wikis


def _format_wiki_context(wikis: list[dict]) -> str:
    """Format loaded wikis into a context string for the LLM prompt."""
    if not wikis:
        return "No Business Knowledge Base wikis available."

    parts = []
    for w in wikis:
        meta_str = json.dumps(w["metadata"], indent=2, default=str)
        parts.append(
            f"--- [{w['category']}] {w.get('name', 'unknown')} ---\n"
            f"Metadata: {meta_str}\n"
            f"Content: {w['content']}\n"
        )

    return "\n".join(parts)


def _format_db_results(questions: list[dict]) -> str:
    """Format DB results from questions into a context string."""
    parts = []

    for q in questions:
        db_res = q.get("db_results")
        if db_res is None:
            parts.append(f"Q{q['index']}: {q['text']}\n  [No database query was needed]")
            continue

        if "error" in db_res and db_res["error"]:
            parts.append(
                f"Q{q['index']}: {q['text']}\n"
                f"  [Database query failed: {db_res['error']}]"
            )
            continue

        rows = db_res.get("rows", [])
        if not rows:
            parts.append(
                f"Q{q['index']}: {q['text']}\n"
                f"  SQL: {db_res.get('sql', 'N/A')}\n"
                f"  [No results returned from database]"
            )
            continue

        # Format rows as a readable table
        row_strs = []
        for i, row in enumerate(rows[:20]):  # Limit to 20 rows for context
            row_strs.append(f"    Row {i+1}: {json.dumps(row, default=str)}")

        parts.append(
            f"Q{q['index']}: {q['text']}\n"
            f"  SQL: {db_res.get('sql', 'N/A')}\n"
            f"  Results ({db_res.get('row_count', 0)} rows):\n"
            + "\n".join(row_strs)
        )

    return "\n\n".join(parts)


def node_generate_response(state: dict) -> dict:
    """Generate the final response using all gathered context.
    
    Combines: user query, questions, DB results, Business KB wikis, and knowledge graph.
    """
    raw_query = state["raw_query"]
    normalized_query = state.get("normalized_query", raw_query)
    questions = state["questions"]
    salesperson_info = state["salesperson_info"]

    print(f"\n[ResponseGenerator] Building context and generating response...")

    # 1. Load and traverse Business Knowledge Graph
    print(f"  [Context] Loading Business Knowledge Graph...")
    kg = load_business_knowledge_graph()
    subgraph_nodes = _build_context_subgraph(kg, salesperson_info)

    # 2. Select and load relevant wikis
    print(f"  [Context] Selecting relevant Business wikis...")
    relevant_wikis = _select_relevant_wikis(subgraph_nodes, salesperson_info)

    wiki_context = _format_wiki_context(relevant_wikis)
    db_context = _format_db_results(questions)

    # 3. Build the response prompt
    questions_list = "\n".join([f"  Q{q['index']}: {q['text']}" for q in questions])

    prompt = f"""You are an expert sales assistant. Answer the user's query based STRICTLY on the provided data.

SALESPERSON:
- Name: {salesperson_info['name']}
- Role: {salesperson_info['role']}
- Email: {salesperson_info['email']}

ORIGINAL QUERY: {raw_query}

NORMALIZED QUERY: {normalized_query}

EXTRACTED QUESTIONS (answer ALL in this order):
{questions_list}

DATABASE RESULTS:
{db_context}

BUSINESS KNOWLEDGE BASE CONTEXT:
{wiki_context}

RULES:
1. Answer EVERY question listed above, in the same order.
2. GROUND every answer in the provided data (database results and/or business KB).
3. DO NOT infer, fabricate, or guess information that is not in the provided data.
4. If the data does not contain enough information to answer a question, explicitly state: "This information is not available in the current data."
5. Clearly distinguish between what is known (from data) and what is unavailable.
6. Be concise but thorough.
7. Use specific data points (dates, names, statuses) from the results where available.
8. Format the response clearly — use bullet points or numbered lists where appropriate.

Provide your complete response now:"""

    print(f"  [LLM] Generating final response...")
    response = invoke_llm(RESPONSE_MODELS, prompt, parse_as_json=False)
    print(f"  [ResponseGenerator] Response generated ({len(response)} chars)")

    return {"final_response": response}
