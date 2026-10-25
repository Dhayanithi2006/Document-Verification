# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Pydantic Schemas: Deficiency Resolution & Corrective Actions (backend/schemas/deficiency.py)

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.schemas.regulatory import FindingEvidence


class CorrectionDraftRequest(BaseModel):
    """Payload to save or update an applicant's draft correction response."""
    response_text: str = Field(..., min_length=5, max_length=5000, description="Applicant explanation or remediation notes")
    response_category: str = Field(default="DOCUMENT_REPLACEMENT", description="DOCUMENT_REPLACEMENT, CLARIFICATION_JUSTIFICATION, or CORRECTION_AFFIDAVIT")
    document_id: Optional[str] = Field(default=None, description="Referenced supporting document ID")
    document_version_id: Optional[str] = Field(default=None, description="Exact supporting document version ID")


class CorrectionSubmitRequest(BaseModel):
    """Payload to formally submit a corrective response."""
    response_text: str = Field(..., min_length=10, max_length=5000, description="Final formal corrective response text")
    response_category: str = Field(default="DOCUMENT_REPLACEMENT")
    document_id: Optional[str] = None
    document_version_id: Optional[str] = None


class CorrectionSubmissionResponse(BaseModel):
    """Serialised correction submission or draft."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: str
    application_id: str
    cycle_number: int
    user_id: str
    status: str  # 'DRAFT', 'SUBMITTED', 'SUPERSEDED'
    response_text: str
    response_category: str
    document_id: Optional[str] = None
    document_version_id: Optional[str] = None
    initial_validation_run_id: Optional[str] = None
    revalidation_run_id: Optional[str] = None
    revalidation_status: Optional[str] = None
    resolution_outcome: Optional[str] = None
    comparison_notes: Optional[str] = None
    reviewer_disposition: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None


class DeficiencyItemResponse(BaseModel):
    """Comprehensive deficiency item including finding details and current resolution state."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    validation_run_id: str
    application_id: str
    rule_code: str
    rule_title: str
    official_source: Optional[str] = None
    category: str
    severity: str
    outcome: str
    status: str
    title: str
    explanation: str
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    evidence: FindingEvidence
    verification_status: str
    recommended_action: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Workflow & Resolution additions
    resolution_status: str  # OPEN, ACKNOWLEDGED, RESPONSE_IN_PROGRESS, CORRECTION_SUBMITTED, AWAITING_REVIEW, RESOLVED
    active_draft: Optional[CorrectionSubmissionResponse] = None
    latest_submission: Optional[CorrectionSubmissionResponse] = None
    document_title: Optional[str] = None


class ApplicationDeficienciesResponse(BaseModel):
    """Collection response for an application's actionable deficiency workspace."""
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    application_status: str
    total_deficiencies: int
    actionable_count: int
    acknowledged_count: int
    in_progress_count: int
    submitted_count: int
    awaiting_review_count: int
    resolved_count: int
    latest_validation_run_id: Optional[str] = None
    deficiencies: List[DeficiencyItemResponse]


class ComparisonItem(BaseModel):
    """Delta comparison between previous finding and revalidated outcome."""
    finding_id: str
    rule_code: str
    rule_title: str
    previous_outcome: str
    latest_outcome: str
    status_change: str  # 'CLEARED', 'PERSISTS', 'NEW', 'UNCHANGED'
    previous_observed_value: Optional[str] = None
    latest_observed_value: Optional[str] = None
    details: str


class RevalidationResponse(BaseModel):
    """Outcome of invoking the regulatory engine for revalidation."""
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    validation_run_id: str
    run_number: int
    status: str
    total_checks: int
    findings_cleared: int
    findings_persisting: int
    new_findings: int
    comparison: List[ComparisonItem]


class TimelineEvent(BaseModel):
    """Single chronological timeline entry for finding history."""
    event_type: str  # 'FINDING_IDENTIFIED', 'ACKNOWLEDGED', 'DRAFT_SAVED', 'CORRECTION_SUBMITTED', 'DOCUMENT_UPLOADED', 'REVALIDATION_RUN', 'REVIEWER_DISPOSITION'
    timestamp: datetime
    actor: Optional[str] = None
    actor_role: Optional[str] = None
    description: str
    details: Optional[Dict[str, Any]] = None


class FindingHistoryResponse(BaseModel):
    """Complete chronological audit trail for a single deficiency finding."""
    finding_id: str
    application_id: str
    history: List[TimelineEvent]
