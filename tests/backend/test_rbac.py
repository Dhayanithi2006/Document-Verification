# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Server-Side Role-Based Access Control (RBAC) Tests (tests/backend/test_rbac.py)

import pytest
from fastapi import status


def get_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == status.HTTP_200_OK
    return res.json()["access_token"]


def test_anonymous_access_denied(client):
    """Verifies that unauthenticated anonymous calls to RBAC routes return 401."""
    res = client.get("/api/v1/auth/admin-check")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    res2 = client.get("/api/v1/auth/reviewer-check")
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED


def test_institution_user_cannot_access_admin_or_reviewer_endpoints(client):
    """Verifies that an INSTITUTION user is blocked from admin and reviewer routes with 403 Forbidden."""
    inst_token = get_token(client, "applicant@institution.test", "Password123!")

    # Attempt admin access
    admin_res = client.get(
        "/api/v1/auth/admin-check",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    assert admin_res.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient permissions" in admin_res.json()["detail"]

    # Attempt reviewer access
    rev_res = client.get(
        "/api/v1/auth/reviewer-check",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    assert rev_res.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient permissions" in rev_res.json()["detail"]


def test_reviewer_permissions(client):
    """Verifies that a REVIEWER user can access reviewer routes but is blocked from admin routes."""
    rev_token = get_token(client, "reviewer@reviewer.test", "ReviewerPass123!")

    # Allowed reviewer route
    rev_res = client.get(
        "/api/v1/auth/reviewer-check",
        headers={"Authorization": f"Bearer {rev_token}"}
    )
    assert rev_res.status_code == status.HTTP_200_OK
    assert "Reviewer authorization verified" in rev_res.json()["message"]

    # Blocked admin route
    admin_res = client.get(
        "/api/v1/auth/admin-check",
        headers={"Authorization": f"Bearer {rev_token}"}
    )
    assert admin_res.status_code == status.HTTP_403_FORBIDDEN


def test_admin_permissions(client):
    """Verifies that an ADMIN user possesses both admin and reviewer authorizations."""
    admin_token = get_token(client, "admin@platform.test", "AdminPass123!")

    admin_res = client.get(
        "/api/v1/auth/admin-check",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == status.HTTP_200_OK

    rev_res = client.get(
        "/api/v1/auth/reviewer-check",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rev_res.status_code == status.HTTP_200_OK
