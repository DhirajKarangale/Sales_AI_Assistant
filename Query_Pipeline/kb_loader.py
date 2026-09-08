import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_KB_DIR = os.path.join(PROJECT_ROOT, "Knowledge_Bases", "Database")
BUSINESS_KB_DIR = os.path.join(PROJECT_ROOT, "Knowledge_Bases", "Business")


def load_db_root_wiki() -> str:
    """Load the Database Root Wiki markdown content."""
    path = os.path.join(DB_KB_DIR, "Root_Wiki.md")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_db_knowledge_graph() -> str:
    """Load the Database Knowledge Graph markdown content."""
    path = os.path.join(DB_KB_DIR, "Knowledge_Graph.md")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_db_table_wiki(table_name: str) -> str:
    """Load a specific table's wiki markdown content."""
    path = os.path.join(DB_KB_DIR, "Tables", f"{table_name}_Wiki.md")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_business_knowledge_graph() -> dict:
    """Load the Business Knowledge Graph JSON."""
    path = os.path.join(BUSINESS_KB_DIR, "knowledge_graph.json")
    if not os.path.exists(path):
        return {"nodes": [], "edges": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_wiki(file_path: str) -> dict:
    """Parse a wiki file with YAML-like frontmatter.
    
    Reuses the same format used by Business_Knowledge_Generation/wiki_generator.py:
    ---
    key: json_value
    ---
    markdown content
    """
    if not os.path.exists(file_path):
        return {"metadata": {}, "content": ""}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if match:
        meta_str = match.group(1)
        body = match.group(2).strip()
        metadata = {}
        for line in meta_str.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                try:
                    metadata[key.strip()] = json.loads(val.strip())
                except json.JSONDecodeError:
                    metadata[key.strip()] = val.strip()
        return {"metadata": metadata, "content": body}

    return {"metadata": {}, "content": content}


def load_business_wiki(category: str, name: str) -> dict:
    """Load a specific Business wiki by category and filename.
    
    Args:
        category: One of 'Salespersons', 'Customers', 'Projects', 'People', 'Events'
        name: The filename (without .md extension)
    
    Returns:
        Parsed wiki dict with 'metadata' and 'content' keys.
    """
    path = os.path.join(BUSINESS_KB_DIR, "Wikis", category, f"{name}.md")
    return parse_wiki(path)


def list_business_wikis(category: str) -> list[str]:
    """List all wiki filenames (without .md) in a Business wiki category.
    
    Args:
        category: One of 'Salespersons', 'Customers', 'Projects', 'People', 'Events'
    
    Returns:
        List of filenames without the .md extension.
    """
    wiki_dir = os.path.join(BUSINESS_KB_DIR, "Wikis", category)
    if not os.path.exists(wiki_dir):
        return []
    return [
        f[:-3] for f in os.listdir(wiki_dir)
        if f.endswith(".md") and os.path.isfile(os.path.join(wiki_dir, f))
    ]


def load_business_structured_data() -> list[dict]:
    """Load the structured data JSONL from the Business KB."""
    path = os.path.join(BUSINESS_KB_DIR, "Structured_Data", "structured_data.jsonl")
    events = []
    if not os.path.exists(path):
        return events
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events
