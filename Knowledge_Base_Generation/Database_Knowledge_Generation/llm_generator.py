import sys
import os
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.huggingface import invoke_llm

# Generation Models (Strong logic, structures)
GEN_MODELS = [
    "qwen2_5_72b",
    "llama3_3_70b",
]

# Graph extraction models (Strong reasoning)
GRAPH_MODELS = [
    "deepseek_r1",
    "llama3_3_70b",
    "qwen2_5_72b"
]

# Fact Checking / Validation Models
VALIDATION_MODELS = [
    "veritas_8b_fact_checker",
    "deepseek_v3",
    "deepseek_r1_distill_llama_8b",
    "llama3_3_70b"
]

def generate_root_wiki(schema_info, feedback=None):
    tables_summary = ""
    for table, info in schema_info.items():
        cols = ", ".join([c["name"] for c in info["columns"]])
        tables_summary += f"- Table: {table}\n  Columns: {cols}\n"

    prompt = f"""
You are an expert Database Architect. Based ONLY on the following database schema, generate a Root Wiki in Markdown format.
Do NOT hallucinate or invent tables, columns, or business purposes not supported by the schema.

Schema Overview:
{tables_summary}

Requirements for Root Wiki:
1. List all schemas/tables.
2. Provide a short description of each table.
3. Describe the business purpose/use of each table.
4. Explain what each table does and holds.
5. If information is not available, explicitly mark it as "Unknown" or "Not Available".
"""
    if feedback:
        prompt += f"\nPREVIOUS FEEDBACK TO CORRECT:\n{feedback}\nEnsure you fix these errors!"

    prompt += "\nRespond ONLY with the Markdown content. Do not wrap it in code blocks like ```markdown, just return the raw text."
    
    return invoke_llm(GEN_MODELS, prompt)

def generate_table_wiki(table_name, table_info, feedback=None):
    schema_json = json.dumps(table_info, indent=2)
    prompt = f"""
You are an expert Database Architect. Based ONLY on the following schema for the table '{table_name}', generate a Table Wiki in Markdown format.
Do NOT hallucinate or invent information.

Table Schema:
{schema_json}

Requirements for Table Wiki:
1. Table description.
2. Every column listed with its data type.
3. Column description.
4. Business use of the column.
5. How the column affects the record.
6. Primary keys.
7. Foreign keys (Detailed FK relationships).
8. Maximum 5 real example values per column (from the provided sample_values, do not invent examples).
9. If information is not available, explicitly mark it as "Unknown" or "Not Available".
"""
    if feedback:
        prompt += f"\nPREVIOUS FEEDBACK TO CORRECT:\n{feedback}\nEnsure you fix these errors!"

    prompt += "\nRespond ONLY with the Markdown content. Do not wrap it in code blocks like ```markdown, just return the raw text."

    return invoke_llm(GEN_MODELS, prompt)

def generate_knowledge_graph(schema_info, feedback=None):
    simplified_schema = {}
    for table, info in schema_info.items():
        simplified_schema[table] = {
            "columns": [c["name"] for c in info["columns"]],
            "foreign_keys": info["foreign_keys"]
        }
    
    schema_json = json.dumps(simplified_schema, indent=2)
    prompt = f"""
You are an expert Database Architect. Based ONLY on the following database relationships, generate a Knowledge Graph representation in Markdown format.
Do NOT hallucinate tables, columns, or relationships.

Schema Relationships:
{schema_json}

Requirements for Knowledge Graph:
1. Detail relationships from Table → table.
2. Detail relationships from Column → column.
3. Specify the Relationship type/details.
4. Trace and present relationship paths up to 4 hops.
5. If information is not available, explicitly mark it as "Unknown" or "Not Available".
"""
    if feedback:
        prompt += f"\nPREVIOUS FEEDBACK TO CORRECT:\n{feedback}\nEnsure you fix these errors!"

    prompt += "\nRespond ONLY with the Markdown content. Do not wrap it in code blocks like ```markdown, just return the raw text."

    return invoke_llm(GRAPH_MODELS, prompt)

def validate_knowledge(raw_schema, generated_markdown, scope="General"):
    schema_json = json.dumps(raw_schema, indent=2)
    prompt = f"""
You are a strict Fact-Checker. Your ONLY job is to compare the GENERATED DOCUMENT against the RAW SCHEMA.
Identify ANY hallucinations: tables, columns, or examples in the document that DO NOT exist in the raw schema.
Scope: {scope}

RAW SCHEMA:
{schema_json}

GENERATED DOCUMENT:
{generated_markdown}

If there are NO hallucinations and the document is strictly accurate based on the schema, reply EXACTLY with the word "PASS".
If you find hallucinations, list them out clearly as feedback. Do NOT be lenient.
"""
    return invoke_llm(VALIDATION_MODELS, prompt)

def clean_markdown(text):
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[11:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
