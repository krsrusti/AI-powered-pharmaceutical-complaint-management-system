"""
Database layer — SQLite via SQLAlchemy.

Two tables:
  - complaints: one row per complaint, storing the full Complaint schema as JSON
                (simplest reliable way to persist a nested Pydantic model without
                maintaining a parallel relational schema for an assignment scope).
  - audit_log:  one row per field change, so every AI edit is traceable —
                this is what the diff/changelog UI reads from.

Rationale for JSON-blob storage: the assignment scope doesn't need relational
querying across complaint fields (e.g. "find all complaints where quantity > X"),
so a normalized schema would add complexity without real payoff here. Duplicate
detection queries against product_name/batch_number/description are done by
loading rows and comparing in Python (see duplicate_detector.py), which is fine
at assignment scale. Noting this as a known scaling limitation.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from config import settings
from schemas import Complaint

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class ComplaintRecord(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String, primary_key=True, index=True)
    data = Column(Text, nullable=False)           # JSON-serialized Complaint
    status = Column(String, index=True, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String, index=True, nullable=False)
    field = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    source = Column(String, nullable=False)        # "user_stated" | "ai_inferred"
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def save_complaint(db: Session, complaint: Complaint) -> None:
    complaint.updated_at = datetime.utcnow()
    payload = complaint.model_dump_json()

    record = db.get(ComplaintRecord, complaint.complaint_id)
    if record is None:
        record = ComplaintRecord(
            complaint_id=complaint.complaint_id,
            data=payload,
            status=complaint.status.value,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at,
        )
        db.add(record)
    else:
        record.data = payload
        record.status = complaint.status.value
        record.updated_at = complaint.updated_at

    db.commit()


def load_complaint(db: Session, complaint_id: str) -> Optional[Complaint]:
    record = db.get(ComplaintRecord, complaint_id)
    if record is None:
        return None
    return Complaint(**json.loads(record.data))


def list_complaints(db: Session) -> List[Complaint]:
    records = db.query(ComplaintRecord).order_by(ComplaintRecord.updated_at.desc()).all()
    return [Complaint(**json.loads(r.data)) for r in records]


def new_complaint_id() -> str:
    return f"CMP-{uuid.uuid4().hex[:8].upper()}"


def log_field_change(
    db: Session,
    complaint_id: str,
    field: str,
    old_value: Optional[str],
    new_value: Optional[str],
    source: str,
) -> None:
    entry = AuditLogEntry(
        complaint_id=complaint_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        source=source,
    )
    db.add(entry)
    db.commit()


def get_audit_log(db: Session, complaint_id: str) -> List[AuditLogEntry]:
    return (
        db.query(AuditLogEntry)
        .filter(AuditLogEntry.complaint_id == complaint_id)
        .order_by(AuditLogEntry.timestamp.asc())
        .all()
    )