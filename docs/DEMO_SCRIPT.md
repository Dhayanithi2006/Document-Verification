# AICTE Pre-Scrutiny and Deficiency Resolution Platform
## Demonstration Script (`DEMO_SCRIPT.md`)

**Document Version:** 1.0.0  
**Phase:** P10 — Final Stabilization, Verification, and Demo Freeze  
**Classification:** Controlled Demonstration Walkthrough  
**Notice:** *SIH Prototype — Not an official AICTE portal. Decision-support demonstration only.*

---

## 1. Demonstration Overview & Setup

### 1.1 Objective
This demonstration script provides an end-to-end, repeatable, 16-step walkthrough of the AICTE Pre-Scrutiny and Deficiency Resolution Platform. It validates the complete lifecycle:
- Synthetic Applicant submission, OCR extraction, spatial provenance, and deficiency remediation.
- Committee Reviewer scrutiny console, spatial observation logging, and regulatory stage disposition.
- Administrator governance, access control audit timeline, and strict RBAC/IDOR isolation.

### 1.2 Environment Prerequisites
1. **Python Service:** Python 3.11+ running FastAPI at `http://127.0.0.1:8000`
2. **Frontend Service:** Node.js static server running at `http://localhost:3000`
3. **Database:** SQLite with WAL mode enabled at `data/aicte.db` (seeded via `python -m backend.core.seed`)

### 1.3 Verified Test Credentials (Synthetic Accounts)
> **Note:** The passwords listed below are synthetic credentials intended solely for local hackathon evaluation and testing convenience. They are populated by the platform seed script (`python -m backend.core.seed`) and do not represent live production or government credentials.

| Role | Synthetic Identity / Email | Seed Password | Primary Scope |
| :--- | :--- | :--- | :--- |
| **Institution Applicant** | `applicant@institution.test` | `Password123!` | Apex Institute of Technology & Management (`inst_001`, `app_9812`) |
| **Committee Reviewer** | `reviewer@reviewer.test` | `ReviewerPass123!` | Scrutiny Committee Panelist (`rev_krishnan`) |
| **Platform Administrator**| `admin@platform.test` | `AdminPass123!` | System Operations & Governance (`usr_admin_01`) |

---

## 2. Step-by-Step 16-Step Walkthrough

### Step 1: Introduce the Problem and the Platform's Scope
- **Action:** Open `http://localhost:3000/#/login`.
- **Narration:**
  > "Every year, thousands of technical institutions submit hundreds of pages of statutory documents for AICTE Extension of Approval (EoA). Manual pre-scrutiny suffers from human fatigue, overlooked discrepancies, and weeks of back-and-forth communication. Our platform is an AI-assisted, explainable decision-support system that accelerates pre-scrutiny while keeping human experts strictly in control. Notice the persistent disclaimer: **SIH Prototype — Not an official AICTE portal**."
- **Expected Outcome:** Login view loads cleanly with high-contrast accessibility tokens (WCAG 2.1 AA) and visible prototype disclaimers.

---

### Step 2: Sign In as the Institutional Applicant
- **Action:** Select **Institution Applicant** from the Demo Credentials drawer (or enter `applicant@institution.test` / `Password123!`), then click **"Sign In"**.
- **Expected Outcome:** 
  - JWT tokens (`access_token`, `refresh_token`) securely persisted in `sessionStorage`.
  - Redirected to `#/dashboard`.
  - Header displays authenticated user: *Dr. Ramesh Sharma (Principal)* for *Apex Institute of Technology & Management*.

---

### Step 3: Create or Open a Synthetic EoA Application
- **Action:** From the Dashboard, view the active application card for `AICTE-EOA-2026-9812` (Application Type: *Extension of Approval 2026–27*). Click **"Open Workspace"** (navigating to `#/applications/app_9812`).
- **Expected Outcome:** 
  - Application summary card displays status `UNDER_SCRUTINY` (or `DEFICIENCY_NOTED`).
  - Statutory 8-document checklist appears with verification progress (e.g., 6/8 uploaded, validated).

---

### Step 4: Inspect Required Checklist & Upload a Supporting Document
- **Action:** In the Document Checklist, locate the **Fire Safety Certificate (Fire NOC)** or **Building Completion Certificate** slot. Click **"Upload / Replace"** and select a synthetic PDF fixture (e.g., `tests/fixtures/sample_fire_noc.pdf`).
- **Expected Outcome:**
  - File undergoes frontend MIME and magic-byte checks before upload.
  - POST `/api/v1/applications/app_9812/documents` returns HTTP 201 with server-assigned hash (`sha256`) and storage path (`data/storage/documents/`).
  - Checklist item updates to status `UPLOADED` with file size and timestamp.

---

### Step 5: Demonstrate Actual Text Extraction and Real Scanned-PDF OCR
- **Action:** Click **"Process Document"** on the uploaded file (or inspect pre-processed Fire NOC document `doc_fire_01`).
- **Verification Note:** 
  - If a digital PDF is supplied, `pypdf`/`pdfplumber` extracts structured digital text streams.
  - If a scanned PDF or raster page is supplied, the backend invokes the local CPU ONNX OCR pipeline (PaddleOCR v6), bounding character coordinates without external SaaS calls.
- **Expected Outcome:** Document status transitions to `PROCESSED`. Extracted page text and metadata are saved in SQLite tables `documents` and `document_extractions`.

---

### Step 6: Inspect Extracted Fields and Spatial Page-Level Evidence
- **Action:** Click **"Inspect Evidence"** on the Land Title or Fire NOC card (navigating to `#/applications/app_9812/evidence/find_0042`).
- **Expected Outcome:**
  - **Split-Screen Inspector:**
    - Left Pane: PDF document viewer highlighting exact page `1` with an amber bounding box (`ymin: 0.72, xmin: 0.15, ymax: 0.76, xmax: 0.65`).
    - Right Pane: Extracted field card displaying:
      - Field Name: `fire_noc_validity_date`
      - Extracted Value: `2025-04-30`
      - Confidence: `0.96`
      - Provenance: `Doc: Fire Safety Certificate (V1), Page 1, Coordinates [0.72, 0.15, 0.76, 0.65]`
      - Deficiency Flag: *Fire Safety Certificate expired prior to commencement of academic session 2026–27 (Required: $\ge 2026-06-30$).*

---

### Step 7: Run Pre-Scrutiny Engine Using Active Regulatory Rules
- **Action:** Click **"Run Pre-Scrutiny Check"** on the workspace banner (`POST /api/v1/applications/app_9812/validate`).
- **Engine Logic:**
  - The deterministic rule engine evaluates structured fields against active rules in the Regulatory Catalog:
    - `LAND-AREA-MIN-001` (Minimum 5.0 Acres for Mega/Metro category)
    - `FIRE-NOC-VALID-001` (Valid throughout academic year)
    - `BUILDING-PLAN-APPRV-001` (Competent municipal authority seal)
    - `CADRE-RATIO-FACULTY-001` (Cadre ratio 1:2:6 for Professor:Associate:Assistant)
- **Expected Outcome:** Validation executes in $<250$ms. A new evaluation run is persisted with deterministic finding statuses: `DEFICIENCY`, `WARNING`, `COMPLIANT`.

---

### Step 8: Inspect an Evidence-Linked Finding
- **Action:** In the Findings list, click on Finding `find_0042` (*Fire NOC Expired*).
- **Expected Outcome:**
  - Rule Identifier: `REG-FIRE-2024-V1`
  - Clause Reference: AICTE APH Chapter II, Clause 2.14.3
  - Finding Severity: `DEFICIENCY` (Blocking)
  - Actionable Guidance: *"Upload a renewed Fire Safety Certificate issued by State Fire Services or a valid extension letter."*

---

### Step 9: Submit a Corrective Response & Revised Evidence
- **Action:** In the Deficiency Remediation panel:
  1. Click **"Remediate Deficiency"**.
  2. Enter applicant explanation: *"Renewed Fire NOC obtained from Directorate of Fire and Emergency Services dated 15-May-2026. Renewal certificate attached."*
  3. Upload the revised document version (V2).
  4. Click **"Save Draft"** then **"Submit Response"** (`POST /api/v1/applications/app_9812/deficiencies/find_0042/submit`).
- **Expected Outcome:** Status transitions to `SUBMITTED`. Correction submission is locked with timestamp and cryptographic file reference.

---

### Step 10: Reprocess the Revised Document
- **Action:** Trigger text extraction on Revised Fire NOC V2 (`POST /api/v1/documents/doc_fire_02/process`).
- **Expected Outcome:**
  - Document V2 extracted validity date: `2027-05-14`.
  - Provenance coordinates updated to V2 Page 1.
  - Document version history maintains both V1 and V2 in SQLite with full immutable traceability.

---

### Step 11: Revalidate and Compare Historical vs. Latest Results
- **Action:** Click **"Re-run Pre-Scrutiny"** (`POST /api/v1/applications/app_9812/validate`).
- **Expected Outcome:**
  - Finding `find_0042` transitions from `DEFICIENCY` to `RESOLVED`.
  - Pre-scrutiny compliance summary updates from *1 Deficiency, 1 Warning, 6 Compliant* to *0 Deficiencies, 1 Warning, 7 Compliant*.
  - Version comparison tab allows comparing Run #1 findings with Run #2 findings side-by-side.

---

### Step 12: Sign In as Scrutiny Committee Reviewer
- **Action:** 
  1. Click **"Sign Out"** in the top navigation.
  2. Sign in as `reviewer@reviewer.test` / `ReviewerPass123!`.
  3. The reviewer is directed to `#/reviewer/queue`.
- **Expected Outcome:**
  - Reviewer Workqueue loads with metrics: Total Queue, Assigned to Me, Under Scrutiny, Returned for Correction.
  - Applications list displays `AICTE-EOA-2026-9812` under scrutiny.

---

### Step 13: Record Reviewer Observations & Stage Decision
- **Action:**
  1. Open Case `app_9812` (`#/reviewer/scrutiny/app_9812`).
  2. Review the 8-item statutory checklist and applicant's submitted correction on Fire NOC.
  3. In the Scrutiny Remarks panel, add a formal committee observation: *"Applicant submitted renewed Fire NOC valid through May 2027. Verified against municipal issuing authority portal. Deficiency resolved satisfactorily."*
  4. Select Review Disposition: **"Pre-Scrutiny Recommended Clear"** (`PRE_SCRUTINY_RECOMMENDED_CLEAR`).
  5. Click **"Submit Stage Decision"** (`POST /api/v1/reviewer/applications/app_9812/decision`).
- **Expected Outcome:**
  - Application `review_status` updates to `RECOMMENDED_CLEAR`.
  - Immutable audit event `PRE_SCRUTINY_REVIEW_COMPLETED` written to audit log.
  - Human review decision remains strictly distinct from automated engine score.

---

### Step 14: Sign In as Administrator & Inspect Audit Timeline
- **Action:** 
  1. Sign out and sign in as `admin@platform.test` / `AdminPass123!`.
  2. Navigate to `#/admin` (Overview) and `#/admin/audit` (Audit Timeline).
- **Expected Outcome:**
  - System Overview KPI counters: Total Institutions (1), Total Applications (1), Total Users (4), Total Audit Events (15+).
  - Audit Trail table displays recent chronological events with Actor, Role, IP Address, Action, Target Entity, and Timestamp:
    - `PRE_SCRUTINY_REVIEW_COMPLETED` (Actor: `reviewer@reviewer.test`)
    - `CORRECTION_SUBMISSION` (Actor: `applicant@institution.test`)
    - `EVALUATION_RUN` (Actor: `applicant@institution.test`)
    - `DOCUMENT_UPLOADED` (Actor: `applicant@institution.test`)

---

### Step 15: Demonstrate Strict Security & Tenant Isolation
- **Action:**
  1. Sign back in as Applicant `applicant@institution.test`.
  2. In the browser address bar or developer console, attempt to access privileged reviewer/admin routes:
     - Access `#/reviewer/queue` or fetch `GET /api/v1/reviewer/queue`
     - Access `#/admin/users` or fetch `GET /api/v1/admin/users`
     - Fetch another institution's application: `GET /api/v1/applications/app_9999`
- **Expected Outcome:**
  - Frontend router redirects unauthorized roles to `#/forbidden` or `#/dashboard`.
  - Backend API returns **HTTP 403 Forbidden** for privileged endpoints (`detail: "Requires ROLE_SCRUTINY_REVIEWER or higher"`).
  - Backend API returns **HTTP 404 Not Found** for cross-institution IDOR probes, masking resource existence to prevent institutional enumeration.

---

### Step 16: Explain System Boundaries & Human-in-the-Loop Safeguards
- **Action:** Conclude demonstration with key architectural principles:
- **Narration Points:**
  1. **Decision Support, Not Automated Approval:** The system assists human experts by extracting data and flagging discrepancies. It does not replace the statutory AICTE Approval Bureau or Scrutiny Committee.
  2. **Zero Hallucination Guarantee:** Findings are linked directly to bounding boxes on physical document pages with immutable SHA-256 hashes.
  3. **Data Sovereignty:** All OCR and evaluations execute on local CPU infrastructure; zero private institutional documents are transmitted to third-party generative APIs.
  4. **Full Traceability:** Every correction, document version, evaluation run, and reviewer remark is preserved immutably.

---

## 3. Demonstration Troubleshooting & Recovery Notes

| Issue / Symptom | Root Cause | Immediate Recovery Action |
| :--- | :--- | :--- |
| Login fails with `401 Unauthorized` | Database not initialized or credentials modified | Run `python -m backend.core.seed` in terminal to restore standard test accounts. |
| Port 8000 or 3000 already in use | Stale process running from previous demo | Run `Get-Process python, node \| Stop-Process` in PowerShell and restart services. |
| Evidence Viewer displays blank PDF | Document storage file moved or unlinked | File path is linked to `data/storage/documents/`. Verify file existence; re-upload using Step 4. |
| OCR takes $>3$ seconds on low-spec laptop | CPU thread contention during first ONNX run | Subsequent OCR passes are cached or fast; digital PDFs execute in $<150$ms via `pdfplumber`. |
| Reviewer cannot recommend clearance (`HTTP 400`) | Open unresolved blocking deficiency exists | Engine enforces that all `DEFICIENCY` items must be resolved prior to `PRE_SCRUTINY_RECOMMENDED_CLEAR`. Select `RETURNED_FOR_CORRECTION` or resolve deficiencies first. |
