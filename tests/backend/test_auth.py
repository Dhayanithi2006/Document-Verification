# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Authentication & Account Lifecycle Tests (tests/backend/test_auth.py)

import pytest
from fastapi import status


def test_login_success(client):
    """Verifies that authenticating with valid credentials returns a signed JWT and user profile."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "applicant@institution.test", "password": "Password123!"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["email"] == "applicant@institution.test"
    assert data["user"]["role"] == "INSTITUTION"
    assert data["user"]["institution_id"] == "inst_01"


def test_login_invalid_password(client):
    """Verifies that invalid password returns generic 401 Unauthorized without account enumeration."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "applicant@institution.test", "password": "WrongPassword!"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password." in response.json()["detail"]


def test_login_nonexistent_email(client):
    """Verifies that non-existent email returns identical generic 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent.user@random.org", "password": "Password123!"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password." in response.json()["detail"]


def test_login_inactive_account(client):
    """Verifies that inactive/deactivated account is blocked with 403 Forbidden."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@institution.test", "password": "Password123!"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "deactivated" in response.json()["detail"]


def test_get_current_user_profile(client):
    """Verifies /auth/me returns current user profile when supplied valid Bearer token."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == status.HTTP_200_OK
    data = me_res.json()
    assert data["email"] == "reviewer@reviewer.test"
    assert data["role"] == "REVIEWER"


def test_get_me_unauthenticated(client):
    """Verifies /auth/me returns 401 when no token is provided."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_and_token_revocation(client):
    """Verifies that logging out revokes the token so subsequent requests are rejected."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@platform.test", "password": "AdminPass123!"}
    )
    token = login_res.json()["access_token"]

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == status.HTTP_200_OK

    # Attempting to use the revoked token
    retry_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert retry_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in retry_res.json()["detail"]
