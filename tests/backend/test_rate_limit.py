# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Rate Limiting & Abuse Prevention Tests (tests/backend/test_rate_limit.py)

import pytest
from fastapi import status
from backend.services.auth_service import _failed_attempts


def test_login_rate_limiting_lockout(client):
    """Verifies that 5 consecutive failed login attempts trigger HTTP 429 Too Many Requests."""
    target_email = "target.user@apex-tech.edu.in"
    # Ensure clean state
    if target_email in _failed_attempts:
        del _failed_attempts[target_email]

    # Attempt 5 failed logins
    for attempt in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": "WrongPassword!"}
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # 6th attempt should be blocked by rate limiter with HTTP 429
    blocked_res = client.post(
        "/api/v1/auth/login",
        json={"email": target_email, "password": "WrongPassword!"}
    )
    assert blocked_res.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many failed login attempts" in blocked_res.json()["detail"]

    # Clean up state after test
    if target_email in _failed_attempts:
        del _failed_attempts[target_email]
