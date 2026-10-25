# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Evaluator & Judge Demo Runbook (`DEMO_RUNBOOK.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P10 — End-to-End Verification, Accessibility Audit, Performance Hardening & Demo Freeze  
**Platform Status:** Feature-Complete SIH Prototype  
**Audience:** Hackathon Evaluators, Jury Members & Technical Reviewers  
**Estimated Demo Duration:** 8–10 Minutes  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal. For decision-support demonstration purposes only.*

---

## 1. Quick Start & Server Health Verification (60 Seconds)

### 1.1 Prerequisites
- Python 3.11+ / 3.13 (Audited on Python 3.13.15)
- Node.js v18+ / v20+ / v22+ (Audited on Node v22.23.2)

### 1.2 Start Services
Open two terminal windows in the project root:

**Terminal 1 (Backend API Service):**
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
*Health verification:* Navigate to [http://127.0.0.1:8000/api/v1/health/readiness](http://127.0.0.1:8000/api/v1/health/readiness). You should see `{"status":"ready","database":"connected"}`.

**Terminal 2 (Frontend Static Server):**
```powershell
node server.js
```
*Access Application:* Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 2. Seeded User Credentials (Zero Manual Setup Required)

> **Synthetic Test Credential Notice:** All passwords and user accounts listed below are synthetic credentials intended solely for local hackathon evaluation and testing. They are populated by the platform seed script (`python -m backend.core.seed`) and do not represent live production or government credentials.

| Role | Synthetic Email Address | Seed Password | Intended Workflow |
| :--- | :--- | :--- | :--- |
| **Institution Applicant** | `applicant@institution.test` | `Password123!` | EoA application, document upload, OCR review, deficiency remediation. |
| **Committee Reviewer** | `reviewer@reviewer.test` | `ReviewerPass123!` | Case scrutiny queue, spatial evidence inspection, observations, stage recommendations. |
| **Platform Administrator**| `admin@platform.test` | `AdminPass123!` | System overview KPIs, user provisioning, rule activation, audit log timeline. |

> **Pro-Tip for Quick Testing:** On the login page (`#/login`), click the **"Synthetic Demo Accounts"** drawer on the right to auto-fill credentials for any role with a single click.

---

## 3. End-to-End Demonstration Journey (8-Minute Guided Walkthrough)

### Step 1: Institutional Applicant Experience (3 Minutes)
1. **Login:** Log in as `applicant@institution.test` (`Password123!`).
2. **Dashboard Overview (`#/dashboard`):**
   - Note the **persistent disclaimer banner**: `⚠️ SIH PROTOTYPE — NOT AN OFFICIAL AICTE PORTAL`.
   - Observe the active application card for **Apex Institute of Technology & Management** (`AICTE-EOA-2026-9812`).
3. **Application Workspace (`#/applications/app_9812`):**
   - Click **"Open Workspace"**.
   - Inspect the **Statutory 8-Document Checklist**: all mandatory regulatory slots (Land Title Deed, Land Use Certificate, Building Plan, Building Completion, Fire NOC, Structural Stability, Previous AICTE Approval, Faculty Cadre Roster).
4. **Primary USP — Split-Screen Evidence Inspector:**
   - In the sidebar or top banner, click **"Inspect Evidence"** (or navigate to `#/applications/app_9812/evidence/find_0042`).
   - Observe the **split-screen layout**:
     - *Left Pane:* Detailed regulatory finding explaining the cross-document survey mismatch between Land Title Deed (`Sy. No. 44/2A`) and Land Use Certificate (`Sy. No. 44/2B`) with AICTE APH clause reference.
     - *Right Pane:* Live document viewport highlighting the exact **visual bounding box** around the extracted survey number.
5. **Deficiency Resolution Bridge (`#/applications/app_9812/deficiencies`):**
   - Navigate to the Deficiency Bridge.
   - Click **"Acknowledge"** on an open finding to record review awareness.
   - Click **"Respond / Resolve"** to open the interactive response drawer:
     - Select category: `DOCUMENT_REPLACEMENT`.
     - Enter explanatory remarks.
     - Click **"Save Draft"** or **"Submit Correction"**.
   - Click **"Trigger Controlled Revalidation"**:
     - The real P7 Regulatory Rule Engine re-evaluates the application.
     - Observe the **Before-vs-After Delta Modal** showing status `CLEARED` and handoff status `AWAITING_REVIEW`.
   - Click **"View History"** on any finding to inspect the immutable audit timeline.

---

### Step 2: Committee Reviewer Scrutiny Console (2.5 Minutes)
1. **Switch Role / Login:** Log in as `reviewer@reviewer.test` (`ReviewerPass123!`).
2. **Reviewer Workqueue (`#/reviewer/queue`):**
   - Observe the real-time **Queue Metrics Bar**: `Total Applications`, `Assigned to Me`, `Unassigned`, `Under Scrutiny`, `Recommended Clear`, `Returned for Correction`.
   - Test the interactive **Filter Chips** (`All Cases`, `Assigned to Me`, `Under Scrutiny`).
   - Use the **Search Bar** to filter applications dynamically.
   - Click **"Assign to Me"** on `AICTE-EOA-2026-9812` to assign the case.
3. **Comprehensive Scrutiny Console (`#/reviewer/scrutiny/app_9812`):**
   - Click **"Open Scrutiny Case"**.
   - Review the complete case file:
     - Institution details, academic year, and category.
     - All 8 statutory checklist document versions and verification statuses.
     - Findings with spatial evidence coordinates.
     - Applicant's submitted corrective remarks and replacement documents.
     - Automated revalidation delta (`CLEARED` vs `PERSISTS`).
4. **Record Scrutiny Observation:**
   - Scroll to **Scrutiny Observations**.
   - Choose a finding, select decision: `ACCEPT_CORRECTION`, enter justification: *"Verified civil structural stability certificate. Compliance verified under AICTE APH norms."*
   - Click **"Record Scrutiny Observation"**.
   - Confirm immediate appearance in the **Chronological Observation History** stream below.
5. **Pre-Scrutiny Stage Signoff:**
   - Scroll to **Pre-Scrutiny Stage Decision**.
   - Select `PRE_SCRUTINY_RECOMMENDED_CLEAR` (or `RETURNED_FOR_CORRECTION`).
   - Enter committee remarks and click **"Submit Pre-Scrutiny Stage Recommendation"**.
   - Notice the status badge updates to `PRE_SCRUTINY_RECOMMENDED_CLEAR` while clearly stating the advisory prototype nature.

---

### Step 3: Administrator Governance & Audit Trail (2 Minutes)
1. **Switch Role / Login:** Log in as `admin@platform.test` (`AdminPass123!`).
2. **Admin Overview (`#/dashboard` or `/admin/overview` API):**
   - Real-time KPIs aggregated from SQLite: total users, active accounts, registered institutions, and applications under scrutiny.
3. **User Governance Directory (`#/admin/users`):**
   - View the complete platform user roster with role badges and active statuses.
   - Click **"+ Provision New User"**:
     - Full Name: `Prof. Meera Sen`
     - Email: `user@platform.test`
     - Role: `REVIEWER`
     - Password: `SecurePassword123!`
     - Click **"Create User Account"**. Notice instant appearance in directory table with zero credential leakage.
   - **Self-Lockout Protection Test:** Try clicking the toggle button on the currently logged-in administrator account. The system denies self-deactivation with an informative safety warning.
4. **Regulatory Rule Governance (`#/admin/rules`):**
   - Browse the versioned AICTE Approval Process Handbook (APH) rule catalogue.
   - Select a draft or unverified rule and toggle its activation state.
5. **Tamper-Evident Forensic Audit Stream (`#/admin/audit`):**
   - View the real-time append-only security audit log.
   - Filter by actor role (`REVIEWER`, `ADMIN`, `INSTITUTION`) or action (`REVIEWER_OBSERVATION_RECORDED`, `PRE_SCRUTINY_REVIEW_COMPLETED`, `USER_PROVISIONED`).
   - Click on an audit event to inspect its structured JSON payload.

---

### Step 4: Negative Security & Boundary Verification (1.5 Minutes)
1. **Role Escalation Defense:**
   - Log in as Institution Applicant (`applicant@institution.test`).
   - Try navigating to `#/reviewer/queue` or `#/admin/users`.
   - **Result:** You are greeted by the clean **403 Access Denied** view; API requests return HTTP 403 Forbidden with zero information leakage.
2. **Cross-Tenant IDOR Defense:**
   - In the API or browser console, attempt to query another institution's application details:
     `fetch('http://127.0.0.1:8000/api/v1/applications/app_2048', { headers: { Authorization: 'Bearer ' + sessionStorage.getItem('aicte_token') } })`
   - **Result:** Returns `HTTP 404 Not Found` (masking existence to prevent resource enumeration).
3. **Magic-Byte Gatekeeper Defense:**
   - Try renaming a `.txt` or `.exe` file to `.pdf` and uploading it.
   - **Result:** Rejected with `HTTP 422 Unprocessable Entity` ("File header does not match %PDF-").

---

## 4. Automated Verification Suite Execution

To execute all automated verification suites independently in your terminal:

```powershell
# 1. Complete Backend Suite (62 tests, 100% pass)
python -m pytest tests/backend/ -v

# 2. Complete Frontend & Accessibility Suite (80 tests, 100% pass)
npm test

# 3. Production Build & Lint Verification
npm run lint
npm run build
```

---

## 5. Architectural Highlights & Defense Checklist for Jury Q&A

1. **Q: Does this platform replace statutory AICTE approval committees?**
   - **A:** Absolutely not. The platform is explicitly an **SIH Decision-Support Prototype**. It accelerates pre-scrutiny by highlighting discrepancies with verifiable page coordinates and versioned rule citations. Final statutory approval remains strictly with official AICTE committees.
2. **Q: How does the system prevent black-box AI hallucinations?**
   - **A:** Every finding is anchored to an immutable regulatory rule code from the *AICTE Approval Process Handbook (APH 2024-2027)*, includes normalized spatial bounding box coordinates `[ymin, xmin, ymax, xmax]`, and displays exact expected vs observed values.
3. **Q: How is applicant privacy and multi-tenancy guaranteed?**
   - **A:** Strict server-side database scoping. Any cross-institution lookup triggers an automatic `HTTP 404` mask to prevent enumeration. Uploaded documents are stored outside static roots and streamed only through authenticated, tenant-verified routes.
4. **Q: Can an applicant game the revalidation system?**
   - **A:** No. Replacement documents (`v2`) undergo full re-extraction via the P6 IDP pipeline and re-evaluation via the deterministic P7 rule engine. If the condition persists, the system flags `CONDITION_PERSISTS` and preserves historical detection runs permanently.
