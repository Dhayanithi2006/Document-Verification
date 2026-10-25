# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Reviewer Scrutiny Observation Relational Model (backend/models/reviewer.py)

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class ReviewerObservation(Base):
    """
    Official scrutiny observation, annotation, or decision recorded by an authorised human reviewer
    during application pre-scrutiny case review.
    """
    __tablename__ = "reviewer_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="SET NULL"), nullable=True, index=True)
    submission_id = Column(String(36), ForeignKey("correction_submissions.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewer_user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Decision:
    # Finding-level: 'CONCUR_DEFICIENCY', 'ACCEPT_CORRECTION', 'OVERRULE_DEFICIENCY', 'REQUIRE_ADDITIONAL_EVIDENCE', 'GENERAL_OBSERVATION'
    # Application-level: 'PRE_SCRUTINY_RECOMMENDED_CLEAR', 'RETURNED_FOR_CORRECTION', 'FURTHER_REVIEW_REQUIRED'
    decision = Column(String(50), nullable=False)
    justification = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    application = relationship("Application", back_populates="reviewer_observations")
    finding = relationship("Finding")
    submission = relationship("CorrectionSubmission")
    reviewer = relationship("User", foreign_keys=[reviewer_user_id])

    def __repr__(self) -> str:
        return f"<ReviewerObservation {self.id} on App {self.application_id}: {self.decision}>"
