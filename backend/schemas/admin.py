# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Administrator Workspace Schemas (backend/schemas/admin.py)

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, Field


class AdminOverviewMetrics(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    total_reviewers: int
    total_institutions: int
    total_applications: int
    applications_by_status: Dict[str, int]
    applications_by_review_status: Dict[str, int]
    total_findings: int
    total_audit_events: int


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(..., description="INSTITUTION, REVIEWER, ADMIN")
    institution_id: Optional[str] = None
    is_active: bool = True


class AdminUserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[str] = Field(None, description="INSTITUTION, REVIEWER, ADMIN")
    institution_id: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminInstitutionResponse(BaseModel):
    id: str
    aicte_permanent_id: str
    name: str
    category: str
    state: str
    district: str
    is_rural: bool
    created_at: datetime
    applications_count: int = 0
    users_count: int = 0

    model_config = {"from_attributes": True}


class AdminInstitutionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    is_rural: Optional[bool] = None


class AdminAuditEventResponse(BaseModel):
    id: str
    actor_user_id: str
    actor_email: Optional[str] = None
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    payload_json: str
    ip_address: str
    created_at: datetime

    model_config = {"from_attributes": True}
