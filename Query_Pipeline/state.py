from typing import TypedDict, Optional


class DBResult(TypedDict, total=False):
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    error: str


class QuestionItem(TypedDict, total=False):
    index: int
    text: str
    needs_db: Optional[bool]
    db_results: Optional[DBResult]


class PipelineState(TypedDict, total=False):
    salesperson_id: str
    raw_query: str
    salesperson_info: dict
    normalized_query: str
    questions: list[QuestionItem]
    final_response: str
    error: str
