# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Authentication API Endpoints (backend/api/v1/auth.py)

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import create_access_token, revoke_token
from backend.core.deps import get_current_user, require_admin, require_reviewer
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse, LogoutResponse
from backend.schemas.user import UserResponse
from backend.services.auth_service import authenticate_user
from backend.services.audit_service import create_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticates user credentials, enforces rate limits, logs audit events,
    and returns a signed JWT access token with profile context.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user = authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
        ip_address=client_ip
    )

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "institution_id": user.institution_id
    }
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieves identity and authorization context for the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    authorization: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes the current bearer token and records an audit log event."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
        revoke_token(raw_token)

    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="USER_LOGOUT",
        entity_type="USER",
        entity_id=current_user.id,
        payload={"email": current_user.email},
        ip_address=client_ip
    )

    return LogoutResponse(message="Session successfully terminated and token revoked.")


@router.get("/admin-check")
def admin_check(current_user: User = Depends(require_admin)):
    """Verifies that the caller possesses Administrator role privileges."""
    return {"message": "Admin authorization verified", "user_id": current_user.id}


@router.get("/reviewer-check")
def reviewer_check(current_user: User = Depends(require_reviewer)):
    """Verifies that the caller possesses Reviewer or Admin role privileges."""
    return {"message": "Reviewer authorization verified", "user_id": current_user.id}
