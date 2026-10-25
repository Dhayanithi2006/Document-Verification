# AICTE Pre-Scrutiny & Deficiency Resolution Platform
## REST API Contract Specification (`API_CONTRACT.md`)

**Document Version:** 1.0.0  
**Phase:** Phase P1 — Specification & Architecture Blueprint  
**Status:** Approved API Baseline  
**Base URL:** `/api/v1`  
**Disclaimer:** *SIH Prototype — Not an official AICTE portal.*

---

## 1. Authentication & Security Headers

All protected endpoints require a standard Bearer Token in the HTTP Authorization header:
```http
Authorization: Bearer <jwt_access_token>
```
Standard JSON error responses conform to RFC 7807 (Problem Details):
```json
{
  "type": "https://errors.aicte-prescrutiny.sih/forbidden",
  "title": "Access Forbidden",
  "status": 403,
  "detail": "Institution users cannot access records of another institution.",
  "instance": "/api/v1/applications/app_9812"
}
```

---

## 2. Authentication Endpoints

### 2.1 `POST /auth/login`
- **Purpose:** Authenticate user credentials and return JWT bearer token.
- **Roles:** Public
- **Request Body (`application/json`):**
  ```json
  {
    "email": "applicant@institution.test",
    "password": "Password123!"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 28800,
    "user": {
      "id": "usr_inst_01",
      "email": "applicant@institution.test",
      "full_name": "Dr. R. K. Sharma",
      "role": "INSTITUTION",
      "institution_id": "inst_01"
    }
  }
  ```
- **Errors:** `401 Unauthorized` (Invalid credentials).

### 2.2 `GET /auth/me`
- **Purpose:** Retrieve current authenticated identity profile, assigned role, and linked institution context.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (`200 OK`):**
  ```json
  {
    "id": "usr_inst_01",
    "email": "applicant@institution.test",
    "full_name": "Dr. R. K. Sharma",
    "role": "INSTITUTION",
    "institution_id": "inst_01",
    "is_active": true,
    "institution": {
      "id": "inst_01",
      "aicte_permanent_id": "1-10972412",
      "name": "Apex Institute of Technology & Management (Synthetic Demo)",
      "category": "ENGINEERING_TECHNOLOGY",
      "state": "Karnataka",
      "district": "Bengaluru Urban",
      "is_rural": false
    }
  }
  ```
- **Errors:** `401 Unauthorized` (Missing, expired, or revoked token).

### 2.3 `POST /auth/logout`
- **Purpose:** Invalidate and revoke the active JWT bearer token session.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (`200 OK`):**
  ```json
  {
    "message": "Successfully logged out. Session revoked."
  }
  ```
- **Errors:** `401 Unauthorized` (Token already invalid or revoked).

### 2.4 `GET /auth/reviewer-check`
- **Purpose:** RBAC boundary verification endpoint restricted to authorized scrutiny committee members and administrators.
- **Roles:** `REVIEWER`, `ADMIN`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (`200 OK`):** Status confirmation and reviewer user profile.
- **Errors:** `403 Forbidden` (Institution Applicant attempted access).

### 2.5 `GET /auth/admin-check`
- **Purpose:** RBAC boundary verification endpoint strictly restricted to platform administrators.
- **Roles:** `ADMIN`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (`200 OK`):** Status confirmation and administrator user profile.
- **Errors:** `403 Forbidden` (Reviewers and Institution Applicants denied).

---

## 3. Application Lifecycle Endpoints

### 3.1 `GET /applications`
- **Purpose:** List applications. Scoped to caller's institution for `INSTITUTION` users; all applications for `REVIEWER` and `ADMIN`.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Query Params:** `academic_year`, `status`, `page` (default 1), `limit` (default 20)
- **Response (`200 OK`):**
  ```json
  {
    "items": [
      {
        "id": "app_9812",
        "application_number": "AICTE-EOA-2026-9812",
        "institution_name": "Apex Institute of Technology",
        "academic_year": "2026-2027",
        "application_type": "EOA",
        "status": "FINDINGS_AVAILABLE",
        "total_intake_applied": 720,
        "created_at": "2026-10-24T08:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
  ```

### 3.2 `POST /applications`
- **Purpose:** Create a new Extension of Approval (EoA) draft application.
- **Roles:** `INSTITUTION`
- **Request Body:**
  ```json
  {
    "academic_year": "2026-2027",
    "total_intake_applied": 720,
    "declared_fields": {
      "declared_land_acres": "5.5",
      "total_faculty_count": "36",
      "approved_carpet_area_sqm": "8420.5"
    }
  }
  ```
- **Response (`201 Created`):** Complete application record initialized with 8 mandatory checklist document slots in `PENDING` state.

### 3.3 `GET /applications/{id}`
- **Purpose:** Retrieve details of a specific application with strict tenant isolation.
- **Roles:** `INSTITUTION` (own institution only), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):** Application metadata including application number, academic year, status, and intake.
- **Errors:** `404 Not Found` (Masked tenant isolation error for cross-institution requests).

### 3.4 `PUT /applications/{id}`
- **Purpose:** Update editable parameters (intake, declared fields) for an application in `DRAFT` status.
- **Roles:** `INSTITUTION` (own institution only)
- **Request Body:**
  ```json
  {
    "total_intake_applied": 750,
    "declared_land_acres": 5.5
  }
  ```
- **Response (`200 OK`):** Updated application record.
- **Errors:** `400 Bad Request` (Attempting to modify post-draft application), `404 Not Found`.

### 3.5 `GET /applications/{id}/checklist`
- **Purpose:** Fetch the mandatory 8-document statutory checklist status and version metadata.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "application_id": "app_9812",
    "total_slots": 8,
    "uploaded_slots": 1,
    "pending_slots": 7,
    "checklist": [
      {
        "id": "doc_01",
        "application_id": "app_9812",
        "document_type": "LAND_TITLE_DEED",
        "title": "1. Land Title Deed / Registered Lease Deed",
        "is_mandatory": true,
        "status": "UPLOADED",
        "current_version": {
          "id": "ver_01",
          "version_number": 1,
          "file_name": "Land_Title_Deed_Registered.pdf",
          "file_size_bytes": 1845120,
          "file_hash_sha256": "8f4e2c8a1b...",
          "page_count": 6,
          "upload_timestamp": "2026-10-24T08:15:00Z"
        }
      }
    ]
  }
  ```

### 3.6 `DELETE /applications/{id}/documents/{document_type}`
- **Purpose:** Remove an uploaded document and reset its statutory checklist slot to `PENDING`.
- **Roles:** `INSTITUTION` (own institution only)
- **Response (`200 OK`):**
  ```json
  {
    "status": "PENDING",
    "message": "Document LAND_TITLE_DEED removed successfully and reset to PENDING."
  }
  ```
- **Errors:** `400 Bad Request` (Post-draft applications locked), `404 Not Found`.

---

## 4. Document Ingestion & Processing Endpoints (Engine A)

### 4.1 `POST /applications/{id}/documents`
- **Purpose:** Upload a PDF document for a specific checklist slot.
- **Roles:** `INSTITUTION`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `document_type`: String (e.g. `FIRE_SAFETY_NOC`)
  - `file`: Binary PDF file (Max 15MB)
- **Validation Rules:**
  - File header must start with `%PDF-`.
  - Max file size $\le 15 \times 1024 \times 1024$ bytes.
  - Generates SHA-256 hash immediately.
- **Response (`202 Accepted`):**
  ```json
  {
    "document_id": "doc_05",
    "version_number": 1,
    "file_name": "Fire_Safety_NOC_2026.pdf",
    "file_hash_sha256": "8f4e2c8a1b...",
    "status": "PROCESSING",
    "quality_gatekeeper": {
      "is_valid_pdf": true,
      "page_count": 2,
      "estimated_dpi": 200,
      "quality_score": 0.96
    },
    "message": "File accepted. Background OCR and structured extraction initiated."
  }
  ```

### 4.2 `GET /documents/{document_id}/versions/{version}/file`
- **Purpose:** Stream document binary for secure in-browser viewing.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Headers Returned:**
  - `Content-Type: application/pdf`
  - `Content-Disposition: inline; filename="Fire_Safety_NOC_2026.pdf"`
  - `X-Content-Type-Options: nosniff`
  - `Cache-Control: private, no-cache`
- **Authorisation:** Validates caller's institution ID matches document's owning institution (masked with 404 on foreign access).

### 4.3 `POST /documents/{document_id}/process`
- **Purpose:** Triggers genuine Intelligent Document Processing (digital PDF text extraction, OCR, field parsing).
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Query Parameters:**
  - `version` (optional int): Target document version number. Defaults to latest.
  - `force` (optional bool, default false): Force re-running extraction even if already completed.
- **Response (`200 OK`):**
  ```json
  {
    "run_id": "9b12a845-...",
    "document_id": "doc_01",
    "document_version_id": "ver_01",
    "status": "COMPLETED",
    "processor_version": "idp-pipeline-v1.0.0",
    "extraction_method": "DIGITAL_PDF_TEXT",
    "pages_processed": 1,
    "pages_digital": 1,
    "pages_ocr": 0,
    "average_confidence": 1.0,
    "error_message": null,
    "created_at": "2026-10-24T08:30:00Z",
    "completed_at": "2026-10-24T08:30:02Z",
    "fields_count": 4
  }
  ```

### 4.4 `GET /documents/{document_id}/processing-status`
- **Purpose:** Check real-time processing status and execution summary metrics.
- **Aliases:** `GET /documents/{document_id}/status`
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):** Returns `DocumentProcessingStatusResponse` schema.

### 4.5 `GET /documents/{document_id}/extracted-fields`
- **Purpose:** Inspect parsed statutory fields with normalized values, spatial coordinates, and genuine token confidence ratings.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "document_id": "doc_05",
    "document_version_id": "ver_05",
    "version_number": 1,
    "document_type": "FIRE_SAFETY_NOC",
    "status": "COMPLETED",
    "processing_run": {
      "run_id": "9b12a845-...",
      "status": "COMPLETED",
      "extraction_method": "DIGITAL_PDF_TEXT",
      "pages_processed": 1,
      "average_confidence": 0.99
    },
    "extracted_fields": [
      {
        "id": "field_9912",
        "processing_run_id": "9b12a845-...",
        "field_key": "valid_until_date",
        "field_label": "Fire NOC Expiry Date",
        "raw_value": "31-03-2027",
        "normalized_value": "2027-03-31",
        "data_type": "DATE",
        "page_number": 1,
        "bounding_box": {
          "ymin": 0.342,
          "xmin": 0.581,
          "ymax": 0.378,
          "xmax": 0.812
        },
        "confidence": 1.0,
        "extraction_method": "DIGITAL_PDF_TEXT",
        "created_at": "2026-10-24T08:30:02Z"
      }
    ]
  }
  ```

### 4.6 `GET /documents/{document_id}/pages`
- **Purpose:** Inspect page-level extracted text, character count, word count, OCR confidence, and extraction method (`DIGITAL_PDF_TEXT` vs `OCR`).
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  [
    {
      "id": "page_01",
      "document_version_id": "ver_05",
      "page_number": 1,
      "extraction_method": "DIGITAL_PDF_TEXT",
      "text_content": "GOVERNMENT FIRE AND RESCUE SERVICES DEPARTMENT...",
      "confidence": 1.0,
      "char_count": 420,
      "word_count": 52,
      "created_at": "2026-10-24T08:30:01Z"
    }
  ]
  ```

---

## 5. Regulatory Validation & Deficiency Endpoints (Engine B & C)

### 5.1 `POST /applications/{id}/validate`
- **Purpose:** Trigger Engine B regulatory cross-matching across all extracted document entities.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "validation_run_id": "run_551",
    "application_id": "app_9812",
    "run_number": 1,
    "status": "COMPLETED",
    "total_checks": 14,
    "findings_summary": {
      "deficiencies": 2,
      "warnings": 1,
      "passed": 11
    },
    "completed_at": "2026-10-24T08:30:12Z"
  }
  ```

### 5.2 `GET /applications/{id}/findings`
- **Purpose:** Retrieve all evidence-anchored findings produced by the latest validation run.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "application_id": "app_9812",
    "validation_run_id": "run_551",
    "findings": [
      {
        "id": "find_0043",
        "rule_code": "RULE-EOA-FIRE-003",
        "rule_title": "Fire Safety Certificate Current Validity",
        "official_source": "AICTE APH 2024-27 Clause 5.2",
        "category": "MANDATORY_SAFETY_CERTIFICATE",
        "severity": "DEFICIENCY",
        "status": "OPEN",
        "explanation": "Fire Safety NOC expired on 2026-03-31 prior to commencement of academic session 2026-2027.",
        "expected_value": "Valid on or after 2026-07-01",
        "observed_value": "2026-03-31",
        "evidence": {
          "document_id": "doc_05",
          "document_title": "Fire Safety NOC",
          "version_number": 1,
          "page_number": 1,
          "bounding_box": {
            "ymin": 0.342,
            "xmin": 0.581,
            "ymax": 0.378,
            "xmax": 0.812
          }
        },
        "verification_status": "VERIFIED_INTERNAL",
        "recommended_action": "Upload renewed Fire NOC issued by competent Fire Services Department.",
        "created_at": "2026-10-24T08:30:12Z"
      }
    ]
  }
  ```

### 5.3 `GET /applications/{id}/deficiencies`
- **Purpose:** Retrieve all actionable findings, composite resolution status, active response drafts, and submission metrics.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "application_id": "app_9812",
    "application_status": "SUBMITTED",
    "total_deficiencies": 2,
    "actionable_count": 2,
    "acknowledged_count": 1,
    "in_progress_count": 1,
    "submitted_count": 0,
    "awaiting_review_count": 0,
    "resolved_count": 0,
    "latest_validation_run_id": "run_001",
    "deficiencies": [
      {
        "id": "find_0043",
        "validation_run_id": "run_001",
        "application_id": "app_9812",
        "rule_code": "RULE-EOA-FIRE-003",
        "rule_title": "Mandatory Fire Safety Certificate (NOC) Validity",
        "category": "MANDATORY_SAFETY_CERTIFICATE",
        "severity": "DEFICIENCY",
        "outcome": "DEFICIENCY_DETECTED",
        "status": "RESPONSE_IN_PROGRESS",
        "resolution_status": "RESPONSE_IN_PROGRESS",
        "title": "Fire NOC Expired Prior to Academic Session",
        "explanation": "Fire Safety Certificate expires on 2026-03-31, prior to the commencement of the academic session.",
        "expected_value": "Valid on or after 2026-07-01",
        "observed_value": "2026-03-31",
        "evidence": {
          "document_id": "doc_05",
          "page_number": 1,
          "confidence": 1.0
        },
        "verification_status": "VERIFIED_INTERNAL",
        "recommended_action": "Upload renewed Fire NOC issued by competent Fire Services Department.",
        "created_at": "2026-10-24T08:30:12Z",
        "acknowledged_at": "2026-10-24T09:00:00Z",
        "active_draft": {
          "id": "sub_draft_01",
          "cycle_number": 1,
          "status": "DRAFT",
          "response_text": "Institution has applied for renewal before Karnataka State Fire & Emergency Services."
        }
      }
    ]
  }
  ```

### 5.4 `POST /findings/{id}/acknowledge`
- **Purpose:** Acknowledge an open finding without resolving it, recording applicant review awareness.
- **Roles:** `INSTITUTION` (own tenant)
- **Response (`200 OK`):** Updated `DeficiencyItemResponse` with `acknowledged_at` timestamp.

### 5.5 `GET /findings/{id}/response`
- **Purpose:** Retrieve the active draft or latest submission response for a finding.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):** `CorrectionSubmissionResponse` or `null`.

### 5.6 `PUT /findings/{id}/response`
- **Purpose:** Save or update an applicant's draft correction response.
- **Roles:** `INSTITUTION` (own tenant)
- **Request Body (`application/json`):**
  ```json
  {
    "response_text": "Fire safety inspection has been conducted and renewed NOC is awaited.",
    "response_category": "CLARIFICATION_JUSTIFICATION",
    "document_id": "doc_05"
  }
  ```
- **Response (`200 OK`):** `CorrectionSubmissionResponse` with `status: "DRAFT"`.

### 5.7 `POST /findings/{id}/submit`
- **Purpose:** Formally submit a corrective response, transition finding to `CORRECTION_SUBMITTED`, and make eligible for revalidation.
- **Roles:** `INSTITUTION` (own tenant)
- **Request Body (`application/json`):**
  ```json
  {
    "response_text": "Inspection completed; renewed NOC attached for verification.",
    "response_category": "DOCUMENT_REPLACEMENT",
    "document_id": "doc_05"
  }
  ```
- **Response (`200 OK`):** `CorrectionSubmissionResponse` with `status: "SUBMITTED"`, `revalidation_status: "PENDING"`.

### 5.8 `POST /applications/{id}/revalidate`
- **Purpose:** Execute controlled regulatory revalidation using the real P7 engine with latest document versions and extraction evidence.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "application_id": "app_9812",
    "validation_run_id": "run_002",
    "run_number": 2,
    "status": "COMPLETED",
    "total_checks": 8,
    "findings_cleared": 1,
    "findings_persisting": 1,
    "new_findings": 0,
    "comparison": [
      {
        "finding_id": "find_0043",
        "rule_code": "RULE-EOA-FIRE-003",
        "rule_title": "Mandatory Fire Safety Certificate (NOC) Validity",
        "previous_outcome": "DEFICIENCY_DETECTED",
        "latest_outcome": "NO_ISSUE_DETECTED",
        "status_change": "CLEARED",
        "details": "Rule check re-evaluated: requirement is now satisfied under latest evidence."
      }
    ]
  }
  ```

### 5.9 `GET /findings/{id}/history`
- **Purpose:** Retrieve the full, immutable chronological audit trail for a finding.
- **Roles:** `INSTITUTION` (own tenant), `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "finding_id": "find_0043",
    "application_id": "app_9812",
    "history": [
      {
        "event_type": "FINDING_IDENTIFIED",
        "timestamp": "2026-10-24T08:30:12Z",
        "actor": "System Regulatory Engine",
        "actor_role": "SYSTEM",
        "description": "Pre-scrutiny finding detected under RULE-EOA-FIRE-003"
      },
      {
        "event_type": "ACKNOWLEDGED",
        "timestamp": "2026-10-24T09:00:00Z",
        "actor": "Dr. R. K. Sharma",
        "actor_role": "INSTITUTION",
        "description": "Applicant reviewed and acknowledged the deficiency finding."
      },
      {
        "event_type": "DRAFT_SAVED",
        "timestamp": "2026-10-24T09:15:00Z",
        "actor": "Dr. R. K. Sharma",
        "actor_role": "INSTITUTION",
        "description": "Cycle 1 draft response prepared."
      },
      {
        "event_type": "CORRECTION_SUBMITTED",
        "timestamp": "2026-10-24T09:30:00Z",
        "actor": "Dr. R. K. Sharma",
        "actor_role": "INSTITUTION",
        "description": "Cycle 1 formal response submitted."
      },
      {
        "event_type": "REVALIDATION_RUN",
        "timestamp": "2026-10-24T09:35:00Z",
        "actor": "Regulatory Rule Engine",
        "actor_role": "SYSTEM",
        "description": "Automated revalidation completed. Outcome: CONDITION_CLEARED"
      }
    ]
  }
  ```

### 5.10 `POST /findings/{id}/resolve`
- **Purpose:** Bridge endpoint to upload a replacement document version (`v2`), extract via IDP, submit correction, and trigger immediate revalidation.
- **Roles:** `INSTITUTION`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: Binary PDF file (optional)
  - `remarks`: String explanation of the correction (required)
  - `response_category`: Category string (default `DOCUMENT_REPLACEMENT`)
- **Response (`200 OK`):**
  ```json
  {
    "finding_id": "find_0043",
    "submission_id": "sub_102",
    "status": "CORRECTION_SUBMITTED",
    "new_version_number": 2,
    "revalidation": {
      "status": "COMPLETED",
      "findings_cleared": 1
    },
    "message": "Corrected version uploaded and revalidation executed successfully."
  }
  ```

---

## 6. Reviewer Scrutiny & Case Management Endpoints

### 6.1 `GET /reviewer/queue`
- **Purpose:** Retrieve live operational worklist of applications awaiting scrutiny with real-time operational metrics.
- **Roles:** `REVIEWER`, `ADMIN`
- **Query Params:** `filter`: `ALL`, `ASSIGNED_TO_ME`, `UNASSIGNED`, `UNDER_SCRUTINY`, `PRE_SCRUTINY_RECOMMENDED_CLEAR`, `RETURNED_FOR_CORRECTION`
- **Response (`200 OK`):**
  ```json
  {
    "metrics": {
      "awaiting_scrutiny": 1,
      "pending_responses": 1,
      "assigned_to_me": 1,
      "under_scrutiny": 1,
      "recommended_clear": 0,
      "returned_for_correction": 0
    },
    "items": [
      {
        "id": "app_9812",
        "application_number": "AICTE-EOA-2026-9812",
        "institution_name": "Apex Institute of Technology & Management",
        "academic_year": "2026-2027",
        "status": "SUBMITTED",
        "review_status": "UNDER_SCRUTINY",
        "assigned_reviewer_id": "usr_rev_01",
        "assigned_reviewer_name": "Dr. V. Narayanan (Reviewer)",
        "open_deficiencies": 1,
        "submitted_corrections": 1,
        "resolved_findings": 1,
        "updated_at": "2026-10-24T10:00:00Z"
      }
    ],
    "total": 1
  }
  ```

### 6.2 `GET /reviewer/applications/{id}/scrutiny`
- **Purpose:** Full scrutiny case console bringing together institutional profile, statutory checklist, findings with spatial evidence coordinates, P8 correction submissions, revalidation deltas, and observation history.
- **Roles:** `REVIEWER`, `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "application_id": "app_9812",
    "application_number": "AICTE-EOA-2026-9812",
    "academic_year": "2026-2027",
    "status": "SUBMITTED",
    "review_status": "UNDER_SCRUTINY",
    "assigned_reviewer": {
      "id": "usr_rev_01",
      "full_name": "Dr. V. Narayanan (Reviewer)",
      "email": "reviewer@reviewer.test"
    },
    "institution": {
      "name": "Apex Institute of Technology & Management",
      "aicte_permanent_id": "1-10972412",
      "category": "ENGINEERING_TECHNOLOGY",
      "state": "Karnataka",
      "district": "Bengaluru Urban"
    },
    "documents": [...],
    "findings": [...],
    "correction_submissions": [...],
    "observations": [...]
  }
  ```

### 6.3 `POST /reviewer/applications/{id}/assign`
- **Purpose:** Assign or reassign an application case to an eligible active Reviewer.
- **Roles:** `REVIEWER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "reviewer_user_id": "usr_rev_01",
    "remarks": "Assigned for statutory civil & fire clearance review."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "message": "Application assigned successfully.",
    "application_id": "app_9812",
    "assigned_reviewer_id": "usr_rev_01",
    "review_status": "UNDER_SCRUTINY"
  }
  ```

### 6.4 `POST /reviewer/applications/{id}/observations`
- **Purpose:** Record formal scrutiny committee observations or finding-level decisions (`CONCUR_DEFICIENCY`, `ACCEPT_CORRECTION`, `OVERRULE_DEFICIENCY`, `REQUIRE_ADDITIONAL_EVIDENCE`).
- **Roles:** `REVIEWER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "finding_id": "find_0043",
    "submission_id": "sub_102",
    "decision": "ACCEPT_CORRECTION",
    "justification": "Verified renewed Fire NOC (v2) issued by Karnataka Fire Services. Validity requirement satisfied.",
    "is_internal_note": false
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "obs_102",
    "application_id": "app_9812",
    "finding_id": "find_0043",
    "submission_id": "sub_102",
    "reviewer_user_id": "usr_rev_01",
    "reviewer_name": "Dr. V. Narayanan (Reviewer)",
    "decision": "ACCEPT_CORRECTION",
    "justification": "Verified renewed Fire NOC (v2) issued by Karnataka Fire Services. Validity requirement satisfied.",
    "is_internal_note": false,
    "created_at": "2026-10-24T10:15:00Z"
  }
  ```

### 6.5 `POST /reviewer/applications/{id}/decision`
- **Purpose:** Complete pre-scrutiny stage recommendation (`PRE_SCRUTINY_RECOMMENDED_CLEAR`, `RETURNED_FOR_CORRECTION`, `FURTHER_REVIEW_REQUIRED`).
- **Roles:** `REVIEWER`, `ADMIN`
- **Request Body:**
  ```json
  {
    "decision": "PRE_SCRUTINY_RECOMMENDED_CLEAR",
    "justification": "All statutory checklist requirements and revalidation corrections verified under APH norms."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "message": "Pre-scrutiny stage decision recorded successfully.",
    "application_id": "app_9812",
    "review_status": "PRE_SCRUTINY_RECOMMENDED_CLEAR",
    "completed_at": "2026-10-24T10:20:00Z"
  }
  ```

---

## 7. Platform Administration & Governance Endpoints

### 7.1 `GET /admin/overview`
- **Purpose:** System-wide operational dashboard metrics derived from the real database.
- **Roles:** `ADMIN`
- **Response (`200 OK`):**
  ```json
  {
    "total_users": 5,
    "active_users": 5,
    "inactive_users": 0,
    "total_institutions": 2,
    "total_applications": 2,
    "applications_under_scrutiny": 1,
    "pending_correction_responses": 1,
    "system_audit_events_count": 28
  }
  ```

### 7.2 `GET /admin/users`
- **Purpose:** List platform user directory with role, active status, institution linkage, and login timestamps.
- **Roles:** `ADMIN`
- **Query Params:** `role` (optional filter: `INSTITUTION`, `REVIEWER`, `ADMIN`), `is_active` (optional bool)
- **Response (`200 OK`):** List of user profiles with safe metadata (no password hashes).

### 7.3 `POST /admin/users`
- **Purpose:** Provision a new platform user account with bcrypt password hashing and mandatory audit logging.
- **Roles:** `ADMIN`
- **Request Body:**
  ```json
  {
    "email": "reviewer2@reviewer.test",
    "password": "SecurePassword123!",
    "full_name": "Prof. S. Sengupta",
    "role": "REVIEWER",
    "institution_id": null
  }
  ```
- **Response (`201 Created`):** Safe user profile object.

### 7.4 `PATCH /admin/users/{id}`
- **Purpose:** Update user status or attributes (e.g. deactivate account, reassign role, change institution linkage). Features self-lockout and self-demotion protection.
- **Roles:** `ADMIN`
- **Request Body:**
  ```json
  {
    "is_active": false
  }
  ```
- **Response (`200 OK`):** Updated user profile.
- **Errors:** `400 Bad Request` (Attempting to deactivate own administrator account).

### 7.5 `GET /admin/institutions`
- **Purpose:** List registered institutions with AICTE Permanent IDs and geographical/category classifications.
- **Roles:** `ADMIN`
- **Response (`200 OK`):** List of institution records.

### 7.6 `PATCH /admin/institutions/{id}`
- **Purpose:** Update non-sensitive institution metadata (e.g. name, classification, urban/rural status). Preserves AICTE Permanent ID immutability.
- **Roles:** `ADMIN`
- **Request Body:**
  ```json
  {
    "is_rural": true
  }
  ```
- **Response (`200 OK`):** Updated institution profile.

### 7.7 `GET /admin/audit-events` (and `GET /audit-events`)
- **Purpose:** Query immutable tamper-evident forensic audit log with entity, actor, and role filters.
- **Roles:** `ADMIN` (`GET /audit-events` also accessible to `REVIEWER`)
- **Query Params:** `action`, `actor_role`, `entity_type`, `entity_id`, `limit` (default 50), `offset` (default 0)
- **Response (`200 OK`):** List of audit events with actor details, action, timestamp, and parsed payload context.

### 7.8 `GET /rules`
- **Purpose:** List all versioned AICTE regulatory rules from the engine catalogue.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Query Params:** `category` (optional filter)
- **Response (`200 OK`):** Array of regulatory rule records with active versions.

### 7.9 `GET /rules/{rule_code}`
- **Purpose:** Retrieve full regulatory rule details, official source clause, parameters, and complete version history.
- **Roles:** `INSTITUTION`, `REVIEWER`, `ADMIN`
- **Response (`200 OK`):** Detailed rule representation including `versions` array.

### 7.10 `POST /rules/{rule_code}/activate`
- **Purpose:** Authorize and activate a verified regulatory rule for automated enforcement.
- **Roles:** `ADMIN` (strict RBAC requirement)
- **Response (`200 OK`):**
  ```json
  {
    "message": "Regulatory rule RULE-DRAFT-BANK-009 activated for automated enforcement.",
    "rule_code": "RULE-DRAFT-BANK-009",
    "is_active": true
  }
  ```
- **Errors:** `403 Forbidden` (non-admin caller), `404 Not Found` (non-existent rule).

---

## 8. Health & Diagnostic Probes

### 8.1 `GET /health/liveness`
- **Purpose:** Basic application liveness probe. Indicates the process is accepting HTTP traffic.
- **Roles:** Public
- **Response (`200 OK`):**
  ```json
  {
    "status": "ok",
    "timestamp": "2026-10-24T07:11:10.747404Z"
  }
  ```

### 8.2 `GET /health/readiness`
- **Purpose:** Dependency readiness probe verifying database connectivity before routing user requests.
- **Roles:** Public
- **Response (`200 OK` when healthy):**
  ```json
  {
    "status": "ready",
    "database": "connected",
    "environment": "development",
    "version": "1.0.0"
  }
  ```
- **Response (`503 Service Unavailable` when database fails):**
  ```json
  {
    "status": "degraded",
    "database": "disconnected",
    "environment": "development",
    "version": "1.0.0"
  }
  ```
