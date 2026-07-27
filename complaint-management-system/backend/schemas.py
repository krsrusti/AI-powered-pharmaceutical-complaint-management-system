"""
Core data models for the AI Complaint Management System.

The Complaint schema is the single source of truth that every LangGraph node
reads from and writes to. Keep field names stable — routers, prompts, and the
frontend form all key off these exact names.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ComplaintCategory(str, Enum):
    QUALITY_DEFECT = "quality_defect"
    PACKAGING = "packaging"
    LABELING = "labeling"
    POTENCY_STRENGTH = "potency_strength"
    CONTAMINATION = "contamination"
    ADVERSE_EVENT = "adverse_event"          # flagged, not auto-reported (out of scope)
    OTHER = "other"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNASSESSED = "unassessed"


class ComplaintStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_INVESTIGATION = "under_investigation"
    CLOSED = "closed"


class FieldSource(str, Enum):
    """Where a field's current value came from — used for confidence display."""
    USER_STATED = "user_stated"      # explicitly said by the user
    AI_INFERRED = "ai_inferred"      # LLM inferred/guessed
    UNSET = "unset"


# ---------------------------------------------------------------------------
# Complaint core model
# ---------------------------------------------------------------------------

class CustomerDetails(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None       # e.g. "Apollo Hospital"
    contact_info: Optional[str] = None


class ManufacturingInfo(BaseModel):
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    manufacturing_site: Optional[str] = None


class RiskAssessment(BaseModel):
    risk_level: RiskLevel = RiskLevel.UNASSESSED
    product_impact: Optional[str] = None
    patient_impact: Optional[str] = None
    investigation_priority: Optional[str] = None
    reasoning_summary: Optional[str] = None
    rubric_criteria_matched: List[str] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    changed_this_turn: bool = False   # True only if this turn's edit actually altered risk


class Complaint(BaseModel):
    complaint_id: str

    # --- Origin & customer ---
    complaint_source: Optional[str] = None      # e.g. "Phone call", "Email", "Distributor report"
    customer_details: CustomerDetails = Field(default_factory=CustomerDetails)

    # --- Product & batch identification ---
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None   # e.g. "500mg"
    batch_number: Optional[str] = None
    manufacturing_info: ManufacturingInfo = Field(default_factory=ManufacturingInfo)

    # --- Complaint details ---
    complaint_type: Optional[ComplaintCategory] = None   # UI label "Complaint Type" -> same as complaint_category
    complaint_date: Optional[str] = None                  # date the complaint was received
    complaint_description: Optional[str] = None
    affected_quantity: Optional[str] = None
    affected_quantity_unit: Optional[str] = None          # e.g. "kg", "tablets", "capsules", "units"

    status: ComplaintStatus = ComplaintStatus.DRAFT
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Frontend status badge labels (mockup shows "Pending Triage" for a new/draft
# complaint) — kept as a display-only mapping so the backend enum values stay
# stable and machine-readable.
STATUS_DISPLAY_LABELS = {
    ComplaintStatus.DRAFT: "Pending Triage",
    ComplaintStatus.SUBMITTED: "Submitted",
    ComplaintStatus.UNDER_INVESTIGATION: "Under Investigation",
    ComplaintStatus.CLOSED: "Closed",
}


# Fields required before a complaint can move out of DRAFT — used by the
# completeness checker node.
REQUIRED_FIELDS = [
    "product_name",
    "batch_number",
    "complaint_description",
    "complaint_type",
    "affected_quantity",
]

# Fields whose change should trigger a risk re-assessment (Tier 2, change-aware).
RISK_RELEVANT_FIELDS = [
    "complaint_description",
    "complaint_type",
    "affected_quantity",
    "affected_quantity_unit",
    "product_name",
]


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    complaint_id: Optional[str] = None   # None = start a new complaint
    message: str


class FieldDiff(BaseModel):
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    source: FieldSource = FieldSource.AI_INFERRED


class CompletenessResult(BaseModel):
    is_complete: bool
    missing_fields: List[str] = Field(default_factory=list)
    message: Optional[str] = None   # e.g. "Missing batch number and quantity"


class DuplicateMatch(BaseModel):
    complaint_id: str
    similarity_score: float
    matched_on: List[str] = Field(default_factory=list)   # e.g. ["batch_number", "description"]


class DuplicateCheckResult(BaseModel):
    has_duplicates: bool
    matches: List[DuplicateMatch] = Field(default_factory=list)


class ChatResponse(BaseModel):
    complaint_id: str
    complaint: Complaint
    diff: List[FieldDiff] = Field(default_factory=list)
    ai_message: str                        # natural-language reply shown in chat
    completeness: CompletenessResult
    duplicates: DuplicateCheckResult
    risk_changed: bool


class UploadResponse(ChatResponse):
    extracted_text_preview: Optional[str] = None