# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Environment Isolation & Database Protection Regression Tests (tests/backend/test_isolation_guard.py)

import pytest
from fastapi import status
from backend.core.config import Settings


def test_settings_database_isolation_properties():
    """Verifies that Settings correctly distinguishes test databases from demo/production databases."""
    # Test databases
    s_test1 = Settings(DATABASE_URL="sqlite:///./data/test_frontend.db")
    assert s_test1.is_isolated_test_db is True
    assert s_test1.is_demo_or_live_db is False

    s_test2 = Settings(DATABASE_URL="sqlite:///:memory:")
    assert s_test2.is_isolated_test_db is True

    # Demonstration / Live databases
    s_demo = Settings(DATABASE_URL="sqlite:///./data/demo.db")
    assert s_demo.is_isolated_test_db is False
    assert s_demo.is_demo_or_live_db is True

    s_aicte = Settings(DATABASE_URL="sqlite:///./data/aicte.db")
    assert s_aicte.is_isolated_test_db is False
    assert s_aicte.is_demo_or_live_db is True


def test_readiness_probe_exposes_database_isolation_status(client):
    """Verifies that /health/readiness reports database isolation metadata to client test runners."""
    res = client.get("/api/v1/health/readiness")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "is_isolated_test_db" in data
    assert "database_name" in data
    assert data["status"] == "ready"
