# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# User Account Relational Model (backend/models/user.py)

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'INSTITUTION', 'REVIEWER', 'ADMIN'
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    institution = relationship("Institution", back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
