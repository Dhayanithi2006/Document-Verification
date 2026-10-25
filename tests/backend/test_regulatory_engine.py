# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Phase P7 Regulatory Rule Engine & Cross-Matching Tests (tests/backend/test_regulatory_engine.py)

import io
import json
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from backend.models.application import Application
from backend.models.institution import Institution
from backend.models.document import Document, DocumentVersion
from backend.models.extraction import ExtractedField, DocumentProcessingRun
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, ValidationRun, Finding
from backend.services.regulatory_engine import RegulatoryEngine, seed_regulatory_rules
from tests.backend.test_extraction_pipeline import make_synthetic_digital_pdf


# -------------------------------------------------------------------------
# Test 1: Rule Catalog Seeding & Activation Lifecycle
# -------------------------------------------------------------------------
def test_regulatory_rule_catalog_and_activation_lifecycle(client, db_session):
    """Verifies that the versioned rule catalog is seeded with official APH clauses,
    draft rules are inactive by default, and only admin can activate rules."""
    seed_regulatory_rules(db_session)

    # 1. Anonymous cannot view rules without auth
    resp = client.get("/api/v1/rules")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Authenticate as Institution user
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. View rules catalog
    rules_resp = client.get("/api/v1/rules", headers=headers)
    assert rules_resp.status_code == status.HTTP_200_OK
    rules = rules_resp.json()
    assert len(rules) >= 10  # 8 active + 2 draft

    rule_codes = {r["rule_code"]: r for r in rules}
    assert "RULE-EOA-LAND-001" in rule_codes
    assert "RULE-EOA-FIRE-003" in rule_codes
    assert "RULE-EOA-CROSS-006" in rule_codes
    assert "RULE-DRAFT-BANK-009" in rule_codes

    # Verify active vs draft status
    assert rule_codes["RULE-EOA-FIRE-003"]["status"] == "APPROVED_FOR_PROTOTYPE_USE"
    assert rule_codes["RULE-EOA-FIRE-003"]["is_active"] is True
    assert rule_codes["RULE-DRAFT-BANK-009"]["status"] == "DRAFT_MISSING_OFFICIAL_SOURCE"
    assert rule_codes["RULE-DRAFT-BANK-009"]["is_active"] is False

    # 4. Institution user cannot activate a draft rule (403 Forbidden)
    act_resp = client.post("/api/v1/rules/RULE-DRAFT-BANK-009/activate", headers=headers)
    assert act_resp.status_code == status.HTTP_403_FORBIDDEN

    # 5. Authenticate as Admin user
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@platform.test",
        "password": "AdminPass123!"
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 6. Admin can activate rule
    admin_act = client.post("/api/v1/rules/RULE-DRAFT-BANK-009/activate", headers=admin_headers)
    assert admin_act.status_code == status.HTTP_200_OK
    assert admin_act.json()["is_active"] is True

    # 7. Query specific rule detail
    detail_resp = client.get("/api/v1/rules/RULE-EOA-FIRE-003", headers=headers)
    assert detail_resp.status_code == status.HTTP_200_OK
    rule_detail = detail_resp.json()
    assert rule_detail["rule_code"] == "RULE-EOA-FIRE-003"
    assert "NBC Part IV" in rule_detail["official_source"]
    assert len(rule_detail["versions"]) >= 1


# -------------------------------------------------------------------------
# Test 2: Missing Mandatory Document Checks
# -------------------------------------------------------------------------
def test_missing_mandatory_document_deficiency_detection(client, db_session):
    """Verifies that an application with empty checklist produces explicit deficiencies
    for missing mandatory statutory documents without crashing or fabricating results."""
    # 1. Login as Institution 1
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create brand-new EoA Application with no uploaded documents
    c_resp = client.post("/api/v1/applications", headers=headers, json={
        "academic_year": "2026-2027",
        "total_intake_applied": 720
    })
    assert c_resp.status_code == status.HTTP_201_CREATED
    app_id = c_resp.json()["id"]

    # 3. Trigger validation via POST /applications/{id}/validate
    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_resp.status_code == status.HTTP_200_OK
    run_data = val_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["findings_summary"]["deficiencies"] > 0

    # 4. Fetch findings via GET /applications/{id}/findings
    findings_resp = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers)
    assert findings_resp.status_code == status.HTTP_200_OK
    findings_data = findings_resp.json()
    assert findings_data["total_checks"] >= 8

    # Find the missing Fire NOC finding
    fire_finding = next((f for f in findings_data["findings"] if f["rule_code"] == "RULE-EOA-FIRE-003"), None)
    assert fire_finding is not None
    assert fire_finding["severity"] == "DEFICIENCY"
    assert fire_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert "missing" in fire_finding["title"].lower() or "not uploaded" in fire_finding["observed_value"].lower()
    assert fire_finding["evidence"]["document_id"] is not None

    # Verify application status transitioned to DEFICIENCIES_DETECTED
    app_status_resp = client.get(f"/api/v1/applications/{app_id}", headers=headers)
    assert app_status_resp.json()["status"] == "DEFICIENCIES_DETECTED"


# -------------------------------------------------------------------------
# Test 3: Date and Validity Checks (Fire Safety NOC Expiry)
# -------------------------------------------------------------------------
def test_date_and_validity_check_fire_noc(client, db_session):
    """Verifies that an expired Fire Safety NOC produces a deficiency,
    while a renewed/valid Fire Safety NOC produces a passing outcome."""
    # 1. Login as Institution 1
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027", "total_intake_applied": 720})
    app_id = c_resp.json()["id"]

    # 2. Upload EXPIRED Fire NOC (valid until 2026-03-31, prior to 2026-07-01 session start)
    expired_pdf = make_synthetic_digital_pdf([
        "GOVERNMENT FIRE AND RESCUE SERVICES DEPARTMENT",
        "NO OBJECTION CERTIFICATE - FIRE SAFETY",
        "NOC Reference Number: FS-NOC-BLR-2025-EXPIRED",
        "Issued to: Apex Institute of Technology and Management",
        "Issue Date: 01-04-2025",
        "Valid Until Date: 31-03-2026",
        "Fire Safety Clearance: SATISFACTORY"
    ])
    files = {"file": ("Fire_NOC_Expired.pdf", io.BytesIO(expired_pdf), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "FIRE_SAFETY_NOC"},
        files=files
    )
    assert up_resp.status_code == status.HTTP_201_CREATED

    # 3. Validate
    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_resp.status_code == status.HTTP_200_OK

    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    fire_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FIRE-003")
    assert fire_finding["severity"] == "DEFICIENCY"
    assert fire_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert "2026-03-31" in fire_finding["observed_value"]
    assert "2026-07-01" in fire_finding["expected_value"]
    assert fire_finding["evidence"]["page_number"] == 1
    assert fire_finding["evidence"]["bounding_box"] is not None

    # 4. Now upload RENEWED Fire NOC (valid until 2027-04-30) as v2
    renewed_pdf = make_synthetic_digital_pdf([
        "GOVERNMENT FIRE AND RESCUE SERVICES DEPARTMENT",
        "RENEWED FIRE SAFETY CERTIFICATE",
        "NOC Reference Number: FS-NOC-BLR-2026-RENEWED",
        "Issued to: Apex Institute of Technology and Management",
        "Issue Date: 15-04-2026",
        "Valid Until Date: 30-04-2027",
        "Fire Safety Clearance: SATISFACTORY / ADEQUATE"
    ])
    files_v2 = {"file": ("Fire_NOC_Renewed_v2.pdf", io.BytesIO(renewed_pdf), "application/pdf")}
    up_v2_resp = client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=headers,
        data={"document_type": "FIRE_SAFETY_NOC"},
        files=files_v2
    )
    assert up_v2_resp.status_code == status.HTTP_201_CREATED
    assert up_v2_resp.json()["version_number"] == 2

    # 5. Re-evaluate
    val_v2_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_v2_resp.status_code == status.HTTP_200_OK
    assert val_v2_resp.json()["run_number"] == 2

    findings_v2 = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    fire_finding_v2 = next(f for f in findings_v2 if f["rule_code"] == "RULE-EOA-FIRE-003")
    assert fire_finding_v2["outcome"] == "NO_ISSUE_DETECTED"
    assert fire_finding_v2["severity"] == "INFO"
    assert "2027-04-30" in fire_finding_v2["observed_value"]
    assert fire_finding_v2["evidence"]["version_number"] == 2


# -------------------------------------------------------------------------
# Test 4: Land Area & FSI/FAR Applicability Checks (Step 4 Verified Framework)
# -------------------------------------------------------------------------
def test_numeric_land_area_rural_vs_urban_norm(client, db_session):
    """Verifies that land area norms evaluate according to AICTE APH Appendix 4 FSI/FAR
    compliance and lease duration without rigid unverified 4.0/2.5 acre mandatory floors."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027", "total_intake_applied": 720})
    app_id = c_resp.json()["id"]

    # 1. Upload Land Deed with 2.80 Acres and Permissible FAR: 2.0 (FSI/FAR declared)
    pdf_bytes = make_synthetic_digital_pdf([
        "GOVERNMENT OF KARNATAKA REVENUE DEPARTMENT",
        "REGISTERED LAND TITLE DEED",
        "Deed Registration Number: TD-8821-2024",
        "Total Contiguous Land Area: 2.80 Acres",
        "Permissible FAR: 2.0",
        "Survey Numbers: 102/1A, 102/1B",
        "Owner: Apex Educational Trust"
    ])
    files = {"file": ("Land_Title_2.8Acres_FAR.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "LAND_TITLE_DEED"}, files=files)

    # Validate -> FAR is declared and complies -> PASS
    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    land_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-LAND-001")
    assert land_finding["outcome"] == "NO_ISSUE_DETECTED"
    assert "2.80" in land_finding["observed_value"]

    # 2. Upload Land Deed with short lease (< 30 years) -> DEFICIENCY
    short_lease_pdf = make_synthetic_digital_pdf([
        "GOVERNMENT OF KARNATAKA REVENUE DEPARTMENT",
        "REGISTERED LEASE DEED",
        "Deed Registration Number: LD-4412-2024",
        "Total Contiguous Land Area: 3.50 Acres",
        "Lease Duration: 15 Years",
        "Lessee: Apex Educational Trust"
    ])
    files_lease = {"file": ("Land_Lease_Short.pdf", io.BytesIO(short_lease_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "LAND_TITLE_DEED"}, files=files_lease)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    findings_lease = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    lease_finding = next(f for f in findings_lease if f["rule_code"] == "RULE-EOA-LAND-001")
    assert lease_finding["severity"] == "DEFICIENCY"
    assert lease_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert "30" in lease_finding["expected_value"]
    assert "15" in lease_finding["observed_value"]


# -------------------------------------------------------------------------
# Test 5: Faculty-to-Student Ratio (FSR) Calculation (1:20 UG Engineering Norm)
# -------------------------------------------------------------------------
def test_faculty_to_student_ratio_evaluation(client, db_session):
    """Verifies that FSR evaluates the statutory 1:20 ratio for UG Engineering & Technology
    under APH Annexure-5 Section 5.2."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027", "total_intake_applied": 720})
    app_id = c_resp.json()["id"]

    # 1. Deficient Faculty Roster: 20 faculty for 720 students (FSR = 1:36.0 > 1:20.0)
    deficient_roster = make_synthetic_digital_pdf([
        "APEX INSTITUTE OF TECHNOLOGY - FACULTY CADRE ROSTER",
        "ACADEMIC YEAR: 2026-2027",
        "Total Qualified Full-Time Faculty Count: 20",
        "Cadre Breakdown: Professors: 4, Associate Professors: 6, Assistant Professors: 10",
        "Certification Date: 2026-02-15"
    ])
    files = {"file": ("Faculty_Roster_Deficient.pdf", io.BytesIO(deficient_roster), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "FACULTY_ROSTER"}, files=files)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    fsr_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-FSR-005")
    assert fsr_finding["severity"] == "DEFICIENCY"
    assert fsr_finding["outcome"] == "DEFICIENCY_DETECTED"
    assert "1:36.0" in fsr_finding["observed_value"]
    assert "1:20.0" in fsr_finding["expected_value"]

    # 2. Compliant Faculty Roster: 50 faculty for 720 students (FSR = 1:14.4 <= 1:20.0)
    compliant_roster = make_synthetic_digital_pdf([
        "APEX INSTITUTE OF TECHNOLOGY - FACULTY CADRE ROSTER",
        "ACADEMIC YEAR: 2026-2027",
        "Total Qualified Full-Time Faculty Count: 50",
        "Cadre Breakdown: Professors: 10, Associate Professors: 15, Assistant Professors: 25",
        "Certification Date: 2026-03-01"
    ])
    files_v2 = {"file": ("Faculty_Roster_Compliant_v2.pdf", io.BytesIO(compliant_roster), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "FACULTY_ROSTER"}, files=files_v2)

    client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    findings_v2 = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    fsr_finding_v2 = next(f for f in findings_v2 if f["rule_code"] == "RULE-EOA-FSR-005")
    assert fsr_finding_v2["outcome"] == "NO_ISSUE_DETECTED"
    assert "1:14.4" in fsr_finding_v2["observed_value"]

    # 3. Category Guard: Non-technical category emits NOT_APPLICABLE
    inst = db_session.query(Institution).filter(Institution.id == "inst_01").first()
    original_cat = inst.category
    try:
        inst.category = "ARTS_AND_HUMANITIES"
        db_session.commit()
        client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
        findings_cat = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
        fsr_cat = next(f for f in findings_cat if f["rule_code"] == "RULE-EOA-FSR-005")
        assert fsr_cat["outcome"] == "NOT_APPLICABLE"
        assert fsr_cat["severity"] == "INFO"
    finally:
        inst.category = original_cat
        db_session.commit()


# -------------------------------------------------------------------------
# Test 6: Cross-Document Consistency Matching (Survey Numbers)
# -------------------------------------------------------------------------
def test_cross_document_survey_number_consistency(client, db_session):
    """Verifies that cross-document discrepancies between Land Title Deed and Land Use Certificate
    are flagged as WARNING consistency checks without implying legal non-compliance."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    c_resp = client.post("/api/v1/applications", headers=headers, json={"academic_year": "2026-2027", "total_intake_applied": 720})
    app_id = c_resp.json()["id"]

    # Title Deed specifies Survey Numbers: 44/2A and 44/2B
    title_pdf = make_synthetic_digital_pdf([
        "REVENUE DEPARTMENT GOVERNMENT OF KARNATAKA",
        "REGISTERED LAND TITLE DEED",
        "Deed Registration Number: TD-9912-2024",
        "Total Contiguous Land Area: 5.50 Acres",
        "Survey Numbers: 44/2A, 44/2B",
        "Owner: Apex Educational Trust"
    ])
    files1 = {"file": ("Title_Deed_44_2A_2B.pdf", io.BytesIO(title_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "LAND_TITLE_DEED"}, files=files1)

    # Land Use Certificate ONLY covers Survey Number: 44/2A (missing 44/2B)
    land_use_pdf = make_synthetic_digital_pdf([
        "DEPUTY COMMISSIONER OFFICE BENGALURU URBAN",
        "LAND USE CONVERSION ORDER FOR EDUCATIONAL PURPOSE",
        "Conversion Order Number: LUC-BLR-2024-5512",
        "Converted Survey Number: 44/2A",
        "Extent Converted: 2.75 Acres",
        "Date of Order: 2024-08-10"
    ])
    files2 = {"file": ("Land_Use_Cert_44_2A_only.pdf", io.BytesIO(land_use_pdf), "application/pdf")}
    client.post(f"/api/v1/applications/{app_id}/documents", headers=headers, data={"document_type": "LAND_USE_CERTIFICATE"}, files=files2)

    # Run validation
    val_resp = client.post(f"/api/v1/applications/{app_id}/validate", headers=headers)
    assert val_resp.status_code == status.HTTP_200_OK

    findings = client.get(f"/api/v1/applications/{app_id}/findings", headers=headers).json()["findings"]
    survey_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-CROSS-006")
    assert survey_finding["severity"] == "WARNING"
    assert survey_finding["outcome"] == "ADVISORY_WARNING"
    assert "44/2B" in survey_finding["explanation"]
    
    # Verify secondary evidence preserves Document 2 (Land Use Certificate)
    evidence = survey_finding["evidence"]
    assert evidence["document_id"] is not None
    assert evidence["secondary_evidence"] is not None
    assert evidence["secondary_evidence"]["document_type"] == "LAND_USE_CERTIFICATE"
    assert "44/2A" in evidence["secondary_evidence"]["normalized_value"]


# -------------------------------------------------------------------------
# Test 7: Multi-Tenant Isolation & IDOR Protection on Regulatory APIs
# -------------------------------------------------------------------------
def test_cross_institution_regulatory_isolation_denied(client, db_session):
    """Verifies that an institution cannot trigger validation or access findings
    belonging to another institution."""
    # Inst 1 Login
    login1 = client.post("/api/v1/auth/login", json={
        "email": "applicant@institution.test",
        "password": "Password123!"
    })
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Inst 2 Login
    login2 = client.post("/api/v1/auth/login", json={
        "email": "applicant2@institution2.test",
        "password": "Password123!"
    })
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Inst 1 creates application and runs validation
    app1 = client.post("/api/v1/applications", headers=headers1, json={"academic_year": "2026-2027", "total_intake_applied": 720}).json()
    val_run = client.post(f"/api/v1/applications/{app1['id']}/validate", headers=headers1).json()
    findings1 = client.get(f"/api/v1/applications/{app1['id']}/findings", headers=headers1).json()["findings"]
    finding_id = findings1[0]["id"]

    # ATTACK 1: Inst 2 attempts to trigger validation on Inst 1 application -> 404
    atk1 = client.post(f"/api/v1/applications/{app1['id']}/validate", headers=headers2)
    assert atk1.status_code == status.HTTP_404_NOT_FOUND

    # ATTACK 2: Inst 2 attempts to view findings of Inst 1 application -> 404
    atk2 = client.get(f"/api/v1/applications/{app1['id']}/findings", headers=headers2)
    assert atk2.status_code == status.HTTP_404_NOT_FOUND

    # ATTACK 3: Inst 2 attempts to fetch specific finding of Inst 1 by ID -> 404
    atk3 = client.get(f"/api/v1/findings/{finding_id}", headers=headers2)
    assert atk3.status_code == status.HTTP_404_NOT_FOUND

    # SUCCESS: Inst 1 can access their own finding
    legit = client.get(f"/api/v1/findings/{finding_id}", headers=headers1)
    assert legit.status_code == status.HTTP_200_OK
    assert legit.json()["id"] == finding_id
