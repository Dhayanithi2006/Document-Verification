# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Audit Event Model (backend/models/audit.py)

import uuid
from sqlalchemy import Column, String, DateTime
from backend.core.database import Base, utc_now


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id = Column(String(36), nullable=False, index=True)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False)
    payload_json = Column(String(2048), nullable=False, default="{}")
    ip_address = Column(String(50), nullable=False, default="127.0.0.1")
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)

    def __repr__(self) -> str:
        return f"<AuditEvent {self.action} on {self.entity_type}:{self.entity_id} by {self.actor_user_id}>"
