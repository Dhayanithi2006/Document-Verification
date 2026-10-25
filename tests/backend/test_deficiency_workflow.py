# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Phase P8 Deficiency Resolution, Corrective Actions & Revalidation Tests (tests/backend/test_deficiency_workflow.py)

import io
import json
import pytest
from fastapi import status

from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.extraction import ExtractedField, DocumentProcessingRun
from backend.models.regulatory import RegulatoryRule, ValidationRun, Finding
from backend.models.deficiency import CorrectionSubmission
from backend.services.regulatory_engine import RegulatoryEngine, seed_regulatory_rules
from tests.backend.test_extraction_pipeline import make_synthetic_digital_pdf


def get_auth_token(client, email="applicant@institution.test", password="Password123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["access_token"]


# -------------------------------------------------------------------------
# Test 1: Actionable Findings Workspace and Acknowledgement Workflow
# -------------------------------------------------------------------------
def test_deficiency_workspace_and_acknowledgement(client, db_session):
    """
    Verifies that an applicant can list actionable findings in their deficiency workspace,
    and acknowledge findings without prematurely marking them resolved.
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create an application and run regulatory pre-scrutiny
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 600
    })
    assert c_resp.status_code == status.HTTP_201_CREATED
    app_id = c_resp.json()["id"]

    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_resp.status_code == status.HTTP_200_OK

    # 2. Query application deficiency workspace
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    assert def_resp.status_code == status.HTTP_200_OK
    data = def_resp.json()

    assert data["application_id"] == app_id
    assert data["total_deficiencies"] > 0
    assert data["actionable_count"] > 0
    assert len(data["deficiencies"]) > 0

    first_def = data["deficiencies"][0]
    finding_id = first_def["id"]
    assert first_def["resolution_status"] == "OPEN"
    assert first_def["severity"] in ["DEFICIENCY", "WARNING"]

    # 3. Acknowledge finding
    ack_resp = client.post(f"/api/v1/findings/{finding_id}/acknowledge", headers=headers)
    assert ack_resp.status_code == status.HTTP_200_OK
    ack_data = ack_resp.json()
    assert ack_data["acknowledged_at"] is not None
    assert ack_data["resolution_status"] == "ACKNOWLEDGED"

    # 4. Workspace reflect updated acknowledgement metric
    def_resp2 = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    data2 = def_resp2.json()
    assert data2["acknowledged_count"] >= 1


# -------------------------------------------------------------------------
# Test 2: Corrective Response Draft and Submission Lifecycle
# -------------------------------------------------------------------------
def test_correction_draft_and_submission_lifecycle(client, db_session):
    """
    Verifies saving draft corrective responses, retrieving drafts,
    and formally submitting responses with state-machine transition to CORRECTION_SUBMITTED.
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Setup application and validation
    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]
    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)

    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    finding_id = def_resp.json()["deficiencies"][0]["id"]

    # 1. Invalid draft (too short) rejected
    bad_draft = client.put(f"/api/v1/findings/{finding_id}/response", headers=headers, json={
        "response_text": "Hi",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert bad_draft.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # 2. Save valid draft
    draft_payload = {
        "response_text": "Institution has applied for renewal of certificate before local fire department.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    }
    draft_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=headers, json=draft_payload)
    assert draft_resp.status_code == status.HTTP_200_OK
    draft_data = draft_resp.json()
    assert draft_data["status"] == "DRAFT"
    assert draft_data["cycle_number"] == 1
    assert draft_data["response_text"] == draft_payload["response_text"]

    # 3. Retrieve draft
    get_draft = client.get(f"/api/v1/findings/{finding_id}/response", headers=headers)
    assert get_draft.status_code == status.HTTP_200_OK
    assert get_draft.json()["id"] == draft_data["id"]

    # 4. Formally submit correction
    submit_payload = {
        "response_text": "Inspection by Fire Services completed; awaiting formal dispatch of renewed certificate.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    }
    sub_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=headers, json=submit_payload)
    assert sub_resp.status_code == status.HTTP_200_OK
    sub_data = sub_resp.json()
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["submitted_at"] is not None
    assert sub_data["revalidation_status"] == "PENDING"

    # 5. Check deficiency item status in workspace
    def_resp2 = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    target_def = next(d for d in def_resp2.json()["deficiencies"] if d["id"] == finding_id)
    assert target_def["resolution_status"] == "CORRECTION_SUBMITTED"
    assert target_def["status"] == "CORRECTION_SUBMITTED"


# -------------------------------------------------------------------------
# Test 3: Controlled Revalidation and Delta Comparison Engine
# -------------------------------------------------------------------------
def test_controlled_revalidation_with_delta_comparison(client, db_session):
    """
    Tests end-to-end controlled revalidation:
    1. Initial deficient document version uploaded and validated (condition detected).
    2. Applicant drafts and submits corrective response.
    3. Revalidation shows condition persists if evidence unchanged.
    4. Applicant uploads compliant replacement version v2.
    5. Revalidation re-checks rules and clears condition, setting outcome to CONDITION_CLEARED and status AWAITING_REVIEW.
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Application
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 600
    })
    app_id = c_resp.json()["id"]

    # 2. Upload Land Title Deed with deficient area (1.80 Acres vs 2.50 required in Metro/Urban)
    pdf_v1 = make_synthetic_digital_pdf([
        "Registered Land Title Deed for Apex Institute of Technology",
        "Contiguous Land Area: 1.80 Acres",
        "Lease Duration: 15 Years",
        "Survey Numbers: 44/2A",
        "Registration Date: 12-05-2020",
        "Executing Authority: Sub-Registrar Office, Bangalore"
    ])
    up_resp1 = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "LAND_TITLE_DEED"},
        files={"file": ("land_title_v1.pdf", pdf_v1, "application/pdf")}
    )
    assert up_resp1.status_code == status.HTTP_201_CREATED
    doc_id = up_resp1.json()["document_id"]

    # Trigger IDP extraction for v1
    proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_resp.status_code == status.HTTP_200_OK

    # 3. Initial Regulatory Validation
    val_resp1 = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_resp1.status_code == status.HTTP_200_OK

    # Get deficiency finding for Land
    def_resp1 = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    land_def = next(d for d in def_resp1.json()["deficiencies"] if d["rule_code"] == "RULE-EOA-LAND-001")
    assert land_def["outcome"] == "DEFICIENCY_DETECTED"
    finding_id = land_def["id"]

    # 4. Submit explanation without new document
    sub1 = client.post(f"/api/v1/findings/{finding_id}/submit", headers=headers, json={
        "response_text": "We are in the process of acquiring an adjoining parcel of 1.0 acres.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert sub1.status_code == status.HTTP_200_OK

    # 5. Trigger Revalidation: condition should persist
    reval_resp1 = client.post(f"/api/v1/applications/{app_id}/revalidate", headers=headers)
    assert reval_resp1.status_code == status.HTTP_200_OK
    reval1_data = reval_resp1.json()
    assert reval1_data["findings_persisting"] >= 1
    land_comp1 = next(c for c in reval1_data["comparison"] if c["rule_code"] == "RULE-EOA-LAND-001")
    assert land_comp1["status_change"] == "PERSISTS"

    # 6. Upload Compliant Document Version v2 (3.20 Acres > 2.50 Acres)
    pdf_v2 = make_synthetic_digital_pdf([
        "Registered Consolidated Land Title Deed for Apex Institute of Technology",
        "Contiguous Land Area: 3.20 Acres",
        "Lease Duration: 35 Years",
        "Permissible FAR: 2.0",
        "Survey Numbers: 44/2A, 44/2B",
        "Registration Date: 15-08-2026",
        "Executing Authority: Sub-Registrar Office, Bangalore"
    ])
    up_resp2 = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "LAND_TITLE_DEED"},
        files={"file": ("land_title_v2.pdf", pdf_v2, "application/pdf")}
    )
    assert up_resp2.status_code == status.HTTP_201_CREATED
    assert up_resp2.json()["version_number"] == 2

    # Process v2
    client.post(f"/api/v1/documents/{doc_id}/process?force=true", headers=headers)

    # 7. Submit Correction Cycle 2 referencing version v2
    sub2 = client.post(f"/api/v1/findings/{finding_id}/submit", headers=headers, json={
        "response_text": "Uploaded renewed consolidated title deed (v2) establishing 3.20 contiguous acres.",
        "response_category": "DOCUMENT_REPLACEMENT",
        "document_id": doc_id,
    })
    assert sub2.status_code == status.HTTP_200_OK
    assert sub2.json()["cycle_number"] == 2

    # 8. Revalidate with compliant evidence
    reval_resp2 = client.post(f"/api/v1/applications/{app_id}/revalidate", headers=headers)
    assert reval_resp2.status_code == status.HTTP_200_OK
    reval2_data = reval_resp2.json()

    land_comp2 = next(c for c in reval2_data["comparison"] if c["rule_code"] == "RULE-EOA-LAND-001")
    assert land_comp2["status_change"] == "CLEARED"
    assert reval2_data["findings_cleared"] >= 1

    # 9. Verify finding transitioned to AWAITING_REVIEW (decision-support reviewer handoff)
    def_resp2 = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    land_def_after = next(d for d in def_resp2.json()["deficiencies"] if d["rule_code"] == "RULE-EOA-LAND-001")
    assert land_def_after["resolution_status"] == "AWAITING_REVIEW"
    assert land_def_after["latest_submission"]["resolution_outcome"] == "CONDITION_CLEARED"
    assert land_def_after["latest_submission"]["reviewer_disposition"] == "PENDING_REVIEW"


# -------------------------------------------------------------------------
# Test 4: Multi-Tenant Tenant Isolation & Cross-Institution Defense
# -------------------------------------------------------------------------
def test_deficiency_multi_tenant_isolation_and_security(client, db_session):
    """
    Verifies that tenant isolation is strictly enforced:
    Institution 2 cannot inspect, acknowledge, draft, submit, or revalidate Institution 1 findings.
    Masks existence with HTTP 404 (IDOR defense).
    """
    token_inst1 = get_auth_token(client, email="applicant@institution.test")
    headers_inst1 = {"Authorization": f"Bearer {token_inst1}"}

    token_inst2 = get_auth_token(client, email="applicant2@institution2.test")
    headers_inst2 = {"Authorization": f"Bearer {token_inst2}"}

    # 1. Institution 1 creates application and finding
    c_resp = client.post("/api/v1/applications", headers=headers_inst1, json={"academic_year": "2026-2027"})
    app_id_1 = c_resp.json()["id"]
    client.post(f"/api/v1/applications/{app_id_1}/validate", headers=headers_inst1)

    def_resp1 = client.get(f"/api/v1/applications/{app_id_1}/deficiencies", headers=headers_inst1)
    finding_id_1 = def_resp1.json()["deficiencies"][0]["id"]

    # 2. Institution 2 cannot view Institution 1 deficiencies
    t2_get = client.get(f"/api/v1/applications/{app_id_1}/deficiencies", headers=headers_inst2)
    assert t2_get.status_code == status.HTTP_404_NOT_FOUND

    # 3. Institution 2 cannot acknowledge Institution 1 finding
    t2_ack = client.post(f"/api/v1/findings/{finding_id_1}/acknowledge", headers=headers_inst2)
    assert t2_ack.status_code == status.HTTP_404_NOT_FOUND

    # 4. Institution 2 cannot draft correction
    t2_draft = client.put(f"/api/v1/findings/{finding_id_1}/response", headers=headers_inst2, json={
        "response_text": "Malicious cross-tenant override attempt.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert t2_draft.status_code == status.HTTP_404_NOT_FOUND

    # 5. Institution 2 cannot submit correction
    t2_sub = client.post(f"/api/v1/findings/{finding_id_1}/submit", headers=headers_inst2, json={
        "response_text": "Malicious submission from another tenant.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert t2_sub.status_code == status.HTTP_404_NOT_FOUND

    # 6. Institution 2 cannot trigger revalidation
    t2_reval = client.post(f"/api/v1/applications/{app_id_1}/revalidate", headers=headers_inst2)
    assert t2_reval.status_code == status.HTTP_404_NOT_FOUND

    # 7. Anonymous requests receive 401 Unauthorized
    anon_resp = client.get(f"/api/v1/applications/{app_id_1}/deficiencies")
    assert anon_resp.status_code == status.HTTP_401_UNAUTHORIZED


# -------------------------------------------------------------------------
# Test 5: Full Chronological Timeline & Audit Trail
# -------------------------------------------------------------------------
def test_finding_history_chronological_timeline(client, db_session):
    """
    Verifies that GET /findings/{id}/history returns a strictly ordered,
    traceable chronological history including finding identification, acknowledgement,
    draft saving, formal submission, and revalidation outcomes.
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Application & Finding
    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]
    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)

    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    finding_id = def_resp.json()["deficiencies"][0]["id"]

    # Acknowledge
    client.post(f"/api/v1/findings/{finding_id}/acknowledge", headers=headers)

    # Draft
    client.put(f"/api/v1/findings/{finding_id}/response", headers=headers, json={
        "response_text": "Initial draft remarks regarding deficiency remediation.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Submit
    client.post(f"/api/v1/findings/{finding_id}/submit", headers=headers, json={
        "response_text": "Formal submission of corrective explanation for evaluation committee.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })

    # Revalidate
    client.post(f"/api/v1/applications/{app_id}/revalidate", headers=headers)

    # Query Timeline History
    hist_resp = client.get(f"/api/v1/findings/{finding_id}/history", headers=headers)
    assert hist_resp.status_code == status.HTTP_200_OK
    hist = hist_resp.json()

    assert hist["finding_id"] == finding_id
    assert hist["application_id"] == app_id
    events = hist["history"]
    assert len(events) >= 4

    event_types = [e["event_type"] for e in events]
    assert "FINDING_IDENTIFIED" in event_types
    assert "ACKNOWLEDGED" in event_types
    assert "DRAFT_SAVED" in event_types
    assert "CORRECTION_SUBMITTED" in event_types
    assert "REVALIDATION_RUN" in event_types

    # Ensure chronological timestamp ordering
    for i in range(len(events) - 1):
        assert events[i]["timestamp"] <= events[i + 1]["timestamp"]


# -------------------------------------------------------------------------
# Test 6: Multipart Document Resolve Bridge Endpoint
# -------------------------------------------------------------------------
def test_multipart_document_resolve_bridge_endpoint(client, db_session):
    """
    Verifies the bridge endpoint POST /findings/{id}/resolve accepting multipart upload
    for immediate document version creation, extraction, submission, and revalidation.
    """
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]
    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)

    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=headers)
    finding_id = def_resp.json()["deficiencies"][0]["id"]

    pdf_bytes = make_synthetic_digital_pdf([
        "GOVERNMENT FIRE SERVICES DEPARTMENT",
        "NO OBJECTION CERTIFICATE - FIRE SAFETY",
        "Valid Until Date: 31-03-2027",
        "Total Built-up Area Inspected: 5000 Sq.m"
    ])

    files = {"file": ("fire_noc_renewed.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "remarks": "Uploaded renewed Fire NOC certificate covering 2026-2027 academic session.",
        "response_category": "DOCUMENT_REPLACEMENT"
    }

    resolve_resp = client.post(f"/api/v1/findings/{finding_id}/resolve", headers=headers, data=data, files=files)
    assert resolve_resp.status_code == status.HTTP_200_OK
    res_data = resolve_resp.json()
    assert res_data["status"] == "CORRECTION_SUBMITTED"
    assert "revalidation" in res_data
    assert res_data["revalidation"]["status"] == "COMPLETED"

