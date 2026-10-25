# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Functional Specification & Product Requirements Document (`PROJECT_SPEC.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P1 — Specification & Architecture Blueprint  
**Status:** Approved Specification Baseline  
**Problem Statement:** AICTE Extension of Approval (EoA) Pre-Scrutiny & Deficiency Resolution  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Executive Summary & Problem Context

Every academic year, thousands of technical and higher-education institutions apply to the **All India Council for Technical Education (AICTE)** for **Extension of Approval (EoA)** to continue offering existing engineering, management, pharmacy, and polytechnic programmes.

### The Problem
1. **Prolonged Scrutiny Turnaround:** Institutional applications accompanied by dozens of mandatory statutory documents (Land deeds, Building Completion Certificates, Fire Safety NOCs, Structural Stability Certificates, Faculty Cadre Rosters) undergo rigorous manual scrutiny by AICTE Scrutiny Committees.
2. **Late-Stage Deficiency Notices:** Minor typographical discrepancies, expired certificates, mismatched survey numbers, or arithmetic miscalculations in faculty-to-student ratios (FSR) are often detected late in the approval cycle.
3. **Severe Operational Burden:** Late deficiency notifications lead to emergency appeals, Standing Appellate Committee (SAC) hearings, delayed academic sessions, and high administrative overhead for both institutions and AICTE officials.
4. **Lack of Evidence Anchoring:** When deficiencies are issued, institutions frequently struggle to understand exactly which page, paragraph, or calculation triggered the query, leading to generic or non-responsive resubmissions.

### The Solution: AICTE Pre-Scrutiny Platform
An AI-assisted decision-support platform designed to allow institutions to run **automated, self-service pre-scrutiny** on their EoA applications prior to final submission. The platform:
- Ingests mandatory regulatory documents securely.
- Performs automated document quality and readability pre-checks.
- Extracts structured regulatory parameters using hybrid OCR and layout parsing.
- Executes versioned, rule-based cross-matching against the official **AICTE Approval Process Handbook (APH)**.
- Surfaces an interactive **Deficiency Resolution Bridge**, allowing institutions to remediate findings with new document versions and evidence-linked clarifications.
- Provides authorised AICTE reviewers with an auditable, evidence-backed scrutiny workspace.

---

## 2. Target Users & Role Taxonomy

| Role | Primary Responsibilities | Access Constraints |
| :--- | :--- | :--- |
| **Institution Applicant** | - Create and edit institution EoA applications.<br>- Upload mandatory regulatory documents.<br>- Run pre-scrutiny checks.<br>- Review evidence-linked deficiency findings.<br>- Upload corrected document versions and trigger revalidation. | - Scoped strictly to applications belonging to their own Institution (`institution_id`).<br>- Cannot modify regulatory rules.<br>- Cannot view reviewer internal notes or other institutions' records. |
| **Authorised Reviewer** | - Access applications in the scrutiny queue.<br>- Inspect extracted fields, document evidence, and rule findings side-by-side.<br>- Record formal scrutiny observations.<br>- Accept corrections or request additional evidence.<br>- Issue formal pre-scrutiny summary reports. | - Scoped to applications assigned to the reviewer.<br>- Read-only access to institution documents (cannot alter uploaded files).<br>- Cannot approve statutory AICTE approvals (decision-support only). |
| **Administrator** | - Manage system users and institutional accounts.<br>- Maintain the Regulatory Rule Catalog (create drafts, version rules).<br>- Audit system health and immutable security audit logs. | - Cannot bypass tenant isolation to view proprietary documents without explicit audit logging.<br>- Rule activation requires formal governance check. |

---

## 3. Workflow Comparison

```
TRADITIONAL MANUAL SCRUTINY WORKFLOW:
Institution uploads 20+ PDFs -> Application Locked -> AICTE Scrutiny Committee Convenes (Weeks later)
-> Manual inspection of documents -> Deficiency Notice issued -> Institutional Appeal / SAC -> Re-inspection -> Prolonged Cycle

PROPOSED AI-ASSISTED PRE-SCRUTINY WORKFLOW:
Institution drafts EoA -> Real-time Document Quality Gatekeeper -> Dual-Mode OCR & Extraction
-> Automated Regulatory Cross-Matching -> Evidence-Backed Finding (with Page/Box Anchors)
-> Institution Self-Corrects / Uploads v2 -> Instant Revalidation -> Clean Scrutiny Package -> Authorised Reviewer Fast-Track
```

---

## 4. The Three Core Engines

```
+-----------------------------------------------------------------------------------+
|               AICTE PRE-SCRUTINY & DEFICIENCY RESOLUTION PLATFORM                 |
+-----------------------------------------------------------------------------------+
|  ENGINE A: INTELLIGENT DOCUMENT PROCESSING (IDP)                                   |
|  - File Ingestion & Magic Byte Validation                                         |
|  - Quality Gatekeeper (Resolution, Corruption, Encryption Check)                  |
|  - Dual-Path Extraction: Digital PDF Text (pdfplumber) + Scanned OCR (PaddleOCR) |
|  - Bounding Box Coordinate & Page-Level Evidence Anchoring                        |
|  - Extraction Confidence Scoring & Schema Normalisation                           |
+-----------------------------------------------------------------------------------+
                                          | (Extracted Structured Entities)
                                          v
+-----------------------------------------------------------------------------------+
|  ENGINE B: REGULATORY CROSS-MATCHING ENGINE                                       |
|  - Versioned Regulatory Rule Catalog (AICTE APH Norms)                            |
|  - Single-Document Validations (Validity, Expiry, Signatures)                     |
|  - Cross-Document Consistency (Land Title vs Land Use, Plan vs Completion Area)   |
|  - Application Field vs Document Reconciliation (Declared vs Certified)          |
|  - Structured Finding Generation with Severity, Rule ID & Explanation             |
+-----------------------------------------------------------------------------------+
                                          | (Evidence-Linked Findings)
                                          v
+-----------------------------------------------------------------------------------+
|  ENGINE C: DEFICIENCY RESOLUTION BRIDGE                                           |
|  - Institution Deficiency Dashboard (Findings grouped by severity & document)     |
|  - Side-by-Side Visual Evidence Inspector (PDF Viewer + Bounding Box Highlight)   |
|  - Targeted Remediation Workflow (Upload Document v2 to resolve specific finding)|
|  - Delta-Revalidation Engine (re-runs affected rules on updated version)          |
|  - Authorised Reviewer Scrutiny Workspace & Append-Only Audit Trail              |
+-----------------------------------------------------------------------------------+
```

---

## 5. Primary Unique Selling Proposition (USP)

> **Every finding is an evidence-anchored, auditable item connecting the exact source document version, page number, bounding box coordinates, applicable AICTE rule version, plain-language reason, and actionable remediation path.**

The system explicitly refuses to present ungrounded AI predictions as regulatory facts. If extraction confidence is low or an external registry cannot be reached, the finding is explicitly classified as `MANUAL_REVIEW_REQUIRED` rather than an unsubstantiated failure.

---

## 6. Supported Application Category & Document Types (MVP Baseline)

### Application Category
- **Extension of Approval (EoA) — Technical / Engineering & Technology UG/PG**

### Mandatory Document Catalog for EoA:
1. **Land Title Deed / Ownership Document:** Validates ownership or registered leasehold, survey/khasra numbers, contiguous area (acres/sq.m).
2. **Land Use Certificate / Conversion Order:** Validates government conversion for educational institutional use and zoning authority.
3. **Approved Building Plan:** Issued by local Municipal/Development Authority showing sanctioned instructional, administrative, and amenities carpet area.
4. **Building Completion / Occupancy Certificate (BCC / OC):** Issued by competent civil authority certifying construction completion and fitness for occupation.
5. **Fire Safety Certificate (NOC):** Issued by the State Fire Services Department certifying compliance and current validity (non-expired).
6. **Structural Stability Certificate:** Issued by a certified structural engineer certifying seismic and structural soundness.
7. **Previous Year AICTE Approval Letter:** Validates previously approved program names, intake capacity, and compliance conditions.
8. **Faculty Cadre & Roster Summary:** Tabular declaration of faculty count, cadres (Prof, Assoc Prof, Asst Prof), and student intake to compute Faculty-Student Ratio (FSR).

---

## 7. Functional Requirements (FR)

### Module 1: Ingestion & Quality Gatekeeper (Engine A)
- **FR-1:** The system shall accept PDF documents up to 15MB.
- **FR-2:** The system shall validate file integrity by inspecting file magic bytes (`%PDF-`) and reject disguised executables or unsupported file types.
- **FR-3:** The system shall detect encrypted/password-protected PDFs and prompt the user for an unencrypted version before processing.
- **FR-4:** The system shall assess page rendering resolution and warn the user if DPI is below 150 DPI, preventing unreadable scans from entering extraction.
- **FR-5:** The system shall calculate and store a SHA-256 hash for every uploaded file version to guarantee provenance and detect exact duplicates.

### Module 2: Extraction & Evidence Anchoring (Engine A)
- **FR-6:** The system shall attempt digital text extraction using embedded PDF text streams (`pdfplumber`/`pypdf`).
- **FR-7:** If digital text is sparse or absent (scanned document), the system shall automatically invoke optical character recognition (`paddleocr`) on rendered page images.
- **FR-8:** For every extracted regulatory field (e.g., Land Area, Issue Date, Validity Date, Sanctioned Area), the system shall record:
  - Document ID & Version ID
  - Page Number
  - Normalized Bounding Box Coordinates `[ymin, xmin, ymax, xmax]` (percentage of page)
  - Raw extracted text string
  - Normalized numeric/date representation
  - Extraction confidence score (0.00 to 1.00)
- **FR-9:** The system shall validate extracted values against strict Pydantic schemas.

### Module 3: Regulatory Rule Execution (Engine B)
- **FR-10:** The system shall evaluate documents against active versions of rules configured in the Regulatory Rule Catalog.
- **FR-11:** The system shall verify date validity (e.g., Fire NOC validity date $\ge$ current academic session).
- **FR-12:** The system shall perform arithmetic cross-checks (e.g., total enrolled students / total faculty $\le$ 20.0 for Engineering UG).
- **FR-13:** The system shall cross-match survey numbers between Land Title Deed and Land Use Certificate.
- **FR-14:** The system shall cross-match built-up area between Approved Building Plan and Building Completion Certificate.
- **FR-15:** The system shall generate structured `Finding` objects categorized as `DEFICIENCY` (blocking non-compliance), `WARNING` (potential discrepancy), or `INFO` (advisory).

### Module 4: Deficiency Resolution Bridge (Engine C)
- **FR-16:** The system shall present an interactive deficiency matrix to the institution user, linking each finding directly to its document evidence.
- **FR-17:** The system shall allow institution users to resolve a finding by uploading an updated document version (`v2`) accompanied by explanatory remarks.
- **FR-18:** The system shall trigger targeted revalidation upon document resubmission, updating the finding status to `RESOLVED`, `PARTIALLY_RESOLVED`, or `REFLAGGED`.
- **FR-19:** The system shall provide authorised reviewers with a split-screen scrutiny console displaying application details, findings, and live PDF page evidence with bounding box highlights.
- **FR-20:** The system shall maintain an immutable, append-only audit trail recording every state change, document upload, validation execution, and reviewer observation.

---

## 8. Non-Functional Requirements (NFR)

- **NFR-1 (Security & Data Isolation):** Complete tenant isolation. An institution shall never access or view another institution's documents or findings under any circumstance (enforced via database query scoping).
- **NFR-2 (Explainability & Grounding):** Zero black-box rejections. Every finding must display the plain-language reasoning, the official rule reference, and the specific text/coordinates in the document.
- **NFR-3 (Performance):** A standard 8-document EoA package shall complete full ingestion, OCR, and regulatory cross-matching within 90 seconds in a local development environment.
- **NFR-4 (Accessibility & UX):** UI shall conform to WCAG 2.1 AA accessibility guidelines and adhere to formal Indian e-governance aesthetic standards with high contrast and intuitive navigation.
- **NFR-5 (Auditability):** All system events must be logged with actor ID, timestamp, IP address, and payload hash.

---

## 9. Assumptions, Boundaries & Non-Goals

### Assumptions
- In the hackathon prototype, institutional records and uploaded documents are synthetic or anonymized.
- Official AICTE regulatory norms are derived from the publicly available *AICTE Approval Process Handbook (APH 2024-2027)*.

### Explicit Non-Goals
1. **Automated Regulatory Approval:** The platform **does not grant official approvals**. Final regulatory approval is strictly reserved for statutory AICTE Scrutiny Committees.
2. **Fraud Determination:** The platform **never labels an anomaly as "proven fraud"**. Discrepancies are flagged as deficiencies requiring human verification.
3. **Live Government Registry Scraping:** Live scraping of external municipal or fire department portals without sanctioned APIs is prohibited. External verification is modeled via a sandboxed/mocked connector interface.
4. **General Category Expansions:** Workflows outside the technical EoA scope (e.g., New Institute Setup, Closure of Institution, Increase in Intake) are out of scope for the MVP.
