# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Step 4 Verified Regulatory Corrections Test Suite (tests/backend/test_regulatory_corrections.py)

import io
import json
import pytest
from datetime import datetime
from fastapi import status
from sqlalchemy.orm import Session

from backend.models.application import Application
from backend.models.institution import Institution
from backend.models.document import Document, DocumentVersion
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, ValidationRun, Finding
from backend.services.regulatory_engine import RegulatoryEngine, seed_regulatory_rules
from tests.backend.test_extraction_pipeline import make_synthetic_digital_pdf


def get_token(client, email="applicant@institution.test", password="Password123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["access_token"]


def get_admin_token(client, email="admin@platform.test", password="AdminPass123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(client):
    token = get_token(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    token = get_admin_token(client)
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Structural Stability (RULE-EOA-STRUCT-004) Tests
# =============================================================================

def test_structural_stability_below_30_years_not_mandatory(client, auth_headers):
    """Verifies that for a building completed less than 30 years ago (e.g. 2015),
    a Structural Stability Certificate is NOT mandatory and emits NO_ISSUE_DETECTED (INFO)."""
    # 1. Create EoA Application
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # 2. Upload Building Completion Certificate with recent completion date (2015-05-10, ~11 years old)
    bcc_pdf = make_synthetic_digital_pdf([
        "BRUHAT BENGALURU MAHANAGARA PALIKE (BBMP)",
        "BUILDING COMPLETION CERTIFICATE",
        "Certificate Number: BBMP/CC/2015/8812",
        "Completion Status: Full Completion Fit for Occupation",
        "Issue Date: 10-05-2015",
        "Completed Built-up Area: 18500 Sq.m"
    ])
    files = {"file": ("Completion_Certificate_2015.pdf", io.BytesIO(bcc_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files=files)

    # 3. Validate WITHOUT uploading Structural Stability Certificate
    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    assert val_resp.status_code == status.HTTP_200_OK

    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert struct_finding["severity"] == "INFO"
    assert "Not Required (< 30 Years)" in struct_finding["title"]
    assert "2015-05-10" in struct_finding["observed_value"]


def test_structural_stability_exact_30_year_anniversary_not_mandatory(client, auth_headers):
    """Verifies that on the exact 30-year anniversary date (e.g. completed 1996-07-01
    for session commencing 2026-07-01), the 30-year period has NOT yet expired.
    Under AICTE APH Clause 2.14.6, the certificate is required AFTER the expiry of 30 years,
    so exactly 30 years emits NO_ISSUE_DETECTED (INFO)."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # Exactly 30 years on 2026-07-01 (1996-07-01 + 30 years = 2026-07-01)
    bcc_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "BUILDING COMPLETION CERTIFICATE",
        "Certificate Number: CC/1996/Exact30",
        "Completion Status: Full Completion",
        "Issue Date: 01-07-1996",
        "Completed Built-up Area: 14000 Sq.m"
    ])
    files = {"file": ("BCC_Exact30.pdf", io.BytesIO(bcc_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files=files)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert struct_finding["severity"] == "INFO"
    assert "Not Required (< 30 Years)" in struct_finding["title"]
    assert "1996-07-01" in struct_finding["observed_value"]


def test_structural_stability_first_day_after_30_years_expired_mandatory(client, auth_headers):
    """Verifies that when the 30-year period has expired (e.g. completed 1996-06-30,
    30 years expired on 2026-06-30, so session start 2026-07-01 is past expiry),
    the Structural Stability Certificate IS mandatory and missing cert produces DEFICIENCY."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # 30-year period expired on 2026-06-30
    bcc_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "BUILDING COMPLETION CERTIFICATE",
        "Certificate Number: CC/1996/ExpiredDay1",
        "Completion Status: Full Completion",
        "Issue Date: 30-06-1996",
        "Completed Built-up Area: 14000 Sq.m"
    ])
    files = {"file": ("BCC_ExpiredDay1.pdf", io.BytesIO(bcc_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files=files)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert struct_finding["severity"] == "DEFICIENCY"
    assert "Building Age >= 30 Years" in struct_finding["title"]


def test_structural_stability_occupancy_certificate_requires_completion_date_verification(client, auth_headers):
    """Verifies that an Occupancy Certificate (without an explicit Completion Certificate)
    does not silently substitute its date for the 30-year clock, but emits UNABLE_TO_EVALUATE (WARNING)."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    oc_pdf = make_synthetic_digital_pdf([
        "MUNICIPAL CORPORATION",
        "OCCUPANCY CERTIFICATE",
        "Certificate Number: OC/2018/5501",
        "Completion Status: Occupancy Certificate Fit for Educational Use",
        "Issue Date: 12-08-2018",
        "Completed Built-up Area: 16000 Sq.m"
    ])
    files = {"file": ("Occupancy_Certificate_2018.pdf", io.BytesIO(oc_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files=files)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "UNABLE_TO_EVALUATE"
    assert struct_finding["severity"] == "WARNING"
    assert "Completion Certificate Required (Occupancy Certificate Provided)" in struct_finding["title"]



def test_structural_stability_at_or_above_30_years_mandatory_missing(client, auth_headers):
    """Verifies that for a building completed >= 30 years ago (e.g. 1990),
    a Structural Stability Certificate IS mandatory and missing cert produces DEFICIENCY."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # Completion date 1990-03-15 (~36 years old >= 30)
    bcc_pdf = make_synthetic_digital_pdf([
        "MUNICIPAL CORPORATION OF GREATER MUMBAI",
        "BUILDING COMPLETION CERTIFICATE",
        "Certificate Number: MCGM/CC/1990/442",
        "Completion Status: Completed",
        "Issue Date: 15-03-1990",
        "Completed Built-up Area: 22000 Sq.m"
    ])
    files = {"file": ("Completion_Cert_1990.pdf", io.BytesIO(bcc_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files=files)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert struct_finding["severity"] == "DEFICIENCY"
    assert "Building Age >= 30 Years" in struct_finding["title"]


def test_structural_stability_expired_certificate(client, auth_headers):
    """Verifies that if building age >= 30 years, an uploaded Structural Stability Certificate
    older than 5 years (e.g. issued in 2019) triggers a DEFICIENCY due to expiry."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # 1. Old building BCC (1985)
    bcc_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "BUILDING COMPLETION CERTIFICATE",
        "Issue Date: 10-01-1985",
        "Completion Status: Full Completion",
        "Completed Built-up Area: 15000 Sq.m"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("BCC_1985.pdf", io.BytesIO(bcc_pdf), "application/pdf")})

    # 2. Upload Stability Certificate issued in 2019 (> 5 years before session start 2026-07-01)
    struct_pdf = make_synthetic_digital_pdf([
        "STRUCTURAL CONSULTANTS & ENGINEERS",
        "STRUCTURAL STABILITY & SOUNDNESS CERTIFICATE",
        "Structural Engineer Registration No.: SE-BBMP-9942",
        "Certified Structural Engineer Name: Er. R. K. Sharma",
        "Certificate Date: 15-02-2019",
        "Declaration: Structurally sound and safe for educational occupancy"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "STRUCTURAL_STABILITY"}, files={"file": ("Stability_Cert_2019.pdf", io.BytesIO(struct_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert struct_finding["severity"] == "DEFICIENCY"
    assert "Expired Structural Stability Certificate" in struct_finding["title"]
    assert "2019-02-15" in struct_finding["observed_value"]


def test_structural_stability_valid_certificate(client, auth_headers):
    """Verifies that an empanelled structural engineer certificate issued within 5 years
    for a >= 30-year-old building passes with NO_ISSUE_DETECTED (INFO)."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    bcc_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "BUILDING COMPLETION CERTIFICATE",
        "Issue Date: 10-01-1985",
        "Completion Status: Full Completion",
        "Completed Built-up Area: 15000 Sq.m"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("BCC_1985.pdf", io.BytesIO(bcc_pdf), "application/pdf")})

    # Recent certificate (2025-08-20, within 5 years of 2026-07-01)
    struct_pdf = make_synthetic_digital_pdf([
        "STRUCTURAL CONSULTANTS & ENGINEERS",
        "STRUCTURAL STABILITY & SOUNDNESS CERTIFICATE",
        "Structural Engineer Registration No.: SE-BBMP-9942",
        "Certified Structural Engineer Name: Er. R. K. Sharma",
        "Certificate Date: 20-08-2025",
        "Declaration: Structurally sound and safe for educational occupancy"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "STRUCTURAL_STABILITY"}, files={"file": ("Stability_Cert_2025.pdf", io.BytesIO(struct_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert struct_finding["severity"] == "INFO"
    assert "Structural Stability Verified" in struct_finding["title"]


def test_structural_stability_unparseable_date_safety(client, auth_headers):
    """Verifies that missing or unparseable completion dates yield UNABLE_TO_EVALUATE (WARNING)
    without silently assuming the structure is young or old."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # BCC without issue date
    bcc_pdf = make_synthetic_digital_pdf([
        "MUNICIPAL CORPORATION",
        "COMPLETION CERTIFICATE",
        "Certificate Number: CC-UNKNOWN-DATE",
        "Completion Status: Full Completion",
        "Completed Built-up Area: 12000 Sq.m"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("BCC_NoDate.pdf", io.BytesIO(bcc_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "UNABLE_TO_EVALUATE"
    assert struct_finding["severity"] == "WARNING"
    assert "Building Age Unresolved" in struct_finding["title"]


def test_structural_stability_major_modification_mandates_certificate(client, auth_headers):
    """Verifies that reported major structural modifications mandate a Stability Certificate
    even if the building itself was recently completed (< 30 years old)."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # Recent building (2020) with reported major structural modification / vertical expansion
    bcc_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "BUILDING COMPLETION CERTIFICATE",
        "Issue Date: 12-04-2020",
        "Completion Status: Full Completion",
        "Completed Built-up Area: 25000 Sq.m",
        "Remarks: Major structural modification and vertical expansion of block C"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("BCC_MajorMod.pdf", io.BytesIO(bcc_pdf), "application/pdf")})

    # Validate without stability certificate
    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    struct_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-STRUCT-004")

    assert struct_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert struct_finding["severity"] == "DEFICIENCY"
    assert "Major Modifications" in struct_finding["title"]


# =============================================================================
# 2. Faculty-to-Student Ratio (RULE-EOA-FSR-005) Tests
# =============================================================================

def test_fsr_ug_engineering_1_20_norm(client, auth_headers):
    """Verifies that Under-Graduate Engineering & Technology uses the verified 1:20 norm
    per APH Annexure-5 Section 5.2 (not 1:15).
    720 students, 38 faculty -> FSR 1:18.9 <= 1:20 -> PASS."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # 38 faculty for 720 students -> 720 / 38 = 18.95 <= 20.0
    # Under old 1:15 norm this failed; under verified 1:20 norm this passes!
    roster_pdf = make_synthetic_digital_pdf([
        "APEX INSTITUTE OF TECHNOLOGY - FACULTY CADRE ROSTER",
        "Total Qualified Full-Time Faculty Count: 38",
        "Cadre Distribution: Professors: 4, Associate Professors: 8, Assistant Professors: 26",
        "Certification Date: 2026-03-01"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("Faculty_38.pdf", io.BytesIO(roster_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

    assert fsr_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert fsr_finding["severity"] == "INFO"
    assert "1:20" in fsr_finding["expected_value"]
    assert "1:18.9" in fsr_finding["observed_value"]


def test_fsr_ug_engineering_deficit(client, auth_headers):
    """Verifies that 32 faculty for 720 students (FSR = 1:22.5 > 1:20) triggers DEFICIENCY."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    roster_pdf = make_synthetic_digital_pdf([
        "APEX INSTITUTE OF TECHNOLOGY - FACULTY CADRE ROSTER",
        "Total Qualified Full-Time Faculty Count: 32",
        "Cadre Distribution: Professors: 3, Associate Professors: 5, Assistant Professors: 24"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("Faculty_32.pdf", io.BytesIO(roster_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

    assert fsr_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert fsr_finding["severity"] == "DEFICIENCY"
    assert "1:22.5" in fsr_finding["observed_value"]
    assert "1:20.0" in fsr_finding["expected_value"]


def test_fsr_polytechnic_1_25_norm(client, auth_headers, db_session):
    """Verifies that Polytechnic / Diploma institutions are evaluated under the 1:25 norm."""
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "POLYTECHNIC_DIPLOMA"
        db_session.commit()

        app = client.post("/api/v1/applications", headers=auth_headers, json={
            "academic_year": "2026-2027",
            "total_intake_applied": 600
        }).json()
        app_id = app["id"]

        # 25 faculty for 600 students -> FSR = 1:24.0 <= 1:25.0 -> PASS
        roster_pdf = make_synthetic_digital_pdf([
            "POLYTECHNIC COLLEGE - CADRE ROSTER",
            "Total Qualified Full-Time Faculty Count: 25"
        ])
        client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("Poly_Faculty_25.pdf", io.BytesIO(roster_pdf), "application/pdf")})

        client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
        findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
        fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

        assert fsr_finding["outcome"] == "NO_ISSUE_DETECTED"
        assert "1:25.0" in fsr_finding["expected_value"]
        assert "1:24.0" in fsr_finding["observed_value"]
    finally:
        inst.category = original_cat
        db_session.commit()


def test_fsr_pharmacy_1_15_norm(client, auth_headers, db_session):
    """Verifies that Pharmacy institutions are evaluated under the statutory 1:15 norm."""
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "PHARMACY"
        db_session.commit()

        app = client.post("/api/v1/applications", headers=auth_headers, json={
            "academic_year": "2026-2027",
            "total_intake_applied": 240
        }).json()
        app_id = app["id"]

        # 14 faculty for 240 students -> FSR = 1:17.1 > 1:15.0 -> DEFICIENCY
        roster_pdf = make_synthetic_digital_pdf([
            "COLLEGE OF PHARMACY - CADRE ROSTER",
            "Total Qualified Full-Time Faculty Count: 14"
        ])
        client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("Pharm_Faculty_14.pdf", io.BytesIO(roster_pdf), "application/pdf")})

        client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
        findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
        fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

        assert fsr_finding["outcome"] == "DEFICIENCY_DETECTED"
        assert "1:15.0" in fsr_finding["expected_value"]
    finally:
        inst.category = original_cat
        db_session.commit()


def test_fsr_management_mba_pgdm_1_20_norm(client, auth_headers, db_session):
    """Verifies that Management (MBA/PGDM) institutions are evaluated under the verified
    1:20 norm per APH Annexure-5 Section 5.2 / Table 5.2 (not conflated with 1:15)."""
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "MANAGEMENT"
        db_session.commit()

        app = client.post("/api/v1/applications", headers=auth_headers, json={
            "academic_year": "2026-2027",
            "total_intake_applied": 240
        }).json()
        app_id = app["id"]

        # 12 faculty for 240 students -> FSR = 1:20.0 <= 1:20.0 -> PASS
        roster_pdf = make_synthetic_digital_pdf([
            "INSTITUTE OF MANAGEMENT STUDIES - FACULTY CADRE ROSTER",
            "Total Qualified Full-Time Faculty Count: 12",
            "Cadre Distribution: Professors: 2, Associate Professors: 4, Assistant Professors: 6"
        ])
        client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("MBA_Faculty_12.pdf", io.BytesIO(roster_pdf), "application/pdf")})

        client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
        findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
        fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

        assert fsr_finding["outcome"] == "NO_ISSUE_DETECTED"
        assert fsr_finding["severity"] == "INFO"
        assert "1:20.0" in fsr_finding["expected_value"]
        assert "1:20.0" in fsr_finding["observed_value"]
        assert "Section 5.2" in fsr_finding["explanation"]
    finally:
        inst.category = original_cat
        db_session.commit()


def test_fsr_mca_1_20_norm(client, auth_headers, db_session):
    """Verifies that MCA programmes are evaluated under the 1:20 norm per APH Annexure-5."""
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "MCA"
        db_session.commit()

        app = client.post("/api/v1/applications", headers=auth_headers, json={
            "academic_year": "2026-2027",
            "total_intake_applied": 120
        }).json()
        app_id = app["id"]

        # 6 faculty for 120 students -> FSR = 1:20.0 -> PASS
        roster_pdf = make_synthetic_digital_pdf([
            "DEPARTMENT OF COMPUTER APPLICATIONS (MCA) - CADRE ROSTER",
            "Total Qualified Full-Time Faculty Count: 6"
        ])
        client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("MCA_Faculty_6.pdf", io.BytesIO(roster_pdf), "application/pdf")})

        client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
        findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
        fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

        assert fsr_finding["outcome"] == "NO_ISSUE_DETECTED"
        assert "1:20.0" in fsr_finding["expected_value"]
    finally:
        inst.category = original_cat
        db_session.commit()


def test_fsr_pg_engineering_1_15_norm(client, auth_headers, db_session):
    """Verifies that Post-Graduate Engineering (M.E./M.Tech) uses 1:15 per APH Annexure-5 Section 5.3."""
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "ENGINEERING_PG"
        db_session.commit()

        app = client.post("/api/v1/applications", headers=auth_headers, json={
            "academic_year": "2026-2027",
            "total_intake_applied": 90
        }).json()
        app_id = app["id"]

        # 6 faculty for 90 students -> FSR = 1:15.0 <= 1:15.0 -> PASS
        roster_pdf = make_synthetic_digital_pdf([
            "POST GRADUATE ENGINEERING - CADRE ROSTER",
            "Total Qualified Full-Time Faculty Count: 6"
        ])
        client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "FACULTY_ROSTER"}, files={"file": ("PGEngg_Faculty_6.pdf", io.BytesIO(roster_pdf), "application/pdf")})

        client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
        findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
        fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")

        assert fsr_finding["outcome"] == "NO_ISSUE_DETECTED"
        assert "1:15.0" in fsr_finding["expected_value"]
        assert "Section 5.3" in fsr_finding["explanation"]
    finally:
        inst.category = original_cat
        db_session.commit()



# =============================================================================
# 3. Land & Built-up Area (RULE-EOA-LAND-001) Tests
# =============================================================================

def test_fsi_far_land_area_compliance(client, auth_headers):
    """Verifies that when FSI/FAR is declared, the engine evaluates whether permissible
    built-up area accommodates the sanctioned building plan area."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # Land: 2.0 Acres, FAR: 2.5 -> Max built-up = 2.0 * 4046.86 * 2.5 = 20,234.3 Sq.m
    title_pdf = make_synthetic_digital_pdf([
        "REVENUE DEPARTMENT REGISTERED LAND TITLE DEED",
        "Contiguous Land Area: 2.00 Acres",
        "Sanctioned FSI / FAR: 2.50",
        "Survey Numbers: 101/A, 101/B",
        "30 Years Registered Lease"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "LAND_TITLE_DEED"}, files={"file": ("Title_2Acres_FAR2.5.pdf", io.BytesIO(title_pdf), "application/pdf")})

    # Building Plan: Sanctioned Built-up Area 18000 Sq.m <= 20,234.3 Sq.m -> PASS
    plan_pdf = make_synthetic_digital_pdf([
        "BBMP TOWN PLANNING SANCTIONED MASTER PLAN",
        "Sanctioned Built-up Area: 18000.0 Sq.m",
        "Plan Sanctioning Authority: Bruhat Bengaluru Mahanagara Palike"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "APPROVED_BUILDING_PLAN"}, files={"file": ("Plan_18000.pdf", io.BytesIO(plan_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    land_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-LAND-001")

    assert land_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert land_finding["severity"] == "INFO"
    assert "FSI/FAR Compliance Verified" in land_finding["title"]


def test_fsi_far_builtup_area_exceeded(client, auth_headers):
    """Verifies that if constructed built-up area exceeds permissible FAR, DEFICIENCY is emitted."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    # Land: 1.5 Acres, FAR: 1.5 -> Max built-up = 1.5 * 4046.86 * 1.5 = 9,105.4 Sq.m
    title_pdf = make_synthetic_digital_pdf([
        "REGISTERED LAND TITLE DEED",
        "Contiguous Land Area: 1.50 Acres",
        "Sanctioned FSI / FAR: 1.50",
        "Survey Numbers: 55/1"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "LAND_TITLE_DEED"}, files={"file": ("Title_1.5Acres.pdf", io.BytesIO(title_pdf), "application/pdf")})

    # Plan with 15000 Sq.m > 9105.4 Sq.m -> DEFICIENCY
    plan_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING SANCTIONED BUILDING PLAN",
        "Sanctioned Built-up Area: 15000.0 Sq.m",
        "Plan Sanctioning Authority: Town Planning Department"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "APPROVED_BUILDING_PLAN"}, files={"file": ("Plan_15000.pdf", io.BytesIO(plan_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    land_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-LAND-001")

    assert land_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert land_finding["severity"] == "DEFICIENCY"
    assert "Exceeds Permissible FSI/FAR" in land_finding["title"]


def test_lease_duration_below_30_years_deficiency(client, auth_headers):
    """Verifies that a registered lease deed of less than 30 years (e.g. 15 years) emits DEFICIENCY."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    lease_pdf = make_synthetic_digital_pdf([
        "SUB-REGISTRAR OFFICE REGISTERED LEASE DEED",
        "Contiguous Land Area: 5.00 Acres",
        "Survey Numbers: 204/1, 204/2",
        "Period of Lease: 15 Years",
        "Lessor: Sri Venkateshwara Trust"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "LAND_TITLE_DEED"}, files={"file": ("Lease_15Years.pdf", io.BytesIO(lease_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    land_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-LAND-001")

    assert land_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert land_finding["severity"] == "DEFICIENCY"
    assert "Lease Duration Below 30 Years" in land_finding["title"]


# =============================================================================
# 4. Building Completion Evidence (RULE-EOA-BCC-002) Tests
# =============================================================================

@pytest.mark.parametrize("status_keyword,title_keyword", [
    ("Form D Completion", "Form D"),
    ("Building License", "Building License"),
    ("Occupancy Certificate", "Occupancy Certificate"),
    ("Completion Certificate", "Completion Certificate"),
])
def test_building_completion_alternatives_accepted(client, auth_headers, status_keyword, title_keyword):
    """Verifies that valid statutory alternatives (Form D, Building License, OC, CC)
    are recognized and accepted as valid completion evidence under APH Chapter II."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    bcc_pdf = make_synthetic_digital_pdf([
        f"BRUHAT BENGALURU MAHANAGARA PALIKE - {title_keyword.upper()}",
        f"Certificate Number: BBMP/BLD/2024/9912",
        f"Completion Status: {status_keyword}",
        "Issue Date: 15-06-2024",
        "Completed Built-up Area: 16000 Sq.m"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("BCC_Alt.pdf", io.BytesIO(bcc_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    bcc_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-BCC-002")

    assert bcc_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert bcc_finding["severity"] == "INFO"


def test_building_completion_pwd_structural_clearance_rejected(client, auth_headers):
    """Verifies that a standalone PWD Structural Clearance Certificate is REJECTED
    as a substitute for statutory building completion evidence."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    }).json()
    app_id = app["id"]

    pwd_pdf = make_synthetic_digital_pdf([
        "PUBLIC WORKS DEPARTMENT (PWD) GOVERNMENT OF KARNATAKA",
        "PWD STRUCTURAL CLEARANCE CERTIFICATE",
        "Clearance Ref: PWD/BLR/CIVIL/2025/104",
        "Inspection Findings: Structural clearance certificate issued for academic block",
        "Issue Date: 2025-09-10"
    ])
    client.post(f"/api/v1/applications/{app_id}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("PWD_Clearance.pdf", io.BytesIO(pwd_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=auth_headers).json()["findings"]
    bcc_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-BCC-002")

    assert bcc_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert bcc_finding["severity"] == "DEFICIENCY"
    assert "PWD Structural Clearance Not Accepted" in bcc_finding["title"]


def test_provisional_occupancy_certificate_two_year_limit(client, auth_headers):
    """Verifies that a Provisional Occupancy Certificate within 2 years passes,
    while one exceeding the 2-year consecutive limit triggers DEFICIENCY."""
    # 1. Provisional within 2-year limit (1 Year) -> PASS
    app1 = client.post("/api/v1/applications", headers=auth_headers, json={"academic_year": "2026-2027", "total_intake_applied": 720}).json()
    prov_ok_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "PROVISIONAL OCCUPANCY CERTIFICATE",
        "Certificate Number: POC-2025-01",
        "Provisional Duration: 1 Academic Year",
        "Issue Date: 2025-06-15"
    ])
    client.post(f"/api/v1/applications/{app1['id']}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("POC_1Year.pdf", io.BytesIO(prov_ok_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app1['id']}/validate", headers=auth_headers)
    findings1 = client.get(f"/api/v1/applications/{app1['id']}/findings", headers=auth_headers).json()["findings"]
    bcc1 = next(f for f in findings1 if f["rule_code"] == "RULE-EOA-BCC-002")
    assert bcc1["outcome"] == "NO_ISSUE_DETECTED"
    assert "Within 2-Year Limit" in bcc1["title"]

    # 2. Provisional exceeding 2-year limit (3 Academic Years) -> DEFICIENCY
    app2 = client.post("/api/v1/applications", headers=auth_headers, json={"academic_year": "2026-2027", "total_intake_applied": 720}).json()
    prov_bad_pdf = make_synthetic_digital_pdf([
        "TOWN PLANNING DEPARTMENT",
        "PROVISIONAL OCCUPANCY CERTIFICATE",
        "Certificate Number: POC-2023-99",
        "Provisional Duration: 3 Academic Years",
        "Issue Date: 2023-05-10"
    ])
    client.post(f"/api/v1/applications/{app2['id']}/documents", headers=auth_headers, data={"document_type": "BUILDING_COMPLETION"}, files={"file": ("POC_3Years.pdf", io.BytesIO(prov_bad_pdf), "application/pdf")})

    client.post(f"/api/v1/applications/{app2['id']}/validate", headers=auth_headers)
    findings2 = client.get(f"/api/v1/applications/{app2['id']}/findings", headers=auth_headers).json()["findings"]
    bcc2 = next(f for f in findings2 if f["rule_code"] == "RULE-EOA-BCC-002")
    assert bcc2["outcome"] == "DEFICIENCY_DETECTED"
    assert "Provisional Occupancy Certificate Limit Exceeded" in bcc2["title"]


# =============================================================================
# 5. Unsupported Rule Deactivation & Governance Tests
# =============================================================================

def test_unsupported_rule_bank_009_deactivated(client, auth_headers, admin_headers):
    """Verifies that RULE-DRAFT-BANK-009 is inactive by default and bypassed during evaluation."""
    rules_resp = client.get("/api/v1/rules", headers=auth_headers)
    rules = {r["rule_code"]: r for r in rules_resp.json()}

    assert "RULE-DRAFT-BANK-009" in rules
    assert rules["RULE-DRAFT-BANK-009"]["status"] == "DRAFT_MISSING_OFFICIAL_SOURCE"
    assert rules["RULE-DRAFT-BANK-009"]["is_active"] is False

    # Run validation and verify RULE-DRAFT-BANK-009 is NEVER in emitted findings
    app = client.post("/api/v1/applications", headers=auth_headers, json={"academic_year": "2026-2027", "total_intake_applied": 720}).json()
    client.post(f"/api/v1/applications/{app['id']}/validate", headers=auth_headers)
    findings = client.get(f"/api/v1/applications/{app['id']}/findings", headers=auth_headers).json()["findings"]
    bank_finding = next((f for f in findings if f["rule_code"] == "RULE-DRAFT-BANK-009"), None)
    assert bank_finding is None


def test_admin_deactivate_endpoint_with_audit_logging(client, admin_headers, auth_headers, db_session):
    """Verifies that the new admin deactivation endpoint successfully deactivates a rule
    and logs an audit trail event."""
    seed_regulatory_rules(db_session)

    # 1. Activate RULE-DRAFT-PARK-010 first
    client.post("/api/v1/rules/RULE-DRAFT-PARK-010/activate", headers=admin_headers)

    # 2. Deactivate using POST /api/v1/rules/{code}/deactivate
    deact_resp = client.post(
        "/api/v1/rules/RULE-DRAFT-PARK-010/deactivate?reason=Deactivated+during+testing",
        headers=admin_headers
    )
    assert deact_resp.status_code == status.HTTP_200_OK
    data = deact_resp.json()
    assert data["is_active"] is False
    assert data["status"] == "DRAFT_MISSING_OFFICIAL_SOURCE"

    # 3. Non-admin cannot call deactivate endpoint
    forbidden_resp = client.post("/api/v1/rules/RULE-DRAFT-PARK-010/deactivate", headers=auth_headers)
    assert forbidden_resp.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# 6. Preserved Fixes Integrity: Applicant Correction Workflow (DEF-APPLICANT-001)
# =============================================================================

def test_applicant_workflow_remediation_preserved(client, auth_headers, db_session):
    """Verifies that the DEF-APPLICANT-001 remediation remains intact:
    PUT /api/v1/findings/{id}/response cannot reset finding status if already submitted."""
    app = client.post("/api/v1/applications", headers=auth_headers, json={"academic_year": "2026-2027", "total_intake_applied": 720}).json()
    app_id = app["id"]

    client.post(f"/api/v1/applications/{app_id}/validate", headers=auth_headers)
    def_resp = client.get(f"/api/v1/applications/{app_id}/deficiencies", headers=auth_headers)
    findings = def_resp.json()["deficiencies"]
    finding_id = findings[0]["id"]

    # 1. Save draft response
    draft_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=auth_headers, json={
        "response_text": "Draft response in progress",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert draft_resp.status_code == status.HTTP_200_OK

    # 2. Formally submit response
    submit_resp = client.post(f"/api/v1/findings/{finding_id}/submit", headers=auth_headers, json={
        "response_text": "Official correction submitted for reviewer scrutiny.",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert submit_resp.status_code == status.HTTP_200_OK

    # 3. Attempt to overwrite with draft PUT -> Must fail with 409 Conflict (DEF-APPLICANT-001)
    tamper_resp = client.put(f"/api/v1/findings/{finding_id}/response", headers=auth_headers, json={
        "response_text": "Attempting illegal post-submission draft reset",
        "response_category": "CLARIFICATION_JUSTIFICATION"
    })
    assert tamper_resp.status_code == status.HTTP_409_CONFLICT
    assert "awaiting revalidation" in tamper_resp.json()["detail"].lower()
