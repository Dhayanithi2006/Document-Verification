# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Step 4 Remediation Report: Verified Regulatory Corrections
**Academic Year:** Extension of Approval (EoA) 2026–27  
**Official Reference:** AICTE Approval Process Handbook (APH) 2024–25 to 2026–27  
**Platform Notice:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Overview & Baseline Preservation

Step 4 of the AICTE Pre-Scrutiny & Deficiency Resolution Platform implements verified regulatory corrections derived from the Step 3 audit report ([docs/regulatory-rule-audit.md](file:///d:/Desktop/Hackathon/Document%20Verification/docs/regulatory-rule-audit.md)).

### Preserved Prior Remediations
1. **Reviewer Scrutiny Routing Remediation (`DEF-REV-001`)**:
   - Location: `frontend/js/views/reviewer-scrutiny.js`, `frontend/js/router.js`
   - Preserved: Route dispatch correctly passes the application ID (`appId`) into `initReviewerScrutinyView(appId)` without missing parameter errors.
   - Verified: `tests/reviewer_admin_frontend.test.js` Subtests 12 and 13 passed cleanly.
2. **Applicant Correction Workflow Remediation (`DEF-APPLICANT-001`)**:
   - Location: `backend/api/v1/applications.py`, `backend/models/deficiency.py`
   - Preserved: `PUT /api/v1/findings/{id}/response` rejects any attempt to overwrite or create a draft while a formally submitted response is awaiting revalidation, returning `409 Conflict`.
   - Verified: All 10 scenarios in `tests/backend/test_applicant_workflow_remediation.py` passed cleanly.

---

## 2. Confirmed Regulatory Corrections

### 1. Structural Stability (`RULE-EOA-STRUCT-004`)
- **Statutory Source:** AICTE APH 2024–27 Chapter II, Clause 2.14.6; National Building Code of India (NBC) 2016 Part 6.
- **Problem Fixed:** The prototype previously enforced a blanket upload requirement for all institutions regardless of campus building age, creating false deficiencies for recently constructed campuses.
- **Corrected Behavior:**
  - **30-Year Condition:** The building age is measured from the issue date of the Building Completion / Occupancy Certificate. Structural stability certification is conditional: it is **only mandatory** if the structure is $\ge 30$ years old, or if major structural modifications have occurred.
  - **Five-Year Certificate Validity:** When a stability certificate is required, its issue date is verified against the academic session start date (July 1, 2026). If older than 5 years, a `DEFICIENCY` is emitted for certificate expiry under NBC 2016.
  - **Safe Handling of Unparseable Dates:** If the building completion date is missing or unparseable, the engine returns an honest non-blocking `UNABLE_TO_EVALUATE` (WARNING) requiring manual reviewer verification, avoiding silent assumptions.
  - **Major Structural Modifications:** Detected as a distinct trigger that mandates structural stability assessment and building-plan revalidation.

### 2. Faculty-to-Student Ratio (`RULE-EOA-FSR-005`)
- **Statutory Source:** AICTE APH 2024–27 Annexure-5 Section 5.2.
- **Problem Fixed:** The prototype previously enforced a rigid 1:15 ratio universally and failed to handle non-engineering programmes.
- **Corrected Behavior:**
  - Standard Undergraduate Engineering & Technology is evaluated against the statutory **1:20** norm.
  - Polytechnic Diploma is evaluated against **1:25**.
  - Management (MBA/PGDM) and Computer Applications (MCA) are evaluated against **1:20**.
  - Pharmacy is evaluated against **1:15**.
  - Architecture & Planning is evaluated against **1:10**.
  - Non-technical categories emit `NOT_APPLICABLE` (INFO).
  - Unverified 1:15 overrides for autonomous institutions were **not introduced** without official statutory gazette notification.

### 3. Land & Built-up Area (`RULE-EOA-LAND-001`)
- **Statutory Source:** AICTE APH 2024–27 Appendix 4; Clause 2.3.1.
- **Problem Fixed:** The prototype previously enforced hardcoded 4.0-acre (rural) and 2.5-acre (urban) mandatory minimum land thresholds.
- **Corrected Behavior:**
  - Removed arbitrary 4.0/2.5 acre universal floors.
  - Enforced registered lease duration $\ge 30$ years (`DEFICIENCY` if $< 30$ years).
  - Implemented FSI/FAR compliance check: Permissible Built-Up Area $= \text{Land Area (sq.m)} \times \text{FAR}$. If sanctioned built-up area exceeds permissible FAR capacity, `DEFICIENCY` is emitted.
  - When local authority FSI/FAR is undeclared or evidence is pending, engine emits an honest non-blocking `UNABLE_TO_EVALUATE` (INFO) for human scrutiny confirmation instead of guessing.

### 4. Building Completion Evidence (`RULE-EOA-BCC-002`)
- **Statutory Source:** AICTE APH 2024–27 Chapter II, Clause 2.3.2; Appendix 4.
- **Problem Fixed:** The prototype only recognized keyword "Occupancy Certificate" and incorrectly accepted PWD clearance as a substitute.
- **Corrected Behavior:**
  - Recognizes valid statutory alternatives:
    1. Occupancy Certificate (OC)
    2. Completion Certificate (CC)
    3. Building License / Building Permit
    4. Form D Completion
  - Requires issuance by a competent local municipal or town planning authority (BBMP, Municipal Corp, Town Planning, Gram Panchayat).
  - Explicitly rejects standalone PWD Structural Clearance as building completion evidence (`DEFICIENCY`).
  - Enforces the statutory 2-consecutive-academic-year limit on Provisional Occupancy Certificates (`DEFICIENCY` if duration exceeds 2 years).

### 5. Unsupported Database Rule Deactivation (`RULE-DRAFT-BANK-009`)
- **Problem Fixed:** The prototype had `RULE-DRAFT-BANK-009` marked active in the database despite having no evaluation logic in code and relying on unverified regional state board bylaws.
- **Corrected Behavior:**
  - Deactivated via Alembic migration `5a7c92b84102_deactivate_unsupported_draft_bank_rule.py` (`is_active = 0`, `status = 'DRAFT_MISSING_OFFICIAL_SOURCE'`).
  - Logged immutable forensic audit event (`REGULATORY_RULE_DEACTIVATED`).
  - Added administrative deactivation endpoint `POST /api/v1/rules/{rule_code}/deactivate`.
  - Added seed synchronization guard preventing inactive draft rules from activating automatically on startup.

### 6. Documentation & Sample Data Alignment
- Replaced mismatched table in [docs/REGULATORY_RULE_SOURCE_MATRIX.md](file:///d:/Desktop/Hackathon/Document%20Verification/docs/REGULATORY_RULE_SOURCE_MATRIX.md) with the active 10 rules, their evaluators, and Step 4 status.
- Reconciled `find_0042` severity from `DEFICIENCY` to `WARNING` in [frontend/js/sample-data.js](file:///d:/Desktop/Hackathon/Document%20Verification/frontend/js/sample-data.js).

---

## 3. Unresolved Recommendations Left Non-Blocking

| Item | Context | Reason Left Non-Blocking | Status in System |
| :--- | :--- | :--- | :--- |
| **Autonomous 1:15 Override** | Suggested 1:15 ratio for autonomous / NBA accredited colleges | APH 2024–27 Annexure-5 prescribes 1:20 for UG Engineering without an explicit statutory requirement forcing 1:15 as a universal EoA condition. | **Unimplemented / Non-blocking** |
| **Municipal Zonal FSI/FAR Caps** | Specific FAR values (e.g., 1.5 in Tier-2 vs 2.5 in Metro) | Local municipal building bylaws vary widely across Indian states and municipalities. Hardcoding municipal constants would create false deficiencies. | **`UNABLE_TO_EVALUATE` (INFO)** advisory for human reviewer |
| **State FDR Lien Period** | `RULE-DRAFT-BANK-009` joint FDR lien duration | Central AICTE handbook does not prescribe regional state technical board lien rules for EoA. | **Deactivated & Inactive** |

---

## 4. Test Execution Summary

| Test Suite | Scope | Executed Command | Results |
| :--- | :--- | :--- | :--- |
| **Targeted Regulatory Corrections** | Step 4 verified rules (age, validity, FSR, FSI/FAR, BCC alternatives, deactivation) | `pytest tests/backend/test_regulatory_corrections.py -v` | **22 / 22 PASSED** (100%) |
| **Regulatory Engine Suite** | Engine lifecycle, missing docs, fire NOC, land, FSR, cross-matching | `pytest tests/backend/test_regulatory_engine.py -v` | **7 / 7 PASSED** (100%) |
| **Applicant Workflow Suite** | DEF-APPLICANT-001 preservation, state immutability, draft rejection | `pytest tests/backend/test_applicant_workflow_remediation.py -v` | **10 / 10 PASSED** (100%) |
| **Full Backend Suite** | Auth, RBAC, tenant isolation, IDP pipeline, revalidation, reviewer | `pytest tests/backend/ -v` | **94 / 94 PASSED** (100%) |
| **Frontend Integration Suite** | Routes, views, checklist, reviewer queue, deficiency workspace | `npm test` | **82 / 82 PASSED** (100%) |
| **Code Linting** | Frontend JavaScript & CSS syntax linting | `node scripts/lint.js` | **PASSED** |
| **Build Readiness Check** | Asset existence, template linking | `node scripts/build-check.js` | **PASSED** |
| **Git Diff Cleanliness** | Whitespace and merge markers | `git diff --check` | **PASSED (Clean)** |

---

## 5. Scope & Safety Adherence Check

- [x] **No Application Redesign:** Preserved existing single-page architecture, split-screen Evidence Inspector, and human-in-the-loop reviewer signoff workflow.
- [x] **Demo Database Protected:** Zero direct SQL modifications performed against live demo database `data/aicte.db`. All tests executed on isolated in-memory/test database `data/test_isolated.db`.
- [x] **Auditability Preserved:** Deactivations recorded in `audit_events`.
- [x] **Prior Fixes Intact:** DEF-REV-001 and DEF-APPLICANT-001 regression tests verified.
- [x] **No Unsupported Blocking Rules:** Unsubstantiated rules kept inactive or advisory.
- [x] **Prototype Notice Displayed:** *"SIH Prototype — Not an official AICTE portal"* maintained on all views.
- [x] **No Git Commit or Push:** Working tree preserved without commit or push.
