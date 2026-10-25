# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Canonical Phase Execution Crosswalk (`PHASE_EXECUTION_CROSSWALK.md`)

**Document Version:** 1.0.0  
**Phase:** P10 — Final Stabilization, Verification, and Remediation  
**Platform Scope:** SIH Prototype — AICTE Pre-Scrutiny & Deficiency Resolution Platform  
**Classification:** Engineering Lifecycle & Delivery Traceability  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal. For decision-support demonstration purposes only.*

---

## 1. Lifecycle Overview & Canonical Phase Structure

The project was engineered through 11 disciplined sequential milestones (Phases P0 through P10), culminating in the final remediation and stabilization phase. Each phase delivered tangible, tested source code, test modules, and comprehensive documentation:

```
[P0: Environment] -> [P1: Blueprint] -> [P2: Fixtures] -> [P3: Core API/DB]
       |
       v
[P4: Design Tokens] -> [P5: EoA Workspace] -> [P6: IDP/OCR] -> [P7: Rule Engine]
       |
       v
[P8: Deficiency Bridge] -> [P9: Reviewer/Admin] -> [P10: Verification & Remediation]
```

---

## 2. Phase-by-Phase Deliverables Crosswalk

### Phase P0: Environment, Tooling & Foundation Setup
- **Objective:** Establish reproducible Python 3.11+/Node.js workspace, dependency configurations, lint scripts, and project directory structure.
- **Delivered Source Files:**
  - `requirements.txt`: Python dependencies (FastAPI, Uvicorn, SQLAlchemy, Pydantic, ReportLab, Pillow, pdfplumber, ONNX Runtime).
  - `package.json`: Node scripts (`test`, `lint`, `build`).
  - `server.js`: Node.js static file server and reverse proxy routing `/api/v1` to FastAPI on port 8000.
  - `scripts/lint.js`: JavaScript and CSS AST syntax and structure verification script.
  - `scripts/build-check.js`: Production asset integrity and linkage verification check.
- **Delivered Test Files:** Foundation verification in `tests/backend/test_health.py` and `tests/backend/test_config.py`.
- **Delivered Documentation:** `docs/ARCHITECTURE.md`, `README.md`.
- **Verification Evidence:** Environment validated on Python 3.13.15 and Node v22.23.2.

---

### Phase P1: Architectural Blueprint & Technical Specification
- **Objective:** Formalize domain models, database schema, REST API contract, security boundaries, and regulatory testing strategy.
- **Delivered Source Files:**
  - Architectural blueprints and schema specifications.
- **Delivered Documentation:**
  - `docs/ARCHITECTURE.md`: High-level system architecture, component boundaries, and data flow.
  - `docs/API_CONTRACT.md`: Full OpenAPI REST endpoint specifications and payload schemas.
  - `docs/DATABASE_SCHEMA.md`: Relational SQLite schema, foreign keys, and indexes.
  - `docs/SECURITY.md`: Threat model, OWASP Top 10 mitigations, and tenant isolation policies.
  - `docs/TEST_STRATEGY.md`: 12-scenario test matrix, pyramid levels, and quantitative metrics.
- **Verification Evidence:** Approved specification baseline governing downstream implementation.

---

### Phase P2: Synthetic Regulatory Fixtures & Mock Generators
- **Objective:** Build reproducible synthetic document generator producing realistic AICTE statutory PDF documents with spatial layout and ground-truth metadata.
- **Delivered Source Files:**
  - `backend/core/seed.py`: Seed data generator for institutions, users, rules, and mock applications.
  - Synthetic PDF generator functions utilizing ReportLab and Pillow in test suites.
- **Delivered Fixtures & Datasets:**
  - Compliant Land Title Deed, Land Use Certificate, Building Plan, Fire NOC, Building Completion, Structural Stability, Previous EoA, and Faculty Roster.
  - Edge-case fixtures: Expired Fire NOC, mismatched survey numbers, low-confidence scans, corrupt headers.
- **Verification Evidence:** Fixtures generated without PII; verified by gatekeeper and IDP pipelines.

---

### Phase P3: Core REST API, Auth, RBAC & Multi-Tenant Database
- **Objective:** Implement relational SQLite database, password hashing, JWT authentication, rate limiting, and tenant-scoped REST API endpoints.
- **Delivered Source Files:**
  - `backend/main.py`: FastAPI application entrypoint with middleware, CORS, and routers.
  - `backend/core/config.py`: Pydantic settings with RFC 6761 `.test` environment support.
  - `backend/core/database.py`: SQLAlchemy session management with SQLite WAL mode.
  - `backend/core/security.py`: Password hashing (bcrypt) and JWT encode/decode routines.
  - `backend/models/user.py`, `backend/models/institution.py`, `backend/models/audit.py`.
  - `backend/schemas/auth.py`, `backend/schemas/user.py`.
  - `backend/api/v1/auth.py`: Login, logout, `/me`, and token refresh endpoints.
  - `backend/api/v1/health.py`: Liveness and database readiness probes.
- **Delivered Test Files:**
  - `tests/backend/test_auth.py` (7 tests)
  - `tests/backend/test_rbac.py` (4 tests)
  - `tests/backend/test_isolation.py` (2 tests)
  - `tests/backend/test_rate_limit.py` (1 test)
  - `tests/backend/test_database.py` (3 tests)
  - `tests/backend/test_config.py` (3 tests)
  - `tests/backend/test_health.py` (2 tests)
- **Verification Evidence:** All 22 foundation tests passing; IDOR cross-tenant enumeration masked with HTTP 404.

---

### Phase P4: Frontend Design System, Tokens & Semantic Shell
- **Objective:** Create accessible, high-contrast vanilla CSS design system and responsive application shell adhering to WCAG 2.1 AA standards.
- **Delivered Source Files:**
  - `frontend/index.html`: Semantic single-page HTML skeleton with skip links and disclaimer banner.
  - `frontend/css/variables.css`: Design system tokens (HSL palettes, high-contrast text, focus rings, elevation).
  - `frontend/css/layout.css`: Header, navigation, container, and split-screen grid layouts.
  - `frontend/css/components.css`: Buttons, cards, modals, drawers, badges, tables, and form inputs.
  - `frontend/js/app.js`: Main router, state initialization, and component mounting.
  - `frontend/js/state.js`: Client-side state manager and authenticated session handler.
  - `frontend/js/api.js`: Unified HTTP client handling Bearer tokens and error propagation.
  - `frontend/js/views/login.js`: Accessible login form with synthetic demo credential drawer.
  - `frontend/js/views/dashboard.js`: Role-aware operational overview dashboard.
- **Delivered Test Files:**
  - `tests/auth_frontend.test.js` (7 subtests)
  - `tests/accessibility_perf.test.js` (21 subtests)
- **Delivered Documentation:** `docs/UX_AND_NAVIGATION.md`.
- **Verification Evidence:** Zero contrast violations; fully navigable via keyboard Tab/Enter controls.

---

### Phase P5: Institutional EoA Workspace & 8-Document Statutory Checklist
- **Objective:** Implement complete Extension of Approval application workflow and 8-slot statutory document upload architecture with magic-byte gatekeeper.
- **Delivered Source Files:**
  - `backend/models/application.py`: Application entity and document checklist slot state.
  - `backend/models/document.py`: Document metadata, versioning, SHA-256 hashes, storage paths.
  - `backend/api/v1/applications.py`: Application creation, checklist query, secure upload, download, and deletion.
  - `frontend/js/views/applications-list.js`: Active applications registry view.
  - `frontend/js/views/application-detail.js`: 8-document statutory checklist workspace with status indicators.
  - `frontend/js/views/application-new.js`: Application submission modal.
- **Delivered Test Files:**
  - `tests/backend/test_applications_workflow.py` (9 tests)
  - `tests/applications_frontend.test.js` (8 subtests)
- **Verification Evidence:** Secure upload validates `%PDF-` magic bytes; non-PDF rejected with HTTP 422.

---

### Phase P6: Intelligent Document Processing (IDP), Hybrid OCR & Spatial Provenance
- **Objective:** Deliver hybrid document extraction engine supporting digital text extraction (`pdfplumber`) and local CPU ONNX OCR (PaddleOCR v6), persisting spatial bounding boxes for explainability.
- **Delivered Source Files:**
  - `backend/models/extraction.py`: `DocumentProcessingRun`, `ExtractedField`, and `DocumentPage` entities.
  - `backend/services/extraction_service.py`: Pipeline coordinator routing pages to digital text or OCR.
  - `backend/services/ocr_engine.py`: Local CPU ONNX inference wrapper computing normalized coordinates `[ymin, xmin, ymax, xmax]`.
  - `backend/api/v1/documents.py`: Document processing trigger, processing runs, extracted fields, and page coordinates.
  - `frontend/js/views/evidence-inspector.js`: Split-screen evidence inspector rendering visual bounding boxes over document pages.
- **Delivered Test Files:**
  - `tests/backend/test_extraction_pipeline.py` (6 tests, including real scanned OCR)
  - `tests/extraction_frontend.test.js` (6 subtests)
- **Verification Evidence:** Real scanned PDF OCR verified on CPU; zero hallucinated provenance.

---

### Phase P7: Deterministic Regulatory Rules Engine & Explainable Findings
- **Objective:** Build deterministic AICTE regulatory engine evaluating extracted document fields against APH 2024–2027 norms, generating structured findings with handbook citations.
- **Delivered Source Files:**
  - `backend/models/regulatory.py`: `RegulatoryRule` and `EvaluationRun` entities.
  - `backend/models/finding.py`: `DeficiencyFinding` entity with severity levels.
  - `backend/services/regulatory_engine.py`: Deterministic rule evaluator with 10 seed rules (8 active, 2 draft). Includes corrected FSR 1:15 norm and survey discrepancy WARNING severity.
  - `backend/api/v1/regulatory.py`: Evaluation trigger, findings queries, and rule catalog governance endpoints.
  - `frontend/js/views/admin-rules.js`: Administrative rule catalog browser and activation console.
- **Delivered Test Files:**
  - `tests/backend/test_regulatory_engine.py` (7 tests)
  - `tests/regulatory_frontend.test.js` (10 subtests)
- **Delivered Documentation:** `docs/REGULATORY_RULE_CATALOG.md`, `docs/REGULATORY_RULE_SOURCE_MATRIX.md`.
- **Verification Evidence:** Sub-second evaluation ($< 250$ms); 100% deterministic outputs across identical inputs.

---

### Phase P8: Deficiency Resolution Bridge, Corrections & Controlled Revalidation
- **Objective:** Implement applicant remediation workspace allowing deficiency acknowledgement, draft responses, revised document uploads, and before-vs-after delta comparison.
- **Delivered Source Files:**
  - `backend/models/deficiency.py`: `CorrectionSubmission` and `FindingHistory` entities.
  - `backend/api/v1/deficiencies.py`: Acknowledge, draft, submit correction, and revalidation endpoints.
  - `frontend/js/views/deficiency-bridge.js`: Interactive deficiency resolution console with delta revalidation modal.
- **Delivered Test Files:**
  - `tests/backend/test_deficiency_workflow.py` (6 tests)
  - `tests/deficiency_frontend.test.js` (10 subtests)
- **Verification Evidence:** Controlled revalidation demonstrates condition transitions (`CLEARED` vs `PERSISTS`) with immutable historical audit trail.

---

### Phase P9: Committee Reviewer Scrutiny Console & Administrative Governance
- **Objective:** Build multi-role operational consoles: Reviewer scrutiny queue with stage recommendations, and Admin governance console with user provisioning, self-lockout defense, and forensic audit timeline.
- **Delivered Source Files:**
  - `backend/api/v1/reviewer.py`: Reviewer queue metrics, case assignment, observations, and stage decision endpoints.
  - `backend/api/v1/admin.py`: System overview KPIs, user provisioning, active status toggles, and audit log query endpoints.
  - `frontend/js/views/reviewer-queue.js`: Reviewer workqueue with interactive filter chips.
  - `frontend/js/views/reviewer-scrutiny.js`: Detailed scrutiny case file with observation logging.
  - `frontend/js/views/admin-overview.js`: Platform KPI metrics overview.
  - `frontend/js/views/admin-users.js`: User governance directory with self-lockout protection.
  - `frontend/js/views/admin-audit.js`: Append-only forensic audit trail timeline.
- **Delivered Test Files:**
  - `tests/backend/test_reviewer_workflow.py` (5 tests)
  - `tests/backend/test_admin_workflow.py` (6 tests)
  - `tests/reviewer_admin_frontend.test.js` (11 subtests)
- **Verification Evidence:** Strict RBAC boundary enforced; committee observations preserved independently from automated scores.

---

### Phase P10: End-to-End System Verification, Security Hardening & Final Remediation
- **Objective:** End-to-end multi-role journey verification, synthetic identity normalization (RFC 6761 `.test`), audit immutability hardening, regulatory accuracy corrections, and final demo freeze.
- **Delivered Source Files & Remediation Fixes:**
  - `backend/core/config.py`, `backend/schemas/auth.py`, `backend/schemas/user.py`: Added RFC 6761 `.test` domain support.
  - `backend/core/seed.py`: Updated synthetic demo accounts to `.test` domains with safe upsert logic.
  - `backend/services/regulatory_engine.py`: Corrected FSR norm to 1:15 with Engineering & Tech category guard; updated survey consistency check to `WARNING` severity.
  - `backend/api/v1/admin.py`: Audited append-only protection at API layer.
  - All backend and frontend test files: Aligned with `.test` accounts and regulatory corrections.
- **Delivered Test Files:**
  - `tests/backend/test_e2e_journey.py` (1 test covering complete 3-role lifecycle)
  - Complete 62-test backend suite and 80-test frontend suite verified passing (142/142 tests).
- **Delivered Documentation:**
  - `docs/DEMO_SCRIPT.md` (Updated)
  - `docs/DEMO_RUNBOOK.md` (Updated)
  - `docs/TEST_STRATEGY.md` (Updated)
  - `docs/REGULATORY_DOCUMENT_REQUIREMENTS.md` (New)
  - `docs/REGULATORY_RULE_SOURCE_MATRIX.md` (New)
  - `docs/TEST_RESULTS_RECONCILIATION.md` (New)
  - `docs/PHASE_EXECUTION_CROSSWALK.md` (New)
  - `docs/P10_REMEDIATION_REPORT.md` (New)
- **Verification Evidence:** 100% test pass rate, verified build readiness, WCAG 2.1 AA accessibility compliance.
