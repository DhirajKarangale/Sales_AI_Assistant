import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.huggingface import invoke_llm

# Lightweight models for simple boolean classification
DEPENDENCY_MODELS = ["qwen2_5_7b", "llama3_1_8b", "phi3_mini"]


def node_detect_db_dependencies(state: dict) -> dict:
    """For each extracted question, determine whether database data is required.
    
    Returns a boolean per question. Uses a batched LLM call for efficiency.
    """
    questions = state["questions"]

    if not questions:
        return {"questions": questions}

    # Build a batched prompt with all questions
    questions_text = "\n".join([
        f"  {q['index']}: {q['text']}"
        for q in questions
    ])

    prompt = f"""You are a dependency detection agent for a sales assistant system.

The system has a PostgreSQL database with these tables:
- salespersons (id, name, email, role, projects, created_at, updated_at)
- projects (id, project_name, customer_name, salesperson, status, created_at, updated_at)
- events (id, salesperson, participants, customer_name, project_name, summary, data, type, created_at, updated_at)

For each question below, determine if answering it requires querying this database.

Questions:
{questions_text}

Consider:
- Questions about specific project statuses, counts, dates, or listings likely NEED the database.
- Questions about meeting details, event summaries, participants likely NEED the database.
- Questions asking for general advice, explanations, or opinions do NOT need the database.
- Questions about specific data points (amounts, dates, names) likely NEED the database.

Respond with ONLY valid JSON in this exact format:
{{"results": [{{"index": 0, "needs_db": true}}, {{"index": 1, "needs_db": false}}]}}"""

    print(f"[DBDependency] Detecting DB dependencies for {len(questions)} question(s)...")

    try:
        result = invoke_llm(DEPENDENCY_MODELS, prompt, parse_as_json=True)
        results_list = result.get("results", [])

        # Build a lookup map
        dependency_map = {r["index"]: r["needs_db"] for r in results_list}

        # Update questions with the dependency flags
        updated_questions = []
        for q in questions:
            needs_db = dependency_map.get(q["index"], True)  # Default to True if missing
            q_copy = dict(q)
            q_copy["needs_db"] = bool(needs_db)
            updated_questions.append(q_copy)
            print(f"  Q{q_copy['index']}: needs_db={q_copy['needs_db']}")

        return {"questions": updated_questions}

    except Exception as e:
        print(f"[DBDependency] Error during detection: {e}")
        # Fallback: assume all questions need DB
        updated_questions = []
        for q in questions:
            q_copy = dict(q)
            q_copy["needs_db"] = True
            updated_questions.append(q_copy)
        return {"questions": updated_questions}
