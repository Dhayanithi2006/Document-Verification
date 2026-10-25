# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Role-Wise Test Execution & Verification Evidence (`ROLE_WISE_TEST_RESULTS.md`)
**Smart India Hackathon (SIH) Prototype Audit Test Results & Defect Log**

---

### 1. Executive Test Summary

| Test Suite / Category | Command Executed | Total Tests | Passed | Failed / Blocked | Pass Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Pytest Regression** | `python -m pytest tests/backend/ -v` | 101 | 101 | 0 | **100%** |
| **Frontend Node Integration** | `npm test` | 82 | 82 | 0 | **100%** |
| **Role-Wise Functional Harness**| `python scripts/audit_role_wise_functionality.py`| 44 | 44 | 0 | **100%** |
| **Syntax & Module Linting** | `npm run lint` | Full codebase | All Passed | 0 | **100%** |
| **Production Build Assets** | `npm run build` | 26 critical assets | 26 Verified | 0 | **100%** |
| **Multi-Role Browser Journey** | Browser Subagent (`role_wise_audit_e2e`) | 3 Roles / 17 Steps | 17 Verified | 0 | **100%** |

---

### 2. Dedicated Role-Wise Functional Harness Results (44 / 44 Scenarios)

The role-wise test harness was executed against an isolated test environment (`DATABASE_URL=sqlite:///./data/test_frontend.db`). All test inputs, actual HTTP status codes, response payloads, database states, and verdicts were recorded in [scratch/role_wise_audit_results.json](file:///d:/Desktop/Hackathon/Document%20Verification/scratch/role_wise_audit_results.json).

| Test ID | Role | Feature Area | Action / Test Input | Expected Result | Actual HTTP Status | Resulting DB / State | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **INST-AUTH-01** | `INSTITUTION` | Authentication | Login as `applicant@institution.test` / `Password123!` | HTTP 200, JWT token, role=INSTITUTION, institution_id=inst_01 | **200 OK** | User role verified | **PASS** |
| **INST-AUTH-02** | `INSTITUTION` | Authentication | Retrieve identity via `GET /api/v1/auth/me` | HTTP 200, user profile with institution context | **200 OK** | Institution metadata matched | **PASS** |
| **INST-AUTH-03** | `INSTITUTION` | Access Control | List applications (`GET /api/v1/applications`) | HTTP 200, only inst_01 applications returned | **200 OK** | 100% tenant isolation | **PASS** |
| **INST-AUTH-04** | `INSTITUTION` | RBAC Boundary | Direct call to `GET /api/v1/reviewer/queue` | HTTP 403 Forbidden | **403 Forbidden** | RBAC enforced server-side | **PASS** |
| **INST-AUTH-05** | `INSTITUTION` | RBAC Boundary | Direct call to `GET /api/v1/admin/overview` | HTTP 403 Forbidden | **403 Forbidden** | RBAC enforced server-side | **PASS** |
| **INST-APP-01** | `INSTITUTION` | Application Mgmt | Query `GET /api/v1/applications/app_9812` | HTTP 200, returns details for `AICTE-EOA-2026-9812` | **200 OK** | Application details loaded | **PASS** |
| **INST-APP-02** | `INSTITUTION` | Application Mgmt | Create new application (`POST /api/v1/applications`) | HTTP 201 Created, status=DRAFT, bound to inst_01 | **201 Created** | Unique application created | **PASS** |
| **INST-APP-03** | `INSTITUTION` | Application Mgmt | Update intake in draft state (`PUT /api/v1/applications/{id}`) | HTTP 200, updated intake=660 | **200 OK** | Metadata updated in SQLite | **PASS** |
| **INST-DOC-01** | `INSTITUTION` | Document Mgmt | Retrieve checklist (`GET /api/v1/applications/{id}/checklist`)| HTTP 200, 8 mandatory statutory slots seeded | **200 OK** | 8 slots verified | **PASS** |
| **INST-DOC-02** | `INSTITUTION` | Document Mgmt | Upload valid digital PDF (FIRE_SAFETY_NOC) | HTTP 201 Created, version=1, IDP extraction initiated | **201 Created** | File stored; SHA-256 computed | **PASS** |
| **INST-DOC-03** | `INSTITUTION` | IDP & OCR | Query extracted fields (`GET /{doc_id}/extracted-fields`)| HTTP 200, structured fields returned with coordinates | **200 OK** | Extracted fields schema verified | **PASS** |
| **INST-DOC-04** | `INSTITUTION` | Security Check | Upload disallowed file format (`.docx`) | HTTP 422 Unprocessable Content | **422 Unprocessable** | Format rejected | **PASS** |
| **INST-DOC-05** | `INSTITUTION` | Security Check | Upload file with spoofed PDF magic bytes | HTTP 422 Unprocessable Content | **422 Unprocessable** | Spoofed bytes rejected | **PASS** |
| **INST-DOC-06** | `INSTITUTION` | Tenant Isolation | Cross-tenant upload attempt to Inst 2 app (`app_9813`) | HTTP 404 Not Found (tenant isolation guard) | **404 Not Found** | Existence masked | **PASS** |
| **INST-DOC-07** | `INSTITUTION` | Versioning | Upload replacement document (v2) | HTTP 201 Created, version=2, v1 preserved | **201 Created** | Version incremented | **PASS** |
| **INST-REG-01** | `INSTITUTION` | Pre-Scrutiny | Trigger evaluation (`POST /applications/{id}/validate`) | HTTP 200 OK, validation run summary returned | **200 OK** | 8 checks completed | **PASS** |
| **INST-REG-02** | `INSTITUTION` | Pre-Scrutiny | Query findings (`GET /applications/{id}/findings`) | HTTP 200 OK, findings list with rule citations | **200 OK** | Findings persisted in DB | **PASS** |
| **INST-DEF-01** | `INSTITUTION` | Deficiency Mgmt | Acknowledge finding (`POST /findings/{id}/acknowledge`)| HTTP 200 OK, resolution_status=ACKNOWLEDGED | **200 OK** | Timestamp recorded | **PASS** |
| **INST-DEF-02** | `INSTITUTION` | Deficiency Mgmt | Save correction draft (`PUT /findings/{id}/response`) | HTTP 200 OK, status=DRAFT | **200 OK** | Draft persisted | **PASS** |
| **INST-DEF-03** | `INSTITUTION` | Deficiency Mgmt | Submit formal response (`POST /findings/{id}/submit`) | HTTP 200 OK, status=SUBMITTED, cycle_number=1 | **200 OK** | Cycle 1 recorded | **PASS** |
| **INST-DEF-04** | `INSTITUTION` | Workflow Guard | Attempt draft edit while submission active (DEF-APPLICANT-001)| HTTP 409 Conflict | **409 Conflict** | Guard blocks second draft | **PASS** |
| **INST-DEF-05** | `INSTITUTION` | Revalidation | Run revalidation (`POST /applications/{id}/revalidate`)| HTTP 200 OK, comparison results returned | **200 OK** | Delta comparison computed | **PASS** |
| **INST-DEF-06** | `INSTITUTION` | Audit Trail | Query finding history (`GET /findings/{id}/history`) | HTTP 200 OK, chronological timeline returned | **200 OK** | Complete history verified | **PASS** |
| **REV-AUTH-01** | `REVIEWER` | Authentication | Login as `reviewer@reviewer.test` / `ReviewerPass123!` | HTTP 200, JWT token returned, role=REVIEWER | **200 OK** | Reviewer authenticated | **PASS** |
| **REV-AUTH-02** | `REVIEWER` | RBAC Boundary | Reviewer attempts to create application | HTTP 403 Forbidden | **403 Forbidden** | RBAC enforced | **PASS** |
| **REV-AUTH-03** | `REVIEWER` | RBAC Boundary | Reviewer attempts to access `/admin/users` | HTTP 403 Forbidden | **403 Forbidden** | RBAC enforced | **PASS** |
| **REV-QUEUE-01** | `REVIEWER` | Case Mgmt | Query reviewer queue (`GET /api/v1/reviewer/queue`) | HTTP 200 OK, returns queue items and metrics | **200 OK** | Queue metrics returned | **PASS** |
| **REV-QUEUE-02** | `REVIEWER` | Case Mgmt | Assign application (`POST /reviewer/applications/{id}/assign`)| HTTP 200 OK, review_status=ASSIGNED | **200 OK** | Assigned reviewer stored | **PASS** |
| **REV-SCRUT-01** | `REVIEWER` | Scrutiny Console| Retrieve scrutiny details (`GET /scrutiny`) (DEF-REV-001)| HTTP 200 OK, full dossier with checklist & findings | **200 OK** | Full case dossier loaded | **PASS** |
| **REV-SCRUT-02** | `REVIEWER` | Evidence Check | Stream document binary stream (`GET /versions/{v}/file`)| HTTP 200 OK, application/pdf bytes | **200 OK** | Streamed directly from disk | **PASS** |
| **REV-OBS-01** | `REVIEWER` | Scrutiny Action | Record observation (`POST /observations`) | HTTP 201 Created, observation logged | **201 Created** | Observation persisted | **PASS** |
| **REV-DEC-01** | `REVIEWER` | Scrutiny Action | Record decision: RETURNED_FOR_CORRECTION | HTTP 200 OK, review_status=RETURNED_FOR_CORRECTION | **200 OK** | Application returned | **PASS** |
| **ADM-AUTH-01** | `ADMIN` | Authentication | Login as `admin@platform.test` / `AdminPass123!` | HTTP 200, JWT token returned, role=ADMIN | **200 OK** | Admin authenticated | **PASS** |
| **ADM-AUTH-02** | `ADMIN` | Access Control | Query `GET /api/v1/auth/admin-check` | HTTP 200, admin authorization verified | **200 OK** | Admin privilege confirmed | **PASS** |
| **ADM-DASH-01** | `ADMIN` | System KPIs | Query overview (`GET /api/v1/admin/overview`) | HTTP 200 OK, system metrics returned | **200 OK** | Platform KPIs loaded | **PASS** |
| **ADM-USER-01** | `ADMIN` | User Mgmt | List users (`GET /api/v1/admin/users`) | HTTP 200 OK, users across all roles | **200 OK** | User directory loaded | **PASS** |
| **ADM-USER-02** | `ADMIN` | User Mgmt | Provision user (`POST /api/v1/admin/users`) | HTTP 201 Created, user created with designated role | **201 Created** | User created in DB | **PASS** |
| **ADM-USER-03** | `ADMIN` | User Mgmt | Deactivate user (`PATCH /api/v1/admin/users/{id}`) | HTTP 200 OK, is_active=False | **200 OK** | User deactivated | **PASS** |
| **ADM-USER-04** | `ADMIN` | User Mgmt | Reactivate user (`PATCH /api/v1/admin/users/{id}`) | HTTP 200 OK, is_active=True | **200 OK** | User reactivated | **PASS** |
| **ADM-RULE-01** | `ADMIN` | Governance | Deactivate & reactivate rule (`RULE-EOA-FIRE-003`) | HTTP 200 OK, rule state transitions governed | **200 OK** | Rule status updated | **PASS** |
| **ADM-AUDIT-01** | `ADMIN` | Forensic Audit | Query audit trail (`GET /api/v1/admin/audit-events`)| HTTP 200 OK, chronological events with actor IDs | **200 OK** | Events returned | **PASS** |
| **NEG-AUTH-01** | `ANONYMOUS` | Access Control | Unauthenticated request to protected route | HTTP 401 Unauthorized | **401 Unauthorized** | Missing token rejected | **PASS** |
| **NEG-AUTH-02** | `ANONYMOUS` | Access Control | Tampered JWT token signature | HTTP 401 Unauthorized | **401 Unauthorized** | Invalid signature rejected | **PASS** |
| **NEG-RATE-01** | `ANONYMOUS` | Brute Force | Repeated failed login attempts | HTTP 401 or 429 rate limit enforced | **429 Too Many Requests**| Lockout enforced | **PASS** |

---

### 3. Cross-Role Connected Workflow Outcome

The connected end-to-end multi-role test was executed seamlessly through the backend test harness and verified in the live browser subagent session:

1. **Step 1 (Institution):** Applicant `usr_inst_01` created EoA application `AICTE-EOA-2026-3028` in `DRAFT` status.
2. **Step 2 (Institution):** Uploaded `FIRE_SAFETY_NOC` v1. System computed SHA-256 (`594b8b92...`) and saved to isolated disk storage.
3. **Step 3 (Institution):** IDP extraction parsed document; pre-scrutiny evaluation generated 8 findings (4 deficiencies, 1 pass, 3 unable to evaluate).
4. **Step 4 (Institution):** Applicant uploaded renewed `FIRE_SAFETY_NOC` v2; acknowledged finding; submitted formal correction with Cycle 1 remark.
5. **Step 5 (Institution):** Revalidation delta evaluated v2 and transitioned finding to `AWAITING_REVIEW`.
6. **Step 6 (Reviewer):** Reviewer `usr_rev_104` queried queue; claimed case; opened scrutiny dossier resolving ID directly ([DEF-REV-001](file:///d:/Desktop/Hackathon/Document%20Verification/docs/DEF-REV-001)); streamed binary PDF v2 directly.
7. **Step 7 (Reviewer):** Reviewer recorded observation accepting renewed Fire NOC; evaluated remaining blocking deficiencies (Land Title & Building Completion missing); recorded formal disposition `RETURNED_FOR_CORRECTION`.
8. **Step 8 (Admin):** Administrator queried overview KPIs, verified user accounts across roles, tested rule activation governance, and audited immutable events in the forensic audit log.

---

### 4. Browser Verification Artifacts

The multi-role journey was executed in a real browser session via the browser subagent. Session recording and high-resolution screenshots were captured:

- **Browser Session Recording:** `role_wise_audit_e2e_1792907829351.webp`
- **Screenshot 1 — Applicant Evidence Inspector:**
  `C:\Users\Dhayanithi M U\.gemini\antigravity-ide\brain\582f1e67-5fc0-491d-a6f9-7de206fe9ba0\applicant_evidence_inspector_1792907903623.png`
  *Displays split-screen document viewer with visual bounding box overlay anchored to the exact page and clause.*
- **Screenshot 2 — Reviewer Scrutiny Dossier:**
  `C:\Users\Dhayanithi M U\.gemini\antigravity-ide\brain\582f1e67-5fc0-491d-a6f9-7de206fe9ba0\reviewer_scrutiny_dossier_1792907944099.png`
  *Displays reviewer scrutiny console with application details, document checklist, and side-by-side findings.*
- **Screenshot 3 — Admin Forensic Audit Trail:**
  `C:\Users\Dhayanithi M U\.gemini\antigravity-ide\brain\582f1e67-5fc0-491d-a6f9-7de206fe9ba0\admin_audit_trail_1792907974126.png`
  *Displays administrative audit log with timestamped entries, actor roles, operations, and IP addresses.*

---

### 5. Prioritized Defect & Remediations Log

No Critical or High severity security defects were found. All identified issues are categorized as Medium or Low:

#### Medium Severity Defects:
1. **AUDIT-DEFECT-01: `renderWorkspace` Argument Mismatch in `application-detail.js`**
   - **File:** [frontend/js/views/application-detail.js](file:///d:/Desktop/Hackathon/Document%20Verification/frontend/js/views/application-detail.js#L555) (Lines 555, 607, 660).
   - **Root Cause:** Re-rendering workspace after upload, removal, or reprocessing passes 4 arguments instead of 5, causing `state` to receive `router` and `initialFindings` to receive `state`.
   - **Remediation:** Pass `updatedFindingsData?.findings || []` as the 3rd argument.

2. **AUDIT-DEFECT-02: `uploaded_slots` Filter in `applications.py`**
   - **File:** [backend/api/v1/applications.py](file:///d:/Desktop/Hackathon/Document%20Verification/backend/api/v1/applications.py#L261) (Line 261).
   - **Root Cause:** Summing items where `status == "UPLOADED"` ignores items that transitioned to `"PROCESSED"`.
   - **Remediation:** Update condition to `item.status in ["UPLOADED", "PROCESSED"]`.

#### Low Severity Observations:
3. **AUDIT-OBS-01: Duplicate Hash Collision Warning**
   - **File:** [backend/services/document_service.py](file:///d:/Desktop/Hackathon/Document%20Verification/backend/services/document_service.py#L125).
   - **Detail:** Re-uploading an identical PDF binary creates an incremental version without notifying the user that an identical document already exists in that slot.

4. **AUDIT-OBS-02: Upload Toast Alignment with IDP Extraction State**
   - **File:** [frontend/js/views/application-detail.js](file:///d:/Desktop/Hackathon/Document%20Verification/frontend/js/views/application-detail.js#L550).
   - **Detail:** Uploading an encrypted PDF shows a green success toast on HTTP 201 even when the extraction run completes with `FAILED`.

---

### 6. Git Status & Database Baseline Integrity Confirmation

Final Git status inspection confirms that all working tree files have been preserved:
- Active demo database `data/aicte.db` was **NOT modified, reset, reseeded, or migrated**.
- Document storage `storage/documents` was **NOT altered or deleted**.
- All tests were conducted in isolated SQLite databases (`data/test_isolated.db` and `data/test_frontend.db`).
- No commits or pushes have been performed.
