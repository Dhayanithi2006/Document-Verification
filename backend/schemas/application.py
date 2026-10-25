# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Application Schemas (backend/schemas/application.py)

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    academic_year: str = "2026-2027"
    application_type: str = "EOA"
    total_intake_applied: int = 0


class ApplicationUpdate(BaseModel):
    academic_year: Optional[str] = None
    total_intake_applied: Optional[int] = None


class ApplicationResponse(BaseModel):
    id: str
    application_number: str
    institution_id: str
    academic_year: str
    application_type: str
    status: str
    total_intake_applied: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
