# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Institution Schemas (backend/schemas/institution.py)

from pydantic import BaseModel, ConfigDict
from typing import Optional


class InstitutionBase(BaseModel):
    aicte_permanent_id: str
    name: str
    category: str = "ENGINEERING_TECHNOLOGY"
    state: str
    district: str
    is_rural: bool = False


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionResponse(InstitutionBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
