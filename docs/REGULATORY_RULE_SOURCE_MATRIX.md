# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Regulatory Rule Source Matrix (`REGULATORY_RULE_SOURCE_MATRIX.md`)

**Document Version:** 1.1.0  
**Phase:** Step 4 — Verified Regulatory Corrections  
**Regulatory Baseline:** AICTE Approval Process Handbook (APH 2024–2027)  
**Classification:** Regulatory Logic & Statutory Source Traceability  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal. For decision-support demonstration purposes only.*

---

## 1. Overview & Engine Principles

The platform's Deterministic Regulatory Engine evaluates extracted document fields against structured regulatory rules. All rules are persisted in the SQLite `regulatory_rules` table with strict versioning, source citations, and audit traceability.

- **Zero LLM Hallucinations:** Rule evaluations use deterministic Python conditional logic grounded directly in official AICTE Approval Process Handbook (APH 2024–2027) norms and official clarifications.
- **Explainability:** Each emitted finding provides the exact regulatory rule code, official handbook chapter/clause citation, observed value vs statutory threshold, spatial evidence anchoring, and actionable remediation guidance.
- **Governance:** Rules transition between `DRAFT` and `ACTIVE` through administrative authorization (`admin/rules`), verified via immutable audit events. Unsupported rules remain deactivated.

---

## 2. Reconciled 10-Rule Regulatory Source Matrix

| Rule ID & Version | Rule Title & Category | Official Regulatory Citation | Target Document & Extracted Fields | Programme Applicability | Status | Severity | Deterministic Condition & Evaluation Logic | Test Method & Verification Module |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RULE-EOA-LAND-001` (v1.0.0) | Adequate Built-Up Area & FSI/FAR Compliance (`LAND_NORMS`) | AICTE APH 2024–2027 Chapter II, Clause 2.14.1 & Appendix 4 Clause 4.1 | `LAND_TITLE_DEED`, `APPROVED_BUILDING_PLAN`<br>• `contiguous_land_area_acres`<br>• `lease_duration_years`<br>• `permissible_far`<br>• `sanctioned_builtup_area_sqm` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` | Evaluates that land deed/lease is valid (lease $\ge 30$ years). Where competent local authority FSI/FAR is declared, verifies that permissible built-up area accommodates instructional infrastructure. If FAR is undeclared, returns non-blocking `UNABLE_TO_EVALUATE` authority verification flag. | `test_fsi_far_land_area_compliance`<br>(`tests/backend/test_regulatory_corrections.py`) |
| `RULE-EOA-BCC-002` (v1.0.0) | Mandatory Building Completion Evidence (`MANDATORY_CERTIFICATE`) | AICTE APH 2024–2027 Chapter II, Clause 2.3.2 | `BUILDING_COMPLETION`<br>• `completion_status`<br>• `certificate_issuing_authority`<br>• `provisional_duration_years` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` | Recognises Occupancy Certificate, Completion Certificate, Building License, or Form D issued by competent municipal/planning body. Enforces strict 2-consecutive-academic-year limit for Provisional Occupancy Certificates. Rejects standalone PWD Structural Clearance as completion evidence. | `test_building_completion_alternatives_accepted`<br>(`tests/backend/test_regulatory_corrections.py`) |
| `RULE-EOA-FIRE-003` (v1.0.0) | Fire Safety Certificate Expiry & Validity (`MANDATORY_SAFETY_CERTIFICATE`) | AICTE APH 2024–2027 Chapter II, Clause 2.3.4 & NBC Part IV | `FIRE_SAFETY_NOC`<br>• `valid_until_date`<br>• `application.academic_year` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` | Compares `valid_until_date` against academic session commencement date (`2026-07-01` for AY 2026–27). If certificate expires prior to session start, emits `DEFICIENCY` requiring valid renewal. | `test_date_and_validity_check_fire_noc`<br>(`tests/backend/test_regulatory_engine.py`) |
| `RULE-EOA-STRUCT-004` (v1.0.0) | Structural Stability Certificate Verification (`MANDATORY_SAFETY_CERTIFICATE`) | AICTE APH 2024–2027 Chapter II, Clause 2.14.6 & NBC 2016 Part IV | `BUILDING_COMPLETION`, `STRUCTURAL_STABILITY`<br>• `issue_date` (BCC)<br>• `certificate_date`<br>• `engineer_registration_number`<br>• `structural_soundness_certified`<br>• `has_major_modifications` | **Conditional**: Structures $\ge 30$ years or following major structural modifications | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` (When applicable) | Enforces 30-year threshold from Building Completion Certificate issue date or major modifications. When applicable, mandates stability certification by registered structural engineer within 5-year validity. Unparseable completion dates yield non-blocking `UNABLE_TO_EVALUATE` warning. | `test_structural_stability_below_30_years_not_mandatory`<br>(`tests/backend/test_regulatory_corrections.py`) |
| `RULE-EOA-FSR-005` (v1.0.0) | Faculty-to-Student Ratio (FSR) Compliance (`FACULTY_NORMS`) | AICTE APH 2024–2027 Annexure-5, Section 5.2 | `FACULTY_ROSTER`<br>• `total_qualified_faculty_count`<br>• `application.total_intake_applied`<br>• `institution.category` | **Programme-Specific**: UG Engg 1:20, Diploma 1:25, Management/MCA 1:20, Pharmacy 1:15, Architecture 1:10 | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` | Computes ratio $\text{FSR} = \frac{\text{Enrolled Students}}{\text{Full-Time Faculty}}$. Evaluates against programme-specific statutory norms (1:20 for UG Engineering). No autonomous 1:15 overrides applied without verified source. Emits `DEFICIENCY` if ratio exceeds statutory maximum. | `test_fsr_ug_engineering_1_20_norm`<br>(`tests/backend/test_regulatory_corrections.py`) |
| `RULE-EOA-CROSS-006` (v1.0.0) | Cross-Document Survey Number Consistency (`CROSS_DOCUMENT_CONSISTENCY`) | AICTE APH 2024–2027 Chapter II, Clause 4.2 | `LAND_TITLE_DEED`, `LAND_USE_CERTIFICATE`<br>• `survey_numbers_list` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `WARNING` | Compares extracted survey/khasra numbers across statutory property records. If discrepancy exists, emits an **`ADVISORY_WARNING`** flagging the difference for Committee Reviewer verification without blocking processing. | `test_cross_document_survey_number_consistency`<br>(`tests/backend/test_regulatory_engine.py`) |
| `RULE-EOA-CROSS-007` (v1.0.0) | Sanctioned vs Completed Built-Up Area Cross-Match (`CROSS_DOCUMENT_CONSISTENCY`) | AICTE APH 2024–2027 Appendix 4, Clause 4.3 | `APPROVED_BUILDING_PLAN`, `BUILDING_COMPLETION`<br>• `sanctioned_builtup_area_sqm`<br>• `completed_builtup_area_sqm` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `WARNING` | Compares completed area against sanctioned building plan area. Emits `DEFICIENCY` if shortfall exceeds 10% tolerance; passes if within allowable variance. | `test_built_up_area_reconciled`<br>(`tests/backend/test_regulatory_engine.py`) |
| `RULE-EOA-PREV-008` (v1.0.0) | Previous Year AICTE Approval Intake Baseline (`INTAKE_RECONCILIATION`) | AICTE APH 2024–2027 Chapter II, Clause 2.1 | `PREV_AICTE_APPROVAL`<br>• `approved_total_intake`<br>• `application.total_intake_applied` | **All Programmes** | `APPROVED_FOR_PROTOTYPE_USE` (Active) | `DEFICIENCY` | Verifies that applied intake in standard EoA does not exceed previously approved intake without an accompanying expansion sanction. | `test_previous_approval_intake_baseline`<br>(`tests/backend/test_regulatory_engine.py`) |
| `RULE-DRAFT-BANK-009` (v1.0.0) | Joint Fixed Deposit (FDR) Lien Period Check (`FINANCIAL_NORMS`) | State Technical Board Bylaws (Unverified Regional Amendment) | `FINANCIAL_FDR_DEPOSIT`<br>• `lien_years` | **Technical Institutions** | `DRAFT_MISSING_OFFICIAL_SOURCE` (Inactive) | `WARNING` | Deactivated in Step 4 regulatory correction. Unimplemented evaluator and unverified statutory source. Preserved in database with inactive flag; never evaluated against live applications. | `test_unsupported_rule_bank_009_deactivated`<br>(`tests/backend/test_regulatory_corrections.py`) |
| `RULE-DRAFT-PARK-010` (v1.0.0) | Campus Parking Slot Allotment Calculation (`INFRASTRUCTURE_NORMS`) | Local Municipal Bylaws (Unverified Urban / Rural Boundary) | `CAMPUS_LAYOUT_PLAN`<br>• `parking_area_sqm` | **Technical Institutions** | `DRAFT_MISSING_OFFICIAL_SOURCE` (Inactive) | `INFO` | Draft parking norm. Bypassed during active regulatory evaluation. | `test_regulatory_rule_catalog_and_activation_lifecycle`<br>(`tests/backend/test_regulatory_engine.py`) |

---

## 3. Administrative Rule Governance & Activation Lifecycle

Rules in the platform follow a controlled lifecycle:
```
             +-----------+       Admin Activate       +------------+
             |   DRAFT   | ------------------------>  |   ACTIVE   |
             +-----------+       (POST /rules/{id})   +------------+
                   ^                                         |
                   |             Admin Deactivate            |
                   +-----------------------------------------+
```

1. **Role-Based Authorization:** Only users with `ROLE_SYSTEM_ADMIN` (`admin@platform.test`) can toggle rule activation states. Institutional applicants and Scrutiny Reviewers cannot modify rule configurations.
2. **Immutable Traceability:** Every rule state transition triggers an audit event:
   - Action: `REGULATORY_RULE_ACTIVATED` or `REGULATORY_RULE_DEACTIVATED`
   - Actor: Authenticated Administrator ID & Email
   - Metadata: Rule ID, rule code, previous state, new state, reason
3. **Execution Safety:** When `evaluate_application(app_id)` executes, it loads exclusively active approved rules (`status == "APPROVED_FOR_PROTOTYPE_USE"` and `is_active == True`). Draft rules are bypassed, ensuring experimental or unverified rules never block applicant submissions.
