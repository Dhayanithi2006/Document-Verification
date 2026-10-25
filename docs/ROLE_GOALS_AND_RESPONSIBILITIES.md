# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## Role-Based Goals, Responsibilities, and Operational Boundaries
**Smart India Hackathon (SIH) Prototype Specification**

**Execution Date:** October 25, 2026
**Status:** Approved Architectural Baseline
**Governing Standard:** SIH Prototype Role Integrity & Human Authority Safeguards

---

## 1. Executive Overview & Core Principles

The AICTE Pre-Scrutiny & Deficiency Resolution Platform is an algorithmic decision-support and workflow system designed to assist technical institutions preparing AICTE Extension of Approval (EoA) applications, identify documentary and regulatory deficiencies early, facilitate transparent corrective responses, and empower authorised human scrutiny committees with evidence-linked findings.

The platform recognizes three distinct personas, each with bounded responsibilities, strict role separation, and segregated permissions:

1. **`INSTITUTION` (Institution Applicant):** Responsible for preparing institutional profiles, uploading statutory supporting evidence, running algorithmic pre-scrutiny checks, and submitting justified correction responses.
2. **`REVIEWER` (Authorised Scrutiny Reviewer):** Responsible for independent scrutiny, examining ingested evidence, evaluating applicant responses, recording formal observations, and executing authorized scrutiny recommendations.
3. **`ADMIN` (Platform System Administrator):** Responsible for platform operational health, user account governance, regulatory rule catalog maintenance, and forensic audit inspection.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                HUMAN SCRUTINY BOUNDARY                      │
       │                                                             │
       │  Algorithmic decision support assists with:                 │
       │  • Text extraction & spatial bounding-box grounding        │
       │  • APH 2024–27 regulatory rule discrepancy evaluation       │
       │  • Deficiency timeline & correction response tracking       │
       │                                                             │
       │  Algorithmic engine NEVER performs:                         │
       │  • Automated final statutory grant or rejection of EoA      │
       │  • Automatic clearing of deficiencies without human review  │
       │  • Unsupervised privilege elevation or cross-role mutation  │
       └─────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Prototype Nature & Regulatory Disclaimer:**
> This software is an **SIH Demonstration Prototype**. In all documentation, view templates, and generated dossiers, the prominent disclosure **“SIH Prototype — Not an official AICTE portal”** is maintained. Passing automated validation does not guarantee statutory approval. Final decision-making authority rests exclusively with authorized AICTE Scrutiny Committees.

---

## 2. Role 1: Institution Applicant (`INSTITUTION`)

### 2.1 Primary Goal
Enable technical institutions to prepare accurate applications, upload mandatory statutory documentation, detect non-compliance issues prior to formal submission through algorithmic pre-scrutiny, review evidence-grounded findings, and execute structured deficiency remediation cycles.

### 2.2 Core Responsibilities
- Maintain accurate declared institutional parameters (Applied Intake, Land Area, Faculty Roster count, Built-up Area).
- Ingest required statutory documents matching AICTE Approval Process Handbook (APH) 2024–27 requirements.
- Review algorithmic pre-scrutiny findings, categorized into actionable deficiencies, regulatory warnings, and informational advisories.
- Acknowledge identified deficiencies and provide structured corrective justifications or replacement document versions.
- Monitor application status across the scrutiny lifecycle.

### 2.3 Permitted Operations
- **Application Lifecycle:** Create new EoA applications for the current academic year; view own historical applications; edit declared parameters while in `DRAFT` status.
- **Document Workspace:** Ingest statutory PDF documents into 8 mandatory checklist slots; upload replacement versions (`v2+`) while preserving historical records; remove uploaded documents in `DRAFT` status.
- **Pre-Scrutiny Evaluation:** Trigger on-demand regulatory validation runs against the institution's active document versions.
- **Evidence Inspection:** View split-screen evidence overlays comparing declared parameters against extracted text with spatial bounding boxes and OCR confidence scores.
- **Deficiency Resolution Bridge:** Acknowledge open findings; create and save response drafts; submit formal correction packages; trigger controlled revalidation to verify delta improvements.
- **Dossier Generation:** View and export printable Pre-Scrutiny Assessment Dossiers displaying application parameters, checklist completion, and algorithmic discrepancy summaries.

### 2.4 Prohibited Operations
- **Cross-Tenant Access:** Cannot view, query, or mutate applications, documents, or findings belonging to other institutions (strictly blocked by `verify_institution_access` returning HTTP 404).
- **Post-Submission Tampering:** Cannot edit declared parameters or delete uploaded documents once an application is submitted or locked for scrutiny.
- **Reviewer Capabilities:** Cannot access the Scrutiny Reviewer Queue (`#/reviewer/queue`), assign cases, record committee observations, or execute scrutiny dispositions.
- **Administrative Operations:** Cannot provision user accounts, modify regulatory rules, or view system-wide audit logs.
- **Self-Approval:** Cannot clear deficiencies or mark findings as resolved without committee verification or controlled revalidation.

### 2.5 Expected Inputs and Outputs
- **Inputs:** Institutional EoA parameters; PDF files (Land Title Deeds, Approved Building Plans, Building Completion Certificates, Fire Safety NOCs, Structural Stability Certificates, Faculty Rosters, Land Use Certificates, Previous AICTE Approvals); corrective remarks.
- **Outputs:** Verified cryptographic SHA-256 hashes; versioned document records; extracted field values; regulatory findings breakdown; correction response packages; readiness score estimates.

### 2.6 Required Workflow States
- `DRAFT`: Parameter editing and document uploading active.
- `SUBMITTED` / `UNDER_PRE_SCRUTINY`: Read-only parameter state; pre-scrutiny findings active.
- `DEFICIENCY_PENDING`: Actionable deficiencies requiring institutional acknowledgment and correction.
- `REVALIDATED`: Correction package submitted and delta comparison evaluated.

### 2.7 Success Criteria
The Institution Applicant successfully prepares a complete application, uploads valid PDFs across statutory checklist slots, evaluates compliance against APH norms, acknowledges deficiencies, submits substantiated corrective responses, and tracks application progression without unauthorized data exposure.

### 2.8 Dependencies on Other Roles
- Dependent on **System Administrator** for active regulatory rule catalogs and tenant account provisioning.
- Dependent on **Scrutiny Reviewer** for human scrutiny evaluations, observation recording, and disposition recommendations.

---

## 3. Role 2: Authorised Scrutiny Reviewer (`REVIEWER`)

### 3.1 Primary Goal
Enable appointed AICTE scrutiny experts and committee members to examine assigned institutional applications, inspect supporting documentary evidence alongside algorithmic extractions, evaluate applicant corrective responses, record formal scrutiny observations, and execute authorized pre-scrutiny recommendations.

### 3.2 Core Responsibilities
- Manage scrutiny workload through the central Scrutiny Reviewer Queue.
- Verify that declared institutional parameters align with statutory documentary evidence.
- Inspect original and replacement document versions, assessing extracted text, spatial bounding boxes, and OCR confidence indicators.
- Review applicant correction responses and revalidation delta reports.
- Record structured, justified observations linked to specific findings or regulatory rules.
- Execute permitted stage dispositions while respecting system-enforced blocking deficiency safeguards.

### 3.3 Permitted Operations
- **Queue Management:** Query and filter eligible scrutiny cases; claim/assign unassigned cases to oneself.
- **Scrutiny Console:** Access comprehensive case dossiers via direct route (`#/reviewer/scrutiny/:id`) or queue navigation; inspect institutional profiles, statutory checklists, and chronological history.
- **Document & Evidence Inspection:** Stream and examine full PDF documents across current and prior versions; view spatial bounding boxes and field extraction metadata.
- **Observation Recording:** Submit official scrutiny observations detailing documentary compliance, discrepancies, or required clarifications.
- **Scrutiny Dispositions:** Record stage dispositions (`RECOMMEND_CLEAR`, `DEFICIENCY_NOTED`, `RETURNED_FOR_CORRECTION`, `ESCALATE_TO_COMMITTEE`).

### 3.4 Prohibited Operations
- **Application Creation & Editing:** Cannot create applications or edit an institution's declared parameters.
- **Document Upload on Behalf of Applicant:** Cannot upload documents into applicant checklist slots.
- **Invalid Clearance Bypass:** Cannot recommend pre-scrutiny clearance (`RECOMMEND_CLEAR`) while unresolved blocking deficiencies remain active (enforced on both client and backend via HTTP 400).
- **Administrative Capabilities:** Cannot provision users, activate/deactivate regulatory rules, or alter forensic audit records.
- **Cross-Reviewer Reassignment:** Cannot reassign cases assigned to other reviewers without administrative intervention.

### 3.5 Expected Inputs and Outputs
- **Inputs:** Case assignment claims; formal observation notes; scrutiny stage dispositions; committee escalation rationales.
- **Outputs:** Persisted reviewer observations on the scrutiny timeline; updated application workflow statuses; tamper-evident audit log events.

### 3.6 Required Workflow States
- `ASSIGNED`: Case claimed by reviewer; scrutiny in progress.
- `OBSERVATIONS_RECORDED`: Committee observations logged; awaiting applicant response or final signoff.
- `RETURNED_FOR_CORRECTION`: Application returned to applicant with specific documentary requisitions.
- `RECOMMENDED_CLEAR` / `SCRUTINY_COMPLETED`: Pre-scrutiny stage concluded for committee review.

### 3.7 Success Criteria
The Reviewer conducts thorough, evidence-grounded scrutiny of assigned cases, inspects versioned evidence, assesses institutional corrections, records justifiable observations, and enforces statutory compliance without premature automated clearance.

### 3.8 Dependencies on Other Roles
- Dependent on **Institution Applicant** for application preparation and documentary evidence submission.
- Dependent on **System Administrator** for active rule governance and platform access.

---

## 4. Role 3: Platform System Administrator (`ADMIN`)

### 4.1 Primary Goal
Maintain system reliability, govern user access across institutions and reviewer panels, administer regulatory rule catalogs in accordance with published AICTE Approval Process Handbooks, and monitor platform activity through immutable audit logging.

### 4.2 Core Responsibilities
- Monitor platform operational health and application metrics.
- Provision, update, and manage user accounts across all platform roles.
- Govern the regulatory rule catalog, activating verified APH rules and deactivating unverified or draft rules with audit logging.
- Oversee forensic audit events, ensuring end-to-end traceability of document uploads, pre-scrutiny evaluations, reviewer decisions, and administrative actions.
- Enforce tenant isolation and access security policies.

### 4.3 Permitted Operations
- **User Governance:** Query, search, and filter user accounts; provision synthetic and operational accounts (`INSTITUTION`, `REVIEWER`, `ADMIN`); toggle user activation status (`ACTIVE` / `DEACTIVATED`).
- **Regulatory Rule Governance:** Inspect complete rule catalog (Rule Code, Category, Norm Expressions, Applicability, Source Citations); activate draft rules; deactivate rules with mandatory justification strings.
- **Forensic Audit Inspection:** Access the immutable audit log (`#/admin/audit`); filter audit records by actor, event type, institution, or date range.
- **Administrative Scrutiny Access:** Access reviewer queues and application dossiers for administrative oversight, supervisor review, and support.
- **System Metrics:** View system-wide operational metrics (total applications, active rules, pending scrutinies, user breakdown).

### 4.4 Prohibited Operations
- **Scrutiny Decision Usurpation:** Administrative access does not authorize overriding or faking reviewer committee decisions without following the established scrutiny workflow.
- **Direct Database Mutation in Production:** Cannot bypass audit logging or security policies to alter persisted application data.
- **Tampering with Audit Trail:** No endpoints exist to edit, delete, or truncate audit event records.
- **Unverified Rule Enforcement:** Cannot activate unverified or speculative regulatory expressions without documenting regulatory source citations.

### 4.5 Expected Inputs and Outputs
- **Inputs:** User provisioning schemas; rule activation/deactivation triggers with audit reasons; query and filter parameters.
- **Outputs:** Active user credentials; updated regulatory catalog state; system health reports; auditable compliance logs.

### 4.6 Required Workflow States
- `RULE_ACTIVE` / `RULE_INACTIVE`: Governed state of regulatory rules.
- `USER_ACTIVE` / `USER_DEACTIVATED`: Governed state of user authentication profiles.

### 4.7 Success Criteria
The Administrator ensures seamless platform operations, maintains strict access boundaries, keeps regulatory rule sets aligned with statutory standards, and provides complete auditable visibility into all platform transactions.

### 4.8 Dependencies on Other Roles
- Operates as the foundational governance layer supporting both **Institution Applicants** and **Scrutiny Reviewers**.

---

## 5. Cross-Role Dependencies & End-to-End Workflow

The three roles interface across three sequential, interconnected workflows:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW A: APPLICATION PREPARATION (INSTITUTION APPLICANT)                            │
│ 1. Applicant signs in with authenticated JWT credentials                               │
│ 2. Applicant creates EoA application; inputs declared parameters                       │
│ 3. Applicant uploads 8 statutory PDFs; system computes SHA-256 and stores version v1  │
│ 4. IDP pipeline extracts fields; highlights bounding boxes                             │
│ 5. Applicant runs Algorithmic Pre-Scrutiny; system identifies deficiencies             │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW B: DEFICIENCY CORRECTION & HUMAN SCRUTINY (INSTITUTION & REVIEWER)            │
│ 1. Applicant acknowledges findings, drafts responses, uploads replacement PDFs (v2)   │
│ 2. Applicant submits formal correction package; triggers controlled revalidation      │
│ 3. Reviewer signs in, accesses Scrutiny Queue, and claims application                  │
│ 4. Reviewer inspects split-screen evidence, original vs. v2 documents, and IDP boxes  │
│ 5. Reviewer records formal scrutiny observations linked to specific findings           │
│ 6. Reviewer executes scrutiny disposition (Clears or Returns for further correction)   │
│    * Backend strictly blocks RECOMMEND_CLEAR if blocking deficiencies remain open      │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ WORKFLOW C: ADMINISTRATIVE GOVERNANCE & AUDIT OVERSIGHT (PLATFORM ADMINISTRATOR)       │
│ 1. Administrator signs in; accesses Platform Dashboard and Metrics                    │
│ 2. Administrator manages User Directory (provisions accounts, toggles activation)     │
│ 3. Administrator inspects Regulatory Rule Catalog (activates/deactivates with reason)  │
│ 4. Administrator inspects Append-Only Forensic Audit Trail (verifies all operations)   │
│ 5. Cross-role state consistency and tenant boundaries verified across all tiers        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Shared Non-Negotiables & Prototype Transparency

1. **Human Authority Boundary:** The algorithmic engine provides pre-scrutiny decision support; it never grants or rejects statutory EoA applications automatically.
2. **Document Integrity:** A successful PDF upload generates an immutable document version with a SHA-256 hash. It does not imply legal validity or statutory compliance.
3. **Deficiency Remediation Integrity:** Uploading a replacement document does not automatically clear a deficiency. Clearance requires revalidation and human scrutiny evaluation.
4. **Tenant Isolation:** Multi-tenant boundaries are enforced server-side. Access attempts to foreign institutional records return `HTTP 404 Not Found`.
5. **Auditing Standards:** Every state-changing workflow transaction records actor, target, timestamp, action, and payload details in an append-only audit log.
6. **Prototype Disclaimer:** Every page header, dossier export, and report displays the mandatory disclosure: **“SIH Prototype — Not an official AICTE portal.”**
