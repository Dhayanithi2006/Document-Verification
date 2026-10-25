# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Role-Permission & Access Control Matrix (`ROLE_PERMISSION_MATRIX.md`)
**Comprehensive Security, RBAC & Tenant Isolation Specification**

**Execution Date:** October 25, 2026
**Status:** Approved Security Baseline
**Governing Standard:** SIH Prototype Multi-Tenant Isolation & Role Authorization

---

## 1. Executive Summary & Authorization Architecture

The AICTE Pre-Scrutiny & Deficiency Resolution Platform enforces a multi-tier defense-in-depth authorization model to guarantee data confidentiality, tenant segregation, and role integrity:

1. **Client-Side SPA Route Guards:**
   - The native hash router (`frontend/js/router.js`) inspects the active session role (`state.activeRole` and `state.currentUser.role`).
   - Unauthorized attempts to navigate directly to restricted paths (e.g. an applicant attempting `#/reviewer/queue` or `#/admin/users`) render a dedicated `Access Denied` view (`renderAccessDenied`) and block view initialization.
2. **Server-Side Role-Based Access Control (RBAC):**
   - FastAPI endpoint dependencies defined in `backend/core/deps.py`:
     - `require_institution`: Restricts access strictly to users with role `INSTITUTION`.
     - `require_reviewer`: Restricts access to users with role `REVIEWER` or `ADMIN`.
     - `require_admin`: Restricts access strictly to users with role `ADMIN`.
   - Every request validates the signed JWT Bearer token, asserts active account status (`user.is_active == True`), and checks the in-memory token revocation blacklist.
3. **Multi-Tenant Isolation & IDOR Defense:**
   - Multi-tenant data segregation is enforced by `verify_institution_access(application, current_user)` in `backend/core/deps.py`.
   - When an `INSTITUTION` user attempts to access or mutate an application, document, finding, or correction response belonging to another institution, the backend raises `HTTP 404 Not Found` (masking existence to defeat enumeration).
4. **Human Authority Boundary:**
   - Algorithmic pre-scrutiny evaluations generate advisory findings; they are strictly prohibited from mutating application status to a final statutory approval.
   - Reviewer stage signoff dependencies enforce that `RECOMMEND_CLEAR` is blocked on the backend if any unresolved blocking deficiencies exist on the case.

---

## 2. Comprehensive Resource Permission Matrix

| Resource / Entity | Operation | Allowed Roles | Prohibited Roles | Backend Enforcement Mechanism | Verified Test Evidence Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Application** | `LIST` | `INSTITUTION` (own tenant), `REVIEWER` (all), `ADMIN` (all) | Anonymous | `verify_institution_access` / `require_roles` | `test_tenant_isolation_on_application_listing` PASS; returns only caller's tenant apps |
| **Application** | `CREATE` | `INSTITUTION` | `REVIEWER`, `ADMIN`, Anonymous | `current_user.role == 'INSTITUTION'` | `test_reviewer_cannot_create_application` PASS; Reviewer rejected with HTTP 403 |
| **Application** | `GET / VIEW` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `test_tenant_isolation_on_application_detail` PASS; IDOR masked as HTTP 404 |
| **Application** | `UPDATE (Draft)` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `verify_institution_access` & `app.status == 'DRAFT'` | `test_update_application_in_draft_state` PASS; locked applications reject edits |
| **Application** | `DELETE` | `NONE` (Prohibited) | All Roles | No delete endpoint exposed (Audit preservation) | Architectural constraint; immutable application ledger |
| **Document Checklist** | `VIEW` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `tests/applications_frontend.test.js` PASS; 8 statutory slots |
| **Document** | `UPLOAD (v1)` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & tenant check | `test_secure_pdf_upload_success_and_metadata` PASS; computes SHA-256 hash |
| **Document** | `REPLACE (v2+)` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & tenant check | `test_deficiency_workflow.py` PASS; v1 preserved on disk/DB |
| **Document** | `STREAM BINARY` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `_get_authorized_document_and_app` | `test_cross_institution_upload_and_download_denied` PASS; HTTP 404 |
| **Document** | `REMOVE / RESET` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & `app.status == 'DRAFT'` | `test_document_removal_and_slot_reset` PASS; resets slot to PENDING |
| **IDP Extraction** | `TRIGGER PROCESS` | `INSTITUTION` (own tenant), `ADMIN` | `REVIEWER`, Anonymous | Endpoint `POST /documents/{id}/process` | `test_digital_pdf_extraction_and_field_grounding` PASS; extraction run logged |
| **IDP Extraction** | `VIEW FIELDS` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `_get_authorized_document_and_app` | `test_tenant_isolation_on_idp_endpoints` PASS; fields isolated |
| **IDP Extraction** | `VIEW PAGES` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `_get_authorized_document_and_app` | `tests/extraction_frontend.test.js` PASS; page geometry delivered |
| **Pre-Scrutiny** | `RUN VALIDATION` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `test_regulatory_engine.py` PASS; evaluates active APH rules |
| **Findings** | `VIEW` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `tests/regulatory_frontend.test.js` PASS; citations & evidence delivered |
| **Findings** | `ACKNOWLEDGE` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & tenant check | `test_deficiency_workspace_and_acknowledgement` PASS; status=ACKNOWLEDGED |
| **Correction Draft** | `SAVE / RETRIEVE` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & workflow guard | `test_correction_draft_and_submission_lifecycle` PASS |
| **Correction** | `SUBMIT FORMAL` | `INSTITUTION` (own tenant) | `REVIEWER`, `ADMIN`, Anonymous | `require_institution` & acknowledgment guard | `test_correction_draft_and_submission_lifecycle` PASS; cycle 1 recorded |
| **Revalidation** | `TRIGGER CONTROLLED` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `test_controlled_revalidation_with_delta_comparison` PASS; before/after delta |
| **Finding History** | `VIEW TIMELINE` | `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN` | Cross-tenant `INSTITUTION`, Anonymous | `verify_institution_access` | `test_finding_history_chronological_timeline` PASS; chronological trail |
| **Reviewer Queue** | `VIEW / FILTER` | `REVIEWER`, `ADMIN` | `INSTITUTION`, Anonymous | `require_reviewer` (`REVIEWER`, `ADMIN`) | `test_institution_user_cannot_access_admin_or_reviewer_endpoints` PASS; HTTP 403 |
| **Reviewer Queue** | `CLAIM / ASSIGN` | `REVIEWER`, `ADMIN` | `INSTITUTION`, Anonymous | `require_reviewer` | `test_reviewer_case_assignment_and_status_transition` PASS |
| **Scrutiny Console** | `VIEW DOSSIER` | `REVIEWER`, `ADMIN` | `INSTITUTION` (direct scrutiny URL), Anonymous | `require_reviewer` | `tests/reviewer_admin_frontend.test.js` PASS; case data rendered |
| **Observation** | `RECORD OBSERVATION` | `REVIEWER`, `ADMIN` | `INSTITUTION`, Anonymous | `require_reviewer` | `test_record_reviewer_observation_and_timeline_persistence` PASS |
| **Scrutiny Signoff** | `RECORD DISPOSITION` | `REVIEWER`, `ADMIN` | `INSTITUTION`, Anonymous | `require_reviewer` & blocking deficiency check | `test_pre_scrutiny_approval_blocked_with_open_blocking_deficiencies` PASS |
| **Regulatory Rules** | `LIST CATALOG` | `INSTITUTION`, `REVIEWER`, `ADMIN` | Anonymous | `get_current_user` (Read-only catalog) | `test_regulatory_rule_catalog_and_activation_lifecycle` PASS |
| **Regulatory Rules** | `ACTIVATE RULE` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `test_admin_activate_rule_endpoint` PASS; is_active=True |
| **Regulatory Rules** | `DEACTIVATE RULE` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` & mandatory reason string | `test_admin_deactivate_endpoint_with_audit_logging` PASS; is_active=False |
| **User Directory** | `LIST / SEARCH` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `tests/reviewer_admin_frontend.test.js` Subtest 8 PASS |
| **User Management** | `PROVISION USER` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `test_admin_provision_user_success` PASS; returns provisioned profile |
| **User Management** | `DEACTIVATE USER` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `test_admin_deactivate_user` PASS; login subsequently returns HTTP 403 |
| **Audit Events** | `VIEW FORENSIC LOG` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `test_admin_audit_trail_inspection` PASS; returns append-only log |
| **Platform Metrics** | `VIEW DASHBOARD` | `ADMIN` | `INSTITUTION`, `REVIEWER`, Anonymous | `require_admin` | `test_admin_overview_metrics` PASS; returns application & rule totals |

---

## 3. Privilege Analysis: Excessive & Missing Permissions

### 3.1 Excessive Permissions Review
- **Applicant Privilege Boundary:** Institutional applicants cannot claim cases, assign reviewers, query reviewer queues, modify regulatory rules, provision accounts, or view foreign institutional dossiers.
- **Reviewer Privilege Boundary:** Reviewers cannot create applications on behalf of institutions, upload documents into applicant checklists, edit declared parameters, provision users, or modify regulatory rule activation states.
- **Administrator Privilege Boundary:** Administrators cannot delete audit event rows, overwrite historical document versions, or bypass reviewer scrutiny logic to force an automated statutory grant.

### 3.2 Fine-Grained Role Governance Analysis
- **Reviewer Queue Claiming:** In the current prototype implementation, any authenticated user with role `REVIEWER` or `ADMIN` can claim/assign an unassigned application to themselves via `POST /api/v1/reviewer/applications/{id}/assign`. In an enterprise production deployment, assignment could be further restricted to a Committee Convener role.
- **Audit Log Inspection:** `GET /api/v1/admin/audit-events` is restricted strictly to `ADMIN`. Reviewers and Applicants cannot query platform-wide operational logs, preserving overall system privacy while allowing them to inspect application-specific timelines via `/deficiencies/{id}/history`.
- **Public Catalog Accessibility:** `GET /api/v1/rules` is intentionally open to all authenticated users (including `INSTITUTION`), enabling applicants to inspect governing APH 2024–27 criteria and formulaic thresholds prior to application submission. Rule mutation endpoints (`activate`, `deactivate`) strictly enforce `require_admin`.

---

## 4. Multi-Tenant Isolation & IDOR Verification Matrix

| Isolation Boundary Test | Attack Vector | Expected Result | Actual Result | Security Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Cross-Tenant Application Detail** | Inst 1 caller issues `GET /api/v1/applications/app_9813` (Inst 2 application) | HTTP 404 Not Found | HTTP 404 (`detail: Application not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant Application Listing** | Inst 1 caller issues `GET /api/v1/applications` | HTTP 200 OK (Scoped) | HTTP 200 OK; returns only `inst_01` applications; `inst_02` excluded | **PASS (Tenant Scoped)** |
| **Cross-Tenant Document Upload** | Inst 1 caller attempts `POST /api/v1/applications/app_9813/documents` | HTTP 404 Not Found | HTTP 404 (`detail: Application not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant Binary Download** | Inst 1 caller attempts `GET /api/v1/documents/{inst2_doc_id}/stream` | HTTP 404 Not Found | HTTP 404 (`detail: Document not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant Finding Detail** | Inst 1 caller issues `GET /api/v1/findings/{inst2_finding_id}` | HTTP 404 Not Found | HTTP 404 (`detail: Finding not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant Correction Draft** | Inst 1 caller issues `POST /api/v1/findings/{inst2_finding_id}/draft` | HTTP 404 Not Found | HTTP 404 (`detail: Finding not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant Correction Submit** | Inst 1 caller issues `POST /api/v1/findings/{inst2_finding_id}/submit` | HTTP 404 Not Found | HTTP 404 (`detail: Finding not found or access denied.`) | **PASS (IDOR Defended)** |
| **Cross-Tenant IDP Extraction** | Inst 1 caller attempts `POST /api/v1/documents/{inst2_doc_id}/process` | HTTP 404 Not Found | HTTP 404 (`detail: Document not found or access denied.`) | **PASS (IDOR Defended)** |

---

## 5. Security Summary & Compliance Verdict

The platform's authorization layer satisfies all SIH prototype requirements:
1. All sensitive endpoints enforce server-side RBAC dependencies (`require_institution`, `require_reviewer`, `require_admin`).
2. Client-side route transitions are synchronized with server-side Bearer token privileges.
3. Insecure Direct Object References (IDOR) are defeated by masking unauthorized tenant resources as `404 Not Found`.
4. Role permissions and tenant isolation are fully verified by automated unit tests and live browser execution.
