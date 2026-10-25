# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Statutory Document Requirements Matrix (`REGULATORY_DOCUMENT_REQUIREMENTS.md`)

**Document Version:** 1.0.0  
**Phase:** P10 — Final Stabilization, Verification, and Remediation  
**Regulatory Baseline:** AICTE Approval Process Handbook (APH 2024–2027)  
**Classification:** Technical & Regulatory Specification  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal. For decision-support demonstration purposes only.*

---

## 1. Statutory Checklist Overview

Under Chapter II of the AICTE Approval Process Handbook (APH 2024–2027), institutions seeking Extension of Approval (EoA) or approval for new programmes/institutions are mandated to maintain and upload statutory compliance documentation.

The platform implements an automated 8-document checklist slot architecture within `backend/models/application.py` and `backend/models/document.py`, surfaced through the Institutional Application Workspace (`frontend/js/views/application-detail.js`).

---

## 2. Comprehensive 8-Document Statutory Requirements Matrix

| # | Document Type Enum | Document Title | AICTE APH Reference | Statutory Purpose & Scope | Applicability | Key Extracted Fields | Extraction Method | Associated Regulatory Rules | Test Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `LAND_TITLE_DEED` | Registered Land Title Deed / Lease Deed | Chapter II, Clause 2.14.1 & Appendix 4 | Establishes lawful ownership or registered long-term lease ($\ge 30$ years) of institution land. | **Mandatory** for all technical institutions. | `land_area_acres`, `survey_numbers`, `registration_date`, `document_number`, `lessor_name`, `lessee_name` | Digital Text / CPU ONNX OCR | `RULE-EOA-LAND-001`, `RULE-EOA-LAND-002`, `RULE-EOA-CROSS-006` | `test_applications_workflow.py`, `test_extraction_pipeline.py`, `test_regulatory_engine.py` |
| **2** | `LAND_USE_CERTIFICATE` | Land Use Certificate / Conversion Order | Chapter II, Clause 2.14.2 & Appendix 4 | Verifies competent revenue/planning authority has cleared land for Educational Institutional use. | **Mandatory** for all technical institutions. | `land_use_category`, `survey_numbers`, `issuing_authority`, `order_number`, `order_date` | Digital Text / CPU ONNX OCR | `RULE-EOA-CROSS-006`, `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_regulatory_engine.py`, `applications_frontend.test.js` |
| **3** | `APPROVED_BUILDING_PLAN` | Sanctioned / Approved Building Plan | Chapter II, Clause 2.14.4 & Appendix 4 | Verifies architectural drawings sanctioned by Town Planning/Municipal Corporation with authority seal. | **Mandatory** for all technical institutions. | `approval_authority`, `approval_order_number`, `approval_date`, `total_builtup_area`, `authority_seal_detected` | Digital Text / CPU ONNX OCR | `RULE-EOA-BLD-004`, `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_regulatory_engine.py`, `extraction_frontend.test.js` |
| **4** | `BUILDING_COMPLETION_CERT` | Building Completion Certificate (BCC) / Occupancy Certificate | Chapter II, Clause 2.14.5 & Appendix 4 | Confirms structural completion and lawful occupancy clearance by local authority/PWD. | **Mandatory** for all operating institutions. | `completion_certificate_number`, `issuing_authority`, `completion_date`, `plinth_area_sqm`, `occupancy_status` | Digital Text / CPU ONNX OCR | `RULE-EOA-BCC-009` (Draft), `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_regulatory_engine.py`, `regulatory_frontend.test.js` |
| **5** | `FIRE_SAFETY_NOC` | Fire Safety Certificate (Fire NOC) | Chapter II, Clause 2.14.3 & Appendix 4 | Establishes operational fire safety systems, egress compliance, and valid NOC from State Fire Services. | **Mandatory** for all operating technical institutions. Must be valid across the academic year. | `noc_number`, `issuing_fire_officer`, `issue_date`, `valid_until_date`, `safety_measures_status` | Digital Text / CPU ONNX OCR | `RULE-EOA-FIRE-003`, `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_extraction_pipeline.py`, `test_regulatory_engine.py`, `test_deficiency_workflow.py` |
| **6** | `STRUCTURAL_STABILITY_CERT` | Structural Stability Certificate | Chapter II, Clause 2.14.6 & Appendix 4 | Attests that all institutional civil structures conform to National Building Code (NBC 2016) seismic/load standards. | **Conditional / Qualified**: Mandatory for existing buildings, buildings older than 30 years, or multi-storey structures ($\ge G+2$ floors). | `structural_engineer_registration`, `inspection_date`, `validity_period_years`, `building_safety_status` | Digital Text / CPU ONNX OCR | `RULE-EOA-STRUCT-010` (Draft), `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_regulatory_engine.py`, `deficiency_frontend.test.js` |
| **7** | `PREVIOUS_AICTE_APPROVAL` | Previous Academic Year AICTE EoA Approval Letter | Chapter II, Clause 2.14.7 | Validates existing AICTE Permanent Institute ID, approved intake capacity, and existing course roster. | **Mandatory** for Extension of Approval (EoA) applications. (New Institution applications provide LOI/LOA). | `aicte_permanent_id`, `previous_eoa_number`, `approved_academic_year`, `approved_intake` | Digital Text / CPU ONNX OCR | `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_regulatory_engine.py`, `reviewer_admin_frontend.test.js` |
| **8** | `FACULTY_CADRE_ROSTER` | Faculty Cadre & Student Enrollment Roster | Chapter II, Clause 2.16 & Annexure-5 Table 5.1 | Certified roster of full-time teaching faculty and enrolled students to verify Faculty-to-Student Ratio (FSR) and cadre norms. | **Mandatory** for all technical institutions. | `total_enrolled_students`, `total_fulltime_faculty`, `professors_count`, `associate_professors_count`, `assistant_professors_count`, `computed_fsr` | Digital Text / CPU ONNX OCR | `RULE-EOA-FSR-005`, `RULE-EOA-CADRE-008`, `RULE-EOA-DOC-007` | `test_applications_workflow.py`, `test_extraction_pipeline.py`, `test_regulatory_engine.py` |

---

## 3. Applicability Rules & Conditional Logic

### 3.1 Unconditional Mandatory Documents
For all standard Extension of Approval (EoA) applications in Technical programmes (Engineering & Technology, Management, Pharmacy, MCA, Architecture), 7 of the 8 statutory documents are unconditionally mandatory:
1. Land Title Deed
2. Land Use Certificate
3. Approved Building Plan
4. Building Completion Certificate
5. Fire Safety Certificate (Fire NOC)
6. Previous AICTE Approval Letter
7. Faculty Cadre & Student Enrollment Roster

Failure to upload any of these mandatory slots triggers `RULE-EOA-DOC-007` resulting in a blocking `DEFICIENCY` finding that prevents the application from advancing to reviewer clearance.

### 3.2 Conditional Statutory Requirement: Structural Stability Certificate
The Structural Stability Certificate (`STRUCTURAL_STABILITY_CERT`) is governed under AICTE APH Chapter II, Clause 2.14.6:
- **Mandatory Trigger Conditions:**
  - Buildings older than thirty (30) years from the date of completion.
  - Multi-storey academic or administrative blocks exceeding $G+2$ floors.
  - Locations in High-Risk Seismic Zones (Zone IV and Zone V per IS 1893).
  - Renovation, extension, or vertical expansion of existing institutional structures.
- **Prototype Baseline:**
  - In the current prototype seed dataset, the Structural Stability Certificate slot is configured as an active checklist item for complete compliance demonstration.
  - The governing rule `RULE-EOA-STRUCT-010` is currently cataloged in `DRAFT` status pending dynamic building-age conditional triggers in subsequent phase releases.

---

## 4. Technical Extraction Capabilities & Operational Limitations

### 4.1 Digital PDF vs. Scanned Raster PDF Extraction
- **Digital PDFs:** Processed via `pdfplumber` and `pypdf`. Extracts complete text streams, word coordinates, font metadata, and table structures in $<150$ms per page with 1.0 confidence.
- **Scanned / Raster PDFs:** Routed to the local CPU ONNX pipeline (PaddleOCR v6). Renders pages to 200 DPI bitmap buffers, performs text detection and recognition, and computes token bounding boxes `[ymin, xmin, ymax, xmax]`. Execution time averages $1.5$–$3.5$ seconds per page on modern multicore CPUs.

### 4.2 Document-Specific Extraction Nuances & Boundaries
1. **Fire Safety NOC:**
   - Detects issuing authority, NOC reference numbers, and validity/expiry dates.
   - Evaluated against academic session start date (`2026-06-30` for session 2026–27).
   - If expiry occurs prior to session start, triggers `RULE-EOA-FIRE-003` (`DEFICIENCY`).
2. **Faculty Cadre Roster:**
   - Extracts student enrollment and faculty headcounts by designation.
   - Computes empirical Faculty-to-Student Ratio (FSR) $= \frac{\text{Students}}{\text{Faculty}}$.
   - Enforces AICTE APH 2024–2027 Annexure-5 Table 5.1 threshold: Maximum allowed FSR ratio is **1:15** for Engineering & Technology programmes.
   - Non-engineering programmes receive outcome `NOT_APPLICABLE`.
3. **Survey Number Consistency:**
   - Cross-references survey numbers extracted across Land Title Deed, Land Use Certificate, and Building Plan.
   - Discrepancies are flagged as **`WARNING` / `ADVISORY_WARNING`** (`RULE-EOA-CROSS-006`) to accommodate legitimate partitioned sub-surveys (`44/2A` vs `44/2B`), leaving final determination to the Scrutiny Committee.

---

## 5. Automated Test Coverage Traceability

| Statutory Checklist Slot | Backend Test Module | Test Method Name | Verification Check |
| :--- | :--- | :--- | :--- |
| All 8 Slots Initialization | `test_applications_workflow.py` | `test_create_application_with_statutory_checklist` | Asserts application creation populates exactly 8 slots in `NOT_UPLOADED` state. |
| Secure PDF Upload & Magic-Byte Check | `test_applications_workflow.py` | `test_secure_pdf_upload_success_and_metadata` | Asserts PDF upload persists SHA-256 hash, storage path, and updates status to `UPLOADED`. |
| Non-PDF Rejection | `test_applications_workflow.py` | `test_upload_rejected_for_non_pdf_magic_bytes` | Verifies rejection of spoofed `.exe`/`.txt` files with HTTP 422. |
| Slot Removal & Reset | `test_applications_workflow.py` | `test_document_removal_and_slot_reset` | Asserts document deletion cleans storage and resets slot to `NOT_UPLOADED`. |
| Digital PDF Extraction | `test_extraction_pipeline.py` | `test_digital_pdf_extraction_and_field_grounding` | Validates digital text extraction, field mapping, and coordinate persistence. |
| Scanned PDF OCR | `test_extraction_pipeline.py` | `test_real_scanned_pdf_ocr_execution` | Validates genuine PaddleOCR execution on raster scan without mocks. |
| Fire NOC Validity Rule | `test_regulatory_engine.py` | `test_date_and_validity_check_fire_noc` | Validates `RULE-EOA-FIRE-003` evaluates date against session start. |
| FSR Ratio Rule (1:15) | `test_regulatory_engine.py` | `test_faculty_to_student_ratio_evaluation` | Validates 1:15 norm compliance and Engineering & Technology category guard. |
| Survey Number Warning | `test_regulatory_engine.py` | `test_cross_document_survey_number_consistency` | Validates `RULE-EOA-CROSS-006` emits `WARNING` on sub-survey difference. |
| Tenant Isolation on Documents | `test_isolation.py` | `test_tenant_isolation_on_application_detail` | Validates cross-institution document download attempts return HTTP 404. |
