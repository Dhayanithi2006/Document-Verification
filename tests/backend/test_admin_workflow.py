# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Administrator Workspace Integration Tests (tests/backend/test_admin_workflow.py)

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.anyio
async def test_admin_overview_metrics():
    """Verify administrator can retrieve live operational system metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Administrator
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@platform.test", "password": "AdminPass123!"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query admin overview
        resp = await client.get("/api/v1/admin/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_users"] >= 4
        assert data["active_users"] >= 3
        assert data["total_reviewers"] >= 1
        assert data["total_institutions"] >= 2
        assert data["total_applications"] >= 1
        assert "applications_by_status" in data
        assert "applications_by_review_status" in data


@pytest.mark.anyio
async def test_admin_user_provisioning_and_lifecycle():
    """Verify user account provisioning, role setting, active status toggle, and self-lockout prevention."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Administrator
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@platform.test", "password": "AdminPass123!"}
        )
        admin_token = admin_login.json()["access_token"]
        admin_id = admin_login.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Provision a new Reviewer user
        unique_email = f"reviewer_{uuid.uuid4().hex[:6]}@reviewer.test"
        create_payload = {
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "Dr. Test Reviewer",
            "role": "REVIEWER",
            "is_active": True
        }
        create_resp = await client.post("/api/v1/admin/users", json=create_payload, headers=headers)
        assert create_resp.status_code == 201
        new_user = create_resp.json()
        assert new_user["email"] == unique_email
        assert new_user["role"] == "REVIEWER"
        assert "password" not in new_user
        assert "password_hash" not in new_user

        # Verify newly provisioned user can log in
        new_login = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SecurePassword123!"}
        )
        assert new_login.status_code == 200

        # 2. Deactivate the new user account
        update_resp = await client.patch(
            f"/api/v1/admin/users/{new_user['id']}",
            json={"is_active": False},
            headers=headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["is_active"] is False

        # Verify deactivated user cannot log in
        blocked_login = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SecurePassword123!"}
        )
        assert blocked_login.status_code == 403

        # 3. Prevent Administrator from deactivating self
        self_deactivate = await client.patch(
            f"/api/v1/admin/users/{admin_id}",
            json={"is_active": False},
            headers=headers
        )
        assert self_deactivate.status_code == 400
        assert "cannot deactivate their own" in self_deactivate.json()["detail"].lower()


@pytest.mark.anyio
async def test_admin_institution_management():
    """Verify administrator can inspect institutions and update non-sensitive metadata."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Administrator
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@platform.test", "password": "AdminPass123!"}
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # List institutions
        inst_resp = await client.get("/api/v1/admin/institutions", headers=headers)
        assert inst_resp.status_code == 200
        institutions = inst_resp.json()
        assert len(institutions) >= 1
        target_inst = institutions[0]

        # Update metadata
        patch_resp = await client.patch(
            f"/api/v1/admin/institutions/{target_inst['id']}",
            json={"is_rural": True},
            headers=headers
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["is_rural"] is True


@pytest.mark.anyio
async def test_admin_audit_events_query():
    """Verify administrator and reviewer can query the tamper-evident security audit log."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Administrator
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@platform.test", "password": "AdminPass123!"}
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Query audit events
        audit_resp = await client.get("/api/v1/admin/audit-events", headers=headers)
        assert audit_resp.status_code == 200
        events = audit_resp.json()
        assert len(events) >= 1
        for evt in events:
            assert "actor_user_id" in evt
            assert "action" in evt
            assert "created_at" in evt


@pytest.mark.anyio
async def test_admin_rbac_boundary_non_admin_denied():
    """Verify non-admin users cannot access administrative endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Reviewer
        rev_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
        )
        rev_headers = {"Authorization": f"Bearer {rev_login.json()['access_token']}"}

        # Reviewer cannot access admin overview
        resp = await client.get("/api/v1/admin/overview", headers=rev_headers)
        assert resp.status_code == 403

        # Reviewer cannot provision users
        post_resp = await client.post(
            "/api/v1/admin/users",
            json={"email": "test@test.com", "password": "password", "full_name": "Test", "role": "REVIEWER"},
            headers=rev_headers
        )
        assert post_resp.status_code == 403

        # Applicant cannot access audit events
        inst_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "applicant@institution.test", "password": "Password123!"}
        )
        inst_headers = {"Authorization": f"Bearer {inst_login.json()['access_token']}"}

        audit_resp = await client.get("/api/v1/admin/audit-events", headers=inst_headers)
        assert audit_resp.status_code == 403


@pytest.mark.anyio
async def test_audit_event_append_only_at_api_layer():
    """Verify audit events are append-only at API layer: no UPDATE or DELETE endpoints exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Administrator
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@platform.test", "password": "AdminPass123!"}
        )
        headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Query audit events
        audit_resp = await client.get("/api/v1/admin/audit-events", headers=headers)
        assert audit_resp.status_code == 200
        events = audit_resp.json()
        assert len(events) >= 1
        first_event_id = events[0]["id"]

        # Attempt to modify audit event via PATCH -> 405 Method Not Allowed / 404
        patch_resp = await client.patch(
            f"/api/v1/admin/audit-events/{first_event_id}",
            json={"action": "TAMPERED_ACTION"},
            headers=headers
        )
        assert patch_resp.status_code in [404, 405]

        # Attempt to delete audit event via DELETE -> 405 Method Not Allowed / 404
        delete_resp = await client.delete(
            f"/api/v1/admin/audit-events/{first_event_id}",
            headers=headers
        )
        assert delete_resp.status_code in [404, 405]
