"""
LangGraph shared state definition.

This TypedDict is what flows through every node in the graph (see
graph_workflow.py). Each node reads what it needs and writes back updates —
LangGraph merges returned dict keys into this state automatically.

Keeping `previous_complaint` alongside `complaint` is what makes change-aware
risk re-assessment possible: the risk node needs to see the state BEFORE this
turn's edits to decide whether the change actually matters.
"""

from typing import TypedDict, Optional, List
from schemas import (
    Complaint,
    FieldDiff,
    CompletenessResult,
    DuplicateCheckResult,
)


class GraphState(TypedDict, total=False):
    # --- Input ---
    complaint_id: str
    raw_input_text: str          # chat message text, or extracted document text
    is_document_upload: bool
    is_new_complaint: bool

    # --- Complaint state ---
    complaint: Complaint
    previous_complaint: Optional[Complaint]   # snapshot before this turn's edits
    existing_complaints: List[Complaint]      # loaded by router, used for duplicate check

    # --- Intermediate ---
    extraction_result: Optional[dict]         # raw LLM output from extract_node, consumed by merge_node

    # --- Node outputs ---
    diff: List[FieldDiff]
    ai_message: str
    completeness: CompletenessResult
    duplicates: DuplicateCheckResult
    risk_changed: bool

    # --- Error handling ---
    error: Optional[str]          # set if a node fails; downstream nodes should check this
    extracted_text_preview: Optional[str]   # for document uploads, shown to user