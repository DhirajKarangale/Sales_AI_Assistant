import sys
import os
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from psycopg2.extras import RealDictCursor
from utils.db import init_db
from utils.llm import invoke_llm

OPTIMIZER_MODELS = ["llama3_3_70b", "qwen2_5_72b", "deepseek_v3"]


def node_fetch_salesperson_info(state: dict) -> dict:
    salesperson_id = state["salesperson_id"]
    print(f"[QueryOptimizer] Fetching salesperson info for ID: {salesperson_id}")

    conn = None
    try:
        conn = init_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT id, name, email, role FROM salespersons WHERE id = %s",
            (salesperson_id,)
        )
        sp_row = cur.fetchone()

        if not sp_row:
            print(f"[QueryOptimizer] Salesperson not found: {salesperson_id}")
            return {"error": f"Salesperson with ID '{salesperson_id}' not found in the database."}

        cur.execute(
            "SELECT id, project_name, customer_name, status FROM projects WHERE salesperson = %s",
            (salesperson_id,)
        )
        projects = [dict(row) for row in cur.fetchall()]

        salesperson_info = {
            "id": str(sp_row["id"]),
            "name": sp_row["name"],
            "email": sp_row["email"],
            "role": sp_row["role"],
            "projects": [
                {
                    "id": str(p["id"]),
                    "project_name": p["project_name"],
                    "customer_name": p["customer_name"],
                    "status": p["status"]
                }
                for p in projects
            ]
        }

        print(f"[QueryOptimizer] Found salesperson: {salesperson_info['name']} "
              f"({salesperson_info['role']}) with {len(projects)} projects")

        return {"salesperson_info": salesperson_info}

    except Exception as e:
        print(f"[QueryOptimizer] Database error: {e}")
        return {"error": f"Database error while fetching salesperson info: {e}"}
    finally:
        if conn:
            conn.close()


def node_normalize_query(state: dict) -> dict:
    raw_query = state["raw_query"]
    salesperson_info = state["salesperson_info"]

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_day = now.strftime("%A")

    projects_summary = "\n".join([
        f"  - {p['project_name']} (Customer: {p['customer_name']}, Status: {p['status']})"
        for p in salesperson_info.get("projects", [])
    ]) or "  No projects found."

    prompt = f"""You are a query normalization agent for a sales assistant system.

Your task is to clean and normalize the following user query. Follow these rules strictly:

1. RESOLVE ALL DATES: Convert relative dates to absolute dates.
   - Current date: {current_date} ({current_day})
   - "last week" = {(now - timedelta(days=now.weekday() + 7)).strftime("%Y-%m-%d")} to {(now - timedelta(days=now.weekday() + 1)).strftime("%Y-%m-%d")}
   - "this week" = {(now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")} to {current_date}
   - "yesterday" = {(now - timedelta(days=1)).strftime("%Y-%m-%d")}
   - "last month" = previous calendar month
   - Resolve all other relative time references similarly.

2. NORMALIZE UNITS (where applicable):
   - Currency → INR
   - Weight → kg
   - Length → meters
   - Speed/velocity → m/s
   - If no unit conversion is needed, leave as-is.

3. REMOVE FILLER WORDS: Remove "um", "uh", "like", "you know", "basically", etc.

4. PRESERVE MEANING: Do not add information that was not in the original query.

5. RESOLVE PRONOUNS: Replace "I", "me", "my" with the salesperson's context where clear.
   - Salesperson: {salesperson_info['name']} (ID: {salesperson_info['id']}, Role: {salesperson_info['role']})
   - Their projects:
{projects_summary}

6. DO NOT INVENT: If something is ambiguous, keep it as-is. Do not guess.

Original query: {raw_query}

Return ONLY the cleaned/normalized query text. No explanations, no JSON, no code blocks."""

    print(f"[QueryOptimizer] Normalizing query...")
    normalized = invoke_llm(OPTIMIZER_MODELS, prompt, parse_as_json=False)
    print(f"  -> Normalized Query: {normalized}")

    return {"normalized_query": normalized}


def node_extract_questions(state: dict) -> dict:
    normalized_query = state["normalized_query"]
    salesperson_info = state["salesperson_info"]

    prompt = f"""You are a question extraction agent. Your task is to decompose the following query into independent sub-questions.

Rules:
1. Extract ALL independent questions from the query.
2. PRESERVE the original order — question sequence can affect meaning.
3. If the query is already a single question, return it as a single-item list.
4. Each question should be self-contained and answerable independently.
5. DO NOT invent questions that are not present in the query.
6. If a query mentions a specific project, customer, or context (e.g., 'AI Analytics Platform'), that context MUST be explicitly carried over into ALL sub-questions unless a different project is specified. Do not drop project or salesperson context.
7. Include relevant context (like salesperson ID, project names, dates) in each question so it can stand alone.

Salesperson context:
- Name: {salesperson_info['name']}
- ID: {salesperson_info['id']}

Query to decompose:
{normalized_query}

Respond with valid JSON in this exact format:
{{"questions": ["question 1 text", "question 2 text"]}}

Note: It is perfectly fine to output your reasoning inside a <think>...</think> block before providing the final JSON. Do not omit the <think> block if you need it."""

    print(f"[QueryOptimizer] Extracting questions...")
    result = invoke_llm(OPTIMIZER_MODELS, prompt, parse_as_json=True)

    raw_questions = result.get("questions", [normalized_query])
    if not raw_questions:
        raw_questions = [normalized_query]

    questions = [
        {"index": i, "text": q, "needs_db": None, "db_results": None}
        for i, q in enumerate(raw_questions)
    ]

    print(f"[QueryOptimizer] Extracted {len(questions)} question(s):")
    for q in questions:
        print(f"  - {q['text']}")

    return {"questions": questions}
