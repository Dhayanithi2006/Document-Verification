# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Relational Model: Correction Submissions & Deficiency Resolution Lifecycle (backend/models/deficiency.py)

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CorrectionSubmission(Base):
    """
    Immutable and versioned correction response record submitted by an authorised applicant
    against an identified pre-scrutiny finding.
    Supports draft iteration, supporting document (v2/v3) attachment, delta revalidation,
    and before-versus-after outcome comparison.
    """
    __tablename__ = "correction_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False, default=1)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Lifecycle Status: 'DRAFT', 'SUBMITTED', 'SUPERSEDED'
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    
    # Response Content
    response_text = Column(Text, nullable=False)
    response_category = Column(String(50), nullable=False, default="DOCUMENT_REPLACEMENT")  # 'DOCUMENT_REPLACEMENT', 'CLARIFICATION_JUSTIFICATION', 'CORRECTION_AFFIDAVIT'
    
    # Attached Corrected Supporting Document (P5 Document & DocumentVersion references)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Validation Run Provenance: Before vs After Revalidation
    initial_validation_run_id = Column(String(36), ForeignKey("validation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    revalidation_run_id = Column(String(36), ForeignKey("validation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Revalidation Results
    revalidation_status = Column(String(50), nullable=True)  # 'PENDING', 'COMPLETED', 'FAILED'
    resolution_outcome = Column(String(50), nullable=True)   # 'CONDITION_CLEARED', 'CONDITION_PERSISTS', 'NEEDS_HUMAN_REVIEW', 'UNABLE_TO_EVALUATE'
    comparison_notes = Column(Text, nullable=True)           # Human-readable summary of parameter change
    
    # Reviewer Handoff & Governance (P8 prepares; P9 consumes)
    reviewer_disposition = Column(String(50), nullable=True)  # 'PENDING_REVIEW', 'ACCEPTED', 'RETURNED_FOR_CORRECTION', 'OVERRULED'
    reviewer_notes = Column(Text, nullable=True)
    reviewed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    finding = relationship("Finding", backref="correction_submissions")
    application = relationship("Application", backref="correction_submissions")
    user = relationship("User", foreign_keys=[user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    document = relationship("Document")
    document_version = relationship("DocumentVersion")
    initial_validation_run = relationship("ValidationRun", foreign_keys=[initial_validation_run_id])
    revalidation_run = relationship("ValidationRun", foreign_keys=[revalidation_run_id])

    def __repr__(self) -> str:
        return f"<CorrectionSubmission {self.id} [Finding: {self.finding_id}] Cycle {self.cycle_number} ({self.status})>"
