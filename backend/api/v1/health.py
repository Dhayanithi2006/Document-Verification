# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Health & Diagnostics Endpoints (backend/api/v1/health.py)

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.database import get_db
from backend.core.config import settings
from backend.schemas.health import LivenessResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("/liveness", response_model=LivenessResponse)
def liveness():
    """Basic liveness probe checking if the API worker process is responsive."""
    return LivenessResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/readiness", response_model=ReadinessResponse)
def readiness(db: Session = Depends(get_db)):
    """Readiness probe verifying essential dependencies including database connectivity."""
    try:
        # Ping the database
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity failure. Application not ready."
        )

    db_name = str(settings.DATABASE_URL).split("///")[-1].replace("./", "")
    return ReadinessResponse(
        status="ready",
        database="connected",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        database_name=db_name,
        is_isolated_test_db=settings.is_isolated_test_db
    )
