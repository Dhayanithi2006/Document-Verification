# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Role-Workflow Acceptance Test Suite (`ROLE_WORKFLOW_ACCEPTANCE_TESTS.md`)
**Smart India Hackathon (SIH) Multi-Role Functional Verification**

**Execution Date:** October 25, 2026
**Status:** All Acceptance Scenarios Verified (0 Failures, 0 Regressions)
**Governing Standard:** SIH Prototype Multi-Role Verification & Human Authority Safeguards

---

## 1. Executive Summary & Verification Methodology

This document details the complete functional acceptance test suite for the three core roles of the AICTE Pre-Scrutiny & Deficiency Resolution Platform:
1. **`INSTITUTION` (Institution Applicant)**
2. **`REVIEWER` (Authorised Scrutiny Reviewer)**
3. **`ADMIN` (Platform System Administrator)**
4. **Connected End-to-End Workflows (Workflows A, B, and C)**

All test scenarios were executed against isolated test databases (`data/test_frontend.db` and memory test databases) using synthetic RFC 2606 / RFC 6761 `.test` credentials and temporary document storage. The baseline demonstration database (`data/aicte.db`) remained completely pristine and untouched.

---

## 2. Institution Applicant Acceptance Scenarios (`INSTITUTION`)

| Test ID | Role | Preconditions | Action Performed | Expected Result | Actual Result | Persistence & API Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-INST-01** | `INSTITUTION` | Test server online; synthetic user provisioned | Issue `POST /api/v1/auth/login` with `applicant@institution.test` credentials | HTTP 200 OK; access token returned; `user.role == 'INSTITUTION'`; `institution_id == 'inst_01'` | HTTP 200 OK; JWT token generated; profile mapped to Apex Institute | `backend/api/v1/auth.py` line 26; Bearer token received | **PASS** |
| **TC-INST-02** | `INSTITUTION` | Authenticated as `inst_01` applicant | Issue `GET /api/v1/applications` | HTTP 200 OK; returns only applications belonging to `inst_01`; zero leakage of `inst_02` data | HTTP 200 OK; 1 application returned (`app_9812`), all matching `inst_01` | `tests/backend/test_isolation.py` line 43; tenant isolated | **PASS** |
| **TC-INST-03** | `INSTITUTION` | Application `app_9812` in `DRAFT` status | Issue `PUT /api/v1/applications/app_9812` updating `declared_faculty_count` to 42 | HTTP 200 OK; application record updated; audit event `APPLICATION_UPDATED` created | HTTP 200 OK; faculty count updated to 42; persisted in DB | `tests/backend/test_applications_workflow.py` line 125 | **PASS** |
| **TC-INST-04** | `INSTITUTION` | Application `app_9812` created | Issue `GET /api/v1/applications/app_9812/checklist` | HTTP 200 OK; returns 8 statutory checklist slots (Land, Building, Fire, Faculty, etc.) | HTTP 200 OK; 8 statutory slots returned with required metadata | `tests/applications_frontend.test.js` Subtest 1 | **PASS** |
| **TC-INST-05** | `INSTITUTION` | Checklist slot `LAND_TITLE_DEED` is `PENDING` | Issue `POST /api/v1/applications/app_9812/documents` uploading valid PDF `test_upload.pdf` | HTTP 201 Created; status `UPLOADED`; `version_number == 1`; 64-char SHA-256 hash generated | HTTP 201 Created; document record created; file stored in tenant folder | `tests/backend/test_applications_workflow.py` line 158 | **PASS** |
| **TC-INST-06** | `INSTITUTION` | Document uploaded in live browser (`#/applications/app_9812`) | Trigger in-place workspace refresh after upload | UI updates in-place showing `v1 UPLOADED`; zero JavaScript console exceptions | Workspace refreshed cleanly; card rendered status; no `state.getCurrentUser` error | `frontend/js/views/application-detail.js` lines 26–32 | **PASS** |
| **TC-INST-07** | `INSTITUTION` | Document version `v1` exists for slot | Issue `POST /api/v1/applications/app_9812/documents` uploading replacement PDF | HTTP 201 Created; new version created (`version_number == 2`); `v1` preserved | HTTP 201 Created; `v2` active; `v1` retained in historical versions | `tests/backend/test_deficiency_workflow.py` line 219 | **PASS** |
| **TC-INST-08** | `INSTITUTION` | Valid authentication headers | Upload file with `.pdf` extension containing non-PDF bytes (`This is not a PDF`) | HTTP 400 Bad Request; rejected due to invalid magic bytes; no DB record created | HTTP 400 Bad Request (`detail: Invalid file format. Must be a valid PDF.`); rejected | `tests/backend/test_applications_workflow.py` line 195 | **PASS** |
| **TC-INST-09** | `INSTITUTION` | Valid authentication headers | Upload empty 0-byte file | HTTP 400 Bad Request; rejected due to empty payload | HTTP 400 Bad Request (`detail: Uploaded file is empty.`); rejected | `tests/backend/test_applications_workflow.py` line 224 | **PASS** |
| **TC-INST-10** | `INSTITUTION` | Application with ingested documents | Issue `POST /api/v1/regulatory/applications/app_9812/validate` | HTTP 200 OK; APH rules evaluated; findings generated and categorized | HTTP 200 OK; findings returned with rule citations and severity levels | `tests/backend/test_regulatory_engine.py` line 344 | **PASS** |
| **TC-INST-11** | `INSTITUTION` | Open finding on application | Navigate to `#/applications/app_9812/evidence/:finding_id` | Split-screen evidence inspector loads; highlights text region and OCR confidence | Split-screen layout rendered with document viewer and spatial coordinates | `tests/frontend.test.js` Subtest 4 | **PASS** |
| **TC-INST-12** | `INSTITUTION` | Actionable finding in `OPEN` status | Issue `POST /api/v1/deficiencies/findings/:id/acknowledge` | HTTP 200 OK; finding status transitioned to `ACKNOWLEDGED` | HTTP 200 OK; status updated to `ACKNOWLEDGED` in database | `tests/deficiency_frontend.test.js` Subtest 4 | **PASS** |
| **TC-INST-13** | `INSTITUTION` | Finding in `ACKNOWLEDGED` status | Issue `POST /api/v1/deficiencies/findings/:id/draft` with justification text | HTTP 200 OK; draft response saved; retrievable on page refresh | HTTP 200 OK; draft stored in `DeficiencyCorrectionDraft`; persisted | `tests/deficiency_frontend.test.js` Subtest 5 | **PASS** |
| **TC-INST-14** | `INSTITUTION` | Draft response saved | Issue `POST /api/v1/deficiencies/findings/:id/submit` with formal response | HTTP 200 OK; correction submitted; draft locked; cycle 1 recorded | HTTP 200 OK; correction submission created; finding status updated | `tests/deficiency_frontend.test.js` Subtest 6 | **PASS** |
| **TC-INST-15** | `INSTITUTION` | Correction submitted with replacement document | Issue `POST /api/v1/deficiencies/applications/app_9812/revalidate` | HTTP 200 OK; controlled revalidation computes before/after delta | HTTP 200 OK; delta findings computed and returned to applicant | `tests/deficiency_frontend.test.js` Subtest 7 | **PASS** |
| **TC-INST-16** | `INSTITUTION` | Application detail view | Open Pre-Scrutiny Assessment Dossier modal; resize viewport to 600px width | Prototype disclaimer visible; tables scroll horizontally inside `.table-responsive` without overflow | Modal opened with disclaimer; table responsive scrolling confirmed; print reset verified | `frontend/css/components.css` line 628; Defect 4 verification | **PASS** |
| **TC-INST-17** | `INSTITUTION` | Authenticated as `inst_01` applicant | Issue `GET /api/v1/applications/app_9813` (`inst_02` application) | HTTP 404 Not Found (existence masked to defeat IDOR enumeration) | HTTP 404 (`detail: Application not found or access denied.`) | `tests/backend/test_isolation.py` line 32 | **PASS** |

---

## 3. Scrutiny Reviewer Acceptance Scenarios (`REVIEWER`)

| Test ID | Role | Preconditions | Action Performed | Expected Result | Actual Result | Persistence & API Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-REV-01** | `REVIEWER` | Reviewer credentials active | Issue `POST /api/v1/auth/login` with `reviewer@reviewer.test` | HTTP 200 OK; token generated; header displays `Role: Authorised Reviewer` | HTTP 200 OK; reviewer session initialized; role verified | `tests/reviewer_admin_frontend.test.js` Subtest 1 | **PASS** |
| **TC-REV-02** | `REVIEWER` | Authenticated as Reviewer | Issue `GET /api/v1/reviewer/queue` with status and search filters | HTTP 200 OK; returns case queue with institution names, application IDs, and statuses | HTTP 200 OK; queue array returned with review statuses and counts | `tests/reviewer_admin_frontend.test.js` Subtest 2 | **PASS** |
| **TC-REV-03** | `REVIEWER` | Case in `SUBMITTED` status | Issue `POST /api/v1/reviewer/applications/app_9812/assign` to claim case | HTTP 200 OK; case assigned to reviewer; review status updated to `ASSIGNED` | HTTP 200 OK; assigned reviewer ID recorded in database | `tests/reviewer_admin_frontend.test.js` Subtest 4 | **PASS** |
| **TC-REV-04** | `REVIEWER` | Case assigned | Navigate directly to `#/reviewer/scrutiny/app_9812` in browser | View controller resolves `app_9812` parameter; Scrutiny Console renders | Scrutiny Console loaded cleanly; case dossier and documents visible | `tests/reviewer_admin_frontend.test.js` Subtest 13 (`DEF-REV-001`) | **PASS** |
| **TC-REV-05** | `REVIEWER` | Scrutiny console active | Issue `GET /api/v1/documents/:id/stream` for document version | HTTP 200 OK; binary PDF stream delivered with correct MIME type | HTTP 200 OK; binary PDF stream delivered | `tests/reviewer_admin_frontend.test.js` Subtest 3 | **PASS** |
| **TC-REV-06** | `REVIEWER` | Multiple versions exist for document | Query historical versions and inspect replacement diffs | Both `v1` and `v2` accessible; replacement reason and timestamps viewable | Document version timeline displays all iterations cleanly | `tests/backend/test_reviewer_workflow.py` line 115 | **PASS** |
| **TC-REV-07** | `REVIEWER` | Active scrutiny case | Issue `POST /api/v1/reviewer/applications/app_9812/observations` with remarks | HTTP 201 Created; observation persisted in database; visible on timeline | HTTP 201 Created; observation record stored with reviewer identity | `tests/reviewer_admin_frontend.test.js` Subtest 5 | **PASS** |
| **TC-REV-08** | `REVIEWER` | Case has unresolved blocking deficiencies | Issue `POST /api/v1/reviewer/applications/app_9812/signoff` with `RECOMMEND_CLEAR` | HTTP 400 Bad Request; invalid clearance blocked by backend guard | HTTP 400 Bad Request (`detail: Cannot recommend clearance with open blocking deficiencies.`); blocked | `tests/reviewer_admin_frontend.test.js` Subtest 6 | **PASS** |
| **TC-REV-09** | `REVIEWER` | Deficiency noted by reviewer | Issue `POST /api/v1/reviewer/applications/app_9812/signoff` with `DEFICIENCY_NOTED` | HTTP 200 OK; disposition recorded; application status updated to `DEFICIENCY_PENDING` | HTTP 200 OK; case status updated; audit record logged | `tests/backend/test_reviewer_workflow.py` line 185 | **PASS** |
| **TC-REV-10** | `REVIEWER` | Authenticated as Reviewer | Attempt `POST /api/v1/applications` to create new application | HTTP 403 Forbidden; Reviewers denied applicant-only creation endpoints | HTTP 403 Forbidden (`detail: Insufficient permissions for role 'REVIEWER'`); denied | `tests/backend/test_applications_workflow.py` line 85 | **PASS** |

---

## 4. Platform Administrator Acceptance Scenarios (`ADMIN`)

| Test ID | Role | Preconditions | Action Performed | Expected Result | Actual Result | Persistence & API Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-ADM-01** | `ADMIN` | Admin credentials active | Issue `POST /api/v1/auth/login` with `admin@platform.test`; issue `GET /api/v1/admin/overview` | HTTP 200 OK; system overview metrics returned (total users, apps, active rules) | HTTP 200 OK; live counts returned; header renders `Role: System Administrator` | `tests/reviewer_admin_frontend.test.js` Subtest 7 | **PASS** |
| **TC-ADM-02** | `ADMIN` | Authenticated as Admin | Issue `GET /api/v1/admin/users` | HTTP 200 OK; returns complete user directory with role badges and account statuses | HTTP 200 OK; user accounts list returned | `tests/reviewer_admin_frontend.test.js` Subtest 8 | **PASS** |
| **TC-ADM-03** | `ADMIN` | Authenticated as Admin | Issue `POST /api/v1/admin/users` provisioning new reviewer `test_rev@reviewer.test` | HTTP 201 Created; user created; password hashed with bcrypt; role assigned | HTTP 201 Created; provisioned user profile returned; stored in DB | `tests/reviewer_admin_frontend.test.js` Subtest 8 | **PASS** |
| **TC-ADM-04** | `ADMIN` | User account active | Issue `PATCH /api/v1/admin/users/:id/status` setting `is_active = False` | HTTP 200 OK; user deactivated; subsequent login attempts return HTTP 403 Forbidden | HTTP 200 OK; account status updated; login blocked with HTTP 403 | `tests/backend/test_admin_workflow.py` line 112 | **PASS** |
| **TC-ADM-05** | `ADMIN` | User account deactivated | Issue `PATCH /api/v1/admin/users/:id/status` setting `is_active = True` | HTTP 200 OK; user reactivated; login restored | HTTP 200 OK; account restored; login successful | `tests/backend/test_admin_workflow.py` line 130 | **PASS** |
| **TC-ADM-06** | `ADMIN` | Authenticated as Admin | Issue `GET /api/v1/rules` | HTTP 200 OK; complete regulatory rule catalog returned with APH citations | HTTP 200 OK; catalog returned with rule codes and verification metadata | `tests/regulatory_frontend.test.js` Subtest 2 | **PASS** |
| **TC-ADM-07** | `ADMIN` | Active regulatory rule | Issue `POST /api/v1/regulatory/rules/:code/deactivate` with reason string | HTTP 200 OK; rule deactivated (`is_active == False`); audit event logged | HTTP 200 OK; rule deactivated; audit trail records administrative rationale | `tests/backend/test_regulatory_corrections.py` line 48 | **PASS** |
| **TC-ADM-08** | `ADMIN` | Inactive regulatory rule | Issue `POST /api/v1/regulatory/rules/:code/activate` | HTTP 200 OK; rule activated (`is_active == True`); active in pre-scrutiny evaluator | HTTP 200 OK; rule marked active; audit record logged | `tests/regulatory_frontend.test.js` Subtest 10 | **PASS** |
| **TC-ADM-09** | `ADMIN` | Authenticated as Admin | Issue `GET /api/v1/admin/audit-events` | HTTP 200 OK; returns append-only forensic audit trail with actors, actions, timestamps | HTTP 200 OK; audit log returned with complete operational events | `tests/reviewer_admin_frontend.test.js` Subtest 9 | **PASS** |
| **TC-ADM-10** | `INSTITUTION` / `REVIEWER` | Non-admin session active | Issue `GET /api/v1/admin/audit-events` or `POST /api/v1/admin/users` | HTTP 403 Forbidden; non-admin callers strictly blocked | HTTP 403 Forbidden (`detail: Insufficient permissions for role '...'`); blocked | `tests/reviewer_admin_frontend.test.js` Subtest 10 | **PASS** |

---

## 5. Connected End-to-End Workflow Acceptance Scenarios

### 5.1 Workflow A: Application Preparation & Algorithmic Pre-Scrutiny (`TC-E2E-01`)
* **Acting Role:** `INSTITUTION` (`applicant@institution.test`)
* **Execution Flow:**
  1. Signed in as institutional representative. Header rendered `Role: Institution Applicant`.
  2. Created application `app_9812` for Academic Year 2026–2027.
  3. Ingested statutory PDF documents across checklist slots.
  4. Cryptographic SHA-256 hashes generated (`81014138e6...`).
  5. Triggered Algorithmic Pre-Scrutiny check (`POST /api/v1/regulatory/applications/app_9812/validate`).
  6. Evaluator produced evidence-linked findings with APH citations.
* **Outcome:** **PASS** (Application drafted, documents ingested, findings categorized with zero cross-tenant leakage).

### 5.2 Workflow B: Deficiency Correction & Human Reviewer Scrutiny (`TC-E2E-02`)
* **Acting Roles:** `INSTITUTION` & `REVIEWER`
* **Execution Flow:**
  1. Applicant acknowledged deficiency and saved corrective draft response.
  2. Applicant uploaded replacement Fire Safety NOC (`v2`) and submitted formal correction package.
  3. Controlled revalidation executed, generating delta comparison findings.
  4. Reviewer signed in (`reviewer@reviewer.test`).
  5. Reviewer claimed case from Scrutiny Queue and accessed Scrutiny Console via direct URL.
  6. Reviewer examined split-screen evidence, comparing `v1` vs. `v2` PDF documents.
  7. Reviewer recorded formal committee observation with justification.
  8. Reviewer attempted `RECOMMEND_CLEAR` while blocking deficiencies remained; system rejected with HTTP 400.
  9. Reviewer recorded permitted `DEFICIENCY_NOTED` disposition.
* **Outcome:** **PASS** (Correction cycle preserved, human scrutiny recorded, blocking deficiency guard enforced).

### 5.3 Workflow C: Administrative Governance & Audit Trail Verification (`TC-E2E-03`)
* **Acting Role:** `ADMIN` (`admin@platform.test`)
* **Execution Flow:**
  1. Administrator signed in. Header rendered `Role: System Administrator`.
  2. Inspected User Management: verified applicant and reviewer accounts.
  3. Inspected Regulatory Rule Catalog: verified active APH 2024–27 rules.
  4. Inspected Forensic Audit Log: verified complete audit events corresponding to Workflows A and B (`DOCUMENT_UPLOADED`, `PRE_SCRUTINY_VALIDATION_EXECUTED`, `OBSERVATION_RECORDED`, `DISPOSITION_SUBMITTED`).
* **Outcome:** **PASS** (Audit trail accurately reflects multi-role actions with full traceability).

### 5.4 Multi-Role Session Switching & Token Revocation (`TC-E2E-04`)
* **Acting Roles:** `INSTITUTION` -> `REVIEWER` -> `ADMIN`
* **Execution Flow:**
  1. Signed in as Applicant. Verified Applicant role badge and permissions.
  2. Clicked "Switch" in the header: session token cleared from `localStorage`, backend revoked JWT token, redirected to `#/login`.
  3. Attempted using revoked token via direct API call: rejected with `HTTP 401 Unauthorized` (`Token has been revoked upon logout`).
  4. Authenticated as Reviewer: verified Scrutiny Queue loaded; client and backend privileges aligned.
  5. Clicked "Switch" again and authenticated as Admin: verified Admin views accessible.
* **Outcome:** **PASS** (Zero client-side role spoofing; token revocation enforced; seamless role transitions).

---

## 6. Acceptance Summary

| Scenario Category | Total Tests | Passed | Failed | Skipped | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Institution Applicant Scenarios** | 17 | 17 | 0 | 0 | **100% PASS** |
| **Scrutiny Reviewer Scenarios** | 10 | 10 | 0 | 0 | **100% PASS** |
| **Platform Administrator Scenarios** | 10 | 10 | 0 | 0 | **100% PASS** |
| **Connected End-to-End Scenarios** | 4 | 4 | 0 | 0 | **100% PASS** |
| **Total Acceptance Suite** | **41** | **41** | **0** | **0** | **READY FOR DEMO** |
