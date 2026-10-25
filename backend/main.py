# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Main Application Entry Point (backend/main.py)

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import Base, engine, SessionLocal
from backend.core.seed import seed_synthetic_data
from backend.api.router import api_router
# Import models so SQLAlchemy metadata registers them
import backend.models

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aicte-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup initialization and shutdown cleanup."""
    logger.info("Initializing AICTE Pre-Scrutiny Platform backend...")
    
    # 1. Initialize Database Schema
    Base.metadata.create_all(bind=engine)
    logger.info("Database relational schema initialized successfully.")

    # 2. Seed Synthetic Development Baseline and Regulatory Rules
    db = SessionLocal()
    try:
        seed_synthetic_data(db)
        from backend.services.regulatory_engine import seed_regulatory_rules
        seed_regulatory_rules(db)
        logger.info("Synthetic demo accounts, institutions, and regulatory rules seeded.")
    finally:
        db.close()

    yield

    logger.info("Shutting down AICTE Pre-Scrutiny Platform backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API and Decision-Support Engine for AICTE Approval Pre-Scrutiny — SIH Prototype",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler for Unhandled Errors (Prevents leaking stack traces or secrets)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://errors.aicte-prescrutiny.sih/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred while processing your request. Please contact support.",
            "instance": request.url.path
        }
    )

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "disclaimer": "SIH Prototype — Not an official AICTE portal.",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health/readiness"
    }
