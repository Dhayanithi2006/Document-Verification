# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Reviewer Scrutiny Workflow Integration Tests (tests/backend/test_reviewer_workflow.py)

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import get_db
from backend.models.user import User
from backend.models.application import Application
from backend.models.regulatory import Finding, ValidationRun, RegulatoryRule, RegulatoryRuleVersion
from backend.models.deficiency import CorrectionSubmission


@pytest.mark.anyio
async def test_reviewer_queue_retrieval_and_metrics():
    """Verify authorized scrutiny committee member can access review queue with live metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Reviewer
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query reviewer queue
        resp = await client.get("/api/v1/reviewer/queue", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        assert "metrics" in data
        assert "total" in data
        assert data["metrics"]["total_applications"] >= 1
        assert "assigned_to_me" in data["metrics"]
        assert "unassigned" in data["metrics"]

        # Filter by search
        search_resp = await client.get("/api/v1/reviewer/queue?search=AICTE", headers=headers)
        assert search_resp.status_code == 200


@pytest.mark.anyio
async def test_reviewer_assignment_and_reassignment():
    """Verify application assignment, reassignment, and validation of target reviewer eligibility."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Reviewer credentials
        rev_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
        )
        rev_token = rev_login.json()["access_token"]
        rev_user_id = rev_login.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {rev_token}"}

        # Get an application
        queue_resp = await client.get("/api/v1/reviewer/queue", headers=headers)
        apps = queue_resp.json()["items"]
        assert len(apps) > 0
        target_app = apps[0]

        # Assign case to current reviewer
        assign_resp = await client.post(
            f"/api/v1/reviewer/applications/{target_app['id']}/assign",
            json={"target_reviewer_id": rev_user_id, "remarks": "Assigned for statutory EOA pre-scrutiny"},
            headers=headers
        )
        assert assign_resp.status_code == 200
        assigned_app = assign_resp.json()
        assert assigned_app["assigned_reviewer_id"] == rev_user_id

        # Attempt to assign to an applicant account (INSTITUTION role) -> must fail 400
        inst_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "applicant@institution.test", "password": "Password123!"}
        )
        inst_user_id = inst_login.json()["user"]["id"]

        invalid_assign = await client.post(
            f"/api/v1/reviewer/applications/{target_app['id']}/assign",
            json={"target_reviewer_id": inst_user_id},
            headers=headers
        )
        assert invalid_assign.status_code == 400
        assert "not eligible" in invalid_assign.json()["detail"].lower()


@pytest.mark.anyio
async def test_reviewer_scrutiny_details_and_observations():
    """Verify reviewer can inspect case details and record formal observations and finding dispositions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Reviewer
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        # Get an application
        queue_resp = await client.get("/api/v1/reviewer/queue", headers=headers)
        target_app = queue_resp.json()["items"][0]

        # Retrieve scrutiny case details
        detail_resp = await client.get(
            f"/api/v1/reviewer/applications/{target_app['id']}/scrutiny",
            headers=headers
        )
        assert detail_resp.status_code == 200
        case_data = detail_resp.json()

        assert "checklist" in case_data
        assert "findings" in case_data
        assert "correction_submissions" in case_data
        assert "observations" in case_data

        target_finding = None
        if case_data["findings"]:
            target_finding = case_data["findings"][0]

        # Record scrutiny observation
        obs_payload = {
            "finding_id": target_finding["id"] if target_finding else None,
            "decision": "CONCUR_DEFICIENCY" if target_finding else "GENERAL_OBSERVATION",
            "justification": "Verified against AICTE Approval Process Handbook (APH 2024-2027) Appendix 4 norms.",
            "is_internal_note": False
        }
        obs_resp = await client.post(
            f"/api/v1/reviewer/applications/{target_app['id']}/observations",
            json=obs_payload,
            headers=headers
        )
        assert obs_resp.status_code == 201
        obs_data = obs_resp.json()
        assert obs_data["decision"] == obs_payload["decision"]
        assert obs_data["application_id"] == target_app["id"]


@pytest.mark.anyio
async def test_reviewer_decision_and_state_transition():
    """Verify reviewer decision transitions (PRE_SCRUTINY_RECOMMENDED_CLEAR, RETURNED_FOR_CORRECTION)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Reviewer
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"}
        )
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        queue_resp = await client.get("/api/v1/reviewer/queue", headers=headers)
        target_app = queue_resp.json()["items"][0]

        # If application has open deficiencies, PRE_SCRUTINY_RECOMMENDED_CLEAR must be rejected
        if target_app["deficiencies_count"] > 0:
            clear_resp = await client.post(
                f"/api/v1/reviewer/applications/{target_app['id']}/decision",
                json={
                    "decision": "PRE_SCRUTINY_RECOMMENDED_CLEAR",
                    "remarks": "Attempting premature clearance with open blocking deficiencies."
                },
                headers=headers
            )
            assert clear_resp.status_code == 400
            assert "blocking deficiency" in clear_resp.json()["detail"].lower()

        # RETURNED_FOR_CORRECTION should succeed
        return_resp = await client.post(
            f"/api/v1/reviewer/applications/{target_app['id']}/decision",
            json={
                "decision": "RETURNED_FOR_CORRECTION",
                "remarks": "Returned for institutional clarification regarding Fire NOC validity."
            },
            headers=headers
        )
        assert return_resp.status_code == 200
        updated = return_resp.json()
        assert updated["review_status"] == "RETURNED_FOR_CORRECTION"
        assert updated["status"] == "RETURNED_FOR_CORRECTION"


@pytest.mark.anyio
async def test_reviewer_rbac_boundary_institution_denied():
    """Verify institutional applicant cannot access reviewer queue or record reviewer decisions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login as Institution applicant
        inst_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "applicant@institution.test", "password": "Password123!"}
        )
        inst_token = inst_login.json()["access_token"]
        inst_headers = {"Authorization": f"Bearer {inst_token}"}

        # Attempt to access reviewer queue
        queue_resp = await client.get("/api/v1/reviewer/queue", headers=inst_headers)
        assert queue_resp.status_code == 403

        # Attempt to record observation
        obs_resp = await client.post(
            "/api/v1/reviewer/applications/app_dummy/observations",
            json={"decision": "ACCEPT_CORRECTION", "justification": "Illegal bypass attempt"},
            headers=inst_headers
        )
        assert obs_resp.status_code == 403
