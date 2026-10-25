# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Health & Diagnostics Tests (tests/backend/test_health.py)

import pytest
from fastapi import status


def test_liveness_endpoint(client):
    """Verifies that the /health/liveness endpoint returns 200 OK and valid status."""
    res = client.get("/api/v1/health/liveness")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_readiness_endpoint(client):
    """Verifies that the /health/readiness endpoint verifies database connectivity."""
    res = client.get("/api/v1/health/readiness")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert data["version"] == "1.0.0"
