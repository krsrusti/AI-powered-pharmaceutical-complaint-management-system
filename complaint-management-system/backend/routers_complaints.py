"""
Complaint retrieval endpoints — read-only access to saved complaints and
their audit trail. Creation/mutation happens exclusively through /chat and
/upload (routers_chat.py), since the whole point of this system is that the
form is never edited directly.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, load_complaint, list_complaints, get_audit_log, save_complaint
from schemas import Complaint, ComplaintStatus, REQUIRED_FIELDS

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.get("", response_model=list[Complaint])
def get_all_complaints(db: Session = Depends(get_db)) -> list[Complaint]:
    return list_complaints(db)


@router.get("/{complaint_id}", response_model=Complaint)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)) -> Complaint:
    complaint = load_complaint(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")
    return complaint


@router.get("/{complaint_id}/audit-log")
def get_complaint_audit_log(complaint_id: str, db: Session = Depends(get_db)):
    complaint = load_complaint(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")

    entries = get_audit_log(db, complaint_id)
    return [
        {
            "field": e.field,
            "old_value": e.old_value,
            "new_value": e.new_value,
            "source": e.source,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in entries
    ]


@router.patch("/{complaint_id}/submit", response_model=Complaint)
def submit_complaint(complaint_id: str, db: Session = Depends(get_db)) -> Complaint:
    """Backs the mockup's 'Save Complaint' button. Every AI turn already
    persists the complaint automatically (see routers_chat.py) — this
    endpoint is specifically for the deliberate user action of moving a
    complaint out of DRAFT, after confirming all required fields are present.
    Refuses to submit an incomplete complaint rather than silently allowing
    a half-filled record to be finalized."""
    complaint = load_complaint(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")

    missing = [f for f in REQUIRED_FIELDS if not getattr(complaint, f, None)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot save — missing required fields: {', '.join(missing).replace('_', ' ')}",
        )

    complaint.status = ComplaintStatus.SUBMITTED
    save_complaint(db, complaint)
    return complaint