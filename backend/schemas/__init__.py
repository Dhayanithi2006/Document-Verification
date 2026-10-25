# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Schemas Package Initialization (backend/schemas/__init__.py)

from backend.schemas.institution import InstitutionBase, InstitutionCreate, InstitutionResponse
from backend.schemas.user import UserBase, UserCreate, UserResponse
from backend.schemas.auth import LoginRequest, TokenResponse, LogoutResponse
from backend.schemas.application import ApplicationResponse, ApplicationCreate, ApplicationUpdate
from backend.schemas.document import (
    DocumentResponse,
    DocumentVersionResponse,
    ChecklistResponse,
    DocumentUploadResponse,
)
from backend.schemas.health import LivenessResponse, ReadinessResponse
from backend.schemas.extraction import (
    BoundingBox,
    ExtractedFieldResponse,
    DocumentPageResponse,
    DocumentProcessingStatusResponse,
    DocumentExtractionResultResponse,
    ReprocessRequest,
)

__all__ = [
    "InstitutionBase",
    "InstitutionCreate",
    "InstitutionResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "LogoutResponse",
    "ApplicationResponse",
    "ApplicationCreate",
    "ApplicationUpdate",
    "DocumentResponse",
    "DocumentVersionResponse",
    "ChecklistResponse",
    "DocumentUploadResponse",
    "LivenessResponse",
    "ReadinessResponse",
    "BoundingBox",
    "ExtractedFieldResponse",
    "DocumentPageResponse",
    "DocumentProcessingStatusResponse",
    "DocumentExtractionResultResponse",
    "ReprocessRequest",
    # Regulatory
    "FindingResponse",
    "ValidationRunResponse",
    "ApplicationFindingsResponse",
    "RegulatoryRuleResponse",
    # Deficiency & Corrective Action
    "CorrectionDraftRequest",
    "CorrectionSubmitRequest",
    "CorrectionSubmissionResponse",
    "DeficiencyItemResponse",
    "ApplicationDeficienciesResponse",
    "ComparisonItem",
    "RevalidationResponse",
    "TimelineEvent",
    "FindingHistoryResponse",
    # Reviewer Schemas
    "ReviewerQueueItemResponse",
    "ReviewerQueueMetrics",
    "ReviewerQueueResponse",
    "AssignReviewerRequest",
    "ReviewerObservationCreate",
    "ReviewerObservationResponse",
    "ReviewerDecisionRequest",
    "ReviewerScrutinyDetailResponse",
    # Admin Schemas
    "AdminOverviewMetrics",
    "AdminUserCreateRequest",
    "AdminUserUpdateRequest",
    "AdminUserResponse",
    "AdminInstitutionResponse",
    "AdminInstitutionUpdateRequest",
    "AdminAuditEventResponse",
]

from backend.schemas.regulatory import (
    FindingResponse,
    ValidationRunResponse,
    ApplicationFindingsResponse,
    RegulatoryRuleResponse,
)
from backend.schemas.deficiency import (
    CorrectionDraftRequest,
    CorrectionSubmitRequest,
    CorrectionSubmissionResponse,
    DeficiencyItemResponse,
    ApplicationDeficienciesResponse,
    ComparisonItem,
    RevalidationResponse,
    TimelineEvent,
    FindingHistoryResponse,
)
from backend.schemas.reviewer import (
    ReviewerQueueItemResponse,
    ReviewerQueueMetrics,
    ReviewerQueueResponse,
    AssignReviewerRequest,
    ReviewerObservationCreate,
    ReviewerObservationResponse,
    ReviewerDecisionRequest,
    ReviewerScrutinyDetailResponse,
)
from backend.schemas.admin import (
    AdminOverviewMetrics,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AdminUserResponse,
    AdminInstitutionResponse,
    AdminInstitutionUpdateRequest,
    AdminAuditEventResponse,
)


