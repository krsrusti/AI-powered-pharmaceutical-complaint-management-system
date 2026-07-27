"""
Complaint retrieval endpoints — read-only access to saved complaints and
their audit trail. Creation/mutation happens exclusively through /chat and
/upload (routers_chat.py), since the whole point of this system is that the
form is never edited directly.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, load_complaint, list_complaints, get_audit_log
from schemas import Complaint

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