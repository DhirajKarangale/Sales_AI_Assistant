from typing import TypedDict, Optional


class DBResult(TypedDict, total=False):
    """Result from a single DB query execution."""
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    error: str


class QuestionItem(TypedDict, total=False):
    """A single extracted question with its metadata and results."""
    index: int
    text: str
    needs_db: Optional[bool]
    db_results: Optional[DBResult]


class PipelineState(TypedDict, total=False):
    """Top-level LangGraph state for the query-response pipeline."""

    # --- Inputs ---
    salesperson_id: str
    raw_query: str

    # --- Query Optimizer outputs ---
    salesperson_info: dict
    normalized_query: str
    questions: list[QuestionItem]

    # --- Response Generator output ---
    final_response: str

    # --- Control flow ---
    error: str
