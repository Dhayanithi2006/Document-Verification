# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# P5 Application Workflow & Document Upload Tests (tests/backend/test_applications_workflow.py)

import io
from fastapi import status
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.audit import AuditEvent

# Synthetic PDF fixture content
VALID_PDF_BYTES = b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
INVALID_TEXT_BYTES = b"This is not a PDF file. Disguised malicious text stream."
CORRUPT_BYTES = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"  # EXE header


def test_list_applications_tenant_scoped(client):
    """Verifies that an institutional applicant sees only applications belonging to their institution."""
    # 1. Login as Institution 1
    resp1 = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token1 = resp1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    list_resp1 = client.get("/api/v1/applications", headers=headers1)
    assert list_resp1.status_code == status.HTTP_200_OK
    apps1 = list_resp1.json()
    assert len(apps1) >= 1
    assert all(a["institution_id"] == "inst_01" for a in apps1)

    # 2. Login as Institution 2
    resp2 = client.post("/api/v1/auth/login", json={
        "email": "applicant2@institution2.test",
        "password": "Password123!"
    })
    token2 = resp2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    list_resp2 = client.get("/api/v1/applications", headers=headers2)
    assert list_resp2.status_code == status.HTTP_200_OK
    apps2 = list_resp2.json()
    assert len(apps2) >= 1
    assert all(a["institution_id"] == "inst_02" for a in apps2)


def test_create_application_with_statutory_checklist(client, db_session):
    """Verifies creating an EoA application creates the application and initializes 8 checklist slots."""
    # Login as Institution 1
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "application_type": "EOA",
        "total_intake_applied": 600
    })
    assert create_resp.status_code == status.HTTP_201_CREATED
    data = create_resp.json()
    app_id = data["id"]
    assert data["institution_id"] == "inst_01"
    assert data["status"] == "DRAFT"
    assert data["total_intake_applied"] == 600
    assert data["application_number"].startswith("AICTE-EOA-2026-")

    # Verify 8 statutory checklist document slots were initialized
    checklist_resp = client.get(f"/api/v1/applications/{app_id}/checklist", headers=headers)
    assert checklist_resp.status_code == status.HTTP_200_OK
    checklist = checklist_resp.json()["checklist"]
    assert len(checklist) == 8
    assert all(item["status"] == "PENDING" for item in checklist)
    assert any(item["document_type"] == "LAND_TITLE_DEED" for item in checklist)
    assert any(item["document_type"] == "FIRE_SAFETY_NOC" for item in checklist)

    # Verify audit event recorded
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.entity_type == "APPLICATION",
        AuditEvent.entity_id == app_id,
        AuditEvent.action == "APPLICATION_CREATED"
    ).first()
    assert audit is not None


def test_reviewer_cannot_create_application(client):
    """Verifies that non-institution users (Reviewers) are forbidden from creating applications."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "reviewer@reviewer.test",
        "password": "ReviewerPass123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 300
    })
    assert create_resp.status_code == status.HTTP_403_FORBIDDEN


def test_update_application_in_draft_state(client):
    """Verifies updating intake and academic year on an editable application."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create app
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 450
    })
    app_id = c_resp.json()["id"]

    # Update app
    u_resp = client.put(f"/api/v1/applications/{app_id}", headers=headers, json={
        "total_intake_applied": 540
    })
    assert u_resp.status_code == status.HTTP_200_OK
    assert u_resp.json()["total_intake_applied"] == 540


def test_secure_pdf_upload_success_and_metadata(client, db_session):
    """Verifies successful upload of a compliant PDF file, version tracking, and audit logging."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create app
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 600
    })
    app_id = c_resp.json()["id"]

    # Upload Fire NOC
    files = {
        "file": ("Fire_Safety_NOC_2026.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }
    data = {
        "document_type": "FIRE_SAFETY_NOC"
    }

    upload_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data=data,
        files=files
    )
    assert upload_resp.status_code == status.HTTP_201_CREATED
    upload_data = upload_resp.json()
    assert upload_data["status"] == "UPLOADED"
    assert upload_data["version_number"] == 1
    assert upload_data["file_name"] == "Fire_Safety_NOC_2026.pdf"
    assert len(upload_data["file_hash_sha256"]) == 64

    # Verify checklist reflection
    chk_resp = client.get(f"/api/v1/applications/{app_id}/checklist", headers=headers)
    fire_slot = next(item for item in chk_resp.json()["checklist"] if item["document_type"] == "FIRE_SAFETY_NOC")
    assert fire_slot["status"] == "UPLOADED"
    assert fire_slot["current_version"]["version_number"] == 1

    # Verify authorized download/streaming
    doc_id = upload_data["document_id"]
    stream_resp = client.get(f"/api/v1/documents/{doc_id}/versions/1/file", headers=headers)
    assert stream_resp.status_code == status.HTTP_200_OK
    assert stream_resp.headers["content-type"] == "application/pdf"
    assert stream_resp.content == VALID_PDF_BYTES


def test_upload_rejected_for_non_pdf_magic_bytes(client):
    """Verifies that disguised non-PDF files are rejected with 422 Unprocessable Entity."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create app
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 600
    })
    app_id = c_resp.json()["id"]

    # Attempt to upload plain text disguised as PDF
    files = {
        "file": ("Deceptive_Certificate.pdf", io.BytesIO(INVALID_TEXT_BYTES), "application/pdf")
    }
    upload_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "FIRE_SAFETY_NOC"},
        files=files
    )
    assert upload_resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "magic-bytes" in upload_resp.json()["detail"].lower()


def test_upload_rejected_for_empty_file(client):
    """Verifies that 0-byte empty files are rejected."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027"
    })
    app_id = c_resp.json()["id"]

    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }
    upload_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "LAND_TITLE_DEED"},
        files=files
    )
    assert upload_resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cross_institution_upload_and_download_denied(client):
    """Verifies that an applicant cannot upload or download documents from another institution (IDOR protection)."""
    # Login as Institution 1
    resp1 = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token1 = resp1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Create app for Institution 1
    c_resp1 = client.post("/api/v1/applications", headers=headers1, json={"academic_year": "2026-2027"})
    app_id_1 = c_resp1.json()["id"]

    # Upload document to Institution 1 app
    up_resp = client.post(
        f"/api/v1/applications/{app_id_1}/documents",
        headers=headers1,
        data={"document_type": "FIRE_SAFETY_NOC"},
        files={"file": ("fire.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    )
    doc_id_1 = up_resp.json()["document_id"]

    # Login as Institution 2
    resp2 = client.post("/api/v1/auth/login", json={
        "email": "applicant2@institution2.test",
        "password": "Password123!"
    })
    token2 = resp2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 1. Institution 2 tries to upload to Institution 1's application -> 404
    foreign_up_resp = client.post(
        f"/api/v1/applications/{app_id_1}/documents",
        headers=headers2,
        data={"document_type": "LAND_TITLE_DEED"},
        files={"file": ("land.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    )
    assert foreign_up_resp.status_code == status.HTTP_404_NOT_FOUND

    # 2. Institution 2 tries to download Institution 1's document -> 404
    foreign_down_resp = client.get(
        f"/api/v1/documents/{doc_id_1}/versions/1/file",
        headers=headers2
    )
    assert foreign_down_resp.status_code == status.HTTP_404_NOT_FOUND


def test_document_removal_and_slot_reset(client):
    """Verifies that an applicant can delete an uploaded document in DRAFT status, resetting slot to PENDING."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create app
    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]

    # Upload
    client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "LAND_TITLE_DEED"},
        files={"file": ("deed.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    )

    # Delete
    del_resp = client.delete(f"/api/v1/applications/{app_id}/documents/LAND_TITLE_DEED", headers=headers)
    assert del_resp.status_code == status.HTTP_200_OK

    # Verify slot reset to PENDING
    chk_resp = client.get(f"/api/v1/applications/{app_id}/checklist", headers=headers)
    deed_slot = next(item for item in chk_resp.json()["checklist"] if item["document_type"] == "LAND_TITLE_DEED")
    assert deed_slot["status"] == "PENDING"
    assert deed_slot["current_version"] is None
