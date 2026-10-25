# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Quality Assurance & Verification Strategy (`TEST_STRATEGY.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P1 — Specification & Architecture Blueprint  
**Status:** Approved Quality Assurance Baseline  
**Harness:** Pytest 9.1.1 + HTTPX AsyncClient  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Test Pyramid & Verification Levels

```
                     / \
                    /   \
                   / E2E \   <- End-to-End Scrutiny Journey Tests (Workflow)
                  /-------\
                 /  API    \ <- REST API Contracts, RBAC & Security (HTTPX)
                / Integration\
               /---------------\
              / Regulatory Rules \ <- Deterministic AICTE APH Rules Engine (Pure Logic)
             /---------------------\
            / Unit: OCR & Extractors \ <- pdfplumber / PaddleOCR / Geometry Parsers
           /---------------------------\
```

---

## 2. Mandatory 12-Scenario Verification Matrix

This matrix governs all automated integration and regression testing for the platform:

| # | Test Scenario | Input Fixture / Action | Expected Result | Target Test Module |
| :- | :--- | :--- | :--- | :--- |
| **1** | **Valid Supported Document** | Upload compliant Fire Safety NOC (valid for 12 months). | Status `PROCESSED`, validity date extracted, rule passes with 0 findings. | `test_ingestion.py` |
| **2** | **Missing Required Document** | Submit application with 7 of 8 mandatory documents (missing Land Use Cert). | Validation engine emits `DEFICIENCY`: Missing mandatory regulatory document. | `test_regulatory_rules.py` |
| **3** | **Expired Document** | Upload Fire Safety NOC with expiry date `2026-03-31` (prior to session). | Emits `DEFICIENCY` (Rule `RULE-EOA-FIRE-003`) with observed vs expected date. | `test_regulatory_rules.py` |
| **4** | **Inconsistent Cross-Record Values** | Title Deed has Sy. No. `44/2A`, Land Use Cert has Sy. No. `44/2B`. | Emits `WARNING` (Rule `RULE-EOA-CROSS-006`) highlighting survey discrepancy for committee review. | `test_regulatory_rules.py` |
| **5** | **Corrupted or Unreadable Document** | Upload zero-byte file or arbitrary text stream with `.pdf` extension. | Quality Gatekeeper rejects with HTTP 422: `INVALID_PDF_HEADER`. | `test_gatekeeper.py` |
| **6** | **Low-Confidence Extraction** | Upload blurred synthetic scan with extraction confidence $< 0.60$. | System generates `WARNING`: `LOW_EXTRACTION_CONFIDENCE`, routes to manual check. | `test_extraction.py` |
| **7** | **Duplicate Document Indicator** | Upload identical PDF with identical SHA-256 hash for two different slots. | System flags duplicate file submission warning. | `test_ingestion.py` |
| **8** | **Suspicious Metadata Indicator** | Upload PDF with creation date posterior to certificate issuance date. | Emits advisory notice in metadata inspection report. | `test_extraction.py` |
| **9** | **External Source Unavailable** | External land verification mock configured to timeout/fail. | System gracefully emits status `SOURCE_UNAVAILABLE` without crashing. | `test_connectors.py` |
| **10**| **Correction & Successful Revalidation** | Upload renewed Fire NOC `v2` for finding and trigger revalidation. | Condition clears (`CLEARED`), finding transitions to `AWAITING_REVIEW` for human reviewer handoff. | `test_deficiency_workflow.py` |
| **11**| **Unauthorized Cross-Institution Access**| Institution User 1 calls `GET /api/v1/documents/{inst2_doc_id}/file`. | System returns HTTP 404/403, preventing IDOR data leakage. | `test_security_rbac.py` |
| **12**| **Rule Version Immutability** | Update APH rule version; verify past validation run preserves original findings. | Historical validation run unchanged; new run applies updated rule version. | `test_rule_governance.py` |
| **13**| **Reviewer Scrutiny & Observations** | Reviewer assigns case, records finding observation (`ACCEPT_CORRECTION`), and completes pre-scrutiny signoff. | Review status updates, observation persisted, audit event created, automated finding preserved. | `test_reviewer_workflow.py` |
| **14**| **Administrative Provisioning & Governance** | Admin provisions user, toggles account status, attempts self-lockout, and queries audit trail. | Account created, self-lockout rejected (400), audit events logged and queryable. | `test_admin_workflow.py` |

---

## 3. Synthetic Fixture Dataset Specification

To test the platform reproducibly without handling proprietary or PII data, the test suite utilizes a synthetic document generator (`scripts/generate_synthetic_docs.py` in P2):

1. `fixtures/valid_land_deed.pdf`: Synthetic registered deed for 5.50 acres in Sy. No. 102/1, Bengaluru Urban.
2. `fixtures/valid_land_use_cert.pdf`: Matching conversion order for Sy. No. 102/1 for educational use.
3. `fixtures/mismatched_land_use_cert.pdf`: Mismatched conversion order listing Sy. No. 102/2 (triggers Scenario 4).
4. `fixtures/expired_fire_noc.pdf`: Fire certificate with expiry date in the past (triggers Scenario 3).
5. `fixtures/renewed_fire_noc_v2.pdf`: Renewed Fire certificate valid for next 2 years (triggers Scenario 10).
6. `fixtures/valid_building_completion.pdf`: BCC for 8,500 sq.m instructional built-up area.
7. `fixtures/valid_structural_stability.pdf`: Stability certificate signed by empanelled structural engineer.
8. `fixtures/valid_faculty_roster.pdf`: Tabular roster with 50 full-time faculty for 720 students (FSR 1:14.4 compliant under AICTE APH 1:15 norm for Engineering & Technology).
9. `fixtures/deficient_faculty_roster.pdf`: Tabular roster with 36 faculty for 720 students (FSR 1:20.0, non-compliant under 1:15 norm).
10. `fixtures/corrupt_header.pdf`: Broken file for gatekeeper rejection testing (triggers Scenario 5).

---

## 4. Test Execution & Automation Commands

All tests execute reproducibly in the local Python 3.13 / Node.js test environment:

```powershell
# Run the complete backend test suite (62 tests, 100% pass)
python -m pytest tests/backend/ -v

# Run individual backend verification modules:
python -m pytest tests/backend/test_e2e_journey.py -v          # Phase P10: End-to-end multi-role operational journey
python -m pytest tests/backend/test_reviewer_workflow.py -v     # Phase P9: Reviewer queue, scrutiny, observations, stage signoff, assignment
python -m pytest tests/backend/test_admin_workflow.py -v        # Phase P9: Admin metrics, user provisioning, self-lockout defense, audit log
python -m pytest tests/backend/test_deficiency_workflow.py -v   # Phase P8: Deficiency resolution lifecycle, drafts, submissions, revalidations, history
python -m pytest tests/backend/test_regulatory_engine.py -v     # Phase P7: Regulatory rule engine, APH norms, FSR, cross-matching
python -m pytest tests/backend/test_extraction_pipeline.py -v   # Phase P6: IDP digital/OCR pipeline, provenance, isolation
python -m pytest tests/backend/test_applications_workflow.py -v # EoA creation, checklist slots, uploads, removals
python -m pytest tests/backend/test_auth.py -v                  # Login, token lifecycle, /me, revocation
python -m pytest tests/backend/test_rbac.py -v                  # Anonymous, institution, reviewer, admin gates
python -m pytest tests/backend/test_isolation.py -v             # IDOR mitigation and tenant scoping
python -m pytest tests/backend/test_rate_limit.py -v            # Login lockout sliding window (HTTP 429)
python -m pytest tests/backend/test_database.py -v              # Relational schema and uniqueness constraints
python -m pytest tests/backend/test_config.py -v                # Configuration, CORS, secret protection
python -m pytest tests/backend/test_health.py -v                # Liveness and readiness dependency checks

# Run complete frontend test suite (80 tests across 8 suites: routing, design tokens, auth, applications, IDP extraction, regulatory engine, deficiency resolution, reviewer workspace & administration, WCAG 2.1 AA accessibility & performance hardening)
npm test

# Run code lint and build validation
# Note: npm run lint runs scripts/lint.js (syntax & structure check).
# npm run build runs scripts/build-check.js (static asset presence and linkage verification for vanilla JS/CSS architecture).
npm run lint
npm run build
```

---

## 5. Quantitative Evaluation Metrics

| Metric | Target Baseline | Verification Method |
| :--- | :--- | :--- |
| **Gatekeeper Detection Rate** | 100% rejection of corrupt/non-PDF files | Automated fixture test with 20 malformed payloads. |
| **Rule Engine Determinism** | 100% reproducible findings given same extracted inputs | 50 repeated runs over synthetic dataset. |
| **Tenant Isolation Enforcement** | 0% cross-tenant data leakage across all IDOR attack vectors | Pytest security suite executing 30 unauthorized ID lookups. |
| **Pipeline Latency (8 Docs)**| $\le 90$ seconds total processing time on local CPU | End-to-end benchmark run using `pytest --durations=10`. |
