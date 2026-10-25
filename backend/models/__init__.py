# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Models Package Initialization (backend/models/__init__.py)

from backend.models.institution import Institution
from backend.models.user import User
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.audit import AuditEvent
from backend.models.extraction import DocumentProcessingRun, ExtractedField, DocumentPage
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, ValidationRun, Finding
from backend.models.deficiency import CorrectionSubmission
from backend.models.reviewer import ReviewerObservation

__all__ = [
    "Institution",
    "User",
    "Application",
    "Document",
    "DocumentVersion",
    "AuditEvent",
    "DocumentProcessingRun",
    "ExtractedField",
    "DocumentPage",
    "RegulatoryRule",
    "RegulatoryRuleVersion",
    "ValidationRun",
    "Finding",
    "CorrectionSubmission",
    "ReviewerObservation",
]

