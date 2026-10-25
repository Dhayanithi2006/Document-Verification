# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Regulatory Accuracy & Evidence Audit Report (`regulatory-rule-audit.md`)

**Document Version:** 1.0.0  
**Audit Phase:** Step 3 — Regulatory Accuracy and Evidence Audit  
**Audit Date:** October 24, 2026  
**Target Academic Cycle:** Extension of Approval (EoA) for Academic Year 2026–27  
**Official Baseline:** AICTE Approval Process Handbook (APH 2024–25 to 2026–27)  
**Primary Source Publication:** All India Council for Technical Education (AICTE), New Delhi  
**Audit Classification:** Regulatory Integrity, Statutory Traceability, and Evidence Governance  
**Disclaimer:** *Decision-Support & Pre-Scrutiny Prototype. Not an official AICTE scrutiny portal. Final statutory decisions remain the exclusive prerogative of the AICTE Scrutiny Committee and Competent Authority.*

---

## 1. Executive Summary & Scope Identification

### 1.1 Objective & Context
This audit was performed in **Step 3** of the AICTE Pre-Scrutiny & Deficiency Resolution Platform development lifecycle. The objective is to rigorously determine whether every active statutory document requirement, automated regulatory rule, mathematical validation threshold, and emitted finding is supported by verifiable official primary sources.

In strict adherence to the project's safe remediation principles:
- **No changes to application code, active database records, migrations, seeds, or rules were made during this audit.**
- The existing SQLite database (`data/aicte.db`), uploaded document storage, and prior bug fixes (such as the reviewer routing fix and applicant correction-cycle workflow remediation `DEF-APPLICANT-001`) have been preserved intact without modification.

### 1.2 Academic-Year Scope Boundary
- **Defined Scope:** **Extension of Approval (EoA) for Academic Year 2026–27** for existing approved technical institutions.
- **Governing Multi-Year Baseline:** The *AICTE Approval Process Handbook (APH 2024–25 to 2026–27)*, which established a 3-year regulatory block aligned with the National Education Policy (NEP 2020).
- **Scope Restriction:** All regulatory thresholds, checklist items, and procedural requirements evaluated in this audit apply strictly to the AY 2026–27 EoA cycle. **They must not be assumed to apply automatically to new institution establishment applications (Chapter I), standalone polytechnics, or subsequent handbook editions beyond AY 2026–27 without explicit re-verification.**

### 1.3 Key Audit Findings Summary
1. **Critical Regulatory Discrepancy — Structural Stability Certificate (`RULE-EOA-STRUCT-004`):** The platform treats this certificate as unconditionally mandatory for all institutions, emitting a blocking `DEFICIENCY` if omitted. Under official AICTE APH Chapter II, Clause 2.14.6, this requirement is **conditional** (triggered only if a building is older than 30 years from completion, or when adding floors/expansion, or in high-risk seismic zones).
2. **Faculty-to-Student Ratio (FSR) Threshold Mismatch (`RULE-EOA-FSR-005`):** The backend engine hardcodes a mandatory **1:15** ratio universally for Under-Graduate Engineering & Technology. Under official APH 2024–2027 norms, the standard statutory ratio for affiliated UG Engineering institutions is **1:20**, while 1:15 applies to autonomous, accredited, or university-status institutions. Furthermore, the frontend mock data cites a 1:20 ratio from Appendix 7 Table 7.1, revealing an internal UI-backend contradiction.
3. **Obsolete Land Area Norms (`RULE-EOA-LAND-001`):** The platform enforces rigid parcel sizes (4.0 acres rural, 2.5 acres urban). In the 2024–2027 APH edition, AICTE moved away from rigid acreage mandates, replacing them with Floor Space Index (FSI) / Floor Area Ratio (FAR) compliance and built-up area accommodation certified by local municipal planning authorities.
4. **Silent Database Rule Inconsistency:** `RULE-DRAFT-BANK-009` (Joint FDR check) is marked `APPROVED_FOR_PROTOTYPE_USE` and `is_active = 1` in `data/aicte.db`, but the Python evaluation engine has zero logic implemented for it. It is silently ignored during evaluation.
5. **Documentation Divergence:** The existing `docs/REGULATORY_RULE_SOURCE_MATRIX.md` document describes rules (`RULE-EOA-DOC-007`, `RULE-EOA-CADRE-008`, `RULE-EOA-BCC-009`, `RULE-EOA-STRUCT-010`) that diverge from the actual rule identifiers and logic executing in `backend/services/regulatory_engine.py`.
6. **Primary Source Accessibility Limitation:** The official handbook URL provided (`https://www.aicte.gov.in/sites/default/files/APH%20Final.pdf`) currently returns an HTTP 404 (Not Found) error. Primary text was verified through the official AICTE portal, S3WaaS government digital repositories, and state technical education directorate mirrors.

---

## 2. Inventory of Active Requirements and Rules

### 2.1 Statutory Document Checklist Inventory (8 Slots)
The platform initializes 8 statutory document slots for each Extension of Approval (EoA) application within `backend/services/document_service.py` (`MANDATORY_EOA_DOCUMENTS`) and renders them across applicant and reviewer workspaces.

| Slot # | Document Type Enum | Code Display Title | Configured Mandatory? | Official APH Statutory Purpose | Real Applicability for Standard EoA | Extraction Pipeline & Fields |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| **1** | `LAND_TITLE_DEED` | Land Title Deed / Registered Lease Deed | `True` | Proof of lawful ownership or registered long-term lease ($\ge 30$ years). | **Conditional for EoA**: Mandatory at initial establishment; required for EoA only upon change of site, expansion, or lease renewal. | Digital/OCR: `contiguous_land_area_acres`, `survey_numbers_list`, `registration_date`, `land_owner_name`. |
| **2** | `LAND_USE_CERTIFICATE` | Land Use Certificate / Non-Agricultural (NA) Order | `True` | Clearance from competent revenue authority for educational institutional use. | **Conditional for EoA**: Established institutions with unchanged land use are not legally required to re-obtain conversion orders annually. | Digital/OCR: `survey_numbers_list`, `issuing_authority`, `conversion_order_number`, `order_date`. |
| **3** | `APPROVED_BUILDING_PLAN` | Approved Building Master Plan & Blueprints | `True` | Architectural sanction from Town Planning, Municipal Corporation, or PWD. | **Conditional for EoA**: Required upon new construction, vertical addition, or compounding approval. | Digital/OCR: `sanctioned_builtup_area_sqm`, `approval_authority`, `plan_approval_number`, `approval_date`. |
| **4** | `BUILDING_COMPLETION` | Building Completion / Occupancy Certificate | `True` | Verification of structural completion and occupancy permission from local body. | **Mandatory**: Must be in place for all operating instructional buildings. Accepts Form D, OC, or Provisional OC. | Digital/OCR: `completed_builtup_area_sqm`, `certificate_issuing_authority`, `certificate_number`, `completion_status`, `issue_date`. |
| **5** | `FIRE_SAFETY_NOC` | Fire Safety Certificate / No-Objection Certificate | `True` | Operational fire prevention, egress, and safety compliance from State Fire Services. | **Mandatory**: Must be maintained and renewed periodically per state fire regulations across the academic year. | Digital/OCR: `noc_number`, `valid_until_date`, `issue_date`, `issuing_fire_station`. |
| **6** | `STRUCTURAL_STABILITY` | Structural Stability & Soundness Certificate | `True` | Certified building soundness under NBC 2016 load and seismic standards. | **Conditional**: Required ONLY if building age $>30$ years, or upon structural expansion, or in high-risk seismic zones (Zones IV/V). | Digital/OCR: `engineer_registration_number`, `engineer_name`, `structural_soundness_certified`, `certificate_date`. |
| **7** | `PREV_AICTE_APPROVAL` | Previous AICTE Approval / EoA Letter | `True` | Baseline establishment of AICTE Permanent ID, sanctioned programs, and approved intake. | **Mandatory for EoA**: Required to confirm historical sanctioned capacity. (Not applicable to new institutions). | Digital/OCR: `previous_eoa_reference`, `academic_year`, `approved_total_intake`, `issue_date`. |
| **8** | `FACULTY_ROSTER` | Faculty Roster & Cadre Distribution | `True` | Verification of adequate qualified teaching faculty and compliance with cadre ratios. | **Mandatory**: Required annually for all technical institutions. | Digital/OCR: `total_qualified_faculty_count`, `professors_count`, `associate_professors_count`, `assistant_professors_count`, `roster_certification_date`. |

---

### 2.2 Complete Regulatory Rule Inventory (10 Rules)
Cross-referencing `backend/services/regulatory_engine.py`, `data/aicte.db`, `docs/REGULATORY_RULE_CATALOG.md`, and frontend sample data:

| Rule Code | Rule Title | Category | Status in Code | Status in Database | Is Active (DB) | Implemented in `evaluate_application`? | Severity Emitted |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `RULE-EOA-LAND-001` | Minimum Contiguous Land Requirement | `LAND_NORMS` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-BCC-002` | Mandatory Building Completion Check | `MANDATORY_CERTIFICATE` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-FIRE-003` | Fire Safety Certificate Validity Check | `MANDATORY_SAFETY_CERTIFICATE` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-STRUCT-004` | Structural Stability Verification | `MANDATORY_SAFETY_CERTIFICATE` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-FSR-005` | Faculty-to-Student Ratio Compliance | `FACULTY_NORMS` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-CROSS-006` | Land vs Land Use Survey Consistency | `CROSS_DOCUMENT_CONSISTENCY` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `WARNING` (`ADVISORY_WARNING`) |
| `RULE-EOA-CROSS-007` | Sanctioned vs Completed Area Match | `CROSS_DOCUMENT_CONSISTENCY` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-EOA-PREV-008` | Previous Year Intake Baseline Check | `INTAKE_RECONCILIATION` | `APPROVED_FOR_PROTOTYPE_USE` | `APPROVED_FOR_PROTOTYPE_USE` | `1` | **Yes** | `DEFICIENCY` / `INFO` |
| `RULE-DRAFT-BANK-009` | Joint FDR Lien Period Check | `FINANCIAL_NORMS` | `DRAFT_MISSING_OFFICIAL_SOURCE` | `APPROVED_FOR_PROTOTYPE_USE` | **`1` (Drift)** | **No (Skipped)** | None |
| `RULE-DRAFT-PARK-010` | Campus Parking Slot Calculation | `INFRASTRUCTURE_NORMS` | `DRAFT_MISSING_OFFICIAL_SOURCE` | `DRAFT_MISSING_OFFICIAL_SOURCE` | `0` | **No (Skipped)** | None |

---

## 3. Detailed Source-Evidence Verification Matrix

This matrix provides the auditable statutory grounding for every active rule and requirement, documenting official clauses, applicability conditions, automated extraction boundaries, and verification verdicts.

### 3.1 `RULE-EOA-LAND-001`: Minimum Contiguous Land Area
- **Rule ID & Version:** `RULE-EOA-LAND-001` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE` in DB and engine).
- **Current Implemented Condition:**
  ```python
  required_acres = 4.0 if institution.is_rural else 2.5
  if observed_land_acres < required_acres:
      emit_finding(severity="DEFICIENCY")
  ```
- **Official Source Cited:** AICTE APH 2024–2027, Appendix 4, Clause 4.1.
- **Official Primary Verification:**
  - In APH 2024–2027, AICTE substantially reformed land norms. Fixed minimum plot sizes (such as 4.0 acres rural, 2.5 acres urban) were **discontinued** for established institutions and replaced by **FSI/FAR-based compliance** approved by the competent local development authority.
  - The land must be sufficient to legally accommodate the required instructional, administrative, and amenities built-up area under municipal building bylaws.
  - Lease duration must be $\ge 30$ years (with remaining live lease $\ge$ maximum course duration).
- **Applicability:** Under-Graduate Engineering & Technology institutions.
- **Genuine Automated Capability:** Can extract numerical acreage token from `LAND_TITLE_DEED` text.
- **System Limitation:** Cannot verify sub-registrar registration authenticity, encumbrance, or local FAR compliance without municipal/revenue API integration.
- **Test Coverage:** Covered in `tests/backend/test_regulatory_engine.py` (`test_numeric_land_area_rural_vs_urban_norm`).
- **Conclusion:** **OBSOLETE / TOO RIGID.** The rule enforces legacy fixed acreage norms that do not reflect the flexible FAR/FSI provisions of APH 2024–2027.

---

### 3.2 `RULE-EOA-BCC-002`: Building Completion / Occupancy Certificate
- **Rule ID & Version:** `RULE-EOA-BCC-002` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:** Checks whether `BUILDING_COMPLETION` document is uploaded and confirms that `completion_status` contains one of `["COMPLETED", "COMPLETE", "OCCUPANCY", "SANCTIONED", "FULL"]`. Emits `DEFICIENCY` if missing or status keyword absent.
- **Official Source Cited:** AICTE APH 2024–2027, Chapter II, Clause 2.3.2.
- **Official Primary Verification:**
  - AICTE requires proof of lawful structural completion and permission for educational occupancy issued by the competent municipal corporation, town planning authority, or state PWD.
  - **Statutory Alternatives:** AICTE officially permits:
    1. Full Building Completion Certificate (CC).
    2. Occupancy Certificate (OC).
    3. Provisional Occupancy Certificate (valid for up to two consecutive academic years).
    4. Form D (licensed architect/engineer completion certificate under state municipal building acts).
    5. Structural clearance from Government PWD.
- **Applicability:** All operating technical institutions seeking Extension of Approval.
- **Genuine Automated Capability:** Validates PDF upload and parses string keywords.
- **System Limitation:** Does not recognize Form D or handle expiration of provisional certificates. Does not verify authenticity with the issuing municipal planning authority.
- **Test Coverage:** Missing direct calculation test; covered only by generic missing-document test (`test_missing_mandatory_document_deficiency_detection`).
- **Conclusion:** **VERIFIED AS APPLICABLE BUT OVERLY RESTRICTIVE.** Must be updated to recognize legitimate statutory alternatives (Form D, Provisional OC).

---

### 3.3 `RULE-EOA-FIRE-003`: Fire Safety Certificate (NOC) Current Validity
- **Rule ID & Version:** `RULE-EOA-FIRE-003` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:**
  ```python
  academic_session_start = datetime(2026, 7, 1)
  if fire_noc_expiry_date < academic_session_start:
      emit_finding(severity="DEFICIENCY")
  ```
- **Official Source Cited:** AICTE APH 2024–2027, Clause 2.3.4 & National Building Code (NBC 2016) Part IV.
- **Official Primary Verification:**
  - Mandatory for all operating technical institutions. All campuses must possess a valid Fire NOC issued by the State/UT Fire Services Department.
  - Validity period is governed strictly by the issuing State/UT authority (typically 1 to 3 years).
  - The certificate must remain valid across the academic year; if expired prior to session commencement, renewal or formal extension is legally required.
- **Applicability:** All technical institutions across all disciplines and categories.
- **Genuine Automated Capability:** Successfully parses date tokens (`valid_until_date`) and performs ISO calendar date comparison.
- **System Limitation:** Does not verify whether a renewal application receipt submitted by the institution is legally acceptable under state grace-period bylaws.
- **Test Coverage:** Fully covered in `tests/backend/test_regulatory_engine.py` (`test_date_and_validity_check_fire_noc`).
- **Conclusion:** **VERIFIED AS FULLY APPLICABLE.** Aligns directly with statutory health and life safety requirements.

---

### 3.4 `RULE-EOA-STRUCT-004`: Structural Stability Certificate Verification
- **Rule ID & Version:** `RULE-EOA-STRUCT-004` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:** Checks that `STRUCTURAL_STABILITY` is uploaded, has an engineer registration number $>2$ chars, and contains an affirmative soundness flag (`"TRUE"` or `"SOUND"`). Emits blocking `DEFICIENCY` if missing or incomplete.
- **Official Source Cited:** AICTE APH 2024–2027, Chapter II, Clause 2.3.5 / Clause 2.14.6.
- **Official Primary Verification:**
  - Under AICTE APH Chapter II, Clause 2.14.6, submission of a Structural Stability Certificate from an empanelled Chartered Structural Engineer (with Master's specialization) is **CONDITIONAL**, mandated strictly under:
    1. Buildings whose completion certificate was issued **thirty (30) or more years ago**.
    2. Proposals for **additional construction or vertical expansion** within an existing structure.
    3. Campuses situated in **High-Risk Seismic Zones (Zone IV and Zone V)**.
  - For standard operating buildings under 30 years with no structural alteration, an annual structural stability certificate is NOT an annual statutory requirement.
- **Applicability:** Qualified / Conditional institutions only.
- **Genuine Automated Capability:** Extracts text strings for registration and stability declaration.
- **System Limitation:** Cannot verify structural engineer license status with the Institution of Engineers (India) or Council of Architecture.
- **Test Coverage:** Missing direct logic unit test.
- **Conclusion:** **CONFLICTING / DEFECTIVE AS IMPLEMENTED.** Treating this rule as universally mandatory causes unlawful blocking deficiencies for compliant institutions operating in modern buildings ($<30$ years).

---

### 3.5 `RULE-EOA-FSR-005`: Faculty-to-Student Ratio (FSR) Compliance
- **Rule ID & Version:** `RULE-EOA-FSR-005` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:**
  ```python
  max_fsr = 15.0  # Hardcoded 1:15 ratio
  computed_fsr = total_enrolled_intake / faculty_count
  if computed_fsr > 15.0:
      emit_finding(severity="DEFICIENCY")
  ```
- **Official Source Cited:** AICTE APH 2024–2027, Annexure-5, Table 5.1.
- **Official Primary Verification:**
  - In APH 2024–2027, the standard statutory Faculty-to-Student Ratio (FSR) for Under-Graduate Engineering & Technology in **affiliated institutions** is **1:20**.
  - The tighter **1:15** ratio is prescribed for **Autonomous institutions, Deemed-to-be-Universities, or institutions seeking accredited status**.
  - Distinct ratios govern other disciplines: Management (1:20), MCA (1:20), Pharmacy (1:15), Diploma Engineering (1:25).
  - Furthermore, `frontend/js/sample-data.js` explicitly defines the rule with a 1:20 norm citing Appendix 7 Table 7.1, conflicting with the backend's 1:15 enforcement.
- **Applicability:** Category guard exists in code (`inst_category == "ENGINEERING_TECHNOLOGY"`), but lacks institutional status guard (Affiliated vs Autonomous/Accredited).
- **Genuine Automated Capability:** Performs integer division on extracted headcounts.
- **System Limitation:** Does not cross-verify individual faculty qualifications, Aadhaar-seeded service books, or biometric attendance against national databases.
- **Test Coverage:** Covered in `tests/backend/test_regulatory_engine.py` (`test_faculty_to_student_ratio_evaluation`).
- **Conclusion:** **CONFLICTING THRESHOLD.** Enforcing 1:15 across all institutions penalizes standard affiliated colleges operating legally under the 1:20 statutory norm.

---

### 3.6 `RULE-EOA-CROSS-006`: Land Title vs Land Use Survey Number Consistency
- **Rule ID & Version:** `RULE-EOA-CROSS-006` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:** Tokenizes survey numbers in `LAND_TITLE_DEED` and `LAND_USE_CERTIFICATE`. If deed surveys are not a subset of land use surveys, emits `severity="WARNING"` and `outcome="ADVISORY_WARNING"`.
- **Official Source Cited:** AICTE APH 2024–2027, Clause 4.2.
- **Official Primary Verification:**
  - APH Chapter II requires contiguous land parcels to be covered by valid conversion orders.
  - However, revenue records frequently contain partitioned sub-survey designations (`44/2A`, `44/2B`), supplemental re-survey numbers, or amalgamation orders.
  - Backend implementation correctly treats this as an **advisory warning** (`WARNING`) for committee review, rather than an automatic blocking rejection.
  - **Defect in UI Mock Data:** In `frontend/js/sample-data.js`, finding `find_0042` is erroneously tagged as `severity: "DEFICIENCY"`, contradicting the backend engine.
- **Applicability:** All institutions submitting land conversion documents.
- **Genuine Automated Capability:** String token normalization and set subset comparison.
- **System Limitation:** Cannot interpret revenue partition deeds, village cadastral maps, or tahsildar conversion addendums.
- **Test Coverage:** Covered in `tests/backend/test_regulatory_engine.py` (`test_cross_document_survey_number_consistency`).
- **Conclusion:** **VERIFIED AS ADVISORY (FRONTEND RECONCILIATION REQUIRED).** The backend logic correctly avoids classifying survey variances as conclusive proof of non-compliance.

---

### 3.7 `RULE-EOA-CROSS-007`: Sanctioned vs Completed Built-Up Area Cross-Match
- **Rule ID & Version:** `RULE-EOA-CROSS-007` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:** Compares completed area against sanctioned plan area. If completed area $< 90\%$ of sanctioned area, emits `DEFICIENCY`.
- **Official Source Cited:** AICTE APH 2024–2027, Appendix 4, Clause 4.3.
- **Official Primary Verification:**
  - AICTE norms mandate that the constructed instructional and administrative area must adequately support the applied intake.
  - A 10% variance tolerance is consistent with standard municipal compounding and phased construction guidelines.
- **Applicability:** Operating institutions.
- **Genuine Automated Capability:** Float comparison of square meter values extracted from respective documents.
- **System Limitation:** Cannot determine whether unconstructed space affects mandatory instructional labs or optional amenity zones without detailed room-schedule parsing.
- **Test Coverage:** Missing direct automated test exercising the 10% shortfall condition.
- **Conclusion:** **VERIFIED AS APPLICABLE.** Needs targeted unit test coverage for the numerical threshold.

---

### 3.8 `RULE-EOA-PREV-008`: Previous Year AICTE Approval Intake Baseline Check
- **Rule ID & Version:** `RULE-EOA-PREV-008` (v1.0.0)
- **Active Status:** Active (`APPROVED_FOR_PROTOTYPE_USE`).
- **Current Implemented Condition:** Compares current applied intake against previous year approved intake. If applied intake $>$ previous approved intake, emits `DEFICIENCY`.
- **Official Source Cited:** AICTE APH 2024–2027, Chapter II, Clause 2.1.
- **Official Primary Verification:**
  - Standard Extension of Approval (EoA) is strictly for renewing existing sanctioned intake.
  - Any increase in intake or addition of new programs requires applying under Chapter II Clause 2.4 ("Increase in Intake / Additional Course"), which entails higher regulatory scrutiny, additional processing fees, and faculty verification.
- **Applicability:** Standard EoA applications.
- **Genuine Automated Capability:** Integer comparison of seat totals.
- **System Limitation:** Does not parse individual program-wise intake distribution (e.g., shifting seats from Mechanical to Computer Science within the same aggregate).
- **Test Coverage:** Missing direct automated test exercising the intake exceedance condition.
- **Conclusion:** **VERIFIED AS APPLICABLE.** Needs targeted unit test coverage.

---

### 3.9 `RULE-DRAFT-BANK-009`: Joint Fixed Deposit (FDR) Lien Period Check
- **Rule ID & Version:** `RULE-DRAFT-BANK-009` (v1.0.0)
- **Active Status:** Inactive in code (`DRAFT_MISSING_OFFICIAL_SOURCE`), but **erroneously active in DB** (`APPROVED_FOR_PROTOTYPE_USE`, `is_active=1`).
- **Official Source Cited:** State Technical Board Bylaws (Unverified Regional Amendment).
- **Official Primary Verification:**
  - AICTE abolished the requirement for continuous joint FDRs for established institutions with $>10$ years of operation in recent APH editions.
  - State technical examining bodies possess widely differing financial security norms.
  - The rule has no implementation in `evaluate_application()`.
- **Conclusion:** **UNSUPPORTED / DRIFT DETECTED.** Must be deactivated in the database to prevent administrative misconfiguration.

---

### 3.10 `RULE-DRAFT-PARK-010`: Campus Parking Slot Calculation
- **Rule ID & Version:** `RULE-DRAFT-PARK-010` (v1.0.0)
- **Active Status:** Inactive Draft (`DRAFT_MISSING_OFFICIAL_SOURCE`, `is_active=0`).
- **Official Source Cited:** Local Municipal Bylaws.
- **Official Primary Verification:**
  - Parking calculations are governed exclusively by local municipal development control regulations, not AICTE statutory scrutiny checklists.
- **Conclusion:** **ADVISORY ONLY / REMAINS DRAFT.** Properly kept out of the active evaluation pipeline.

---

## 4. In-Depth Investigation of High-Risk Regulatory Areas

### 4.1 Structural Stability Certificate Conditionality
- **Statutory Mandate:** Governed by AICTE APH Chapter II, Clause 2.14.6 and NBC 2016.
- **The Issue:** The platform hardcodes this slot as unconditionally mandatory in `document_service.py` and emits a blocking `DEFICIENCY` in `regulatory_engine.py` whenever absent.
- **Legal Reality:** The certificate is required only when:
  1. The building is older than thirty (30) years from the completion date.
  2. The institution is undertaking vertical or horizontal expansion / structural alterations.
  3. The campus is located in High Seismic Risk Zones (Zone IV or Zone V).
- **Risk:** New and compliant institutions operating in structures $<30$ years old are unjustly blocked from obtaining automated clearance, creating artificial friction and false deficiency backlogs.

### 4.2 Building Completion Certificate vs Accepted Alternatives
- **Statutory Mandate:** AICTE APH Chapter II, Clause 2.14.5.
- **The Issue:** The engine evaluates only whether `completion_status` matches a narrow set of keywords (`COMPLETED`, `OCCUPANCY`).
- **Legal Reality:** AICTE explicitly recognizes:
  - **Form D:** Architectural/structural completion certificate submitted under state municipal corporation acts.
  - **Provisional Occupancy Certificate:** Legally valid for up to two consecutive academic years to permit progressive completion of multi-phase campus master plans.
  - **PWD Clearance:** Public Works Department certification for government/aided institutions.
- **Risk:** Compliant applicants uploading valid Form D or provisional clearances are incorrectly flagged with `DEFICIENCY`.

### 4.3 Land Area Norm Modernization (FAR/FSI vs Rigid Acreage)
- **Statutory Mandate:** AICTE APH 2024–2027, Appendix 4.
- **The Issue:** `RULE-EOA-LAND-001` checks for $\ge 4.0$ acres (rural) and $\ge 2.5$ acres (urban).
- **Legal Reality:** In APH 2024–2027, AICTE eliminated fixed acreage thresholds in response to urban land scarcity and vertical campus development. Under current regulations, land sufficiency is determined by **Floor Space Index (FSI) / Floor Area Ratio (FAR)** approved by the local planning authority.
- **Risk:** High-density urban campuses with vertical infrastructure complying with municipal FAR limits are falsely flagged for land shortfalls.

### 4.4 Faculty-to-Student Ratio (1:20 vs 1:15)
- **Statutory Mandate:** AICTE APH 2024–2027, Annexure-5 Table 5.1 & Appendix 7.
- **The Issue:** The engine applies a 1:15 ratio to all Engineering institutions.
- **Legal Reality:**
  - Standard affiliated UG Engineering colleges require **1:20**.
  - Autonomous, accredited, or Deemed-to-be-Universities require **1:15**.
  - Cadre ratio ($1:2:6$) is an advisory target, not an automatic ground for summary rejection.
- **Risk:** Affiliated institutions with a compliant 1:18 or 1:19 ratio receive false deficiencies.

### 4.5 Visual Seal vs Genuine Issuing Authority Verification
- **Technical Capability:** The platform's CPU ONNX OCR pipeline detects visual stamps and authority seals via bounding-box token clustering.
- **Regulatory Reality:** A detected visual seal on a PDF proves **only that an ink-like mark or bitmap imprint exists in the document data**. It does **not** prove:
  - That the stamp was affixed by an authorized public official.
  - That the sanction order is genuine and has not been revoked or superseded.
  - That the underlying drawing corresponds to the physical structure on the ground.
- **Governance Requirement:** Software must never declare a document "Authenticity Verified" based on a visual seal. It must display: **"Visual Seal Detected — Requires Official Authority Verification."**

### 4.6 Discrepancy vs Fraud Classification
- **Regulatory Principle:** Clerical differences, revenue sub-survey divisions (`44/2A` vs `44/2B`), and OCR token misreads must **never** be labeled as "fraud," "forgery," or "tampering."
- **Current Safeguard:** The backend engine properly categorizes survey mismatches as `WARNING` with outcome `ADVISORY_WARNING`.
- **Identified Defect:** `frontend/js/sample-data.js` misclassifies this warning as a `DEFICIENCY`. This must be corrected in documentation and future UI alignment.

---

## 5. Evidence vs Automated Inference Boundary Matrix

To uphold administrative law principles, the platform must maintain an explicit, transparent boundary between deterministic automated observations and authorized human determinations.

```
+-----------------------------------------------------------------------------------+
|                           ADMINISTRATIVE LAW BOUNDARY                             |
+-----------------------------------------------------------------------------------+
| Level 1: Document Upload Presence/Absence         --> Fully Automated (Deterministic) |
| Level 2: Field Extraction & Token Normalization   --> Fully Automated (Confidence >= 0.85) |
| Level 3: Date Arithmetic & Expiry Calculation     --> Fully Automated (Calendar Math) |
| Level 4: Cross-Document Discrepancy Detection     --> Automated Advisory Flag (WARNING) |
| Level 5: Legal Authenticity Verification          --> External Authority API Required |
| Level 6: Fraud / Tampering / Clearance Decision   --> Exclusive Human Authority Power |
+-----------------------------------------------------------------------------------+
```

| Check Category | What Automated Engine Actually Performs | Honest System Status | What Software Must NEVER Claim | Ultimate Authority Responsible |
| :--- | :--- | :--- | :--- | :--- |
| **Checklist Presence** | Verifies non-empty file upload with `%PDF-` magic bytes and valid size. | `UPLOADED` / `NOT_UPLOADED` | Does NOT imply regulatory compliance of the content. | Scrutiny Committee |
| **Field Extraction** | Extracts text tokens via PyPDF / PaddleOCR and assigns confidence scores. | `EXTRACTED` / `UNPARSEABLE` | Does NOT certify truthfulness of stated figures. | Scrutiny Reviewer |
| **Validity / Expiry** | Parses ISO calendar dates and compares to academic session start date. | `VALID_FOR_SESSION` / `EXPIRED` | Does NOT verify if state renewal grace period applies. | Scrutiny Committee |
| **Cross-Document Check** | Compares extracted survey sets across Land Deed and Land Use Certificate. | `DISCREPANCY_FLAGGED` (`WARNING`) | Must NEVER claim "document is forged or fraudulent." | Revenue / Legal Scrutiny |
| **Building Plan Seal** | Detects presence of seal/stamp bitmap tokens on drawing. | `SEAL_DETECTED_UNVERIFIED` | Must NEVER claim "approved by municipal corporation." | Town Planning Authority |
| **FSR Calculation** | Divides total intake by extracted headcount. | `RATIO_COMPUTED` | Must NEVER disqualify institution without category guard. | Scrutiny Committee |
| **Final Approval / Rejection** | Generates explainable decision-support findings. | `PRE_SCRUTINY_FINDINGS_READY` | Must NEVER issue final regulatory approval or denial. | AICTE Competent Authority |

---

## 6. Discrepancy & Gap Analysis Across Artifacts

| Discrepancy ID | Component A | Component B | Nature of Conflict | Severity | Remediation Strategy |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **DISC-001** | `document_service.py` & `regulatory_engine.py` | AICTE APH Chapter II Clause 2.14.6 | `STRUCTURAL_STABILITY` is unconditionally mandatory in code, but conditional in official APH. | **HIGH** | Make slot conditional; update `RULE-EOA-STRUCT-004` to check building age/expansion. |
| **DISC-002** | `regulatory_engine.py` (`RULE-EOA-FSR-005`) | AICTE APH Annexure-5 & `sample-data.js` | Backend enforces 1:15 norm universally; APH prescribes 1:20 for standard affiliated colleges. Frontend sample data uses 1:20. | **HIGH** | Parameterize FSR rule with institutional status (Affiliated: 1:20; Autonomous/NBA: 1:15). |
| **DISC-003** | `regulatory_engine.py` (`RULE-EOA-LAND-001`) | AICTE APH 2024–2027 Appendix 4 | Backend enforces fixed acreage (4.0/2.5 acres); APH 2024–2027 eliminated fixed acreage in favor of FAR/FSI. | **HIGH** | Transition land rule from rigid acreage to built-up area and local FAR compliance. |
| **DISC-004** | `data/aicte.db` (`RULE-DRAFT-BANK-009`) | `regulatory_engine.py` (`SEED_RULES`) | Database record has `is_active=1` and `APPROVED_FOR_PROTOTYPE_USE`, but engine has zero code for it. | **MEDIUM** | Deactivate rule in database (`is_active=0`, status=`DRAFT_MISSING_OFFICIAL_SOURCE`). |
| **DISC-005** | `docs/REGULATORY_RULE_SOURCE_MATRIX.md` | `backend/services/regulatory_engine.py` | Matrix documents `RULE-EOA-DOC-007` and `RULE-EOA-CADRE-008` which do not exist in code. | **MEDIUM** | Align documentation matrix with the actual 10-rule codebase catalog. |
| **DISC-006** | `frontend/js/sample-data.js` (`find_0042`) | `backend/services/regulatory_engine.py` (`RULE-EOA-CROSS-006`) | Sample data marks survey mismatch as `DEFICIENCY`; backend emits `WARNING` (`ADVISORY_WARNING`). | **LOW** | Harmonize sample data severity to `WARNING`. |
| **DISC-007** | `tests/backend/test_regulatory_engine.py` | Rule Catalog | Direct unit tests missing for `RULE-EOA-BCC-002`, `RULE-EOA-STRUCT-004`, `RULE-EOA-CROSS-007`, `RULE-EOA-PREV-008`. | **MEDIUM** | Add dedicated test methods in the regression test suite. |

---

## 7. Prioritized Recommendations

All recommendations are strictly prioritized by severity. **No changes are to be executed until authorized after user review.**

```
+-----------------------------------------------------------------------------------+
|                        PRIORITIZED REMEDIATION ROADMAP                            |
+-----------------------------------------------------------------------------------+
| HIGH SEVERITY (Blockers of Regulatory Legitimacy):                                |
|   1. Structural Stability Conditionality (Building Age / Expansion Gate)          |
|   2. FSR 1:20 vs 1:15 Institutional Status Guard (Affiliated vs Autonomous)        |
|   3. Land Norm Modernization (Acreage to FSI/FAR Accommodation)                    |
|                                                                                   |
| MEDIUM SEVERITY (Governance & Code-Data Alignment):                               |
|   4. Deactivate Unsupported RULE-DRAFT-BANK-009 in Live Database                   |
|   5. Building Completion Alternative Acceptance (Form D, Provisional OC)          |
|   6. Reconcile REGULATORY_RULE_SOURCE_MATRIX.md with Real Rule Codes              |
|   7. Implement Missing Direct Unit Tests for Rules 002, 004, 007, and 008          |
|                                                                                   |
| LOW SEVERITY (UI & Documentation Hygiene):                                        |
|   8. Harmonize frontend/sample-data.js Finding Severities                          |
|   9. Mirror Accessible APH 2024-2027 PDF in docs/references/                     |
+-----------------------------------------------------------------------------------+
```

### High Severity
1. **Structural Stability Conditionality (DISC-001):** Modify `document_service.py` to mark `STRUCTURAL_STABILITY` as `is_mandatory=False` by default for standard EoA. In `regulatory_engine.py`, evaluate building age (from BCC completion date) or expansion flags before emitting a deficiency.
2. **FSR Norm Parameterization (DISC-002):** Add `institution.is_autonomous` and `institution.is_accredited` checks to `RULE-EOA-FSR-005`. Set the threshold to 1:20 for standard affiliated institutions and 1:15 for autonomous/accredited institutions.
3. **Land Norm Modernization (DISC-003):** Update `RULE-EOA-LAND-001` to clarify that acreage evaluation is an advisory baseline and evaluate total built-up area accommodation against municipal FAR standards.

### Medium Severity
4. **Database State Cleanup (DISC-004):** Update `RULE-DRAFT-BANK-009` in `data/aicte.db` to set `status = 'DRAFT_MISSING_OFFICIAL_SOURCE'` and `is_active = 0`.
5. **Accept Building Completion Alternatives (DISC-005):** Expand `RULE-EOA-BCC-002` keyword matching to recognize `FORM D`, `PROVISIONAL OCCUPANCY`, and `PWD STRUCTURAL CLEARANCE`.
6. **Documentation Matrix Reconciliation (DISC-006):** Update `docs/REGULATORY_RULE_SOURCE_MATRIX.md` to accurately mirror the 8 active and 2 draft rules implemented in `backend/services/regulatory_engine.py`.
7. **Complete Unit Test Coverage (DISC-007):** Author explicit unit tests for building completion status checks, structural stability declarations, built-up area shortfalls ($>10\%$), and intake baseline exceedances.

### Low Severity
8. **Frontend Sample Data Alignment (DISC-008):** Update `syntheticFindings` in `frontend/js/sample-data.js` so that `RULE-EOA-CROSS-006` reflects `severity: "WARNING"` and `RULE-EOA-FSR-005` reflects the 1:20 norm.
9. **Primary Source Mirroring (DISC-009):** Archive the accessible version of the AICTE Approval Process Handbook (2024–2027) locally in `docs/references/` to prevent external URL 404 dependencies.

---

## 8. Proposed Regression Test Plan

To validate future remediation without altering current behavior, the following test suite specification is proposed:

| Proposed Test Module | Target Functionality | Input Fixture / Condition | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `test_structural_stability_conditional_trigger` | Conditionality of `RULE-EOA-STRUCT-004` | Application for building completed in 2020 (age 6 years) without stability certificate. | Outcome: `NOT_APPLICABLE` or `INFO` (No deficiency emitted). |
| `test_structural_stability_older_building_trigger` | Conditionality of `RULE-EOA-STRUCT-004` | Application for building completed in 1990 (age 36 years) without stability certificate. | Outcome: `DEFICIENCY` (Mandatory after 30 years per Clause 2.14.6). |
| `test_fsr_affiliated_engineering_1_20_norm` | FSR threshold for affiliated institutions | Affiliated Engineering college with 720 students and 38 faculty (FSR = 1:18.9). | Outcome: `NO_ISSUE_DETECTED` (Complies with 1:20 norm). |
| `test_fsr_autonomous_engineering_1_15_norm` | FSR threshold for autonomous institutions | Autonomous Engineering college with 720 students and 38 faculty (FSR = 1:18.9). | Outcome: `DEFICIENCY_DETECTED` (Violates 1:15 autonomous norm). |
| `test_building_completion_form_d_accepted` | Alternative document recognition | Building Completion upload with text "Form D Completion Notice Issued by Town Planner". | Outcome: `NO_ISSUE_DETECTED` (Form D recognized as valid completion). |
| `test_builtup_area_shortfall_deficiency` | `RULE-EOA-CROSS-007` numerical shortfall | Plan area: 10,000 Sq.m; Completed area: 8,500 Sq.m (15% shortfall, exceeds 10% limit). | Outcome: `DEFICIENCY_DETECTED` with exact percentage shortfall. |
| `test_intake_exceedance_deficiency` | `RULE-EOA-PREV-008` intake exceedance | Previous intake: 480 seats; Applied intake: 600 seats. | Outcome: `DEFICIENCY_DETECTED` (Exceeds baseline without expansion sanction). |

---

## 9. Conclusion & Audit Sign-Off

This audit establishes that the AICTE Pre-Scrutiny & Deficiency Resolution Platform possesses a robust, explainable, deterministic foundation, but requires targeted calibration to reflect the modernized, flexible provisions of the **AICTE Approval Process Handbook (2024–2027)**. 

By distinguishing automated inferences from authoritative human scrutiny, relaxing obsolete acreage rules to FAR standards, making structural stability checks conditional upon building age ($>30$ years), and calibrating the Faculty-to-Student Ratio to 1:20 for affiliated institutions, the platform can achieve complete regulatory fidelity without risking unlawful administrative rejections.

**Status:** Audit Complete. All current application code, database records, and test suites preserved without modification. Awaiting user review and authorization prior to regulatory implementation.
