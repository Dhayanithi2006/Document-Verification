# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Health & Diagnostics Schemas (backend/schemas/health.py)

from pydantic import BaseModel
from datetime import datetime


class LivenessResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str = "ready"
    database: str = "connected"
    environment: str
    version: str = "1.0.0"
    database_name: str = ""
    is_isolated_test_db: bool = False
