# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Application Relational Model (backend/models/application.py)

import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False)
    application_type = Column(String(50), nullable=False, default="EOA")
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    total_intake_applied = Column(Integer, nullable=False, default=0)
    
    # Reviewer Assignment & Case Management (Phase P9)
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    review_status = Column(String(50), nullable=False, default="UNASSIGNED", index=True)  # 'UNASSIGNED', 'ASSIGNED', 'UNDER_SCRUTINY', 'PRE_SCRUTINY_RECOMMENDED_CLEAR', 'RETURNED_FOR_CORRECTION', 'FURTHER_REVIEW_REQUIRED'
    overall_reviewer_remarks = Column(String(2048), nullable=True)
    scrutiny_completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    institution = relationship("Institution", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    reviewer_observations = relationship("ReviewerObservation", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application {self.application_number} ({self.status}) [Review: {self.review_status}]>"
