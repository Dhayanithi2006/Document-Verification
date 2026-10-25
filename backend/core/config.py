# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Centralized Configuration Management (backend/core/config.py)

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import email_validator
    email_validator.TEST_ENVIRONMENT = True
except ImportError:
    pass


class Settings(BaseSettings):
    PROJECT_NAME: str = "AICTE Pre-Scrutiny Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # 'development', 'testing', 'production'
    DEBUG: bool = False

    # Security & JWT Configuration
    SECRET_KEY: str = "aicte_prescrutiny_super_secret_jwt_key_2026_dev_minimum_32_bytes_length!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./data/aicte.db"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"

    # Storage Configuration
    STORAGE_DIR: str = "storage/documents"
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB

    # Rate Limiting & Abuse Prevention
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300  # 5 minutes lockout

    @property
    def is_isolated_test_db(self) -> bool:
        db_str = str(self.DATABASE_URL).lower()
        return "test_" in db_str or ":memory:" in db_str

    @property
    def is_demo_or_live_db(self) -> bool:
        db_str = str(self.DATABASE_URL).lower()
        return "aicte.db" in db_str or "demo.db" in db_str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # In production mode, forbid default keys and enforce at least 32 characters
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            if "dev" in v or "super_secret" in v:
                raise ValueError("Insecure default SECRET_KEY cannot be used in production environment.")
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long in production.")
        return v

    def __repr__(self) -> str:
        # Prevent secret exposure in diagnostic strings or logs
        return f"<Settings: {self.PROJECT_NAME} ({self.ENVIRONMENT})>"


settings = Settings()
