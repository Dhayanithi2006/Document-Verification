# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Configuration Tests (tests/backend/test_config.py)

import pytest
from backend.core.config import Settings


def test_settings_default_values():
    """Verifies that default configuration values are properly loaded."""
    settings = Settings()
    assert settings.PROJECT_NAME == "AICTE Pre-Scrutiny Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert len(settings.SECRET_KEY) >= 32


def test_cors_origins_parsing():
    """Verifies that comma-separated CORS origins are converted to list."""
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://example.com")
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    assert "http://example.com" in settings.BACKEND_CORS_ORIGINS


def test_secret_not_printed_in_repr():
    """Verifies that sensitive secret keys are never exposed in __repr__."""
    settings = Settings()
    repr_str = repr(settings)
    assert settings.SECRET_KEY not in repr_str
    assert "Settings:" in repr_str
