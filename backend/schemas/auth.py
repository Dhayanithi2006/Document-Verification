# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Authentication Schemas (backend/schemas/auth.py)

from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.schemas.user import UserResponse

try:
    import email_validator
    email_validator.TEST_ENVIRONMENT = True
except ImportError:
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str
