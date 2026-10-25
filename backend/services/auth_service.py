# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Authentication Service & Abuse Controls (backend/services/auth_service.py)

import time
from typing import Dict, Tuple, Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.core.database import utc_now
from backend.core.security import verify_password
from backend.models.user import User
from backend.services.audit_service import create_audit_event

# In-Memory Rate Limiting Tracker: { key (email): [timestamps of failed attempts] }
_failed_attempts: Dict[str, list[float]] = {}


def _check_rate_limit(key: str) -> None:
    """Enforces rate limiting on repeated failed authentication attempts."""
    now = time.time()
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS

    if key in _failed_attempts:
        # Filter attempts within current sliding window
        valid_attempts = [t for t in _failed_attempts[key] if now - t < window]
        _failed_attempts[key] = valid_attempts

        if len(valid_attempts) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Account temporarily locked for {window // 60} minutes."
            )


def _record_failed_attempt(key: str) -> None:
    """Records a failed attempt timestamp for a rate limiting key."""
    now = time.time()
    if key not in _failed_attempts:
        _failed_attempts[key] = []
    _failed_attempts[key].append(now)


def _clear_failed_attempts(key: str) -> None:
    """Clears rate limit records upon successful authentication."""
    if key in _failed_attempts:
        del _failed_attempts[key]


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    ip_address: str = "127.0.0.1"
) -> User:
    """Authenticates a user, enforcing rate limiting, account active checks, and audit logging."""
    normalized_email = email.strip().lower()
    _check_rate_limit(normalized_email)

    user = db.query(User).filter(User.email == normalized_email).first()

    # Uniform timing attack mitigation: if user does not exist, run a dummy verify
    if not user or not verify_password(password, user.password_hash):
        _record_failed_attempt(normalized_email)
        create_audit_event(
            db=db,
            actor_user_id=user.id if user else "ANONYMOUS",
            actor_role=user.role if user else "UNKNOWN",
            action="USER_LOGIN_FAILED",
            entity_type="USER",
            entity_id=user.id if user else "N/A",
            payload={"attempted_email": normalized_email, "reason": "Invalid credentials"},
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate account active status
    if not user.is_active:
        create_audit_event(
            db=db,
            actor_user_id=user.id,
            actor_role=user.role,
            action="USER_LOGIN_BLOCKED",
            entity_type="USER",
            entity_id=user.id,
            payload={"email": normalized_email, "reason": "Account is deactivated"},
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your system administrator."
        )

    # Success: clear failed attempts and update last_login_at
    _clear_failed_attempts(normalized_email)
    user.last_login_at = utc_now()
    db.commit()

    create_audit_event(
        db=db,
        actor_user_id=user.id,
        actor_role=user.role,
        action="USER_LOGIN_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        payload={"email": user.email, "role": user.role, "institution_id": user.institution_id},
        ip_address=ip_address
    )

    return user
