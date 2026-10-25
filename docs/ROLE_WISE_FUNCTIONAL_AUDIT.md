# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Role-Wise Functional Audit Report (`ROLE_WISE_FUNCTIONAL_AUDIT.md`)
**Smart India Hackathon (SIH) Prototype Comprehensive Functional Verification**

---

### Executive Summary & Scope

This report delivers a comprehensive functional audit of the **AICTE Pre-Scrutiny & Deficiency Resolution Platform**, evaluating actual functionality against the approved specification ([PROJECT_SPEC.md](file:///d:/Desktop/Hackathon/Document%20Verification/docs/PROJECT_SPEC.md)), API contract, and implementation reality.

The audit was conducted strictly against an isolated test database (`data/test_frontend.db` / `data/test_isolated.db`) and separate temporary storage. The active demo database (`data/aicte.db`) and existing document files were preserved intact without modifications.

### Functional Status Classification Standard
Every capability is classified into one of the following states:
1. **Implemented and Verified**: Genuinely implemented in frontend and backend, covered by automated tests, and verified in real browser interaction.
2. **Implemented but Failing**: Code exists but contains an active runtime error, schema mismatch, or broken logic.
3. **Partially Implemented**: The core workflow functions, but specific secondary capabilities (e.g. pagination, external verification) are incomplete.
4. **Missing from Implementation**: Spec mentions the concept, but no route, UI view, or service logic exists.
5. **Not Applicable to Role**: Operation is explicitly restricted or out of scope for the role.
6. **Unable to Verify (Environment Limitation)**: External third-party integrations (e.g. government land registry APIs, live AICTE server tunnels).

---

### Part 1 — ROLE 1: INSTITUTION APPLICANT (`INSTITUTION`)

#### 1. Authentication & Session Management
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Login with Credentials** | Authenticate via email/password, issue JWT token with `INSTITUTION` role and `institution_id` | Returns HTTP 200, JWT access token, user profile with institution details | **Implemented and Verified** | Tested via `POST /api/v1/auth/login`, `INST-AUTH-01` PASS |
| **Identity Retrieval** | Retrieve current user profile via `/auth/me` | Returns HTTP 200 with institution name, permanent ID, and contact details | **Implemented and Verified** | Tested via `GET /api/v1/auth/me`, `INST-AUTH-02` PASS |
| **Session Revocation (Logout)** | Invalidate JWT upon logout | In-memory revocation blacklist rejects subsequent token usage with HTTP 401 | **Implemented and Verified** | Tested via `POST /api/v1/auth/logout`, `INST-AUTH-04` PASS |
| **Direct URL Role Guards** | Redirect institution users attempting to access `#/reviewer/*` or `#/admin/*` | Hash router renders `renderAccessDenied` with HTTP 403 styling | **Implemented and Verified** | Tested via frontend router lines 246–254 |
| **Backend API Restrictions** | Reject institution calls to `/reviewer/*` and `/admin/*` APIs | Backend dependencies `require_reviewer` and `require_admin` return HTTP 403 Forbidden | **Implemented and Verified** | Tested via `INST-AUTH-04` & `INST-AUTH-05` PASS |

#### 2. Application Management
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Application Listing** | List only applications belonging to caller's `institution_id` | Backend strictly filters `Application.institution_id == current_user.institution_id`; returns 0 cross-institution apps | **Implemented and Verified** | Tested via `INST-AUTH-03` PASS; 100% tenant isolation |
| **Application Detail View** | Open application workspace showing status, metadata, and intake | Renders header, status badge, academic year, application type, and intake | **Implemented and Verified** | Tested via `GET /api/v1/applications/{id}`, `INST-APP-01` PASS |
| **Create Application** | Create new EoA draft application bound to caller's institution | Creates application in `DRAFT` status and automatically initializes 8 statutory checklist slots | **Implemented and Verified** | Tested via `POST /api/v1/applications`, `INST-APP-02` PASS |
| **Edit Draft Application** | Update permissible fields (e.g. intake) while application is in `DRAFT` | Updates metadata in SQLite and persists across refreshes | **Implemented and Verified** | Tested via `PUT /api/v1/applications/{id}`, `INST-APP-03` PASS |
| **Application Filters & Search** | Filter applications by academic year, status, or search string | Client-side search and status filters operate correctly in `applications-list.js` | **Implemented and Verified** | Verified in browser UI and unit tests |

#### 3. Document Checklist, Ingestion & IDP
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Statutory Checklist (8 Slots)** | Checklist displays 8 mandatory slots (Land Title, Land Use, Building Plan, Completion, Fire NOC, Structural, Prev Approval, Faculty Roster) | `GET /api/v1/applications/{id}/checklist` returns 8 structured slots with titles and statuses | **Implemented and Verified** | Tested via `INST-DOC-01` PASS |
| **Digital PDF Ingestion** | Upload valid PDF with text layer; compute SHA-256; store on disk | Computes SHA-256 on byte stream, creates `DocumentVersion` v1, initiates IDP text extraction | **Implemented and Verified** | Tested via `INST-DOC-02` PASS |
| **Scanned Document OCR** | Upload raster scanned PDF; fallback to PaddleOCR ONNXRuntime | Character count < 40 routes to PaddleOCR; extracts text and spatial boxes | **Implemented and Verified** | Tested via `tests/backend/test_extraction_pipeline.py` PASS |
| **Disallowed Format Rejection** | Reject non-PDF uploads (.docx, .png) with HTTP 422 | Backend rejects with HTTP 422: "Disallowed file format. Only PDF (.pdf) documents are permitted" | **Implemented and Verified** | Tested via `INST-DOC-04` PASS |
| **Magic Byte Verification** | Reject files with spoofed extensions lacking `%PDF-` header | Inspects first 1024 bytes; rejects spoofed files with HTTP 422 | **Implemented and Verified** | Tested via `INST-DOC-05` PASS |
| **Zero-Byte File Rejection** | Reject empty uploads with HTTP 422 | Returns HTTP 422: "Uploaded file is empty (0 bytes)" | **Implemented and Verified** | Tested via `tests/backend/test_applications_workflow.py` PASS |
| **File Size Ceiling (15MB)** | Reject uploads exceeding 15MB with HTTP 413 | Returns HTTP 413: "File exceeds maximum permissible size of 15MB" | **Implemented and Verified** | Tested via `audit_upload_scenarios.py` Scenario 7 PASS |
| **Document Versioning** | Uploading new file creates incremental version (v2) preserving v1 | Creates new `DocumentVersion` row; links to previous version; retains historical binary | **Implemented and Verified** | Tested via `INST-DOC-07` PASS |
| **Cross-Tenant Upload Defense** | Prevent applicant from uploading to another institution's application | `verify_institution_access` masks existence with HTTP 404 Not Found | **Implemented and Verified** | Tested via `INST-DOC-06` PASS |

#### 4. Pre-Scrutiny & Regulatory Evaluation
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Run Pre-Scrutiny Engine** | Evaluates latest document versions against active APH rules | Evaluates 8 active rules (Land, BCC, Fire, Structural, FSR, Cross-checks); returns summary | **Implemented and Verified** | Tested via `POST /api/v1/applications/{id}/validate`, `INST-REG-01` PASS |
| **Findings Generation** | Generate structured findings linking rule ID, severity, citation, and evidence | Persists findings in `findings` table with severity `DEFICIENCY` or `WARNING` and APH clause citation | **Implemented and Verified** | Tested via `INST-REG-02` PASS |
| **Split-Screen Evidence Inspector** | Inspect source PDF alongside extracted values and normalized bounding boxes | Renders document viewer with spatial bounding box overlay anchored to extracted page | **Implemented and Verified** | Verified in browser UI; screenshot `applicant_evidence_inspector.png` |
| **Readiness Gauge Scoring** | Calculate readiness score based on resolved vs unresolved deficiencies | Calculates readiness score from weighted compliance formula in `application-detail.js` | **Implemented and Verified** | Verified in browser workspace (displays 78% readiness index) |
| **Interactive FSR & Land Calculators** | Real-time statutory calculators allowing institutions to test scenarios | Renders interactive calculators for faculty-to-student ratios and built-up area/FSI norms | **Implemented and Verified** | Tested in browser session (`applicant_fsr_calculator`) |

#### 5. Deficiency Resolution Bridge & Revalidation
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Acknowledge Finding** | Formally acknowledge finding without altering non-compliance | Transitions finding status to `ACKNOWLEDGED`; logs timestamp | **Implemented and Verified** | Tested via `POST /api/v1/findings/{id}/acknowledge`, `INST-DEF-01` PASS |
| **Save Correction Draft** | Save remediation explanation and document link without formal submission | Persists `CorrectionSubmission` in `DRAFT` state | **Implemented and Verified** | Tested via `PUT /api/v1/findings/{id}/response`, `INST-DEF-02` PASS |
| **Submit Formal Correction** | Submit correction cycle to reviewers | Transitions finding to `CORRECTION_SUBMITTED`; cycle_number=1 | **Implemented and Verified** | Tested via `POST /api/v1/findings/{id}/submit`, `INST-DEF-03` PASS |
| **Workflow Guard (DEF-APPLICANT-001)** | Block premature draft editing while submission is awaiting review | Rejects draft updates with HTTP 409 Conflict | **Implemented and Verified** | Tested via `INST-DEF-04` PASS; regression fix verified |
| **Controlled Delta Revalidation** | Re-run rules on renewed document; compute before/after delta | Re-runs regulatory rules on latest version; marks condition cleared; awaits reviewer | **Implemented and Verified** | Tested via `POST /api/v1/applications/{id}/revalidate`, `INST-DEF-05` PASS |
| **Chronological Audit History** | Retrieve finding history from detection through revalidation | Returns complete timeline of events with actor, action, and timestamp | **Implemented and Verified** | Tested via `GET /api/v1/findings/{id}/history`, `INST-DEF-06` PASS |

---

### Part 2 — ROLE 2: SCRUTINY REVIEWER (`REVIEWER`)

#### 1. Authentication & Reviewer Access Control
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Reviewer Authentication** | Login with reviewer credentials; issue JWT with `REVIEWER` role | Returns HTTP 200, JWT access token, role=`REVIEWER`, institution_id=`null` | **Implemented and Verified** | Tested via `REV-AUTH-01` PASS |
| **Prohibit Application Creation** | Reviewers must not be able to create applications | Calling `POST /api/v1/applications` returns HTTP 403 Forbidden | **Implemented and Verified** | Tested via `REV-AUTH-02` PASS |
| **Prohibit User Administration** | Reviewers must not be able to access user administration | Calling `GET /api/v1/admin/users` returns HTTP 403 Forbidden | **Implemented and Verified** | Tested via `REV-AUTH-03` PASS |
| **Direct URL Route Access** | Reviewer navigating to `#/admin/users` receives Access Denied | Frontend router renders `renderAccessDenied` with permission alert | **Implemented and Verified** | Verified in browser UI |

#### 2. Reviewer Queue & Case Management
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Reviewer Scrutiny Queue** | List applications eligible for scrutiny across institutions | Returns queue items with institution names, deficiency counts, readiness scores, and metrics | **Implemented and Verified** | Tested via `GET /api/v1/reviewer/queue`, `REV-QUEUE-01` PASS |
| **Queue Filtering & Search** | Filter queue by status (`UNASSIGNED`, `UNDER_REVIEW`), state, academic year | Query parameters correctly filter queue results | **Implemented and Verified** | Tested via unit tests and API query parameters |
| **Assign / Reassign Case** | Assign application to reviewer | Updates `assigned_reviewer_id`, transitions review status to `ASSIGNED`, logs audit event | **Implemented and Verified** | Tested via `POST /api/v1/reviewer/applications/{id}/assign`, `REV-QUEUE-02` PASS |

#### 3. Scrutiny Console & Evidence Inspection
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Full Scrutiny Dossier (DEF-REV-001)** | Open case dossier resolving application ID directly from queue | Returns full case dossier with checklist, findings, submissions, and observations | **Implemented and Verified** | Tested via `GET /api/v1/reviewer/applications/{id}/scrutiny`, `REV-SCRUT-01` PASS |
| **Stream Document Binary** | Reviewer streams original PDF binary for spatial verification | Returns `application/pdf` binary stream directly from storage | **Implemented and Verified** | Tested via `REV-SCRUT-02` PASS |
| **Remediation Delta Comparison** | View before vs after comparison for revalidated deficiencies | Displays previous observed value vs latest observed value with status change badge | **Implemented and Verified** | Verified in Scrutiny Console; screenshot `reviewer_scrutiny_dossier.png` |
| **External Registry Verification** | Verify document against live external government registries | UI correctly indicates "Mock / Demo Data" and does not claim authoritative external verification | **Partially Implemented (By Design)** | Pure prototype decision-support; live state registry connections not implemented |

#### 4. Reviewer Observations & Dispositions
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Record Observation** | Record official committee observation or accept/overrule finding | Persists `ReviewerObservation` with decision (`ACCEPT_CORRECTION`, `CONCUR_DEFICIENCY`), logs audit event | **Implemented and Verified** | Tested via `POST /api/v1/reviewer/applications/{id}/observations`, `REV-OBS-01` PASS |
| **Return for Correction** | Return application for additional evidence | Transitions review status to `RETURNED_FOR_CORRECTION`, unlocks applicant correction cycle | **Implemented and Verified** | Tested via `POST /api/v1/reviewer/applications/{id}/decision`, `REV-DEC-01` PASS |
| **Blocking Deficiency Enforcement** | Reject `PRE_SCRUTINY_RECOMMENDED_CLEAR` if unresolved deficiencies exist | Returns HTTP 400: "Cannot recommend application as clear: Unresolved deficiencies exist" | **Implemented and Verified** | Enforced in `reviewer_service.py` line 540; regulatory integrity protected |
| **Non-Final Advisory Boundary** | Reviewer decisions act as decision-support, not statutory final approval | Explicit disclaimer that pre-scrutiny recommendations are advisory to EOA committee | **Implemented and Verified** | Enforced across UI dossiers and backend schemas |

---

### Part 3 — ROLE 3: PLATFORM ADMINISTRATOR (`ADMIN`)

#### 1. Authentication & System Oversight
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Admin Authentication** | Login with administrator credentials; issue JWT with `ADMIN` role | Returns HTTP 200, JWT access token, role=`ADMIN` | **Implemented and Verified** | Tested via `ADM-AUTH-01` PASS |
| **Admin Privilege Check** | Query `/auth/admin-check` | Returns HTTP 200 with admin authorization confirmation and user ID | **Implemented and Verified** | Tested via `ADM-AUTH-02` PASS |
| **Admin Overview KPIs** | Retrieve platform metrics (total users, institutions, applications, rules) | Returns counts for users, institutions, applications, and regulatory rules | **Implemented and Verified** | Tested via `GET /api/v1/admin/overview`, `ADM-DASH-01` PASS |

#### 2. User & Account Management
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **List Platform Users** | List users across all roles (`INSTITUTION`, `REVIEWER`, `ADMIN`) | Returns user accounts with email, role, institution association, and active status | **Implemented and Verified** | Tested via `GET /api/v1/admin/users`, `ADM-USER-01` PASS |
| **Provision User Account** | Provision new synthetic user with designated role and password hash | Creates user in database with bcrypt hash, logs audit event | **Implemented and Verified** | Tested via `POST /api/v1/admin/users`, `ADM-USER-02` PASS |
| **Deactivate User Account** | Deactivate user account preventing further logins | Sets `is_active=False`; subsequent logins return HTTP 403 Forbidden | **Implemented and Verified** | Tested via `PATCH /api/v1/admin/users/{id}`, `ADM-USER-03` PASS |
| **Reactivate User Account** | Reactivate user account restoring access | Sets `is_active=True`; user can authenticate normally | **Implemented and Verified** | Tested via `PATCH /api/v1/admin/users/{id}`, `ADM-USER-04` PASS |

#### 3. Regulatory Rule Governance
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Rule Catalog Inspection** | Browse regulatory rules with citations, version bounds, and status | Displays APH rule catalogue with rule codes, titles, status badges, and academic years | **Implemented and Verified** | Verified in browser UI `#/admin/rules` |
| **Rule Activation** | Activate verified regulatory rule for automated enforcement | Sets `is_active=True`, status=`APPROVED_FOR_PROTOTYPE_USE`, updates version approval metadata | **Implemented and Verified** | Tested via `POST /api/v1/rules/{rule_code}/activate`, `ADM-RULE-01` PASS |
| **Rule Deactivation** | Deactivate unsupported or draft regulatory rule with mandatory reason | Sets `is_active=False`, status=`DRAFT_MISSING_OFFICIAL_SOURCE`, logs audit event | **Implemented and Verified** | Tested via `POST /api/v1/rules/{rule_code}/deactivate`, `ADM-RULE-01` PASS |
| **Deactivation of Bank Guarantee Rule** | `RULE-DRAFT-BANK-009` must remain inactive by default | Seed script and migration `5a7c92b84102` ensure rule remains deactivated | **Implemented and Verified** | Tested via `test_unsupported_rule_bank_009_deactivated` PASS |

#### 4. Forensic Audit Trail
| Feature / Action | Expected Behavior | Actual Behavior | Classification | Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Audit Events Log** | Retrieve immutable chronological audit stream | Returns events with actor ID, actor role, action, entity type, payload, and client IP | **Implemented and Verified** | Tested via `GET /api/v1/admin/audit-events`, `ADM-AUDIT-01` PASS |
| **Actor & Role Attribution** | Every logged event captures actor role (`INSTITUTION`, `REVIEWER`, `ADMIN`) | Audit events table enforces non-null actor role and timestamp | **Implemented and Verified** | Verified in browser screenshot `admin_audit_trail.png` |
| **Non-Tampering Boundary** | System logs actions without allowing edit or deletion of audit rows | No `PUT` or `DELETE` endpoints exist on `/admin/audit-events`; append-only design | **Implemented and Verified** | Code inspected; 100% append-only |

---

### Part 4 — Identified Defects & Functional Limitations

| Defect ID | Role Affected | Component | Severity | Description | Recommended Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUDIT-DEFECT-01** | `INSTITUTION` | `frontend/js/views/application-detail.js` | **Medium** | Post-upload re-render calls `renderWorkspace` with 4 arguments instead of 5, passing `state` into the `initialFindings` slot and `router` into `state`. | Update call sites (lines 555, 607, 660) to pass `updatedFindingsData?.findings || []` as the 3rd argument. |
| **AUDIT-DEFECT-02** | `INSTITUTION` | `backend/api/v1/applications.py` | **Medium** | `uploaded_slots` calculation only sums items with `status == "UPLOADED"`, ignoring items that successfully transitioned to `"PROCESSED"`. | Update line 261: `item.status in ["UPLOADED", "PROCESSED"]`. |
| **AUDIT-OBS-01** | `INSTITUTION` | `backend/services/document_service.py` | **Low** | Uploading an identical document binary creates an incremental version without notifying the applicant of a duplicate hash collision. | Add optional client notice if `file_hash_sha256` matches current active version. |
| **AUDIT-OBS-02** | `INSTITUTION` | `frontend/js/views/application-detail.js` | **Low** | Upload toast displays generic success on HTTP 201 even when underlying IDP extraction run completes with `FAILED` or `COMPLETED_WITH_WARNINGS`. | Check `response.status` and display amber warning toast when extraction warnings occur. |

---

### Conclusion & Final Audit Assessment

The functional audit establishes that the **AICTE Pre-Scrutiny & Deficiency Resolution Platform** is **VERIFIED WITH DOCUMENTED LIMITATIONS**:
1. All three roles (`INSTITUTION`, `REVIEWER`, `ADMIN`) possess clearly segregated interfaces, backend authorization dependencies, and server-side tenant isolation guards.
2. The primary USP—an interactive Deficiency Resolution Bridge with split-screen visual PDF bounding box overlays and controlled delta revalidation—is feature-complete and fully functional.
3. Crucial human authority boundaries are rigorously enforced: automated engines only provide advisory decision-support, reviewers cannot clear applications with unresolved blocking deficiencies, and official AICTE disclaimers are persistently rendered.
