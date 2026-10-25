# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Regulatory Rule Catalog & Governance Specification (`REGULATORY_RULE_CATALOG.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P1 — Specification & Architecture Blueprint  
**Status:** Approved Catalog Baseline  
**Official Reference:** AICTE Approval Process Handbook (APH 2024-2027)  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Rule Governance Framework & Approval Lifecycle

The platform enforces strict regulatory integrity:
- **No Invented Thresholds:** All active rule thresholds must cite verifiable clauses from the official *AICTE Approval Process Handbook (APH 2024-2027)*.
- **Explicit Rule Status Taxonomy:**
  - `APPROVED_FOR_PROTOTYPE_USE`: Backed by verified official APH clause and tested against synthetic fixtures.
  - `DRAFT_MISSING_OFFICIAL_SOURCE`: Pending verification of specific state/regional amendment. Cannot trigger blocking deficiencies.
  - `RESEARCH_REQUIRED`: Under analysis by regulatory subject matter experts.
  - `RETIRED`: Deprecated due to updated annual APH editions.
- **Rule Immutability & Versioning:** When an APH norm changes, existing rule definitions are never edited in place. A new `RegulatoryRuleVersion` is published, preserving historical validation runs.

```mermaid
graph LR
    Draft["DRAFT (Missing Source)"] -->|Verify APH Clause| Research["RESEARCH REQUIRED"]
    Research -->|Pass Synthetic Unit Tests| Tested["TESTED"]
    Tested -->|Admin Approval| Approved["APPROVED FOR PROTOTYPE USE"]
    Approved -->|APH Update| Retired["RETIRED"]
```

---

## 2. Active Regulatory Rule Catalog (EoA Workflow)

### 2.1 `RULE-EOA-LAND-001`: Minimum Contiguous Land Area
- **Title:** Minimum Contiguous Land Requirement for Engineering & Technology Institutions
- **Official Source:** AICTE APH 2024-2027, Appendix 4 (Norms for Land and Built-up Area), Clause 4.1.
- **Category:** `LAND_NORMS`
- **Applicability:** Category: `ENGINEERING_TECHNOLOGY`, Under-Graduate programmes.
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `LAND_TITLE_DEED` (Field: `contiguous_land_area_acres`)
  - Application Context: `institution.is_rural` (Boolean: Urban/Metro vs Rural)
- **Validation Logic:**
  ```python
  required_land = 4.0 if is_rural else 2.5  # APH Appendix 4.1: Rural=4.0 Acres, Urban/Metro=2.5 Acres
  if observed_land_acres < required_land:
      emit_finding(
          severity="DEFICIENCY",
          expected=f">= {required_land} Acres",
          observed=f"{observed_land_acres} Acres",
          explanation="Contiguous land area is below the minimum mandatory AICTE norm for this location."
      )
  ```
- **Recommended Action:** Provide registered title deed for contiguous land meeting the required acreage or apply under mega-city relaxation provisions.

---

### 2.2 `RULE-EOA-BCC-002`: Building Completion / Occupancy Certificate Mandatory Check
- **Title:** Mandatory Building Completion / Occupancy Certificate (BCC / OC)
- **Official Source:** AICTE APH 2024-2027, Chapter II, Clause 2.3.2 (Mandatory Statutory Documents).
- **Category:** `MANDATORY_CERTIFICATE`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `BUILDING_COMPLETION` (Field: `certificate_issuing_authority`, `completion_status`)
- **Validation Logic:**
  - Verify that the issuing authority is a competent municipal, development authority, or town planning body.
  - Verify that the certificate certifies full or sanctioned instructional phase completion.
- **Severity:** `DEFICIENCY` (Blocking).
- **Recommended Action:** Upload Building Completion or Occupancy Certificate issued by the competent town planning or municipal corporation.

---

### 2.3 `RULE-EOA-FIRE-003`: Fire Safety Certificate (NOC) Current Validity
- **Title:** Fire Safety Certificate (NOC) Validity Period Check
- **Official Source:** AICTE APH 2024-2027, Clause 2.3.4 & National Building Code (NBC) Part IV.
- **Category:** `MANDATORY_SAFETY_CERTIFICATE`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `FIRE_SAFETY_NOC` (Field: `valid_until_date`)
  - Application Context: `academic_session_start` (e.g. `2026-07-01`)
- **Validation Logic:**
  ```python
  if fire_noc_expiry_date < academic_session_start_date:
      emit_finding(
          severity="DEFICIENCY",
          expected=f"Valid on or after {academic_session_start_date}",
          observed=f"Expired on {fire_noc_expiry_date}",
          explanation="The Fire Safety Certificate has expired or expires prior to the academic session."
      )
  ```
- **Recommended Action:** Upload renewed Fire Safety NOC or formal extension letter from State Fire Services Department.

---

### 2.4 `RULE-EOA-STRUCT-004`: Structural Stability Certificate Verification
- **Title:** Structural Stability Certificate Certification by Empanelled Engineer
- **Official Source:** AICTE APH 2024-2027, Chapter II, Clause 2.3.5.
- **Category:** `MANDATORY_SAFETY_CERTIFICATE`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `STRUCTURAL_STABILITY` (Fields: `engineer_registration_number`, `structural_soundness_certified`)
- **Validation Logic:**
  - Check presence of structural engineer license/registration number and explicit affirmative stability declaration.
- **Severity:** `DEFICIENCY`.
- **Recommended Action:** Submit certificate bearing registration number of structural engineer empanelled with municipal/government body.

---

### 2.5 `RULE-EOA-FSR-005`: Faculty-to-Student Ratio (FSR) Compliance
- **Title:** Mandatory Faculty-to-Student Ratio for Engineering UG Programs (1:15 Norm)
- **Official Source:** AICTE APH 2024-2027, Annexure-5 (Norms for Faculty Requirements and Cadre Ratio), Table 5.1.
- **Category:** `FACULTY_NORMS`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `FACULTY_ROSTER` (Field: `total_qualified_faculty_count`)
  - Application Context: `total_enrolled_intake` (e.g. 720 students)
  - Institution Category: `ENGINEERING_TECHNOLOGY` (category applicability guard: other categories evaluated under distinct statutory ratios)
- **Validation Logic:**
  ```python
  computed_fsr = total_enrolled_intake / total_qualified_faculty_count
  max_allowed_fsr = 15.0  # APH Annexure-5 Table 5.1: 1:15 ratio for Under-Graduate Engineering & Technology
  if computed_fsr > max_allowed_fsr:
      emit_finding(
          severity="DEFICIENCY",
          expected=f"Ratio <= 1:15.0 (Min {math.ceil(total_enrolled_intake/15)} faculty)",
          observed=f"Ratio 1:{computed_fsr:.1f} ({total_qualified_faculty_count} faculty)",
          explanation="Faculty count is inadequate for the applied student intake under AICTE APH Annexure-5 Table 5.1 (1:15 UG Engineering norm)."
      )
  ```
- **Recommended Action:** Provide updated faculty roster with approved faculty selections or adjust intake request.

---

### 2.6 `RULE-EOA-CROSS-006`: Land Title Deed vs Land Use Certificate Survey Match
- **Title:** Cross-Document Survey / Khasra Number Consistency Check
- **Official Source:** AICTE APH 2024-2027, Clause 4.2.
- **Category:** `CROSS_DOCUMENT_CONSISTENCY`
- **Rule Version:** 1.0.0
- **Severity:** `WARNING`
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document 1: `LAND_TITLE_DEED` (Field: `survey_numbers_list`)
  - Document 2: `LAND_USE_CERTIFICATE` (Field: `survey_numbers_list`)
- **Validation Logic:**
  ```python
  title_surveys = set(normalize_surveys(title_deed_surveys))
  land_use_surveys = set(normalize_surveys(land_use_cert_surveys))
  if not title_surveys.issubset(land_use_surveys):
      mismatched = title_surveys - land_use_surveys
      emit_finding(
          severity="WARNING",
          outcome="ADVISORY_WARNING",
          title="Survey Number Consistency Check — Discrepancy Flagged for Review",
          expected=f"Land use conversion covering survey numbers: {title_surveys}",
          observed=f"Land use conversion covers: {land_use_surveys}. Unmatched: {mismatched}",
          explanation="Consistency check: Survey numbers listed in Land Title Deed do not match Land Use Conversion Certificate. Flagged for committee scrutiny to verify whether an updated conversion order or clerical variance applies."
      )
  ```
- **Recommended Action:** Verify survey numbers across land records during committee scrutiny to determine if supplemental conversion orders or revenue entries cover the parcels.

---

### 2.7 `RULE-EOA-CROSS-007`: Approved Building Plan vs Completion Built-Up Area
- **Title:** Sanctioned Built-Up Area vs Completed Built-Up Area Cross-Match
- **Official Source:** AICTE APH 2024-2027, Appendix 4, Clause 4.3.
- **Category:** `CROSS_DOCUMENT_CONSISTENCY`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document 1: `APPROVED_BUILDING_PLAN` (Field: `sanctioned_builtup_area_sqm`)
  - Document 2: `BUILDING_COMPLETION` (Field: `completed_builtup_area_sqm`)
- **Validation Logic:**
  - Completed area must be $\ge$ 90% of the sanctioned instructional requirement, and cannot exceed sanctioned area by $> 10\%$ without revised sanction plan.
- **Severity:** `WARNING` / `DEFICIENCY` depending on shortfall percentage.
- **Recommended Action:** Submit compounding approval or revised municipal sanction plan.

---

### 2.8 `RULE-EOA-PREV-008`: Previous Year AICTE Approval Intake Consistency
- **Title:** Current Year Applied Intake vs Previous Year Approved Intake Baseline
- **Official Source:** AICTE APH 2024-2027, Chapter II, Clause 2.1.
- **Category:** `INTAKE_RECONCILIATION`
- **Rule Version:** 1.0.0
- **Status:** `APPROVED_FOR_PROTOTYPE_USE`
- **Inputs & Evidence:**
  - Document: `PREV_AICTE_APPROVAL` (Field: `approved_program_intake_map`)
  - Application Context: `applied_program_intake_map`
- **Validation Logic:**
  - In standard EoA (without applied expansion), applied intake must not exceed previously approved intake without an accompanying fee/expansion application.
- **Severity:** `DEFICIENCY`.
- **Recommended Action:** Reconcile applied program seats with previous year extension letter.

---

## 3. Draft Rules (Pending Regional Amendment Verification)

| Rule Code | Intended Check | Missing Information / Reason for Draft Status |
| :--- | :--- | :--- |
| `RULE-DRAFT-BANK-009` | Fixed Deposit Joint Account (FDR) validity check | Exact lien-period requirement varies across state technical boards. Marked as `DRAFT_MISSING_OFFICIAL_SOURCE`. |
| `RULE-DRAFT-PARK-010` | Minimum parking slot area calculation | Municipal corporation bylaws differ between metro and rural municipal boundaries. Marked as `DRAFT_MISSING_OFFICIAL_SOURCE`. |

---

## 4. Deficiency Resolution Eligibility & Remediation Mapping (Phase P8)

### 4.1 Finding Actionability Criteria
Not every evaluation record creates an applicant corrective obligation:
- **Actionable Deficiencies:** Findings with severity `DEFICIENCY` or `WARNING` originating from active rules with status `APPROVED_FOR_PROTOTYPE_USE`. These populate the applicant's Deficiency Resolution Workspace with explicit remediation guidance.
- **Draft & Inactive Rules:** Rules marked `DRAFT_MISSING_OFFICIAL_SOURCE` or `RETIRED` are excluded from actionable pre-scrutiny evaluations. They never trigger blocking applicant deficiency requirements.
- **Informational Advisories:** Findings with severity `INFO` or uncertain extractions (`LOW_EXTRACTION_CONFIDENCE`) prompt institutional advisory review or manual scrutiny routing without requiring formal re-submission.

### 4.2 Corrective Action Mapping
| Finding Category | Root Cause | Permitted Remediation Path | Expected Outcome on Revalidation |
| :--- | :--- | :--- | :--- |
| `RULE-EOA-FIRE-003` | Expired Fire Safety NOC | Upload renewed certificate version (`v2`) | Rule re-checks validity date; condition clears (`CLEARED`) -> transitions to `AWAITING_REVIEW`. |
| `RULE-EOA-CROSS-006` | Survey Number Mismatch | Upload rectified Land Use Order or Rectification Deed (`v2`) | Cross-matching verifies survey consistency; condition clears (`CLEARED`) -> transitions to `AWAITING_REVIEW`. |
| `RULE-EOA-FSR-005` | Faculty Ratio Shortfall | Upload updated faculty roster or provide institutional clarification | FSR recalculated against total intake; condition updates based on new ratio. |
| `RULE-EOA-BCC-002` | Missing Occupancy Cert | Upload valid Building Completion Certificate (`v1` or `v2`) | Document presence confirmed; condition clears (`CLEARED`) -> transitions to `AWAITING_REVIEW`. |

### 4.3 Revalidation Isolation
Targeted revalidation executes the active regulatory catalog against newly extracted replacement document versions. If a rule's condition is no longer detected, the automated status reflects clearance while maintaining immutable previous run findings and advancing the finding to `AWAITING_REVIEW` for formal human scrutiny handoff.
