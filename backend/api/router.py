# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# API Router Aggregation (backend/api/router.py)

from fastapi import APIRouter
from backend.api.v1.auth import router as auth_router
from backend.api.v1.health import router as health_router
from backend.api.v1.applications import router as applications_router
from backend.api.v1.documents import router as documents_router
from backend.api.v1.regulatory import router as regulatory_router
from backend.api.v1.deficiencies import router as deficiencies_router
from backend.api.v1.reviewer import router as reviewer_router
from backend.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(regulatory_router)
api_router.include_router(deficiencies_router)
api_router.include_router(reviewer_router)
api_router.include_router(admin_router)


