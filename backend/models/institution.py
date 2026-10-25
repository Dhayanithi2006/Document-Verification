# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Institution Relational Model (backend/models/institution.py)

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aicte_permanent_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="ENGINEERING_TECHNOLOGY")
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    is_rural = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Institution {self.aicte_permanent_id}: {self.name}>"
