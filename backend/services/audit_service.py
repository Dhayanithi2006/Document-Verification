# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Audit Service (backend/services/audit_service.py)

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.audit import AuditEvent


def create_audit_event(
    db: Session,
    actor_user_id: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1"
) -> AuditEvent:
    """Records an immutable forensic audit event in the database."""
    # Sanitize payload: never log secrets, passwords, or raw tokens
    sanitized_payload = payload.copy() if payload else {}
    for sensitive_key in ["password", "token", "access_token", "secret", "secret_key"]:
        if sensitive_key in sanitized_payload:
            sanitized_payload[sensitive_key] = "[REDACTED]"

    event = AuditEvent(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=json.dumps(sanitized_payload),
        ip_address=ip_address
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
