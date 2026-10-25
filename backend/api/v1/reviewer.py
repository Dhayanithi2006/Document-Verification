# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Reviewer Scrutiny Endpoints (backend/api/v1/reviewer.py)

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import require_reviewer
from backend.models.user import User
from backend.schemas.reviewer import (
    ReviewerQueueResponse,
    ReviewerQueueItemResponse,
    ReviewerScrutinyDetailResponse,
    AssignReviewerRequest,
    ReviewerObservationCreate,
    ReviewerObservationResponse,
    ReviewerDecisionRequest,
)
from backend.services.reviewer_service import ReviewerService

router = APIRouter(prefix="/reviewer", tags=["Reviewer Scrutiny Console"])


@router.get("/queue", response_model=ReviewerQueueResponse)
def get_reviewer_queue(
    status_filter: Optional[str] = Query(None, alias="status"),
    review_status_filter: Optional[str] = Query(None, alias="review_status"),
    assigned_filter: Optional[str] = Query(None, alias="assigned"),
    academic_year: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Retrieves paginated applications for authorised scrutiny with queue metrics."""
    service = ReviewerService(db)
    return service.get_reviewer_queue(
        current_user=current_user,
        status_filter=status_filter,
        review_status_filter=review_status_filter,
        assigned_filter=assigned_filter,
        academic_year=academic_year,
        search=search,
        page=page,
        limit=limit,
    )


@router.get("/applications/{id}/scrutiny", response_model=ReviewerScrutinyDetailResponse)
def get_scrutiny_details(
    id: str,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Retrieves comprehensive scrutiny case details, findings, submissions, and observations."""
    service = ReviewerService(db)
    return service.get_scrutiny_case_details(application_id=id, current_user=current_user)


@router.post("/applications/{id}/assign", response_model=ReviewerQueueItemResponse)
def assign_reviewer_case(
    id: str,
    payload: AssignReviewerRequest,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Assigns or reassigns an application to an active scrutiny reviewer."""
    service = ReviewerService(db)
    return service.assign_reviewer(
        application_id=id,
        target_reviewer_id=payload.target_reviewer_id,
        current_user=current_user,
        remarks=payload.remarks,
    )


@router.post("/applications/{id}/observations", response_model=ReviewerObservationResponse, status_code=status.HTTP_201_CREATED)
def record_observation(
    id: str,
    payload: ReviewerObservationCreate,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Records an official scrutiny observation or finding disposition."""
    service = ReviewerService(db)
    return service.record_scrutiny_observation(
        application_id=id,
        payload=payload,
        current_user=current_user,
    )


@router.post("/applications/{id}/decision", response_model=ReviewerQueueItemResponse)
def complete_prescrutiny_decision(
    id: str,
    payload: ReviewerDecisionRequest,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Records formal pre-scrutiny recommendation (e.g. Recommended Clear, Returned for Correction).
    
    Advisory Disclaimer: Automated checks and scrutiny recommendations do not constitute official statutory AICTE approval.
    """
    service = ReviewerService(db)
    return service.complete_prescrutiny_review(
        application_id=id,
        decision=payload.decision,
        remarks=payload.remarks,
        current_user=current_user,
    )
