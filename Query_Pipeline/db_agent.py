import sys
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from psycopg2.extras import RealDictCursor
from utils.db import init_db
from utils.huggingface import invoke_llm
from Query_Pipeline.kb_loader import (
    load_db_root_wiki,
    load_db_knowledge_graph,
    load_db_table_wiki,
)

# Navigator models (schema comprehension)
NAVIGATOR_MODELS = ["qwen2_5_72b", "llama3_3_70b", "deepseek_v3"]

# Planner models (deep reasoning for SQL strategy)
PLANNER_MODELS = ["deepseek_r1", "qwen2_5_72b", "llama3_3_70b"]

# Writer models (precise SQL generation)
WRITER_MODELS = ["deepseek_v3", "qwen2_5_72b", "llama3_3_70b"]

# Known tables in the database (from schema)
KNOWN_TABLES = {"salespersons", "projects", "events"}

# Known columns per table (from inspected table wikis)
KNOWN_COLUMNS = {
    "salespersons": {"id", "name", "email", "role", "projects", "created_at", "updated_at"},
    "projects": {"id", "project_name", "customer_name", "salesperson", "status", "created_at", "updated_at"},
    "events": {"id", "salesperson", "participants", "customer_name", "project_name", "summary", "data", "type", "created_at", "updated_at"},
}

# SQL mutation keywords to reject
MUTATION_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
    r"\bTRUNCATE\b", r"\bALTER\b", r"\bCREATE\b", r"\bGRANT\b",
    r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bMERGE\b",
    r"\bUPSERT\b", r"\bREPLACE\b",
]

MAX_VALIDATION_RETRIES = 3


def _navigate(question_text: str) -> list[str]:
    """Identify relevant tables for a question using the DB Root Wiki.
    
    Returns a list of unique table names.
    """
    root_wiki = load_db_root_wiki()
    if not root_wiki:
        print("  [Navigator] WARNING: Root Wiki not found, defaulting to all tables")
        return list(KNOWN_TABLES)

    prompt = f"""You are a database navigation agent. Based on the database schema below, determine which tables are needed to answer the question.

Database Schema:
{root_wiki}

Question: {question_text}

Rules:
1. Return ONLY table names that exist in the schema above.
2. Include tables needed for JOINs even if not directly queried.
3. Do NOT invent tables.

Respond with ONLY valid JSON:
{{"tables": ["table_name1", "table_name2"]}}"""

    result = invoke_llm(NAVIGATOR_MODELS, prompt, parse_as_json=True)
    tables = result.get("tables", [])

    # Filter to only known tables
    valid_tables = [t for t in tables if t in KNOWN_TABLES]
    if not valid_tables:
        print("  [Navigator] WARNING: No valid tables identified, defaulting to all")
        valid_tables = list(KNOWN_TABLES)

    return list(set(valid_tables))


def _expand_relationships(tables: list[str]) -> dict:
    """Expand the table list with related tables using the Knowledge Graph.
    
    Python-only — no LLM needed. Parses Knowledge_Graph.md for relationships.
    Returns expanded tables and relationship details.
    """
    kg_content = load_db_knowledge_graph()

    # Parse relationships from the Knowledge Graph markdown
    relationships = []

    # Extract table relationships from the markdown table
    # Format: | Source Table | Target Table | Relationship Type | Details |
    table_pattern = re.compile(
        r"\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*([^|]+)\|\s*([^|]+)\|"
    )

    for match in table_pattern.finditer(kg_content):
        source = match.group(1).strip()
        target = match.group(2).strip()
        rel_type = match.group(3).strip()
        details = match.group(4).strip()

        # Skip header rows
        if source in ("Source Table", "Source Column", "---", "------------"):
            continue

        relationships.append({
            "source_table": source.split(".")[0],  # Handle column references
            "target_table": target.split(".")[0],
            "type": rel_type,
            "details": details,
        })

    # Expand: for each selected table, add directly related tables (1-hop)
    expanded = set(tables)
    initial_tables = set(tables)
    for rel in relationships:
        src = rel["source_table"]
        tgt = rel["target_table"]
        if src in initial_tables and tgt in KNOWN_TABLES:
            expanded.add(tgt)
        if tgt in initial_tables and src in KNOWN_TABLES:
            expanded.add(src)

    # Filter relevant relationships (both endpoints in expanded set)
    relevant_rels = [
        r for r in relationships
        if r["source_table"] in expanded and r["target_table"] in expanded
    ]

    return {
        "tables": list(expanded),
        "relationships": relevant_rels,
    }


def _load_table_schemas(tables: list[str]) -> dict[str, str]:
    """Load full wiki content for each table.
    
    Python-only. Reads from Knowledge_Bases/Database/Tables/.
    """
    schemas = {}
    for table in tables:
        wiki = load_db_table_wiki(table)
        if wiki:
            schemas[table] = wiki
        else:
            print(f"  [SchemaLoader] WARNING: No wiki found for table '{table}'")
    return schemas


def _plan_query(question_text: str, table_schemas: dict, relationships: list,
                salesperson_id: str, salesperson_info: dict,
                validation_feedback: str = None) -> str:
    """Plan the SQL query strategy using an LLM.
    
    Returns a natural language plan describing what the SQL should do.
    """
    # Build schema context
    schema_context = ""
    for table, wiki in table_schemas.items():
        schema_context += f"\n--- Table: {table} ---\n{wiki}\n"

    # Build relationships context
    rel_context = ""
    for r in relationships:
        rel_context += f"  - {r['source_table']} → {r['target_table']} ({r['type']}): {r['details']}\n"
    if not rel_context:
        rel_context = "  No documented relationships.\n"

    prompt = f"""You are a SQL query planning agent. Plan a read-only SQL query to answer the question.

Question: {question_text}

Salesperson ID: {salesperson_id}
Salesperson Name: {salesperson_info.get('name', 'Unknown')}

Available Tables & Schemas:
{schema_context}

Table Relationships:
{rel_context}

Rules:
1. Plan a READ-ONLY SELECT query only. No INSERT, UPDATE, DELETE, etc.
2. Use PostgreSQL syntax.
3. Use proper JOINs based on the documented foreign keys.
4. Filter by salesperson ID where relevant.
5. Consider the column data types carefully (UUID, TIMESTAMPTZ, VARCHAR, JSONB, ARRAY, ENUM).
6. Be specific about which columns to select, what conditions to apply, and what ordering/limits to use.
7. For ENUM types: salesperson_role values are 'sales_rep', 'senior_sales_rep', 'sales_manager', 'sales_director', 'admin'. event_type values are 'calendar_event', 'mail', 'meeting'.
8. VERY IMPORTANT: To find when an event or meeting happened, query the `created_at` column as the date field. There is no other date field.
9. VERY IMPORTANT: When searching for "meetings", make sure to filter the `type` column to include 'calendar_event' or 'meeting'.
10. ALWAYS filter by `project_name` if a project is mentioned in the query.
"""

    if validation_feedback:
        prompt += f"""
IMPORTANT — PREVIOUS VALIDATION FAILED. You must fix these issues:
{validation_feedback}

Revise your plan to address the validation errors above.
"""

    prompt += "\nReturn ONLY the query plan in plain text. No SQL code, just the strategy."

    return invoke_llm(PLANNER_MODELS, prompt, parse_as_json=False)


def _write_sql(plan: str, table_schemas: dict, relationships: list) -> str:
    """Convert the plan into an actual SQL query.
    
    Returns the SQL string.
    """
    schema_context = ""
    for table, wiki in table_schemas.items():
        schema_context += f"\n--- Table: {table} ---\n{wiki}\n"

    rel_context = ""
    for r in relationships:
        rel_context += f"  - {r['source_table']} → {r['target_table']} ({r['type']}): {r['details']}\n"

    prompt = f"""You are a SQL writer agent. Convert the following query plan into a valid PostgreSQL SQL query.

Query Plan:
{plan}

Available Tables & Schemas:
{schema_context}

Table Relationships:
{rel_context}

Rules:
1. Write a SINGLE SELECT statement only. No mutations.
2. Use PostgreSQL syntax.
3. Use proper table aliases for readability.
4. Only reference tables and columns that exist in the schemas above.
5. Use appropriate JOINs based on the foreign key relationships.
6. Do NOT use semicolons at the end of additional statements — only one statement allowed.

Return ONLY the SQL query. No explanations, no markdown code fences, no prefixes."""

    sql = invoke_llm(WRITER_MODELS, prompt, parse_as_json=False)

    # Strip common markdown artifacts
    sql = sql.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    if sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    sql = sql.strip()

    # Ensure it ends with a single semicolon
    sql = sql.rstrip(";").strip() + ";"

    return sql


def _validate_sql(sql: str, expanded_tables: list[str], table_schemas: dict) -> dict:
    """Validate the SQL query using Python-based checks.
    
    Returns {"valid": True} or {"valid": False, "feedback": "..."}.
    """
    feedback_items = []

    # 1. Check for mutation keywords
    for kw_pattern in MUTATION_KEYWORDS:
        if re.search(kw_pattern, sql, re.IGNORECASE):
            keyword = kw_pattern.replace(r"\b", "")
            feedback_items.append(f"REJECTED: SQL contains mutation keyword '{keyword}'. Only SELECT queries are allowed.")

    # 2. Check it starts with SELECT
    sql_upper = sql.strip().upper()
    # Remove leading comments
    clean_sql = re.sub(r"--.*?\n", "", sql, flags=re.MULTILINE).strip().upper()
    clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL).strip()
    if not clean_sql.startswith("SELECT") and not clean_sql.startswith("WITH"):
        feedback_items.append("REJECTED: SQL must start with SELECT or WITH (CTE). Found something else.")

    # 3. Check for multiple statements safely (ignoring semicolons inside single quotes)
    sql_no_strings = re.sub(r"'[^']*'", "''", sql)
    statements = [s.strip() for s in sql_no_strings.rstrip(";").split(";") if s.strip()]
    if len(statements) > 1:
        feedback_items.append("REJECTED: Multiple SQL statements detected. Only a single SELECT statement is allowed.")

    # 4. Validate table references and extract aliases
    table_refs = set()
    alias_map = {}
    
    # Match FROM/JOIN table AS alias or FROM/JOIN table alias
    from_join_pattern = re.compile(
        r"(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?", re.IGNORECASE
    )
    for match in from_join_pattern.finditer(sql_no_strings):
        table_name = match.group(1).lower()
        table_refs.add(table_name)
        alias = match.group(2)
        if alias and alias.upper() not in ("ON", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "LEFT", "RIGHT", "INNER", "OUTER", "CROSS", "JOIN"):
            alias_map[alias.lower()] = table_name

    for table in table_refs:
        if table not in KNOWN_TABLES:
            feedback_items.append(
                f"INVALID TABLE: '{table}' does not exist in the database. "
                f"Valid tables are: {', '.join(sorted(KNOWN_TABLES))}."
            )

    # 5. Validate column references (table.column format)
    col_ref_pattern = re.compile(r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)")
    for match in col_ref_pattern.finditer(sql_no_strings):
        table_or_alias = match.group(1).lower()
        column = match.group(2).lower()

        # Resolve alias to actual table name if it exists
        actual_table = alias_map.get(table_or_alias, table_or_alias)

        # Validate if it maps to a known table
        if actual_table in KNOWN_COLUMNS:
            if column not in KNOWN_COLUMNS[actual_table]:
                feedback_items.append(
                    f"INVALID COLUMN: '{table_or_alias}.{column}' (resolved to '{actual_table}.{column}'). "
                    f"Valid columns for '{actual_table}': {', '.join(sorted(KNOWN_COLUMNS[actual_table]))}."
                )

    if feedback_items:
        return {"valid": False, "feedback": "\n".join(feedback_items)}

    return {"valid": True}


def _execute_sql(sql: str) -> dict:
    """Execute the validated SQL query and return results.
    
    Returns {sql, columns, rows, row_count} or {sql, error}.
    """
    conn = None
    try:
        conn = init_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]

        # Get column names
        columns = [desc[0] for desc in cur.description] if cur.description else []

        # Convert non-serializable types to strings
        for row in rows:
            for key, val in row.items():
                if not isinstance(val, (str, int, float, bool, type(None), list, dict)):
                    row[key] = str(val)

        return {
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

    except Exception as e:
        print(f"  [SQLExecutor] Database error: {e}")
        return {
            "sql": sql,
            "error": f"SQL execution error: {e}",
        }
    finally:
        if conn:
            conn.close()


def node_db_agent_process(state: dict) -> dict:
    """Orchestrate the DB agent pipeline for all questions that need database data.
    
    For each question with needs_db=True:
      1. Navigate → identify relevant tables
      2. Expand relationships → add related tables
      3. Load table schemas
      4. Plan → Write → Validate → (retry or execute)
    """
    questions = state["questions"]
    salesperson_id = state["salesperson_id"]
    salesperson_info = state["salesperson_info"]

    updated_questions = []

    for q in questions:
        q_copy = dict(q)

        if not q.get("needs_db"):
            updated_questions.append(q_copy)
            continue

        print(f"\n[DBAgent] Processing Q{q['index']}: {q['text']}")

        # Step 1: Navigate
        print(f"  [Navigator] Identifying relevant tables...")
        tables = _navigate(q["text"])

        # Step 2: Expand relationships
        print(f"  [RelExpander] Expanding with related tables...")
        expanded = _expand_relationships(tables)
        expanded_tables = expanded["tables"]
        relationships = expanded["relationships"]

        # Step 3: Load table schemas
        print(f"  [SchemaLoader] Loading table schemas...")
        table_schemas = _load_table_schemas(expanded_tables)

        # Step 4: Plan → Write → Validate → Retry loop
        validation_feedback = None
        db_result = None

        for attempt in range(MAX_VALIDATION_RETRIES):
            print(f"  [Attempt {attempt + 1}/{MAX_VALIDATION_RETRIES}]")

            # Plan
            print(f"    [Planner] Planning SQL query...")
            plan = _plan_query(
                q["text"], table_schemas, relationships,
                salesperson_id, salesperson_info,
                validation_feedback
            )

            # Write
            print(f"    [Writer] Generating SQL...")
            sql = _write_sql(plan, table_schemas, relationships)

            # Validate
            print(f"    [Validator] Validating SQL...")
            validation = _validate_sql(sql, expanded_tables, table_schemas)

            if validation["valid"]:
                print(f"    [Validator] PASS")

                # Execute
                print(f"    [Executor] Executing SQL...")
                db_result = _execute_sql(sql)

                if "error" in db_result:
                    print(f"    [Executor] Error: {db_result['error']}")
                    # Treat execution error as validation failure for retry
                    validation_feedback = f"SQL execution failed: {db_result['error']}. Fix the SQL."
                    db_result = None
                    continue
                else:
                    print(f"    [Executor] Success: {db_result['row_count']} row(s) returned")
                    break
            else:
                print(f"    [Validator] FAIL: {validation['feedback']}")
                validation_feedback = validation["feedback"]

        # If all retries exhausted
        if db_result is None:
            print(f"  [DBAgent] All attempts exhausted for Q{q['index']}")
            db_result = {
                "sql": "",
                "error": f"Failed to generate valid SQL after {MAX_VALIDATION_RETRIES} attempts. Last feedback: {validation_feedback}",
            }

        q_copy["db_results"] = db_result
        updated_questions.append(q_copy)

    return {"questions": updated_questions}
