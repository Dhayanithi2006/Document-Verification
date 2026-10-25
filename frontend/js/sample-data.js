// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// Explicitly Labeled Synthetic Demo Data (sample-data.js)
// NOTE: All data herein is synthetic for demonstration and testing purposes only.

export const syntheticInstitutions = [
  {
    id: "inst_01",
    aictePermanentId: "1-10972412",
    name: "Apex Institute of Technology & Management (Synthetic Demo)",
    category: "ENGINEERING_TECHNOLOGY",
    state: "Karnataka",
    district: "Bengaluru Urban",
    isRural: false,
    address: "Survey No. 44/2A, Electronic City Phase 1, Bengaluru - 560100"
  },
  {
    id: "inst_02",
    aictePermanentId: "1-20485913",
    name: "National Polytechnic & Science Academy (Synthetic Demo)",
    category: "POLYTECHNIC_DIPLOMA",
    state: "Tamil Nadu",
    district: "Coimbatore",
    isRural: true,
    address: "National Highway 47, Rural Campus, Coimbatore - 641014"
  }
];

export const syntheticApplications = [
  {
    id: "app_9812",
    applicationNumber: "AICTE-EOA-2026-9812",
    institutionId: "inst_01",
    institutionName: "Apex Institute of Technology & Management (Synthetic Demo)",
    academicYear: "2026-2027",
    applicationType: "Extension of Approval (EoA)",
    status: "FINDINGS_AVAILABLE",
    totalIntakeApplied: 720,
    preScrutinyScore: 78,
    createdAt: "2026-10-24T08:00:00Z",
    summary: {
      totalDocuments: 8,
      uploadedCount: 8,
      deficienciesCount: 2,
      warningsCount: 1,
      compliantCount: 5
    }
  },
  {
    id: "app_9813",
    applicationNumber: "AICTE-EOA-2026-9813",
    institutionId: "inst_02",
    institutionName: "National Polytechnic & Science Academy (Synthetic Demo)",
    academicYear: "2026-2027",
    applicationType: "Extension of Approval (EoA)",
    status: "REVALIDATED",
    totalIntakeApplied: 480,
    preScrutinyScore: 95,
    createdAt: "2026-10-23T14:30:00Z",
    summary: {
      totalDocuments: 8,
      uploadedCount: 8,
      deficienciesCount: 0,
      warningsCount: 1,
      compliantCount: 7
    }
  }
];

// The 8 Mandatory Documents for EoA (per docs/PROJECT_SPEC.md)
export const syntheticChecklist = [
  {
    documentId: "doc_01",
    documentType: "LAND_TITLE_DEED",
    title: "1. Land Title Deed / Registered Lease Deed",
    isMandatory: true,
    status: "PROCESSED",
    findingCount: 0,
    currentVersion: {
      versionNumber: 1,
      fileName: "Land_Title_Deed_Registered_5.2Acres.pdf",
      fileSizeBytes: 1845120,
      pageCount: 6,
      isScanned: false,
      uploadedAt: "2026-10-24 08:15"
    }
  },
  {
    documentId: "doc_02",
    documentType: "LAND_USE_CERTIFICATE",
    title: "2. Land Use Certificate / Conversion Order",
    isMandatory: true,
    status: "DEFICIENCY_DETECTED",
    findingCount: 1,
    findingId: "find_0042",
    currentVersion: {
      versionNumber: 1,
      fileName: "Land_Use_Certificate_DC_Order.pdf",
      fileSizeBytes: 942150,
      pageCount: 4,
      isScanned: true,
      uploadedAt: "2026-10-24 08:17"
    }
  },
  {
    documentId: "doc_03",
    documentType: "APPROVED_BUILDING_PLAN",
    title: "3. Approved Building Plan (Municipal Authority)",
    isMandatory: true,
    status: "PROCESSED",
    findingCount: 0,
    currentVersion: {
      versionNumber: 1,
      fileName: "Approved_Sanction_Plan_BDA.pdf",
      fileSizeBytes: 4210900,
      pageCount: 8,
      isScanned: false,
      uploadedAt: "2026-10-24 08:20"
    }
  },
  {
    documentId: "doc_04",
    documentType: "BUILDING_COMPLETION",
    title: "4. Building Completion / Occupancy Certificate (OC)",
    isMandatory: true,
    status: "PROCESSED",
    findingCount: 0,
    currentVersion: {
      versionNumber: 1,
      fileName: "Building_Completion_Certificate_Phase1.pdf",
      fileSizeBytes: 1210400,
      pageCount: 3,
      isScanned: false,
      uploadedAt: "2026-10-24 08:22"
    }
  },
  {
    documentId: "doc_05",
    documentType: "FIRE_SAFETY_NOC",
    title: "5. Fire Safety Certificate (State Fire NOC)",
    isMandatory: true,
    status: "DEFICIENCY_DETECTED",
    findingCount: 1,
    findingId: "find_0043",
    currentVersion: {
      versionNumber: 1,
      fileName: "Fire_Safety_Certificate_Expired.pdf",
      fileSizeBytes: 812400,
      pageCount: 2,
      isScanned: true,
      uploadedAt: "2026-10-24 08:25"
    }
  },
  {
    documentId: "doc_06",
    documentType: "STRUCTURAL_STABILITY",
    title: "6. Structural Stability Certificate",
    isMandatory: true,
    status: "PROCESSED",
    findingCount: 0,
    currentVersion: {
      versionNumber: 1,
      fileName: "Structural_Soundness_Certified.pdf",
      fileSizeBytes: 654200,
      pageCount: 2,
      isScanned: false,
      uploadedAt: "2026-10-24 08:28"
    }
  },
  {
    documentId: "doc_07",
    documentType: "PREV_AICTE_APPROVAL",
    title: "7. Previous Year AICTE Approval Letter (2025-26)",
    isMandatory: true,
    status: "PROCESSED",
    findingCount: 0,
    currentVersion: {
      versionNumber: 1,
      fileName: "AICTE_Extension_Letter_2025_2026.pdf",
      fileSizeBytes: 712000,
      pageCount: 4,
      isScanned: false,
      uploadedAt: "2026-10-24 08:30"
    }
  },
  {
    documentId: "doc_08",
    documentType: "FACULTY_ROSTER",
    title: "8. Faculty Cadre & Student Roster Summary",
    isMandatory: true,
    status: "WARNING_DETECTED",
    findingCount: 1,
    findingId: "find_0044",
    currentVersion: {
      versionNumber: 1,
      fileName: "Faculty_Cadre_Roster_2026.pdf",
      fileSizeBytes: 1420800,
      pageCount: 5,
      isScanned: false,
      uploadedAt: "2026-10-24 08:32"
    }
  }
];

// Evidence-Linked Findings matching docs/REGULATORY_RULE_CATALOG.md
export const syntheticFindings = [
  {
    id: "find_0042",
    applicationId: "app_9812",
    ruleCode: "RULE-EOA-CROSS-006",
    ruleVersion: "1.0.0",
    ruleTitle: "Cross-Document Survey / Khasra Number Consistency Check",
    officialSource: "AICTE APH 2024-2027 Clause 4.2",
    category: "CROSS_DOCUMENT_CONSISTENCY",
    severity: "WARNING",
    status: "OPEN",
    explanation: "Survey Number in Land Use Conversion Order ('Sy. No. 44/2B') does not match the Title Deed ('Sy. No. 44/2A').",
    expectedValue: "Survey No: 44/2A (matching Title Deed)",
    observedValue: "Survey No: 44/2B (in Land Use Certificate)",
    evidence: {
      documentId: "doc_02",
      documentTitle: "Land Use Certificate / Conversion Order",
      versionNumber: 1,
      pageNumber: 2,
      boundingBox: {
        ymin: 0.38,
        xmin: 0.22,
        ymax: 0.44,
        xmax: 0.78
      },
      extractedSnippet: "Order No. ALN/CR-44: Certified that land bearing Sy. No. 44/2B in Electronic City is permitted for commercial/educational conversion...",
      confidence: 0.948,
      extractionMethod: "PaddleOCR Hybrid Engine"
    },
    verificationStatus: "VERIFIED_INTERNAL",
    recommendedAction: "Upload updated Land Use Endorsement or registered Survey Rectification Deed covering Sy. No. 44/2A.",
    createdAt: "2026-10-24 08:35"
  },
  {
    id: "find_0043",
    applicationId: "app_9812",
    ruleCode: "RULE-EOA-FIRE-003",
    ruleVersion: "1.0.0",
    ruleTitle: "Fire Safety Certificate (NOC) Current Validity Check",
    officialSource: "AICTE APH 2024-2027 Clause 2.3.4 & NBC Part IV",
    category: "MANDATORY_SAFETY_CERTIFICATE",
    severity: "DEFICIENCY",
    status: "OPEN",
    explanation: "Fire Safety NOC expired on 31-03-2026 prior to commencement of academic session 2026-2027 (01-07-2026).",
    expectedValue: "Valid through or beyond 2026-07-01",
    observedValue: "Expired on 2026-03-31",
    evidence: {
      documentId: "doc_05",
      documentTitle: "Fire Safety Certificate (State Fire NOC)",
      versionNumber: 1,
      pageNumber: 1,
      boundingBox: {
        ymin: 0.48,
        xmin: 0.20,
        ymax: 0.54,
        xmax: 0.80
      },
      extractedSnippet: "...this clearance is valid for a period of one year from the date of issue and expires on 31st March 2026...",
      confidence: 0.985,
      extractionMethod: "DIGITAL_PDF_TEXT"
    },
    verificationStatus: "VERIFIED_INTERNAL",
    recommendedAction: "Upload renewed Fire Safety NOC or formal validity extension endorsement from State Fire Services Department.",
    createdAt: "2026-10-24 08:35"
  },
  {
    id: "find_0044",
    applicationId: "app_9812",
    ruleCode: "RULE-EOA-FSR-005",
    ruleVersion: "1.0.0",
    ruleTitle: "Faculty-to-Student Ratio (FSR) Compliance",
    officialSource: "AICTE APH 2024-2027 Appendix 7 Table 7.1",
    category: "FACULTY_NORMS",
    severity: "WARNING",
    status: "OPEN",
    explanation: "Faculty count (35 full-time teachers) yields an FSR of 1:20.57 for 720 students, slightly exceeding 1:20.0 norm.",
    expectedValue: "Faculty >= 36 (FSR <= 1:20.0)",
    observedValue: "Faculty = 35 (FSR 1:20.57)",
    evidence: {
      documentId: "doc_08",
      documentTitle: "Faculty Cadre & Student Roster Summary",
      versionNumber: 1,
      pageNumber: 1,
      boundingBox: {
        ymin: 0.62,
        xmin: 0.15,
        ymax: 0.70,
        xmax: 0.85
      },
      extractedSnippet: "Total Regular Faculty in Position: 35 | Total Sanctioned Approved Intake: 720 Students | Computed Ratio: 1:20.57",
      confidence: 0.992,
      extractionMethod: "TABLE_PARSER"
    },
    verificationStatus: "VERIFIED_INTERNAL",
    recommendedAction: "Provide updated appointment roster with one additional faculty join confirmation or adjust applied intake.",
    createdAt: "2026-10-24 08:35"
  }
];

export const syntheticRules = [
  {
    ruleCode: "RULE-EOA-LAND-001",
    title: "Adequate Built-Up Area & FSI/FAR Compliance",
    officialSource: "AICTE APH 2024-2027, App. 4 Clause 4.1",
    category: "LAND_NORMS",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Registered lease >= 30 years | Built-up area accommodated under local FSI/FAR norms"
  },
  {
    ruleCode: "RULE-EOA-BCC-002",
    title: "Mandatory Building Completion Evidence (OC / CC / Form D / Building License)",
    officialSource: "AICTE APH 2024-2027, Chapter II Clause 2.3.2",
    category: "MANDATORY_CERTIFICATE",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Issued by competent municipal / town planning authority (Max 2 yrs for provisional)"
  },
  {
    ruleCode: "RULE-EOA-FIRE-003",
    title: "Fire Safety Certificate (NOC) Current Validity",
    officialSource: "AICTE APH 2024-2027, Clause 2.3.4 & NBC Part IV",
    category: "MANDATORY_SAFETY_CERTIFICATE",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Must be valid on or beyond session start date (01-07-2026)"
  },
  {
    ruleCode: "RULE-EOA-STRUCT-004",
    title: "Structural Stability Certificate (After 30 Years from Completion or Modifications)",
    officialSource: "AICTE APH 2024-2027, Chapter II Clause 2.14.6",
    category: "MANDATORY_SAFETY_CERTIFICATE",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Mandatory after expiry of 30 years from Completion Certificate issue or major modifications | 5-year certificate validity"
  },
  {
    ruleCode: "RULE-EOA-FSR-005",
    title: "Faculty-to-Student Ratio (FSR) Compliance",
    officialSource: "AICTE APH 2024-2027, Annexure-5",
    category: "FACULTY_NORMS",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "UG Engg & Tech: 1:20 | PG Management (MBA/PGDM) & MCA: 1:20 | Diploma: 1:25 | PG Engg: 1:15"
  },
  {
    ruleCode: "RULE-EOA-CROSS-006",
    title: "Land Title Deed vs Land Use Survey Match",
    officialSource: "AICTE APH 2024-2027, Clause 4.2",
    category: "CROSS_DOCUMENT_CONSISTENCY",
    severity: "WARNING",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Title deed survey numbers must be a subset of land use order"
  },
  {
    ruleCode: "RULE-EOA-CROSS-007",
    title: "Approved Building Plan vs Completion Built-Up Area",
    officialSource: "AICTE APH 2024-2027, App. 4 Clause 4.3",
    category: "CROSS_DOCUMENT_CONSISTENCY",
    severity: "WARNING",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Completed area must be >= 90% of sanctioned instructional area"
  },
  {
    ruleCode: "RULE-EOA-PREV-008",
    title: "Previous Year AICTE Approval Intake Baseline",
    officialSource: "AICTE APH 2024-2027, Chapter II Clause 2.1",
    category: "INTAKE_RECONCILIATION",
    severity: "DEFICIENCY",
    status: "APPROVED_FOR_PROTOTYPE_USE",
    norm: "Applied intake must reconcile with previous year extension letter"
  }
];

export const syntheticAuditEvents = [
  {
    id: "evt_001",
    timestamp: "2026-10-24 08:15:22",
    actor: "applicant@institution.test",
    role: "INSTITUTION",
    action: "DOCUMENT_UPLOAD",
    entity: "doc_01 (Land Title Deed v1)",
    details: "Uploaded file 'Land_Title_Deed_Registered_5.2Acres.pdf' (1.8MB, SHA-256: 8f4e2c8a...)"
  },
  {
    id: "evt_002",
    timestamp: "2026-10-24 08:25:40",
    actor: "applicant@institution.test",
    role: "INSTITUTION",
    action: "DOCUMENT_UPLOAD",
    entity: "doc_05 (Fire Safety NOC v1)",
    details: "Uploaded file 'Fire_Safety_Certificate_Expired.pdf' (812KB, SHA-256: 3a91b2c4...)"
  },
  {
    id: "evt_003",
    timestamp: "2026-10-24 08:35:10",
    actor: "applicant@institution.test",
    role: "INSTITUTION",
    action: "VALIDATION_RUN",
    entity: "app_9812",
    details: "Automated Pre-Scrutiny Run executed across 8 documents. 2 Deficiencies and 1 Warning flagged."
  },
  {
    id: "evt_004",
    timestamp: "2026-10-24 09:12:05",
    actor: "reviewer@reviewer.test",
    role: "REVIEWER",
    action: "SCRUTINY_OBSERVATION",
    entity: "app_9812",
    details: "Reviewer concurred with Fire Safety NOC expiry finding #find_0043. Notice dispatched."
  }
];
