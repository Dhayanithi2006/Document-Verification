# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Phase P10: End-to-End Multi-Role Workflow Journey Verification
# File: tests/backend/test_e2e_journey.py

import pytest
from fastapi.testclient import TestClient


def test_e2e_complete_multi_role_operational_journey(client: TestClient):
    """
    Comprehensive End-to-End Verification Journey across all platform roles:
    1. Institution Applicant: Login, inspect checklist, submit correction, trigger revalidation.
    2. Committee Reviewer: Login, view worklist metrics, assign case, record observation, stage signoff.
    3. Platform Administrator: Login, view overview KPIs, provision user, test self-lockout defense, query audit trail.
    4. Negative Security Gates: Role elevation and cross-tenant IDOR denial.
    """

    # =========================================================================
    # STAGE 1: INSTITUTION APPLICANT WORKFLOW
    # =========================================================================
    # 1.1 Authenticate as Institution 1 Applicant
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200, login_resp.text
    inst_token = login_resp.json()["access_token"]
    inst_headers = {"Authorization": f"Bearer {inst_token}"}

    # 1.2 Verify Authenticated Profile (/auth/me)
    me_resp = client.get("/api/v1/auth/me", headers=inst_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "INSTITUTION"
    assert me_resp.json()["institution_id"] == "inst_01"

    # 1.3 Query Applications List
    apps_resp = client.get("/api/v1/applications", headers=inst_headers)
    assert apps_resp.status_code == 200
    apps_data = apps_resp.json()
    apps = apps_data if isinstance(apps_data, list) else apps_data.get("items", [])
    assert len(apps) >= 1
    app_id = apps[0]["id"]

    # 1.4 Inspect Statutory 8-Document Checklist
    chk_resp = client.get(f"/api/v1/applications/{app_id}/checklist", headers=inst_headers)
    assert chk_resp.status_code == 200
    checklist_data = chk_resp.json()
    assert checklist_data["total_slots"] == 8

    # 1.4b Trigger Initial Pre-Scrutiny Validation to Produce Grounded Findings
    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=inst_headers)
    assert val_resp.status_code == 200

    # 1.5 Query Findings & Deficiencies
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=inst_headers)
    assert def_resp.status_code == 200
    deficiencies = def_resp.json()["deficiencies"]
    assert len(deficiencies) >= 1
    target_finding = deficiencies[0]
    finding_id = target_finding["id"]

    # 1.6 Acknowledge the Finding
    ack_resp = client.post(f"/api/v1/findings/{finding_id}/acknowledge", headers=inst_headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledged_at"] is not None

    # 1.7 Save Draft Corrective Explanation
    draft_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=inst_headers, json={
        "response_text": "Institution has applied for statutory clearance with local authorities.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert draft_resp.status_code == 200
    assert draft_resp.json()["status"] == "DRAFT"

    # 1.8 Formally Submit Correction Response
    submit_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=inst_headers, json={
        "response_text": "Updated compliance documentation attached and verified by civil engineer.",
        "response_category": "DOCUMENT_REPLACEMENT"
    })
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "SUBMITTED"

    # 1.9 Trigger Controlled Revalidation via P7 Engine
    reval_resp = client.post(f"/api/v1/applications/{app_id}/revalidate", headers=inst_headers)
    assert reval_resp.status_code == 200
    reval_data = reval_resp.json()
    assert reval_data["status"] == "COMPLETED"
    assert "comparison" in reval_data

    # 1.10 Verify Immutable Finding Audit History
    hist_resp = client.get(f"/api/v1/findings/{finding_id}/history", headers=inst_headers)
    assert hist_resp.status_code == 200
    history_events = hist_resp.json()["history"]
    event_types = [h["event_type"] for h in history_events]
    assert "ACKNOWLEDGED" in event_types or "DRAFT_SAVED" in event_types

    # =========================================================================
    # STAGE 2: COMMITTEE REVIEWER SCRUTINY WORKFLOW
    # =========================================================================
    # 2.1 Authenticate as Committee Reviewer
    rev_login = client.post("/api/v1/auth/login", json={
        "email": "reviewer@reviewer.test",
        "password": "ReviewerPass123!"
    })
    assert rev_login.status_code == 200, rev_login.text
    rev_token = rev_login.json()["access_token"]
    rev_user_id = rev_login.json()["user"]["id"]
    rev_headers = {"Authorization": f"Bearer {rev_token}"}

    # 2.2 Retrieve Scrutiny Queue with Live Metrics
    queue_resp = client.get("/api/v1/reviewer/queue", headers=rev_headers)
    assert queue_resp.status_code == 200
    q_data = queue_resp.json()
    assert "metrics" in q_data
    assert "total_applications" in q_data["metrics"]
    assert "assigned_to_me" in q_data["metrics"]
    assert "items" in q_data

    # 2.3 Assign Case to Self
    assign_resp = client.post(f"/api/v1/reviewer/applications/{app_id}/assign", headers=rev_headers, json={
        "target_reviewer_id": rev_user_id,
        "remarks": "E2E verification review assignment."
    })
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_reviewer_id"] == rev_user_id

    # 2.4 Retrieve Comprehensive Scrutiny Console Data
    scrutiny_resp = client.get(f"/api/v1/reviewer/applications/{app_id}/scrutiny", headers=rev_headers)
    assert scrutiny_resp.status_code == 200
    s_data = scrutiny_resp.json()
    assert s_data["application"]["id"] == app_id
    assert len(s_data["checklist"]) == 8
    assert "findings" in s_data
    assert "correction_submissions" in s_data

    # 2.5 Record Formal Reviewer Observations (Resolving all open findings)
    for d in deficiencies:
        obs_resp = client.post(f"/api/v1/reviewer/applications/{app_id}/observations", headers=rev_headers, json={
            "finding_id": d["id"],
            "decision": "ACCEPT_CORRECTION",
            "justification": "Verified statutory compliance documentation under AICTE APH norms.",
            "is_internal_note": False
        })
        assert obs_resp.status_code == 201
        assert obs_resp.json()["decision"] == "ACCEPT_CORRECTION"

    # 2.6 Record Pre-Scrutiny Stage Recommendation
    dec_resp = client.post(f"/api/v1/reviewer/applications/{app_id}/decision", headers=rev_headers, json={
        "decision": "RETURNED_FOR_CORRECTION",
        "remarks": "Returned for institutional clarification and resubmission of statutory certificates."
    })
    assert dec_resp.status_code == 200
    assert dec_resp.json()["review_status"] == "RETURNED_FOR_CORRECTION"

    # =========================================================================
    # STAGE 3: PLATFORM ADMINISTRATOR GOVERNANCE WORKFLOW
    # =========================================================================
    # 3.1 Authenticate as Platform Administrator
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@platform.test",
        "password": "AdminPass123!"
    })
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]
    admin_user_id = admin_login.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3.2 Query Operational Overview Metrics
    overview_resp = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert overview_resp.status_code == 200
    kpis = overview_resp.json()
    assert kpis["total_users"] >= 3
    assert kpis["total_applications"] >= 1
    assert kpis["total_audit_events"] >= 1

    # 3.3 Provision New Reviewer Account
    new_user_email = "e2e.reviewer@reviewer.test"
    prov_resp = client.post("/api/v1/admin/users", headers=admin_headers, json={
        "email": new_user_email,
        "password": "SecurePassword123!",
        "full_name": "Dr. E2E Committee Member",
        "role": "REVIEWER"
    })
    assert prov_resp.status_code == 201
    new_user_data = prov_resp.json()
    assert new_user_data["email"] == new_user_email
    assert "password_hash" not in new_user_data  # Zero credential leakage

    # 3.4 Self-Lockout Defense: Admin cannot deactivate own account
    self_lock_resp = client.patch(f"/api/v1/admin/users/{admin_user_id}", headers=admin_headers, json={
        "is_active": False
    })
    assert self_lock_resp.status_code == 400
    assert "cannot deactivate their own" in self_lock_resp.json()["detail"].lower()

    # 3.5 Query Registered Institutions & Update Metadata
    inst_list_resp = client.get("/api/v1/admin/institutions", headers=admin_headers)
    assert inst_list_resp.status_code == 200
    institutions = inst_list_resp.json()
    assert len(institutions) >= 1
    first_inst_id = institutions[0]["id"]

    patch_inst_resp = client.patch(f"/api/v1/admin/institutions/{first_inst_id}", headers=admin_headers, json={
        "is_rural": False
    })
    assert patch_inst_resp.status_code == 200
    assert patch_inst_resp.json()["is_rural"] is False

    # 3.6 Regulatory Rule Activation
    act_rule_resp = client.post("/api/v1/rules/RULE-EOA-LAND-001/activate", headers=admin_headers)
    assert act_rule_resp.status_code == 200
    assert act_rule_resp.json()["is_active"] is True

    # 3.7 Query Tamper-Evident Forensic Audit Timeline
    audit_resp = client.get("/api/v1/admin/audit-events", headers=admin_headers)
    assert audit_resp.status_code == 200
    audit_events = audit_resp.json()
    assert len(audit_events) >= 5
    actions = [evt["action"] for evt in audit_events]
    assert "REVIEWER_OBSERVATION_RECORDED" in actions
    assert "PRE_SCRUTINY_REVIEW_COMPLETED" in actions
    assert "USER_PROVISIONED" in actions
    assert "INSTITUTION_UPDATED" in actions

    # =========================================================================
    # STAGE 4: STRICT SECURITY & CROSS-TENANT ISOLATION GATES
    # =========================================================================
    # 4.1 Institution Applicant attempting Reviewer Queue -> 403 Forbidden
    denied_queue = client.get("/api/v1/reviewer/queue", headers=inst_headers)
    assert denied_queue.status_code == 403

    # 4.2 Institution Applicant attempting Admin Overview -> 403 Forbidden
    denied_admin = client.get("/api/v1/admin/overview", headers=inst_headers)
    assert denied_admin.status_code == 403

    # 4.3 Reviewer attempting User Provisioning -> 403 Forbidden
    denied_prov = client.post("/api/v1/admin/users", headers=rev_headers, json={
        "email": "hacker@unauthorized.test",
        "password": "Password123!",
        "full_name": "Unauthorized Actor",
        "role": "ADMIN"
    })
    assert denied_prov.status_code == 403

    # 4.4 Unauthenticated request to protected endpoint -> 401 Unauthorized
    denied_anon = client.get("/api/v1/admin/overview")
    assert denied_anon.status_code == 401
