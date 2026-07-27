"""
Chat + document upload endpoints.

This is the orchestration layer: load state from DB -> run the LangGraph
workflow -> persist results -> log the audit trail -> return a structured
response. Nodes themselves never touch the database (see graph_nodes.py) —
that separation is deliberate, so the graph stays pure/testable and all
persistence logic lives in one place.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from database import (
    get_db,
    save_complaint,
    load_complaint,
    list_complaints,
    new_complaint_id,
    log_field_change,
)
from schemas import Complaint, ChatRequest, ChatResponse, UploadResponse
from graph_workflow import complaint_workflow
from graph_state import GraphState
from document_parser import extract_text, DocumentParsingError

router = APIRouter(tags=["chat"])


def _get_or_create_complaint(db: Session, complaint_id: str | None) -> Complaint:
    if complaint_id:
        complaint = load_complaint(db, complaint_id)
        if complaint is None:
            raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")
        return complaint
    return Complaint(complaint_id=new_complaint_id())


def _run_workflow(db: Session, complaint: Complaint, raw_text: str, is_document: bool) -> GraphState:
    existing = [c for c in list_complaints(db) if c.complaint_id != complaint.complaint_id]

    initial_state: GraphState = {
        "complaint_id": complaint.complaint_id,
        "complaint": complaint,
        "raw_input_text": raw_text,
        "is_document_upload": is_document,
        "existing_complaints": existing,
    }

    result_state = complaint_workflow.invoke(initial_state)
    return result_state


def _persist_and_log(db: Session, complaint: Complaint, diff: list) -> None:
    save_complaint(db, complaint)
    for change in diff:
        log_field_change(
            db,
            complaint_id=complaint.complaint_id,
            field=change.field,
            old_value=change.old_value,
            new_value=change.new_value,
            source=change.source.value,
        )


def _build_chat_response(state: GraphState) -> ChatResponse:
    complaint = state["complaint"]
    return ChatResponse(
        complaint_id=complaint.complaint_id,
        complaint=complaint,
        diff=state.get("diff", []),
        ai_message=state.get("ai_message", "Complaint updated."),
        completeness=state["completeness"],
        duplicates=state["duplicates"],
        risk_changed=state.get("risk_changed", False),
    )


# ---------------------------------------------------------------------------
# POST /chat — natural-language message (new complaint or follow-up edit)
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    complaint = _get_or_create_complaint(db, request.complaint_id)
    result_state = _run_workflow(db, complaint, request.message, is_document=False)

    if result_state.get("error"):
        # Persist nothing on extraction/validation failure — surface the
        # error message but don't silently corrupt saved state.
        raise HTTPException(
            status_code=422,
            detail=result_state.get("ai_message", "Failed to process message."),
        )

    _persist_and_log(db, result_state["complaint"], result_state.get("diff", []))
    return _build_chat_response(result_state)


# ---------------------------------------------------------------------------
# POST /upload — document upload (PDF, email, image, txt)
# ---------------------------------------------------------------------------

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB, matches frontend-stated limit


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    complaint_id: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit")

    try:
        extracted_text = extract_text(file_bytes, file.filename or "")
    except DocumentParsingError as e:
        raise HTTPException(status_code=422, detail=str(e))

    complaint = _get_or_create_complaint(db, complaint_id)
    result_state = _run_workflow(db, complaint, extracted_text, is_document=True)

    if result_state.get("error"):
        raise HTTPException(
            status_code=422,
            detail=result_state.get("ai_message", "Failed to process document."),
        )

    _persist_and_log(db, result_state["complaint"], result_state.get("diff", []))
    response = _build_chat_response(result_state)

    return UploadResponse(
        **response.model_dump(),
        extracted_text_preview=extracted_text[:500],
    )