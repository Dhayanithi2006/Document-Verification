# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# User Schemas (backend/schemas/user.py)

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from backend.schemas.institution import InstitutionResponse

try:
    import email_validator
    email_validator.TEST_ENVIRONMENT = True
except ImportError:
    pass


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # 'INSTITUTION', 'REVIEWER', 'ADMIN'
    institution_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    institution_id: Optional[str] = None
    is_active: bool
    institution: Optional[InstitutionResponse] = None

    model_config = ConfigDict(from_attributes=True)
