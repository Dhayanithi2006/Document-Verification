# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## UI/UX & Information Architecture Specification (`UX_AND_NAVIGATION.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P1 — Specification & Architecture Blueprint  
**Status:** Approved UI/UX Baseline  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Design Philosophy & Government E-Governance Aesthetics

The user interface is designed to emulate the dignity, clarity, and authority of official Indian national digital infrastructure (such as DigiLocker, Parivahan, and the National Academic Depository), while providing the responsiveness, micro-animations, and data density expected of a state-of-the-art decision-support system.

### Core Visual Principles
1. **Official Indian E-Governance Color Palette:**
   - **Primary Navy:** `#0A2540` / `#0E1E38` (Conveys trust, institutional stability, and authority).
   - **Ashoka Blue:** `#1A56DB` (Primary interactive buttons, focused states, and key navigational highlights).
   - **Tricolor Saffron Accent:** `#FF9933` (Warning banners, deficiency indicators, and pending action markers).
   - **India Green Accent:** `#138808` / `#059669` (Compliance verified badges, successful validation chips).
   - **Neutral Background:** `#F8FAFC` / Surface White `#FFFFFF` with slate borders `#E2E8F0`.
2. **Typography:**
   - Primary Font Family: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, sans-serif.
   - Clean, tabular numbers (`font-variant-numeric: tabular-nums`) for dates, survey numbers, land areas, and ratios.
3. **Mandatory Disclaimer Banner:**
   A persistent, high-visibility banner rendered across the very top of every screen:
   > **⚠️ SIH PROTOTYPE — NOT AN OFFICIAL AICTE PORTAL. For demonstration and decision-support simulation purposes only.**

---

## 2. Page Inventory & Role Access Matrix

| Route URL | Page Title / Component | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `/login` | Authentication Portal | Public | Real backend authentication with email, password, visibility toggle, synthetic demo drawer, and returnTo redirect preservation. |
| `/dashboard` | Institution Home | `INSTITUTION`, `REVIEWER`, `ADMIN` | Role-aware dashboard: active applications, overall deficiency health, deadline countdown. |
| `/applications/new` | Start EoA Application | `INSTITUTION` | Wizard to create a new academic year Extension of Approval draft. Restricted to applicants. |
| `/applications/{id}` | Application Workspace | `INSTITUTION`, `REVIEWER`, `ADMIN` | 8-document checklist, upload dropzones, processing progress bars (tenant-isolated). |
| `/applications/{id}/evidence/{finding_id}` | Split-Screen Evidence Inspector | `INSTITUTION`, `REVIEWER`, `ADMIN` | Primary USP: Left pane displays finding & rule details; right pane renders PDF with bounding box overlay. |
| `/applications/{id}/deficiencies` | Deficiency Resolution Bridge | `INSTITUTION` | Filterable matrix of deficiencies with "Upload Corrected Version" action. |
| `/reviewer/queue` | Scrutiny Review Queue | `REVIEWER`, `ADMIN` | Filterable list of applications pending scrutiny (`Deficiencies`, `Revalidated`, `Clean`). |
| `/reviewer/scrutiny/{id}`| Reviewer Scrutiny Console | `REVIEWER`, `ADMIN` | Formal verification console with observation recording, acceptance, or objection actions. |
| `/admin/rules` | Rule Governance Catalog | `ADMIN`, `REVIEWER`, `INSTITUTION` | AICTE APH Rule Catalog manager: view rule versions, test rules, and toggle active status. |
| `/admin/users` | User Governance Directory | `ADMIN` | Account management, role assignment, active status toggle, and account provisioning modal. |
| `/admin/audit` | System Audit Log | `ADMIN`, `REVIEWER` | Tamper-evident, filterable timeline of all uploads, validations, and decisions. |
| *Route Guard* | **403 Access Denied View** | Authenticated | Displayed when an authenticated user navigates to an unauthorized route (e.g. Institution Applicant opening reviewer queue). Includes safe return button. |

### 2.1 Route Guard & Session Lifecycle Policy
1. **Unauthenticated Access:** Direct access to protected routes redirects to `#/login?returnTo=<encoded_path>`. Only safe relative paths starting with `/` (no protocol-relative `//` or external domains) are accepted as return destinations.
2. **Authenticated Access:** If an authenticated user visits `#/login`, they are automatically redirected to their role-appropriate default landing workspace (`INSTITUTION` -> `#/dashboard`, `REVIEWER` -> `#/reviewer/queue`, `ADMIN` -> `#/admin/rules`).
3. **Session Expiry:** A `401 Unauthorized` response on any authenticated route triggers instantaneous token revocation, sessionStorage cleanup, and redirection to `#/login` with an informative session-expired alert.
4. **Role Isolation:** Attempts by an `INSTITUTION` user to access reviewer-only or admin-only routes trigger the dedicated **403 Access Denied** view without exposing inaccessible resource metadata.

---

## 3. Detailed Wireframe & Screen Layouts

### 3.1 Institution Application Workspace (`/applications/{id}`)
```
+----------------------------------------------------------------------------------------------------+
| ⚠️ SIH PROTOTYPE — NOT AN OFFICIAL AICTE PORTAL                                       [User: Inst1] |
+----------------------------------------------------------------------------------------------------+
| AICTE Pre-Scrutiny Platform | [Dashboard] [My Applications] [Rules Reference]                      |
+----------------------------------------------------------------------------------------------------+
| Application #AICTE-EOA-2026-9812  | Status: [FINDINGS_AVAILABLE] | Pre-Scrutiny Score: 78%        |
| Institution: National Institute of Technology & Management | Session: 2026-2027                    |
+----------------------------------------------------------------------------------------------------+
| MANDATORY DOCUMENT CHECKLIST (8 Items)                      | SUMMARY ACTION PANEL                 |
| ----------------------------------------------------------- | ------------------------------------ |
| [✓] 1. Land Title Deed (v1)          [PROCESSED] [View Doc] | Total Documents: 8 / 8 Uploaded      |
| [!] 2. Land Use Certificate (v1)     [PROCESSED] [1 Finding]| Deficiencies: 2 Blocking             |
| [✓] 3. Approved Building Plan (v1)   [PROCESSED] [View Doc] | Warnings:     1 Advisory             |
| [!] 4. Building Completion (v1)      [PROCESSED] [1 Finding]| Compliant:    5 Passed               |
| [!] 5. Fire Safety NOC (v1)          [PROCESSED] [EXPIRED]  |                                      |
| [✓] 6. Structural Stability (v1)     [PROCESSED] [View Doc] | [RUN PRE-SCRUTINY VALIDATION]        |
| [✓] 7. Prev Year AICTE Approval (v1) [PROCESSED] [View Doc] | [OPEN DEFICIENCY RESOLUTION BRIDGE]  |
| [✓] 8. Faculty Cadre Roster (v1)     [PROCESSED] [View Doc] |                                      |
+----------------------------------------------------------------------------------------------------+
```

### 3.2 Primary USP: Split-Screen Evidence Inspector (`/applications/{id}/evidence/{finding_id}`)
```
+----------------------------------------------------------------------------------------------------+
| FINDING DETAILS (Left Pane - 40% Width)       | DOCUMENT EVIDENCE (Right Pane - 60% Width)         |
| --------------------------------------------- | -------------------------------------------------- |
| Finding ID: FIND-2026-0042                    | Document: Land_Use_Certificate_2026.pdf (Page 2/4) |
| Severity:   [CRITICAL DEFICIENCY]             | Zoom: [ - ] 100% [ + ]  [Rotate] [Download Original]|
| Rule Code:  RULE-EOA-CROSS-006 (v1.0)         | -------------------------------------------------- |
| Rule Title: Land Deed vs Land Use Survey No.  | +------------------------------------------------+ |
|                                               | | ...certified that land bearing survey details  | |
| EXPLANATION:                                  | | as listed below is approved for institutional: | |
| Survey Number in Land Use Certificate         | |                                                | |
| ('Sy. No. 44/2B') does not match declared     | | +--------------------------------------------+ | |
| Title Deed survey number ('Sy. No. 44/2A').   | | | Survey No: 44/2B   [BOUNDING BOX HIGHLIGHT]| | |
|                                               | | +--------------------------------------------+ | |
| EXTRACTED VALUES:                             | | Extent: 5.20 Acres                             | |
| - Title Deed Survey: '44/2A' (Doc #1, Pg 1)   | | District: Bengaluru Urban                      | |
| - Land Use Survey:   '44/2B' (Doc #2, Pg 2)   | +------------------------------------------------+ |
| - Extraction Confidence: 94.8%                |                                                    |
|                                               | OCR Provenance:                                    |
| RECOMMENDED ACTION:                           | Extracted via: PaddleOCR Hybrid Engine             |
| Upload corrected Land Use Endorsement         | Page Coords: ymin=0.42, xmin=0.18, ymax=0.46...    |
| or registered survey rectification deed.      |                                                    |
|                                               | [ SUBMIT CORRECTED VERSION (v2) ]                  |
+----------------------------------------------------------------------------------------------------+
```

### 3.3 Deficiency Resolution Bridge (`/applications/{id}/deficiencies` or `.../deficiency-bridge`)
```
+----------------------------------------------------------------------------------------------------+
| DEFICIENCY RESOLUTION & REVALIDATION WORKSPACE                                                     |
| Track, acknowledge, remediate, and revalidate compliance findings before human scrutiny.           |
+----------------------------------------------------------------------------------------------------+
| SUMMARY METRICS: [Total: 3] [Acknowledged: 2] [Drafts: 1] [Submitted: 1] [Awaiting Review: 1]     |
| ACTIONS:         [Trigger Controlled Revalidation (P7 Engine)] [Refresh Workspace]                 |
+----------------------------------------------------------------------------------------------------+
| Finding | Target Document | Rule & Description | Status      | Actions                             |
| ------- | --------------- | ------------------ | ----------- | ----------------------------------- |
| #0042   | Land Use Cert   | RULE-EOA-CROSS-006 | IN_PROGRESS | [Acknowledge] [Response Console]    |
|         |                 | Survey Mismatch    |             | [Timeline History] [View Evidence]  |
| #0043   | Fire Safety NOC | RULE-EOA-FIRE-003  | AWAITING_   | [Response Console] [Timeline]       |
|         |                 | Expired NOC (v1)   | REVIEW      | [Latest Revalidation Delta: CLEARED]|
| #0044   | Faculty Roster  | RULE-EOA-FSR-005   | ACKNOWLEDGED| [Acknowledge (Done)] [Respond]      |
+----------------------------------------------------------------------------------------------------+
```
#### Interactive Components in P8:
1. **Interactive Metrics Strip:** Real-time counts reflecting database-persisted statuses (Total, Acknowledged, In Progress, Submitted, Awaiting Review, Resolved).
2. **Response Console Modal:** Interactive drawer allowing applicant to:
   - Select response category (`DOCUMENT_CORRECTION`, `OFFICIAL_CLARIFICATION`, `GOVERNMENT_EXEMPTION`, `OTHER`).
   - Enter detailed justification remarks.
   - Attach or upload replacement document versions (`v2`, `v3`) via secure P5 multipart upload.
   - Save draft without submitting (`Save Draft`) or formally lock and submit (`Submit Correction`).
3. **Chronological Timeline History Modal:** Complete auditable timeline listing finding detection, applicant acknowledgement, draft updates, formal submissions, and revalidation outcomes with UTC timestamps.
4. **Revalidation Delta Modal:** Side-by-side comparison of previous findings vs revalidation findings (`CLEARED`, `PERSISTS`, `NEW`) and explicit human reviewer handoff status (`PENDING_REVIEW`).

### 3.4 Reviewer Scrutiny Console (`/reviewer/queue` and `/reviewer/scrutiny/{id}`)
```
+----------------------------------------------------------------------------------------------------+
| ⚠️ SIH PROTOTYPE — NOT AN OFFICIAL AICTE PORTAL                             [User: Dr. Narayanan]  |
+----------------------------------------------------------------------------------------------------+
| AICTE Pre-Scrutiny Platform | [Scrutiny Queue] [Audit Stream] [Rule Catalog]                      |
+----------------------------------------------------------------------------------------------------+
| SCRUTINY WORKQUEUE & CASE DISPATCH                                                                |
| Real-Time Queue Metrics:                                                                           |
| [Awaiting Scrutiny: 1] [Assigned to Me: 1] [Under Scrutiny: 1] [Recommended Clear: 0]             |
|                                                                                                    |
| Filter Chips: [All Cases] [Assigned to Me] [Unassigned] [Under Scrutiny] [Recommended Clear]      |
| Search: [Filter by College Name or Application No...]                                             |
+----------------------------------------------------------------------------------------------------+
| App Reference    | Institution Name         | Academic Year | Status     | Review Status  | Action |
| ---------------- | ------------------------ | ------------- | ---------- | -------------- | ------ |
| AICTE-EOA-2026-9 | Apex Institute of Tech   | 2026-2027     | SUBMITTED  | UNDER_SCRUTINY | [Open] |
+----------------------------------------------------------------------------------------------------+
```
#### Scrutiny Case Details (`/reviewer/scrutiny/{id}`):
- **Case Summary:** Application reference, academic year, institutional category, state, rural/urban indicator, current assigned reviewer, and review stage badge.
- **Statutory Document Checklist:** All 8 mandatory checklist slots with version number, validation state, file size, and secure document viewer trigger.
- **Evidence-Anchored Findings:** Findings list displaying rule code, severity, condition explanation, spatial bounding boxes, and applicant-uploaded evidence references.
- **P8 Correction Responses & Delta Assessment:** Displays applicant response text, category, attached replacement document version, and automated revalidation status (`CLEARED` vs `PERSISTS`).
- **Interactive Scrutiny Observation Form:** Record finding-level dispositions (`CONCUR_DEFICIENCY`, `ACCEPT_CORRECTION`, `OVERRULE_DEFICIENCY`, `REQUIRE_ADDITIONAL_EVIDENCE`) with mandatory justification.
- **Pre-Scrutiny Stage Recommendation Form:** Formal committee recommendation (`PRE_SCRUTINY_RECOMMENDED_CLEAR`, `RETURNED_FOR_CORRECTION`, `FURTHER_REVIEW_REQUIRED`) with overall remarks.
- **Observation History Stream:** Immutable chronological timeline of reviewer observations, timestamps, and justifications.

### 3.5 Administrative User Governance (`/admin/users`)
```
+----------------------------------------------------------------------------------------------------+
| USER & IDENTITY GOVERNANCE DIRECTORY                                        [User: Administrator]  |
| Authorised user provisioning, role configuration, and active account lifecycle management.          |
+----------------------------------------------------------------------------------------------------+
| Actions: [+ Provision New User Account]                                                            |
| Directory Table:                                                                                   |
| Full Name        | Email                     | Role        | Institution     | Status   | Actions  |
| ---------------- | ------------------------- | ----------- | --------------- | -------- | -------- |
| System Admin     | admin@platform.test       | ADMIN       | Platform Global | ACTIVE   | [Self]   |
| Dr. V. Narayanan | reviewer@reviewer.test    | REVIEWER    | Committee Scope | ACTIVE   | [Toggle] |
| Dr. R. K. Sharma | applicant@institution.test| INSTITUTION | Apex Inst (01)  | ACTIVE   | [Toggle] |
+----------------------------------------------------------------------------------------------------+
```
- **Self-Lockout Protection:** Admins cannot deactivate their own active account.
- **Provisioning Modal:** Secure dialog prompting Full Name, Email, Role, Password, and Institution linkage with bcrypt hashing on backend.

---

## 4. Interaction States & Visual Feedback

### 4.1 Loading States
- **Document Upload:** Displays real-time progress bar with percentage, transfer speed, and instantaneous SHA-256 hash generation indicator.
- **OCR Ingestion:** Displays an animated pulsing badge: `[PROCESSING OCR - Page 1 of 4...]`.
- **Validation Run:** Displays a 3-step progress stepper:
  `[Step 1: Reading Schemas] -> [Step 2: Cross-Matching Rules] -> [Step 3: Generating Evidence Findings]`.

### 4.2 Empty States
- **No Applications:** Displays an informative welcome card with an illustration and a primary call-to-action: `[Start Your First EoA Pre-Scrutiny Application]`.
- **Zero Deficiencies:** Displays a prominent green verification card:
  `🎉 Congratulations! All 8 mandatory documents meet AICTE APH 2024-2027 norms. Zero blocking deficiencies found.`

### 4.3 Error States
- **Corrupt File:** Modal dialog with diagnostic guidance:
  `❌ Invalid PDF Stream: File header does not match %PDF-. Please ensure file is not password-protected or corrupted.`
- **Access Denied (403):** Clean institutional warning banner:
  `🔒 Access Restricted: You do not have permission to view applications belonging to other institutions.`

---

## 5. Accessibility & Responsive Standards

- **Keyboard Navigation:** Full tab-order navigation across all interactive elements, modal traps, and split-screen drawers.
- **Color Contrast:** All text elements maintain a minimum contrast ratio of `4.8:1` against their backgrounds (exceeding WCAG AA requirements).
- **Responsive Layout:** Responsive down to 1024px desktop/tablet displays. On compact screens, the split-screen Evidence Inspector collapses into a tabbed toggle: `[View Details]` / `[View PDF Evidence]`.
