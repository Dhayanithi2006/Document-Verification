# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Reviewer Scrutiny Schemas (backend/schemas/reviewer.py)

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ReviewerQueueItemResponse(BaseModel):
    id: str
    application_number: str
    institution_id: str
    institution_name: str
    aicte_permanent_id: str
    state: str
    district: str
    academic_year: str
    application_type: str
    status: str
    review_status: str
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    deficiencies_count: int = 0
    warnings_count: int = 0
    awaiting_review_count: int = 0
    correction_submitted_count: int = 0
    pre_scrutiny_score: int = 100
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewerQueueMetrics(BaseModel):
    total_applications: int
    assigned_to_me: int
    unassigned: int
    under_scrutiny: int
    awaiting_review: int
    recommended_clear: int
    returned_for_correction: int


class ReviewerQueueResponse(BaseModel):
    items: List[ReviewerQueueItemResponse]
    total: int
    page: int
    limit: int
    metrics: ReviewerQueueMetrics


class AssignReviewerRequest(BaseModel):
    target_reviewer_id: str = Field(..., description="ID of active user with REVIEWER or ADMIN role")
    remarks: Optional[str] = Field(None, max_length=1000)


class ReviewerObservationCreate(BaseModel):
    finding_id: Optional[str] = None
    submission_id: Optional[str] = None
    decision: str = Field(..., description="CONCUR_DEFICIENCY, ACCEPT_CORRECTION, OVERRULE_DEFICIENCY, REQUIRE_ADDITIONAL_EVIDENCE, GENERAL_OBSERVATION")
    justification: str = Field(..., min_length=5, max_length=4000)
    is_internal_note: bool = False


class ReviewerObservationResponse(BaseModel):
    id: str
    application_id: str
    finding_id: Optional[str] = None
    submission_id: Optional[str] = None
    reviewer_user_id: str
    reviewer_name: Optional[str] = None
    decision: str
    justification: str
    is_internal_note: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewerDecisionRequest(BaseModel):
    decision: str = Field(..., description="PRE_SCRUTINY_RECOMMENDED_CLEAR, RETURNED_FOR_CORRECTION, FURTHER_REVIEW_REQUIRED")
    remarks: str = Field(..., min_length=10, max_length=4000)


class ReviewerScrutinyDetailResponse(BaseModel):
    application: ReviewerQueueItemResponse
    checklist: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    correction_submissions: List[Dict[str, Any]]
    observations: List[ReviewerObservationResponse]
    revalidation_comparison: List[Dict[str, Any]]
    eligible_actions: List[str]
