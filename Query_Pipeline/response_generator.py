import sys
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.llm import invoke_llm
from Query_Pipeline.kb_loader import (
    load_business_knowledge_graph,
    load_business_wiki,
    list_business_wikis,
)

RESPONSE_MODELS = ["llama3_3_70b", "qwen2_5_72b", "deepseek_v3"]

MAX_GRAPH_DEPTH = 2
MAX_GRAPH_BREADTH = 10


def _build_context_subgraph(knowledge_graph: dict, salesperson_info: dict) -> set:
    nodes_by_id = {n["id"]: n for n in knowledge_graph.get("nodes", [])}
    edges = knowledge_graph.get("edges", [])

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
        return set()

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

        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))

    return visited


def _select_relevant_wikis(subgraph_nodes: set, salesperson_info: dict) -> list[dict]:
    categories = ["Salespersons", "Customers", "Projects", "Persons", "Events"]
    relevant_wikis = []

    for category in categories:
        wiki_names = list_business_wikis(category)
        for wiki_name in wiki_names:
            wiki = load_business_wiki(category, wiki_name)
            wiki_entity_name = wiki.get("metadata", {}).get("name", "")

            if wiki_entity_name in subgraph_nodes:
                relevant_wikis.append({
                    "category": category,
                    "name": wiki_name,
                    "metadata": wiki.get("metadata", {}),
                    "content": wiki.get("content", ""),
                })

    sp_name = salesperson_info.get("name", "")
    for category in categories:
        wiki_names = list_business_wikis(category)
        for wiki_name in wiki_names:
            if any(w["name"] == wiki_name and w["category"] == category for w in relevant_wikis):
                continue

            wiki = load_business_wiki(category, wiki_name)
            meta = wiki.get("metadata", {})

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


_EVENT_TYPE_MAP = {
    "calendar_event": "Meeting",
    "meet": "Meeting",
    "meeting": "Meeting",
    "mail": "Email",
    "email": "Email",
}


def _humanize_event_type(raw_type: str) -> str:
    return _EVENT_TYPE_MAP.get(raw_type.lower().strip(), raw_type) if raw_type else "Interaction"


def _humanize_date(raw_date: str) -> str:
    if not raw_date:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except Exception:
        return raw_date


def _format_wiki_context(wikis: list[dict]) -> str:
    if not wikis:
        return "No relevant business information available."

    parts = []
    for w in wikis:
        category = w.get("category", "")
        meta = w.get("metadata", {})
        content = w.get("content", "")
        entity_name = meta.get("name", w.get("name", "Unknown"))

        if category == "Events":
            event_type = _humanize_event_type(meta.get("event_type", ""))
            customer = meta.get("customer", "")
            project = meta.get("project", "")
            salesperson = meta.get("salesperson", "")
            created_at = _humanize_date(meta.get("created_at", ""))

            if not created_at and content:
                for line in content.split("\n"):
                    if line.strip().startswith("Created At:"):
                        created_at = _humanize_date(line.split(":", 1)[1].strip())
                        break

            summary = ""
            for line in content.split("\n"):
                if line.strip().startswith("**Summary**:") or line.strip().startswith("**Summary**"):
                    summary = line.split(":", 1)[1].strip() if ":" in line else ""
                    break

            participants = []
            in_participants = False
            for line in content.split("\n"):
                if "## Participants" in line:
                    in_participants = True
                    continue
                if in_participants:
                    if line.strip().startswith("- "):
                        name_part = line.strip()[2:]
                        if "(" in name_part:
                            name_part = name_part.split("(")[0].strip()
                        if name_part.lower().startswith("salesperson"):
                            continue
                        participants.append(name_part)
                    elif line.strip().startswith("#") or (line.strip() and not line.strip().startswith("-")):
                        in_participants = False

            header = f"{event_type}"
            if project:
                header += f" — {project}"
            if customer:
                header += f" (Customer: {customer})"

            detail_lines = [f"--- {header} ---"]
            if created_at:
                detail_lines.append(f"Date: {created_at}")
            if salesperson:
                detail_lines.append(f"Salesperson: {salesperson}")
            if summary:
                detail_lines.append(f"Summary: {summary}")
            if participants:
                detail_lines.append(f"Participants: {', '.join(participants)}")

            raw_data_lines = []
            in_raw = False
            for line in content.split("\n"):
                if "## Raw Data" in line:
                    in_raw = True
                    continue
                if in_raw:
                    if line.strip().startswith("#"):
                        break
                    if line.strip():
                        raw_data_lines.append(line.strip())
            if raw_data_lines:
                detail_lines.append("Discussion: " + " ".join(raw_data_lines))

            parts.append("\n".join(detail_lines))

        elif category == "Projects":
            customer = meta.get("customer", "")
            status = ""
            created_at = ""
            updated_at = ""
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("Status:"):
                    status = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("Created At:"):
                    created_at = _humanize_date(stripped.split(":", 1)[1].strip())
                elif stripped.startswith("Updated At:"):
                    updated_at = _humanize_date(stripped.split(":", 1)[1].strip())

            detail_lines = [f"--- Deal: {entity_name} ---"]
            if customer:
                detail_lines.append(f"Customer: {customer}")
            if status:
                detail_lines.append(f"Status: {status}")
            if created_at:
                detail_lines.append(f"Started: {created_at}")
            if updated_at:
                detail_lines.append(f"Last Updated: {updated_at}")

            parts.append("\n".join(detail_lines))

        elif category in ("Salespersons", "Customers", "Persons"):
            label = "Salesperson" if category == "Salespersons" else (
                "Customer" if category == "Customers" else "Contact"
            )
            parts.append(f"--- {label}: {entity_name} ---")

        else:
            parts.append(f"--- {entity_name} ---\n{content}")

    return "\n\n".join(parts)


def _format_db_results(questions: list[dict]) -> str:
    parts = []

    for q in questions:
        db_res = q.get("db_results")
        if db_res is None:
            continue

        if "error" in db_res and db_res["error"]:
            parts.append(f"Regarding \"{q['text']}\" — the data could not be retrieved.")
            continue

        rows = db_res.get("rows", [])
        if not rows:
            parts.append(f"Regarding \"{q['text']}\" — no matching records were found.")
            continue

        row_strs = []
        for row in rows[:20]:
            fields = []
            for key, val in row.items():
                if key.lower() in ("id",):
                    continue
                if key.lower() in ("created_at", "updated_at") and val:
                    val = _humanize_date(str(val))
                    key = "Date" if key.lower() == "created_at" else "Last Updated"
                if key.lower() == "type" and isinstance(val, str):
                    val = _humanize_event_type(val)
                    key = "Type"
                display_key = key.replace("_", " ").title()
                fields.append(f"{display_key}: {val}")
            if fields:
                row_strs.append("  " + ", ".join(fields))

        parts.append(
            f"Data for \"{q['text']}\":\n" + "\n".join(row_strs)
        )

    return "\n\n".join(parts)


def node_generate_response(state: dict) -> dict:
    raw_query = state["raw_query"]
    questions = state["questions"]
    salesperson_info = state["salesperson_info"]

    print(f"\n[ResponseGenerator] Building context and generating response...")

    print(f"  [Context] Loading Business Knowledge Graph...")
    kg = load_business_knowledge_graph()
    subgraph_nodes = _build_context_subgraph(kg, salesperson_info)

    print(f"  [Context] Selecting relevant Business wikis...")
    relevant_wikis = _select_relevant_wikis(subgraph_nodes, salesperson_info)

    wiki_context = _format_wiki_context(relevant_wikis)
    db_context = _format_db_results(questions)

    data_sections = []
    if wiki_context and wiki_context != "No relevant business information available.":
        data_sections.append(wiki_context)
    if db_context:
        data_sections.append(db_context)
    combined_data = "\n\n".join(data_sections) if data_sections else "No data available."

    prompt = f"""You are a helpful sales assistant speaking directly to {salesperson_info['name']}.

{salesperson_info['name']} asked: "{raw_query}"

Here is the relevant information from our records:

{combined_data}

Using ONLY the information provided above, write a clear and concise response that directly answers {salesperson_info['name']}'s question.

IMPORTANT RULES — follow these strictly:
1. Write in a natural, conversational tone as if you are a helpful colleague.
2. Combine all parts of the answer into ONE cohesive response. Do NOT use a Q&A format, numbered questions, or bullet-point-per-question structure.
3. Use human-readable dates (e.g., "September 8, 2026") instead of raw timestamps.
4. Refer to interactions by their type: "meeting", "email", "call" — never use internal codes.
5. Use real names for people, customers, and deals. Never include IDs, UUIDs, or codes.
6. NEVER mention or reference: database, knowledge base, knowledge graph, metadata, wiki, records, system, query, data source, file names, event IDs, or any internal technical terms.
7. If some information is not available in the data above, simply say you don't have that information — don't speculate or make anything up.
8. Keep the response concise and relevant — only include information that answers the question.
9. When identifying the "last touchpoint" or "most recent" interaction, compare dates across ALL the events provided and pick the latest one. State what type of interaction it was and when it happened.
10. For deal/project status questions, state the status directly and clearly.

Respond now:"""

    print(f"  [LLM] Generating final response...")
    response = invoke_llm(RESPONSE_MODELS, prompt, parse_as_json=False)
    print(f"  [ResponseGenerator] Response generated ({len(response)} chars)")

    return {"final_response": response}
