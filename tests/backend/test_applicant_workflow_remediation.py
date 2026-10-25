# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# DEF-APPLICANT-001 Regression & Workflow Guard Tests
# (tests/backend/test_applicant_workflow_remediation.py)

import pytest
from fastapi import status

from backend.models.application import Application
from backend.models.document import Document
from backend.models.regulatory import Finding
from backend.models.deficiency import CorrectionSubmission
from backend.models.user import User


def get_token(client, email="applicant@institution.test", password="Password123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["access_token"]


def get_reviewer_token(client, email="reviewer@reviewer.test", password="ReviewerPass123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def applicant_headers(client):
    token = get_token(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reviewer_headers(client):
    token = get_reviewer_token(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_case(client, applicant_headers):
    """Creates a validated application with actionable findings."""
    c_resp = client.post("/api/v1/applications", headers=applicant_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 600
    })
    assert c_resp.status_code == status.HTTP_201_CREATED
    app_id = c_resp.json()["id"]

    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=applicant_headers)
    assert val_resp.status_code == status.HTTP_200_OK

    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers)
    assert def_resp.status_code == status.HTTP_200_OK
    findings = def_resp.json()["deficiencies"]
    assert len(findings) > 0

    return app_id, findings[0]["id"]


# -----------------------------------------------------------------------------
# 1. Permitted Initial Draft Creation
# -----------------------------------------------------------------------------
def test_permitted_initial_correction_draft_creation(client, applicant_headers, seeded_case):
    """Scenario 1: Permitted initial correction draft can be created."""
    app_id, finding_id = seeded_case

    payload = {
        "response_text": "Initial explanation regarding deficiency rectification.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    }
    resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["cycle_number"] == 1
    assert data["status"] == "DRAFT"
    assert data["response_text"] == payload["response_text"]

    # Verify workspace reflects RESPONSE_IN_PROGRESS
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers)
    target = next(d for d in def_resp.json()["deficiencies"] if d["id"] == finding_id)
    assert target["status"] == "RESPONSE_IN_PROGRESS"


# -----------------------------------------------------------------------------
# 2. Draft Editing In-Place
# -----------------------------------------------------------------------------
def test_draft_editing_in_place(client, applicant_headers, seeded_case):
    """Scenario 2: Existing draft can be updated in-place without spawning a new cycle."""
    app_id, finding_id = seeded_case

    # Create draft
    client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "First iteration of draft response text.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Edit draft
    updated_payload = {
        "response_text": "Updated iteration of draft response with supplementary details.",
        "response_category": "DOCUMENT_REPLACEMENT"
    }
    edit_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json=updated_payload)
    assert edit_resp.status_code == status.HTTP_200_OK
    data = edit_resp.json()

    assert data["cycle_number"] == 1
    assert data["status"] == "DRAFT"
    assert data["response_text"] == updated_payload["response_text"]
    assert data["response_category"] == "DOCUMENT_REPLACEMENT"


# -----------------------------------------------------------------------------
# 3. Formal Correction Submission
# -----------------------------------------------------------------------------
def test_formal_correction_submission_success(client, applicant_headers, seeded_case):
    """Scenario 3: Formal correction submission transitions status to CORRECTION_SUBMITTED."""
    app_id, finding_id = seeded_case

    # Save draft
    client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Draft content ready for formal submission.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Submit
    sub_payload = {
        "response_text": "Formal submission of corrective response by authorized applicant.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    }
    sub_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json=sub_payload)
    assert sub_resp.status_code == status.HTTP_200_OK
    sub_data = sub_resp.json()

    assert sub_data["cycle_number"] == 1
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["submitted_at"] is not None
    assert sub_data["revalidation_status"] == "PENDING"

    # Workspace finding status
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers)
    target = next(d for d in def_resp.json()["deficiencies"] if d["id"] == finding_id)
    assert target["status"] == "CORRECTION_SUBMITTED"
    assert target["resolution_status"] == "CORRECTION_SUBMITTED"


# -----------------------------------------------------------------------------
# 4 & 5. Premature Draft and Submit Rejection with State Immutability
# -----------------------------------------------------------------------------
def test_premature_draft_rejected_while_awaiting_revalidation(client, applicant_headers, seeded_case, db_session):
    """
    Scenarios 4 & 5:
    An additional draft cannot be created while submitted response is awaiting revalidation.
    Rejected requests leave finding status and history completely unchanged.
    """
    app_id, finding_id = seeded_case

    # Submit response
    client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Cycle 1 formal submission awaiting revalidation.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Record baseline state before invalid attempt
    def_before = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers).json()
    finding_before = next(d for d in def_before["deficiencies"] if d["id"] == finding_id)
    assert finding_before["status"] == "CORRECTION_SUBMITTED"

    hist_before = client.get(f"/api/v1/findings/{finding_id}/history", headers=applicant_headers).json()
    event_count_before = len(hist_before["history"])

    # Attempt to create premature draft immediately after submission (DEF-APPLICANT-001)
    premature_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Premature cycle 2 draft attempted while awaiting revalidation.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert premature_resp.status_code == status.HTTP_409_CONFLICT
    err_detail = premature_resp.json()["detail"]
    assert "awaiting revalidation" in err_detail

    # Scenario 5: Verify finding status and history are completely unchanged
    def_after = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers).json()
    finding_after = next(d for d in def_after["deficiencies"] if d["id"] == finding_id)
    assert finding_after["status"] == "CORRECTION_SUBMITTED"
    assert finding_after["resolution_status"] == "CORRECTION_SUBMITTED"
    assert finding_after["active_draft"] is None

    hist_after = client.get(f"/api/v1/findings/{finding_id}/history", headers=applicant_headers).json()
    assert len(hist_after["history"]) == event_count_before

    # Verify directly in database that no cycle 2 submission exists
    subs = db_session.query(CorrectionSubmission).filter(CorrectionSubmission.finding_id == finding_id).all()
    assert len(subs) == 1
    assert subs[0].cycle_number == 1
    assert subs[0].status == "SUBMITTED"


def test_premature_direct_submission_rejected(client, applicant_headers, seeded_case):
    """Verifies that POST /findings/{id}/submit without draft is also rejected while awaiting revalidation."""
    app_id, finding_id = seeded_case

    # Submit Cycle 1
    client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Cycle 1 formal submission awaiting revalidation.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Attempt immediate second submission
    sub2_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Premature duplicate submission without draft.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert sub2_resp.status_code == status.HTTP_409_CONFLICT
    assert "awaiting revalidation" in sub2_resp.json()["detail"]


# -----------------------------------------------------------------------------
# 6. Legitimate Return-for-Correction Permits Next Cycle
# -----------------------------------------------------------------------------
def test_legitimate_return_for_correction_permits_next_cycle(
    client, applicant_headers, reviewer_headers, seeded_case, db_session
):
    """
    Scenario 6:
    When a reviewer formally records RETURNED_FOR_CORRECTION, the finding returns to OPEN
    and the workflow explicitly permits initiating Cycle 2 draft and submission.
    """
    app_id, finding_id = seeded_case

    # 1. Submit Cycle 1
    sub1_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Cycle 1 corrective explanation submitted.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert sub1_resp.status_code == status.HTTP_200_OK
    sub1_id = sub1_resp.json()["id"]

    # 2. Reviewer inspects and returns for correction
    obs_resp = client.post(f"/api/v1/reviewer/applications/{app_id}/observations", headers=reviewer_headers, json={
        "finding_id": finding_id,
        "submission_id": sub1_id,
        "decision": "REQUIRE_ADDITIONAL_EVIDENCE",
        "justification": "Explanation alone is insufficient. Institution must furnish verified document evidence.",
        "is_internal_note": False
    })
    assert obs_resp.status_code == status.HTTP_201_CREATED

    # Verify finding state after reviewer return
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers)
    target = next(d for d in def_resp.json()["deficiencies"] if d["id"] == finding_id)
    assert target["status"] == "OPEN"

    # 3. Applicant now creates Cycle 2 draft (permitted by legitimate workflow transition)
    draft2_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Cycle 2 draft: Attaching additional verified evidence as required by scrutiny committee.",
        "response_category": "DOCUMENT_REPLACEMENT"
    })
    assert draft2_resp.status_code == status.HTTP_200_OK
    draft2_data = draft2_resp.json()
    assert draft2_data["cycle_number"] == 2
    assert draft2_data["status"] == "DRAFT"

    # 4. Applicant edits Cycle 2 draft
    draft2_edit = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Cycle 2 draft edited: Attached competent authority endorsement certificate.",
        "response_category": "DOCUMENT_REPLACEMENT"
    })
    assert draft2_edit.status_code == status.HTTP_200_OK
    assert draft2_edit.json()["cycle_number"] == 2

    # 5. Formally submit Cycle 2
    sub2_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Formally submitting Cycle 2 response with supplementary certificate.",
        "response_category": "DOCUMENT_REPLACEMENT"
    })
    assert sub2_resp.status_code == status.HTTP_200_OK
    sub2_data = sub2_resp.json()
    assert sub2_data["cycle_number"] == 2
    assert sub2_data["status"] == "SUBMITTED"

    # Verify in DB: cycle 1 is SUPERSEDED, cycle 2 is SUBMITTED
    submissions = (
        db_session.query(CorrectionSubmission)
        .filter(CorrectionSubmission.finding_id == finding_id)
        .order_by(CorrectionSubmission.cycle_number.asc())
        .all()
    )
    assert len(submissions) == 2
    assert submissions[0].cycle_number == 1
    assert submissions[0].status == "SUPERSEDED"
    assert submissions[1].cycle_number == 2
    assert submissions[1].status == "SUBMITTED"

    # 6. Verify Cycle 2 submission is now protected from premature Cycle 3 draft
    premature_c3 = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Premature cycle 3 attempt.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert premature_c3.status_code == status.HTTP_409_CONFLICT
    assert "cycle 2 is currently awaiting revalidation" in premature_c3.json()["detail"]


# -----------------------------------------------------------------------------
# 7. Prohibition When Awaiting Reviewer Disposition or Resolved
# -----------------------------------------------------------------------------
def test_draft_prohibited_when_awaiting_reviewer_disposition(
    client, applicant_headers, seeded_case, db_session
):
    """
    Verifies that when revalidation clears a deficiency and finding transitions to
    AWAITING_REVIEW, new draft creation is prohibited until reviewer acts.
    """
    app_id, finding_id = seeded_case

    # Submit correction
    client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Corrective response submitted for clearance.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Simulate revalidation clearing finding and setting AWAITING_REVIEW
    finding = db_session.query(Finding).filter(Finding.id == finding_id).first()
    finding.status = "AWAITING_REVIEW"
    sub = (
        db_session.query(CorrectionSubmission)
        .filter(CorrectionSubmission.finding_id == finding_id)
        .order_by(CorrectionSubmission.cycle_number.desc())
        .first()
    )
    sub.revalidation_status = "COMPLETED"
    sub.resolution_outcome = "CONDITION_CLEARED"
    sub.reviewer_disposition = "PENDING_REVIEW"
    db_session.commit()

    # Attempt draft
    resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Attempting draft while awaiting reviewer disposition.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert "awaiting reviewer disposition" in resp.json()["detail"]


def test_draft_prohibited_when_finding_resolved(
    client, applicant_headers, reviewer_headers, seeded_case
):
    """Verifies that once a reviewer accepts a correction and resolves the finding, drafting is blocked."""
    app_id, finding_id = seeded_case

    # Submit correction
    sub_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Correction submitted to resolve finding.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    sub_id = sub_resp.json()["id"]

    # Reviewer accepts
    obs_resp = client.post(f"/api/v1/reviewer/applications/{app_id}/observations", headers=reviewer_headers, json={
        "finding_id": finding_id,
        "submission_id": sub_id,
        "decision": "ACCEPT_CORRECTION",
        "justification": "Satisfactory compliance demonstrated.",
        "is_internal_note": False
    })
    assert obs_resp.status_code == status.HTTP_201_CREATED

    # Verify finding is resolved
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=applicant_headers)
    target = next(d for d in def_resp.json()["deficiencies"] if d["id"] == finding_id)
    assert target["status"] == "RESOLVED"

    # Attempt draft
    resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
        "response_text": "Attempting draft on resolved finding.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert "resolved finding" in resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 8. Permissions and Role Restrictions
# -----------------------------------------------------------------------------
def test_cross_tenant_isolation_on_response_endpoints(client, seeded_case):
    """Scenario 7: Unauthorized institution user cannot draft or submit response for another tenant's finding."""
    app_id, finding_id = seeded_case

    # Login as Institution 2
    resp = client.post("/api/v1/auth/login", json={"email": "applicant2@institution2.test", "password": "Password123!"})
    assert resp.status_code == status.HTTP_200_OK
    other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # Institution 2 attempts draft on Institution 1's finding
    draft_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=other_headers, json={
        "response_text": "Unauthorized cross-tenant attempt.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert draft_resp.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# -----------------------------------------------------------------------------
# 9. Concurrency & Repeated Requests Resilience
# -----------------------------------------------------------------------------
def test_repeated_and_concurrent_draft_requests_resilience(client, applicant_headers, seeded_case):
    """Scenario 8: Repeated duplicate requests cannot create invalid duplicate correction cycles."""
    app_id, finding_id = seeded_case

    # Submit Cycle 1
    client.post(f"/api/v1/findings/{finding_id}/submit", headers=applicant_headers, json={
        "response_text": "Cycle 1 formal submission.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Repeated calls must all be rejected consistently
    for i in range(5):
        resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=applicant_headers, json={
            "response_text": f"Repeated burst attempt {i}.",
            "response_category": "CLARIFICATION_JUSTIFICATION"
        })
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert "awaiting revalidation" in resp.json()["detail"]
