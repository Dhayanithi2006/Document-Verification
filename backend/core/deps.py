# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Security Dependencies & RBAC Guards (backend/core/deps.py)

from typing import List, Callable
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.security import decode_access_token, is_token_revoked
from backend.models.user import User
from backend.models.application import Application

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Validates JWT access token, checks revocation, and returns authenticated user."""
    # Support both OAuth2 scheme and direct Authorization header
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token revocation
    if is_token_revoked(raw_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked upon logout. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw_token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Access denied."
        )

    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Generates an endpoint dependency enforcing Server-Side Role-Based Access Control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient permissions for role '{current_user.role}'."
            )
        return current_user
    return role_checker


# Pre-configured RBAC dependencies
require_institution = require_roles("INSTITUTION")
require_reviewer = require_roles("REVIEWER", "ADMIN")
require_admin = require_roles("ADMIN")


def verify_institution_access(application: Application, current_user: User) -> None:
    """Enforces server-side tenant isolation.
    If the caller is an INSTITUTION user, prevents Insecure Direct Object References (IDOR)
    by strictly verifying that the application belongs to their assigned institution.
    """
    if current_user.role == "INSTITUTION":
        if application.institution_id != current_user.institution_id:
            # Mask existence to prevent unauthorized enumeration (404 Not Found)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or access denied."
            )
