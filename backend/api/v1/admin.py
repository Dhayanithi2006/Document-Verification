# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Administrator Workspace Endpoints (backend/api/v1/admin.py)

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import require_admin, require_reviewer
from backend.models.user import User
from backend.schemas.admin import (
    AdminOverviewMetrics,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AdminUserResponse,
    AdminInstitutionResponse,
    AdminInstitutionUpdateRequest,
    AdminAuditEventResponse,
)
from backend.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Administrator Workspace"])


@router.get("/overview", response_model=AdminOverviewMetrics)
def get_admin_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieves live system overview metrics across users, institutions, and applications."""
    service = AdminService(db)
    return service.get_overview_metrics()


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lists registered user accounts with role, status, and linked educational institutions."""
    service = AdminService(db)
    return service.list_users(role=role, is_active=is_active, search=search, skip=skip, limit=limit)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Provisions a new user account with hashed password and role permissions."""
    service = AdminService(db)
    return service.create_user(payload=payload, current_user=current_user)


@router.patch("/users/{id}", response_model=AdminUserResponse)
def update_user(
    id: str,
    payload: AdminUserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Updates user account details, role permissions, or active status."""
    service = AdminService(db)
    return service.update_user(user_id=id, payload=payload, current_user=current_user)


@router.get("/institutions", response_model=List[AdminInstitutionResponse])
def list_institutions(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lists registered institutions with application counts."""
    service = AdminService(db)
    return service.list_institutions(search=search, skip=skip, limit=limit)


@router.patch("/institutions/{id}", response_model=AdminInstitutionResponse)
def update_institution(
    id: str,
    payload: AdminInstitutionUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Updates non-sensitive institutional metadata (e.g. name, location, rural classification)."""
    service = AdminService(db)
    return service.update_institution(institution_id=id, payload=payload, current_user=current_user)


@router.get("/audit-events", response_model=List[AdminAuditEventResponse])
def list_audit_events(
    action: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Queries immutable forensic security audit logs (accessible to Reviewers & Administrators)."""
    service = AdminService(db)
    return service.list_audit_events(
        action=action,
        actor_role=actor_role,
        entity_type=entity_type,
        skip=skip,
        limit=limit,
    )
