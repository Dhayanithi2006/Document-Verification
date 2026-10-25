# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# P6 Intelligent Document Processing (IDP), OCR & Provenance Tests (tests/backend/test_extraction_pipeline.py)

import io
import pytest
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastapi import status
from sqlalchemy.orm import Session
from pypdf import PdfWriter, PdfReader

from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.extraction import DocumentProcessingRun, ExtractedField, DocumentPage
from backend.services.extraction_service import DocumentProcessingPipeline


def make_synthetic_digital_pdf(text_lines: list[str]) -> bytes:
    """Generates a genuine digital PDF with selectable text stream using ReportLab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 720
    for line in text_lines:
        c.drawString(72, y, line)
        y -= 25
    c.showPage()
    c.save()
    return buf.getvalue()


def make_synthetic_scanned_pdf(text_lines: list[str]) -> bytes:
    """Generates a genuine scanned/image-only PDF with NO text layer using Pillow."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 100
    for line in text_lines:
        draw.text((80, y), line, fill=(0, 0, 0))
        y += 45
    
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def make_synthetic_mixed_pdf(digital_lines: list[str], scanned_lines: list[str]) -> bytes:
    """Generates a genuine multi-page mixed PDF: Page 1 digital text, Page 2 raster image."""
    digital_pdf_bytes = make_synthetic_digital_pdf(digital_lines)
    scanned_pdf_bytes = make_synthetic_scanned_pdf(scanned_lines)

    reader1 = PdfReader(io.BytesIO(digital_pdf_bytes))
    reader2 = PdfReader(io.BytesIO(scanned_pdf_bytes))

    writer = PdfWriter()
    writer.add_page(reader1.pages[0])
    writer.add_page(reader2.pages[0])

    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


# -------------------------------------------------------------------------
# Test 1: Digital PDF Extraction & Field Grounding
# -------------------------------------------------------------------------
def test_digital_pdf_extraction_and_field_grounding(client, db_session):
    """Verifies that a digital PDF is routed to text extraction, fields are extracted,
    and genuine confidence and bounding boxes are persisted."""
    # 1. Login as Institution 1
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Application
    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]

    # 3. Create digital Fire NOC PDF with realistic AICTE statutory text
    pdf_bytes = make_synthetic_digital_pdf([
        "GOVERNMENT FIRE AND RESCUE SERVICES DEPARTMENT",
        "NO OBJECTION CERTIFICATE - FIRE SAFETY",
        "NOC Reference Number: FS-NOC-BLR-2026-9812",
        "Issued to: Apex Institute of Technology and Management",
        "Survey No. 44/2A, Electronic City Phase 1, Bengaluru",
        "Total Built-up Area Inspected: 8420.50 Sq.m",
        "Issue Date: 15-04-2025",
        "Valid Until Date: 31-03-2027",
        "Fire Safety Measures Inspected: SATISFACTORY / ADEQUATE",
        "Issued By: Chief Fire Officer, Fire Safety Directorate"
    ])

    files = {"file": ("Fire_Safety_NOC_2026.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "FIRE_SAFETY_NOC"},
        files=files
    )
    assert up_resp.status_code == status.HTTP_201_CREATED
    doc_id = up_resp.json()["document_id"]

    # 4. Trigger IDP Processing via POST /documents/{id}/process
    proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_resp.status_code == status.HTTP_200_OK
    run_data = proc_resp.json()
    assert run_data["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
    assert run_data["extraction_method"] == "DIGITAL_PDF_TEXT"
    assert run_data["pages_digital"] == 1
    assert run_data["pages_ocr"] == 0
    assert run_data["pages_processed"] == 1

    # 5. Retrieve Extracted Fields via GET /documents/{id}/extracted-fields
    fields_resp = client.get(f"/api/v1/documents/{doc_id}/extracted-fields", headers=headers)
    assert fields_resp.status_code == status.HTTP_200_OK
    result_data = fields_resp.json()
    assert result_data["document_id"] == doc_id
    assert result_data["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
    
    fields = {f["field_key"]: f for f in result_data["extracted_fields"]}
    assert "noc_number" in fields
    assert "FS-NOC-BLR-2026-9812" in fields["noc_number"]["normalized_value"]
    assert fields["noc_number"]["extraction_method"] == "DIGITAL_PDF_TEXT"
    assert fields["noc_number"]["page_number"] == 1
    assert fields["noc_number"]["confidence"] == 1.0
    assert fields["noc_number"]["bounding_box"] is not None

    # Check date extraction
    if "valid_until_date" in fields:
        assert "2027-03-31" in fields["valid_until_date"]["normalized_value"]
        assert fields["valid_until_date"]["data_type"] == "DATE"

    # 6. Retrieve Page Content via GET /documents/{id}/pages
    pages_resp = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    assert pages_resp.status_code == status.HTTP_200_OK
    pages = pages_resp.json()
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["extraction_method"] == "DIGITAL_PDF_TEXT"
    assert "FIRE AND RESCUE" in pages[0]["text_content"]


# -------------------------------------------------------------------------
# Test 2: Real Scanned Document OCR Execution with PaddleOCR ONNX
# -------------------------------------------------------------------------
def test_real_scanned_pdf_ocr_execution(client, db_session):
    """Verifies that an image-only scanned PDF routes to real local PaddleOCR inference,
    recognizes text, preserves token confidence and geometry without mocking."""
    from backend.services.extraction_service import get_ocr_engine
    if get_ocr_engine() is None:
        pytest.skip("PaddleOCR engine unavailable on host (blocked by Windows Application Control policy)")

    # 1. Login as Institution 1
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Application
    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]

    # 3. Create pure raster image-based Land Title Deed PDF (no digital text layer)
    scanned_pdf_bytes = make_synthetic_scanned_pdf([
        "REVENUE DEPARTMENT GOVERNMENT OF KARNATAKA",
        "LAND TITLE DEED AND REGISTERED LEASE CERTIFICATE",
        "Deed Registration Number: TD-8841-2024",
        "Contiguous Land Area: 5.25 Acres",
        "Survey Number: 44/2A",
        "Registration Date: 2024-06-12",
        "Owner: Apex Educational Trust",
        "Land Category: Educational Institutional Purpose"
    ])

    files = {"file": ("Land_Title_Deed_Scanned.pdf", io.BytesIO(scanned_pdf_bytes), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "LAND_TITLE_DEED"},
        files=files
    )
    assert up_resp.status_code == status.HTTP_201_CREATED
    doc_id = up_resp.json()["document_id"]

    # 4. Trigger IDP Processing (re-uses existing run or executes if needed)
    proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_resp.status_code == status.HTTP_200_OK
    run_data = proc_resp.json()
    assert run_data["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
    assert run_data["extraction_method"] == "OCR"
    assert run_data["pages_ocr"] == 1
    assert run_data["pages_digital"] == 0
    assert run_data["average_confidence"] > 0.5

    # 5. Check Pages Endpoint
    pages_resp = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    assert pages_resp.status_code == status.HTTP_200_OK
    pages = pages_resp.json()
    assert len(pages) == 1
    assert pages[0]["extraction_method"] == "OCR"
    assert pages[0]["confidence"] > 0.5
    # Verify genuine text was recognized by OCR engine
    assert "LAND" in pages[0]["text_content"].upper() or "DEED" in pages[0]["text_content"].upper()


# -------------------------------------------------------------------------
# Test 3: Mixed PDF (Digital Text Page 1 + Scanned Page 2)
# -------------------------------------------------------------------------
def test_mixed_pdf_routing_and_page_provenance(client, db_session):
    """Verifies that a multi-page PDF with both digital text and scanned pages
    routes each page to its appropriate extractor without dropping pages."""
    from backend.services.extraction_service import get_ocr_engine
    if get_ocr_engine() is None:
        pytest.skip("PaddleOCR engine unavailable on host (blocked by Windows Application Control policy)")

    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]

    mixed_bytes = make_synthetic_mixed_pdf(
        digital_lines=[
            "OFFICIAL BUILDING COMPLETION CERTIFICATE",
            "MUNICIPAL CORPORATION PLANNING AUTHORITY",
            "Certificate Reference: CC-2026-7788",
            "Built-up Carpet Area: 8420.50 Sq.m",
            "Completion Date: 2025-11-20"
        ],
        scanned_lines=[
            "FIRE SAFETY AND OCCUPANCY ANNEXURE",
            "Survey Number 44/2A Block B",
            "Inspected and Approved for Occupancy"
        ]
    )

    files = {"file": ("Building_Completion_Mixed.pdf", io.BytesIO(mixed_bytes), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "BUILDING_COMPLETION"},
        files=files
    )
    assert up_resp.status_code == status.HTTP_201_CREATED
    doc_id = up_resp.json()["document_id"]

    proc_resp = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_resp.status_code == status.HTTP_200_OK
    run_data = proc_resp.json()
    assert run_data["extraction_method"] == "HYBRID"
    assert run_data["pages_processed"] == 2
    assert run_data["pages_digital"] == 1
    assert run_data["pages_ocr"] == 1

    # Check pages
    pages_resp = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    pages = pages_resp.json()
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[0]["extraction_method"] == "DIGITAL_PDF_TEXT"
    assert pages[1]["page_number"] == 2
    assert pages[1]["extraction_method"] == "OCR"


# -------------------------------------------------------------------------
# Test 4: Idempotency and Controlled Reprocessing
# -------------------------------------------------------------------------
def test_processing_idempotency_and_force_reprocess(client, db_session):
    """Verifies that duplicate process requests reuse completed runs unless force=true."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027"})
    app_id = c_resp.json()["id"]

    pdf_bytes = make_synthetic_digital_pdf([
        "STRUCTURAL STABILITY CERTIFICATE",
        "Licensed Structural Engineer Registration: SE-KAT-2024-551",
        "Building Stability Condition: SOUND AND SAFE",
        "Date of Inspection: 2026-01-10"
    ])

    files = {"file": ("Structural_Stability.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "STRUCTURAL_STABILITY"},
        files=files
    )
    doc_id = up_resp.json()["document_id"]

    # First run
    run1 = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers).json()
    run1_id = run1["run_id"]
    assert run1["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]

    # Second run without force should reuse run1
    run2 = client.post(f"/api/v1/documents/{doc_id}/process?force=false", headers=headers).json()
    assert run2["run_id"] == run1_id

    # Third run with force=true should produce fresh run
    run3 = client.post(f"/api/v1/documents/{doc_id}/process?force=true", headers=headers).json()
    assert run3["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]


# -------------------------------------------------------------------------
# Test 5: Tenant Isolation & IDOR Protection on IDP Endpoints
# -------------------------------------------------------------------------
def test_tenant_isolation_on_idp_endpoints(client, db_session):
    """Verifies that an applicant from Institution 2 cannot trigger extraction,
    view status, read extracted fields, or inspect page text for Institution 1."""
    # Institution 1 creates and uploads a document
    resp1 = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token1 = resp1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    c_resp1 = client.post("/api/v1/applications", headers=headers1, json={"academic_year": "2026-2027"})
    app_id_1 = c_resp1.json()["id"]

    pdf_bytes = make_synthetic_digital_pdf(["CONFIDENTIAL INSTITUTION 1 FACULTY ROSTER", "Faculty Count: 45"])
    files = {"file": ("Faculty_Roster.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id_1}/documents",
        headers=headers1,
        data={"document_type": "FACULTY_ROSTER"},
        files=files
    )
    doc_id_1 = up_resp.json()["document_id"]

    # Institution 2 logs in
    resp2 = client.post("/api/v1/auth/login", json={
        "email": "applicant2@institution2.test",
        "password": "Password123!"
    })
    token2 = resp2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 1. Attempt process
    p_attack = client.post(f"/api/v1/documents/{doc_id_1}/process", headers=headers2)
    assert p_attack.status_code == status.HTTP_404_NOT_FOUND

    # 2. Attempt status
    s_attack = client.get(f"/api/v1/documents/{doc_id_1}/processing-status", headers=headers2)
    assert s_attack.status_code == status.HTTP_404_NOT_FOUND

    # 3. Attempt extracted fields
    f_attack = client.get(f"/api/v1/documents/{doc_id_1}/extracted-fields", headers=headers2)
    assert f_attack.status_code == status.HTTP_404_NOT_FOUND

    # 4. Attempt page text
    pg_attack = client.get(f"/api/v1/documents/{doc_id_1}/pages", headers=headers2)
    assert pg_attack.status_code == status.HTTP_404_NOT_FOUND


# -------------------------------------------------------------------------
# Test 6: Safe Failure Handling on Corrupt / Non-existent Documents
# -------------------------------------------------------------------------
def test_safe_error_handling_on_invalid_document(client, db_session):
    """Verifies that non-existent document IDs return 404 and do not crash."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = "doc_non_existent_9999"
    assert client.post(f"/api/v1/documents/{fake_id}/process", headers=headers).status_code == 404
    assert client.get(f"/api/v1/documents/{fake_id}/processing-status", headers=headers).status_code == 404
    assert client.get(f"/api/v1/documents/{fake_id}/extracted-fields", headers=headers).status_code == 404
    assert client.get(f"/api/v1/documents/{fake_id}/pages", headers=headers).status_code == 404
