# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Regulatory Rule Engine & Cross-Matching Service (backend/services/regulatory_engine.py)

import json
import logging
import math
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import utc_now
from backend.models.application import Application
from backend.models.institution import Institution
from backend.models.document import Document, DocumentVersion
from backend.models.extraction import ExtractedField, DocumentProcessingRun, DocumentPage
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, ValidationRun, Finding
from backend.services.audit_service import create_audit_event

logger = logging.getLogger("aicte-regulatory-engine")


# -------------------------------------------------------------------------
# Canonical Seed Catalog (from docs/REGULATORY_RULE_CATALOG.md)
# -------------------------------------------------------------------------

SEED_RULES: List[Dict[str, Any]] = [
    {
        "rule_code": "RULE-EOA-LAND-001",
        "title": "Adequate Built-Up Area & FSI/FAR Compliance",
        "category": "LAND_NORMS",
        "official_source": "AICTE APH 2024-2027, Appendix 4, Clause 4.1",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Verifies that the institution possesses valid registered land title (or lease >= 30 years) accommodating the approved built-up area under competent authority FSI/FAR regulations per AICTE APH Appendix 4.",
        "parameters": {
            "min_lease_years": 30,
            "document_type": "LAND_TITLE_DEED",
            "required_fields": ["survey_numbers_list"]
        },
        "recommended_action": "Provide registered land title deed (or registered lease deed >= 30 years) with local planning authority FSI/FAR sanction."
    },
    {
        "rule_code": "RULE-EOA-BCC-002",
        "title": "Mandatory Building Completion Evidence (OC / CC / Form D / Building License)",
        "category": "MANDATORY_CERTIFICATE",
        "official_source": "AICTE APH 2024-2027, Chapter II, Clause 2.3.2",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Verifies statutory building completion evidence issued by a competent municipal or town planning authority (Occupancy Certificate, Completion Certificate, Building License, or Form D). Provisional certificates are limited to 2 consecutive academic years. Standalone PWD structural clearance is not accepted as completion evidence.",
        "parameters": {
            "accepted_completion_types": ["OCCUPANCY_CERTIFICATE", "COMPLETION_CERTIFICATE", "BUILDING_LICENSE", "FORM_D", "FULL_COMPLETION", "SANCTIONED_PHASE_COMPLETE"],
            "max_provisional_years": 2,
            "document_type": "BUILDING_COMPLETION",
            "required_fields": ["completion_status", "certificate_issuing_authority"]
        },
        "recommended_action": "Upload Occupancy Certificate, Completion Certificate, Building License, or Form D issued by competent municipal or development authority."
    },
    {
        "rule_code": "RULE-EOA-FIRE-003",
        "title": "Fire Safety Certificate (NOC) Current Validity Check",
        "category": "MANDATORY_SAFETY_CERTIFICATE",
        "official_source": "AICTE APH 2024-2027, Clause 2.3.4 & NBC Part IV",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Verifies that the Fire Safety NOC is valid on or after the commencement of the applied academic session.",
        "parameters": {
            "document_type": "FIRE_SAFETY_NOC",
            "date_field_key": "valid_until_date"
        },
        "recommended_action": "Upload renewed Fire Safety NOC or formal extension letter from State Fire Services Department."
    },
    {
        "rule_code": "RULE-EOA-STRUCT-004",
        "title": "Structural Stability Certificate (Building Age >= 30 Years or Modifications)",
        "category": "MANDATORY_SAFETY_CERTIFICATE",
        "official_source": "AICTE APH 2024-2027, Chapter II, Clause 2.14.6",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Mandatory for buildings 30 years or older (measured from Completion Certificate issue date) or following major structural modifications, per AICTE APH Chapter II, Clause 2.14.6. Certificate must be issued by an empanelled structural engineer within a 5-year validity period.",
        "parameters": {
            "age_threshold_years": 30.0,
            "max_validity_years": 5.0,
            "document_type": "STRUCTURAL_STABILITY",
            "registration_field_key": "engineer_registration_number",
            "soundness_field_key": "structural_soundness_certified"
        },
        "recommended_action": "Submit structural stability certificate issued within the past 5 years by an empanelled structural engineer if building age is 30 years or older."
    },
    {
        "rule_code": "RULE-EOA-FSR-005",
        "title": "Faculty-to-Student Ratio (FSR) Compliance",
        "category": "FACULTY_NORMS",
        "official_source": "AICTE APH 2024-2027, Annexure-5, Section 5.2",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Evaluates full-time qualified faculty against programme-specific norms per AICTE APH Annexure-5 Section 5.2 (1:20 for Under-Graduate Engineering & Technology, 1:25 for Diploma, 1:20 for Management/MCA, 1:15 for Pharmacy, 1:10 for Architecture).",
        "parameters": {
            "programme_norms": {
                "ENGINEERING_TECHNOLOGY": 20.0,
                "POLYTECHNIC_DIPLOMA": 25.0,
                "MANAGEMENT": 20.0,
                "MANAGEMENT_STUDIES": 20.0,
                "MCA": 20.0,
                "COMPUTER_APPLICATIONS": 20.0,
                "PHARMACY": 15.0,
                "ARCHITECTURE": 10.0,
                "ARCHITECTURE_PLANNING": 10.0
            },
            "default_ratio": 20.0,
            "document_type": "FACULTY_ROSTER",
            "faculty_field_key": "total_qualified_faculty_count"
        },
        "recommended_action": "Provide updated faculty roster with approved faculty selections meeting programme-specific ratio or adjust applied intake."
    },
    {
        "rule_code": "RULE-EOA-CROSS-006",
        "title": "Cross-Document Survey / Khasra Number Consistency Check",
        "category": "CROSS_DOCUMENT_CONSISTENCY",
        "official_source": "AICTE APH 2024-2027, Clause 4.2",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "WARNING",
        "description": "Consistency check: Cross-matches survey/khasra numbers to flag potential discrepancies for human review. A mismatch may reflect clerical differences, OCR variance, or a genuine issue — human verification required before any conclusion.",
        "parameters": {
            "doc1_type": "LAND_TITLE_DEED",
            "doc1_field": "survey_numbers",
            "doc2_type": "LAND_USE_CERTIFICATE",
            "doc2_field": "survey_number"
        },
        "recommended_action": "Verify survey numbers across land records during human scrutiny to determine if supplemental conversion orders or revenue entries cover the parcels."
    },
    {
        "rule_code": "RULE-EOA-CROSS-007",
        "title": "Sanctioned vs Completed Built-Up Area Cross-Match",
        "category": "CROSS_DOCUMENT_CONSISTENCY",
        "official_source": "AICTE APH 2024-2027, Appendix 4, Clause 4.3",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "WARNING",
        "description": "Compares sanctioned instructional built-up area from Approved Building Plan against completed area in Building Completion Certificate.",
        "parameters": {
            "doc1_type": "APPROVED_BUILDING_PLAN",
            "doc1_field": "total_built_up_area_sqm",
            "doc2_type": "BUILDING_COMPLETION",
            "doc2_field": "completed_builtup_area_sqm",
            "min_ratio": 0.90,
            "max_ratio": 1.10
        },
        "recommended_action": "Submit compounding approval or revised municipal sanction plan if constructed area deviates."
    },
    {
        "rule_code": "RULE-EOA-PREV-008",
        "title": "Previous Year AICTE Approval Intake Baseline Check",
        "category": "INTAKE_RECONCILIATION",
        "official_source": "AICTE APH 2024-2027, Chapter II, Clause 2.1",
        "status": "APPROVED_FOR_PROTOTYPE_USE",
        "version_number": 1,
        "severity": "DEFICIENCY",
        "description": "Verifies that applied intake in standard EoA does not exceed previously approved intake without an accompanying expansion sanction.",
        "parameters": {
            "document_type": "PREV_AICTE_APPROVAL",
            "intake_field_key": "approved_total_intake"
        },
        "recommended_action": "Reconcile applied program seats with previous year extension letter or apply under Expansion of Intake category."
    },
    # Draft Rules (missing official sources, inactive for prototype execution)
    {
        "rule_code": "RULE-DRAFT-BANK-009",
        "title": "Joint Fixed Deposit (FDR) Lien Period Check",
        "category": "FINANCIAL_NORMS",
        "official_source": "State Technical Board Bylaws (Unverified Regional Amendment)",
        "status": "DRAFT_MISSING_OFFICIAL_SOURCE",
        "version_number": 1,
        "severity": "WARNING",
        "description": "Draft check for joint FDR lien period validity. Deactivated in Step 4 regulatory correction: No matching evaluation logic implemented and regional state board official source remains unverified per APH audit.",
        "parameters": {"min_lien_years": 8},
        "recommended_action": "Awaiting regional board clarification on joint FDR validity."
    },
    {
        "rule_code": "RULE-DRAFT-PARK-010",
        "title": "Campus Parking Slot Allotment Calculation",
        "category": "INFRASTRUCTURE_NORMS",
        "official_source": "Local Municipal Bylaws (Unverified Urban / Rural Boundary)",
        "status": "DRAFT_MISSING_OFFICIAL_SOURCE",
        "version_number": 1,
        "severity": "INFO",
        "description": "Draft parking area ratio check. Municipal corporation bylaws differ between metro and rural municipal boundaries.",
        "parameters": {"sqm_per_vehicle": 25.0},
        "recommended_action": "Refer to local town planning municipal building bylaws."
    }
]


def seed_regulatory_rules(db: Session) -> None:
    """Idempotently seeds the official regulatory rules into the database."""
    for item in SEED_RULES:
        rule = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == item["rule_code"]).first()
        if not rule:
            rule = RegulatoryRule(
                rule_code=item["rule_code"],
                title=item["title"],
                category=item["category"],
                official_source=item["official_source"],
                status=item["status"],
                is_active=(item["status"] == "APPROVED_FOR_PROTOTYPE_USE")
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)
        else:
            rule.official_source = item["official_source"]
            rule.title = item["title"]
            rule.category = item["category"]
            rule.status = item["status"]
            if item["status"] == "DRAFT_MISSING_OFFICIAL_SOURCE":
                rule.is_active = False
            db.commit()

        version = db.query(RegulatoryRuleVersion).filter(
            RegulatoryRuleVersion.rule_id == rule.id,
            RegulatoryRuleVersion.version_number == item["version_number"]
        ).first()

        if not version:
            version = RegulatoryRuleVersion(
                rule_id=rule.id,
                version_number=item["version_number"],
                description=item["description"],
                parameters_json=json.dumps(item["parameters"]),
                severity=item["severity"],
                recommended_action=item["recommended_action"],
                is_active=rule.is_active,
                approved_at=utc_now() if rule.is_active else None
            )
            db.add(version)
            db.commit()
        else:
            version.description = item["description"]
            version.parameters_json = json.dumps(item["parameters"])
            version.severity = item["severity"]
            version.recommended_action = item["recommended_action"]
            version.is_active = rule.is_active
            db.commit()


# -------------------------------------------------------------------------
# Helper Functions: Survey Normalization, Date Parsing & Field Lookups
# -------------------------------------------------------------------------

def normalize_survey_set(raw: str) -> set:
    """Normalizes survey number strings into clean comparable tokens."""
    if not raw:
        return set()
    cleaned = raw.replace("and", ",").replace("&", ",").replace(";", ",")
    tokens = re.split(r"[\s,]+", cleaned)
    norm = set()
    for t in tokens:
        clean_t = re.sub(r"[^a-zA-Z0-9/]", "", t).strip().upper()
        if clean_t:
            norm.add(clean_t)
    return norm


def parse_date_safely(raw: str) -> Optional[datetime]:
    """Parses date string safely into datetime object."""
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def add_calendar_years(dt: datetime, years: int) -> datetime:
    """Safely adds exact calendar years, handling leap year Feb 29 to Feb 28."""
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, month=2, day=28)



# -------------------------------------------------------------------------
# Core Regulatory Engine Class
# -------------------------------------------------------------------------

class RegulatoryEngine:
    def __init__(self, db: Session):
        self.db = db
        # Ensure rules exist in DB
        seed_regulatory_rules(self.db)

    def get_latest_extracted_fields(self, application_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Assembles a lookup of latest extracted fields for each document type in the application.
        Returns: {
            "FIRE_SAFETY_NOC": {
                "document": Document,
                "version": DocumentVersion,
                "fields": { "field_key": ExtractedField, ... }
            }, ...
        }
        """
        docs = self.db.query(Document).filter(Document.application_id == application_id).all()
        lookup = {}
        for d in docs:
            # Get latest uploaded version
            v = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == d.id
            ).order_by(DocumentVersion.version_number.desc()).first()

            if not v:
                lookup[d.document_type] = {
                    "document": d,
                    "version": None,
                    "fields": {}
                }
                continue

            fields = self.db.query(ExtractedField).filter(
                ExtractedField.document_version_id == v.id
            ).all()

            field_map = {f.field_key: f for f in fields}
            lookup[d.document_type] = {
                "document": d,
                "version": v,
                "fields": field_map
            }
        return lookup

    def evaluate_application(
        self,
        application_id: str,
        triggered_by_user_id: str,
        trigger_type: str = "INITIAL_PRE_SCRUTINY"
    ) -> Tuple[ValidationRun, List[Finding]]:
        """
        Executes deterministic regulatory rule evaluation against latest extracted document evidence.
        Produces and persists immutable ValidationRun and Finding records.
        """
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        institution = self.db.query(Institution).filter(Institution.id == app.institution_id).first()
        if not institution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution context missing.")

        # Determine next run number
        last_run = self.db.query(ValidationRun).filter(
            ValidationRun.application_id == application_id
        ).order_by(ValidationRun.run_number.desc()).first()
        next_run_number = (last_run.run_number + 1) if last_run else 1

        # Create ValidationRun record
        run = ValidationRun(
            application_id=app.id,
            run_number=next_run_number,
            triggered_by_user_id=triggered_by_user_id,
            trigger_type=trigger_type,
            started_at=utc_now(),
            status="RUNNING"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        # Assemble latest extracted fields
        doc_data = self.get_latest_extracted_fields(application_id)

        # Load active approved rules only
        active_rules = self.db.query(RegulatoryRule).filter(
            RegulatoryRule.status == "APPROVED_FOR_PROTOTYPE_USE",
            RegulatoryRule.is_active == True
        ).all()

        findings: List[Finding] = []
        deficiencies = 0
        warnings = 0
        passed = 0
        unable_count = 0

        # Determine academic session start date
        session_year = 2026
        if app.academic_year:
            m = re.search(r"(\d{4})", app.academic_year)
            if m:
                session_year = int(m.group(1))
        academic_session_start = datetime(session_year, 7, 1)  # July 1st of session year

        for rule in active_rules:
            # Get active version
            version = self.db.query(RegulatoryRuleVersion).filter(
                RegulatoryRuleVersion.rule_id == rule.id,
                RegulatoryRuleVersion.is_active == True
            ).order_by(RegulatoryRuleVersion.version_number.desc()).first()

            if not version:
                continue

            params = json.loads(version.parameters_json)
            code = rule.rule_code

            # -------------------------------------------------------------
            # Rule 1: RULE-EOA-LAND-001 (Built-Up Area & FSI/FAR Compliance)
            # -------------------------------------------------------------
            if code == "RULE-EOA-LAND-001":
                doc_info = doc_data.get("LAND_TITLE_DEED")
                plan_info = doc_data.get("APPROVED_BUILDING_PLAN")

                if not doc_info or not doc_info["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="DEFICIENCY",
                        outcome="DEFICIENCY_DETECTED",
                        title="Missing Mandatory Land Title Deed",
                        explanation="Registered Land Title Deed or Registered Lease Deed is missing. AICTE APH Appendix 4 mandates valid registered ownership or lease agreement for institutional operations.",
                        expected_value="Registered Title Deed / Lease Deed (>= 30 Years)",
                        observed_value="Document Not Uploaded",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="MISMATCH",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    deficiencies += 1
                else:
                    # 1. Lease duration check (if leased)
                    lease_field = doc_info["fields"].get("lease_duration_years")
                    lease_years = None
                    if lease_field and lease_field.normalized_value not in ["ABSENT", None, ""]:
                        try:
                            lease_years = int(float(lease_field.normalized_value))
                        except (ValueError, TypeError):
                            pass

                    min_lease = params.get("min_lease_years", 30)
                    if lease_years is not None and lease_years < min_lease:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="DEFICIENCY",
                            outcome="DEFICIENCY_DETECTED",
                            title="Registered Lease Duration Below 30 Years",
                            explanation=f"Registered lease duration is {lease_years} years, which is below the mandatory minimum of {min_lease} years required under AICTE APH Appendix 4.",
                            expected_value=f"Registered Lease Duration >= {min_lease} Years",
                            observed_value=f"{lease_years} Years",
                            document_id=doc_info["document"].id,
                            document_version_id=doc_info["version"].id,
                            evidence_page_number=lease_field.page_number,
                            evidence_bounding_box_json=json.dumps(lease_field.bounding_box),
                            evidence_raw_text=lease_field.raw_value,
                            evidence_confidence=lease_field.confidence,
                            verification_status="MISMATCH",
                            recommended_action="Submit registered lease agreement amendment confirming a minimum 30-year lease period."
                        )
                        findings.append(f)
                        deficiencies += 1
                    else:
                        # 2. FSI / FAR Built-Up Area accommodation check
                        far_field = doc_info["fields"].get("permissible_far") or (plan_info["fields"].get("permissible_far") if plan_info and plan_info["version"] else None)
                        land_field = doc_info["fields"].get("contiguous_land_area_acres") or doc_info["fields"].get("land_area_acres")

                        far_val = None
                        if far_field and far_field.normalized_value not in ["ABSENT", None, ""]:
                            try:
                                far_val = float(far_field.normalized_value)
                            except (ValueError, TypeError):
                                pass

                        land_acres = None
                        if land_field and land_field.normalized_value not in ["ABSENT", None, ""]:
                            try:
                                land_acres = float(land_field.normalized_value)
                            except (ValueError, TypeError):
                                pass

                        builtup_field = plan_info["fields"].get("sanctioned_builtup_area_sqm") if plan_info and plan_info["version"] else None
                        builtup_val = None
                        if builtup_field and builtup_field.normalized_value not in ["ABSENT", None, ""]:
                            try:
                                builtup_val = float(builtup_field.normalized_value)
                            except (ValueError, TypeError):
                                pass

                        if far_val is not None and land_acres is not None:
                            # Land area in sq.m = land_acres * 4046.86
                            max_permissible_builtup = land_acres * 4046.86 * far_val
                            if builtup_val is not None and builtup_val > max_permissible_builtup:
                                f = Finding(
                                    validation_run_id=run.id,
                                    application_id=app.id,
                                    rule_version_id=version.id,
                                    rule_code=code,
                                    rule_title=rule.title,
                                    category=rule.category,
                                    severity="DEFICIENCY",
                                    outcome="DEFICIENCY_DETECTED",
                                    title="Built-up Area Exceeds Permissible FSI/FAR",
                                    explanation=f"Sanctioned built-up area of {builtup_val:.1f} Sq.m exceeds permissible FAR capacity of {max_permissible_builtup:.1f} Sq.m (Land: {land_acres:.2f} Acres, FAR: {far_val:.2f}) under local authority regulations.",
                                    expected_value=f"Built-up Area <= {max_permissible_builtup:.1f} Sq.m (FAR {far_val:.2f})",
                                    observed_value=f"{builtup_val:.1f} Sq.m",
                                    document_id=doc_info["document"].id,
                                    document_version_id=doc_info["version"].id,
                                    evidence_page_number=far_field.page_number if far_field else 1,
                                    evidence_bounding_box_json=json.dumps(far_field.bounding_box) if far_field else None,
                                    evidence_raw_text=far_field.raw_value if far_field else None,
                                    evidence_confidence=far_field.confidence if far_field else 1.0,
                                    verification_status="MISMATCH",
                                    recommended_action="Submit compounding certificate or acquire additional land to satisfy FSI/FAR norms."
                                )
                                findings.append(f)
                                deficiencies += 1
                            else:
                                builtup_str = f"{builtup_val:.1f} Sq.m" if builtup_val is not None else "sanctioned area"
                                f = Finding(
                                    validation_run_id=run.id,
                                    application_id=app.id,
                                    rule_version_id=version.id,
                                    rule_code=code,
                                    rule_title=rule.title,
                                    category=rule.category,
                                    severity="INFO",
                                    outcome="NO_ISSUE_DETECTED",
                                    title="Land Area & FSI/FAR Compliance Verified",
                                    explanation=f"Land holding ({land_acres:.2f} Acres) and sanctioned FAR ({far_val:.2f}) adequately accommodate the institutional infrastructure ({builtup_str}) under AICTE APH Appendix 4.",
                                    expected_value=f"Permissible Built-up Area >= Sanctioned Area under FAR {far_val:.2f}",
                                    observed_value=f"Land: {land_acres:.2f} Acres, FAR: {far_val:.2f}",
                                    document_id=doc_info["document"].id,
                                    document_version_id=doc_info["version"].id,
                                    evidence_page_number=land_field.page_number if land_field else 1,
                                    evidence_bounding_box_json=json.dumps(land_field.bounding_box) if land_field else None,
                                    evidence_raw_text=land_field.raw_value if land_field else None,
                                    evidence_confidence=land_field.confidence if land_field else 1.0,
                                    verification_status="VERIFIED_INTERNAL",
                                    recommended_action="No remediation needed."
                                )
                                findings.append(f)
                                passed += 1
                        else:
                            # FAR is not declared / evidence unavailable -> Honest unresolved authority verification status
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="UNABLE_TO_EVALUATE",
                                title="FSI/FAR Verification Pending Local Authority Confirmation",
                                explanation="AICTE APH 2024–2027 Appendix 4 permits institutions on land meeting local authority FSI/FAR norms without rigid universal acreage floors. Local planning authority FSI/FAR limits and zonal regulations require human scrutiny or authority verification to confirm vertical campus compliance.",
                                expected_value="Competent Local Authority FSI/FAR Sanction & Compliance",
                                observed_value=f"Land Area: {land_field.raw_value if land_field else 'Extracted'} (FAR undeclared)",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=land_field.page_number if land_field else 1,
                                evidence_bounding_box_json=json.dumps(land_field.bounding_box) if land_field else None,
                                evidence_raw_text=land_field.raw_value if land_field else None,
                                evidence_confidence=land_field.confidence if land_field else 1.0,
                                verification_status="UNVERIFIED",
                                recommended_action="Submit local town planning authority FSI/FAR endorsement or sanctioned building permit showing permissible floor area."
                            )
                            findings.append(f)
                            unable_count += 1

            # -------------------------------------------------------------
            # Rule 2: RULE-EOA-BCC-002 (Building Completion Evidence Check)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-BCC-002":
                doc_info = doc_data.get("BUILDING_COMPLETION")
                if not doc_info or not doc_info["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="DEFICIENCY",
                        outcome="DEFICIENCY_DETECTED",
                        title="Missing Building Completion Certificate",
                        explanation="Mandatory Building Completion / Occupancy Certificate (OC / CC / Form D / Building License) has not been uploaded. Chapter II, Clause 2.3.2 requires valid local authority certification.",
                        expected_value="Valid OC / CC / Form D / Building License from Competent Local Authority",
                        observed_value="Document Not Uploaded",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="MISMATCH",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    deficiencies += 1
                else:
                    status_field = doc_info["fields"].get("completion_status")
                    auth_field = doc_info["fields"].get("certificate_issuing_authority")
                    
                    status_val = status_field.normalized_value.upper() if status_field else ""
                    raw_val = status_field.raw_value.upper() if status_field else ""
                    auth_val = auth_field.normalized_value if auth_field else "Competent Authority"

                    # 1. PWD Structural Clearance Rejection Check
                    if status_val == "PWD_STRUCTURAL_CLEARANCE" or "PWD STRUCTURAL CLEARANCE" in raw_val:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="DEFICIENCY",
                            outcome="DEFICIENCY_DETECTED",
                            title="PWD Structural Clearance Not Accepted as Building Completion",
                            explanation="PWD Structural Clearance certifies structural soundness but does not constitute an Occupancy Certificate, Completion Certificate, Building License, or Form D issued by the competent town planning / municipal authority as required by AICTE APH Chapter II, Clause 2.3.2.",
                            expected_value="Occupancy Certificate / Completion Certificate / Building License / Form D",
                            observed_value="PWD Structural Clearance Only",
                            document_id=doc_info["document"].id,
                            document_version_id=doc_info["version"].id,
                            evidence_page_number=status_field.page_number if status_field else 1,
                            evidence_bounding_box_json=json.dumps(status_field.bounding_box) if status_field else None,
                            evidence_raw_text=status_field.raw_value if status_field else None,
                            evidence_confidence=status_field.confidence if status_field else 1.0,
                            verification_status="MISMATCH",
                            recommended_action="Upload an authorized Occupancy Certificate, Completion Certificate, Building License, or Form D issued by the competent municipal/planning body."
                        )
                        findings.append(f)
                        deficiencies += 1

                    # 2. Provisional Occupancy Certificate 2-year consecutive limit check
                    elif status_val == "PROVISIONAL_OCCUPANCY" or "PROVISIONAL" in status_val or "PROVISIONAL" in raw_val:
                        prov_years_field = doc_info["fields"].get("provisional_duration_years")
                        prov_years = None
                        if prov_years_field and prov_years_field.normalized_value not in ["ABSENT", None, ""]:
                            try:
                                prov_years = int(float(prov_years_field.normalized_value))
                            except (ValueError, TypeError):
                                pass

                        if prov_years is not None and prov_years > 2:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Provisional Occupancy Certificate Limit Exceeded (> 2 Academic Years)",
                                explanation=f"Provisional Occupancy Certificate has been utilized for {prov_years} consecutive academic years. AICTE APH Chapter II restricts provisional occupancy to a strict maximum limit of two consecutive academic years.",
                                expected_value="Provisional Occupancy <= 2 Consecutive Academic Years",
                                observed_value=f"{prov_years} Consecutive Academic Years",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=status_field.page_number if status_field else 1,
                                evidence_bounding_box_json=json.dumps(status_field.bounding_box) if status_field else None,
                                evidence_raw_text=status_field.raw_value if status_field else None,
                                evidence_confidence=status_field.confidence if status_field else 1.0,
                                verification_status="MISMATCH",
                                recommended_action="Obtain and submit final Occupancy Certificate or Completion Certificate from local municipal corporation."
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Provisional Occupancy Certificate Verified (Within 2-Year Limit)",
                                explanation=f"Provisional Occupancy Certificate issued by '{auth_val}' is within the statutory two-consecutive-academic-year limit under AICTE APH Chapter II.",
                                expected_value="Competent Municipal Authority Completion Certification",
                                observed_value=f"Provisional Occupancy ({prov_years if prov_years else 1} Year) issued by {auth_val}",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=status_field.page_number if status_field else 1,
                                evidence_bounding_box_json=json.dumps(status_field.bounding_box) if status_field else None,
                                evidence_raw_text=status_field.raw_value if status_field else None,
                                evidence_confidence=status_field.confidence if status_field else 1.0,
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

                    # 3. Standard Accepted Alternatives: OC, CC, Building License, Form D
                    else:
                        accepted_types = ["OCCUPANCY_CERTIFICATE", "COMPLETION_CERTIFICATE", "BUILDING_LICENSE", "FORM_D", "FULL_COMPLETION", "SANCTIONED_PHASE_COMPLETE"]
                        is_accepted = any(t in status_val for t in accepted_types) or any(kw in raw_val for kw in ["OCCUPANCY", "COMPLETION", "FORM D", "FORM-D", "BUILDING LICENSE", "BUILDING PERMIT", "FULLY COMPLETED", "PHASE COMPLETE", "SANCTIONED"])

                        if not is_accepted:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Building Completion Evidence Unrecognized or Invalid",
                                explanation=f"Building completion document does not furnish a recognised statutory certificate (Occupancy Certificate, Completion Certificate, Building License, or Form D). Observed status: '{status_field.raw_value if status_field else 'Unspecified'}'.",
                                expected_value="Occupancy Certificate / Completion Certificate / Building License / Form D",
                                observed_value=status_field.raw_value if status_field else "Missing Status",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=status_field.page_number if status_field else 1,
                                evidence_bounding_box_json=json.dumps(status_field.bounding_box) if status_field else None,
                                evidence_raw_text=status_field.raw_value if status_field else None,
                                evidence_confidence=status_field.confidence if status_field else 1.0,
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Building Completion Certificate Verified",
                                explanation=f"Building completion certificate ({status_val or 'Statutory Certificate'}) issued by '{auth_val}' confirms instructional completion under AICTE APH Chapter II.",
                                expected_value="Competent Municipal Authority Completion Certification",
                                observed_value=f"{status_val or 'Certified'} issued by {auth_val}",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=status_field.page_number if status_field else 1,
                                evidence_bounding_box_json=json.dumps(status_field.bounding_box) if status_field else None,
                                evidence_raw_text=status_field.raw_value if status_field else None,
                                evidence_confidence=status_field.confidence if status_field else 1.0,
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

            # -------------------------------------------------------------
            # Rule 3: RULE-EOA-FIRE-003 (Fire Safety Certificate NOC Validity)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-FIRE-003":
                doc_info = doc_data.get("FIRE_SAFETY_NOC")
                session_start_str = academic_session_start.strftime("%Y-%m-%d")

                if not doc_info or not doc_info["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="DEFICIENCY",
                        outcome="DEFICIENCY_DETECTED",
                        title="Missing Fire Safety Certificate (NOC)",
                        explanation="Mandatory Fire Safety NOC is missing. AICTE Clause 2.3.4 & NBC Part IV require affirmative fire safety clearance.",
                        expected_value=f"Valid Fire Safety NOC on or after {session_start_str}",
                        observed_value="Document Not Uploaded",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="MISMATCH",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    deficiencies += 1
                else:
                    date_field = doc_info["fields"].get("valid_until_date")
                    if not date_field:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Fire NOC Validity Date Inconclusive",
                            explanation="Fire Safety Certificate is uploaded, but expiry / validity date could not be parsed with certainty from extraction tokens.",
                            expected_value=f"Valid on or after {session_start_str}",
                            observed_value="Date Unparseable",
                            document_id=doc_info["document"].id,
                            document_version_id=doc_info["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action="Upload legible Fire Safety NOC showing clear validity end date."
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        parsed_dt = parse_date_safely(date_field.normalized_value)
                        if not parsed_dt:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="WARNING",
                                outcome="UNABLE_TO_EVALUATE",
                                title="Fire NOC Date Format Ambiguous",
                                explanation=f"Fire NOC validity date string '{date_field.raw_value}' could not be normalized into ISO-8601 calendar date.",
                                expected_value=f"Valid on or after {session_start_str}",
                                observed_value=date_field.raw_value,
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                verification_status="UNVERIFIED",
                                recommended_action="Provide renewed Fire NOC with unambiguous expiry date."
                            )
                            findings.append(f)
                            unable_count += 1
                        elif parsed_dt < academic_session_start:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Expired Fire Safety Certificate",
                                explanation=f"Fire Safety Certificate expired on {parsed_dt.strftime('%Y-%m-%d')} prior to commencement of academic session {app.academic_year} ({session_start_str}).",
                                expected_value=f"Valid on or after {session_start_str}",
                                observed_value=parsed_dt.strftime("%Y-%m-%d"),
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=date_field.page_number,
                                evidence_bounding_box_json=json.dumps(date_field.bounding_box),
                                evidence_raw_text=date_field.raw_value,
                                evidence_confidence=date_field.confidence,
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Fire Safety NOC Currently Valid",
                                explanation=f"Fire Safety Certificate is valid through {parsed_dt.strftime('%Y-%m-%d')}, covering academic session commencement ({session_start_str}).",
                                expected_value=f"Valid on or after {session_start_str}",
                                observed_value=parsed_dt.strftime("%Y-%m-%d"),
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=date_field.page_number,
                                evidence_bounding_box_json=json.dumps(date_field.bounding_box),
                                evidence_raw_text=date_field.raw_value,
                                evidence_confidence=date_field.confidence,
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

            # -------------------------------------------------------------
            # Rule 4: RULE-EOA-STRUCT-004 (Structural Stability Certification)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-STRUCT-004":
                bcc_info = doc_data.get("BUILDING_COMPLETION")
                struct_info = doc_data.get("STRUCTURAL_STABILITY")

                # Check for major structural modification flag
                has_major_mod = False
                if bcc_info and bcc_info["version"]:
                    mod_field = bcc_info["fields"].get("has_major_modifications")
                    if mod_field and mod_field.normalized_value.lower() == "true":
                        has_major_mod = True
                if struct_info and struct_info["version"]:
                    mod_field = struct_info["fields"].get("has_major_modifications")
                    if mod_field and mod_field.normalized_value.lower() == "true":
                        has_major_mod = True

                # Determine completion status and date
                completion_status_field = bcc_info["fields"].get("completion_status") if (bcc_info and bcc_info["version"]) else None
                status_val = (completion_status_field.normalized_value or "").upper() if completion_status_field else ""
                raw_status = (completion_status_field.raw_value or "").upper() if completion_status_field else ""

                completion_field = None
                if bcc_info and bcc_info["version"]:
                    completion_field = bcc_info["fields"].get("issue_date") or bcc_info["fields"].get("completion_date")

                # AICTE APH Chapter II, Clause 2.14.6:
                # "The institution shall submit a Structural Stability Certificate from an empanelled structural engineer
                # after the expiry of thirty (30) years from the date of issue of the Completion Certificate.
                # The certificate is valid for five (5) years."
                # Note: Do not silently substitute an Occupancy Certificate date for the Completion Certificate date.
                is_pure_occupancy_doc = (
                    any(t in status_val for t in ["OCCUPANCY_CERTIFICATE", "BUILDING_LICENSE", "FORM_D", "PROVISIONAL_OCCUPANCY"])
                    and not any(k in raw_status for k in ["COMPLETION CERTIFICATE", "COMPLETED", "FULL COMPLETION"])
                )

                if not has_major_mod and is_pure_occupancy_doc:
                    # An Occupancy Certificate was uploaded without an explicit Completion Certificate.
                    # Per APH Clause 2.14.6, 30-year expiry is computed from Completion Certificate, not Occupancy Certificate.
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="WARNING",
                        outcome="UNABLE_TO_EVALUATE",
                        title="Building Age Unresolved — Completion Certificate Required (Occupancy Certificate Provided)",
                        explanation="The uploaded document is an Occupancy Certificate or local equivalent. AICTE APH Clause 2.14.6 computes the 30-year structural stability threshold specifically from the date of issue of the original Completion Certificate. Scrutiny verification required to verify original Completion Certificate date.",
                        expected_value="Building Completion Certificate Issue Date",
                        observed_value=f"Occupancy Certificate Provided ({completion_field.raw_value if completion_field else 'No Date'})",
                        document_id=bcc_info["document"].id if bcc_info else None,
                        document_version_id=bcc_info["version"].id if bcc_info and bcc_info["version"] else None,
                        verification_status="UNVERIFIED",
                        recommended_action="Submit original Building Completion Certificate or verify completion date during manual scrutiny."
                    )
                    findings.append(f)
                    unable_count += 1
                elif not completion_field or completion_field.normalized_value in ["ABSENT", None, ""]:
                    # Missing or unparseable completion date: unresolved applicability
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="WARNING",
                        outcome="UNABLE_TO_EVALUATE",
                        title="Building Age Unresolved — Completion Date Missing",
                        explanation="Completion Certificate issue date is missing or unparseable. Building age cannot be determined automatically. Requires manual scrutiny verification to determine if 30-year structural stability threshold applies under APH Clause 2.14.6.",
                        expected_value="Building Completion Issue Date to compute structure age",
                        observed_value="Completion Date Not Available",
                        document_id=bcc_info["document"].id if bcc_info else None,
                        document_version_id=bcc_info["version"].id if bcc_info and bcc_info["version"] else None,
                        verification_status="UNVERIFIED",
                        recommended_action="Verify building completion date from municipal sanction records during human scrutiny."
                    )
                    findings.append(f)
                    unable_count += 1
                else:
                    completion_dt = parse_date_safely(completion_field.normalized_value)
                    if not completion_dt:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Building Age Unresolved — Completion Date Ambiguous",
                            explanation=f"Building completion date '{completion_field.raw_value}' could not be parsed into a standard calendar date. Scrutiny verification required.",
                            expected_value="ISO-8601 Calendar Date for Building Completion",
                            observed_value=completion_field.raw_value,
                            document_id=bcc_info["document"].id,
                            document_version_id=bcc_info["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action="Submit legible copy of Completion Certificate showing unambiguous issue date."
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        # 30-year expiry boundary:
                        # AICTE APH Clause 2.14.6 requires certificate AFTER the expiry of 30 years from Completion Certificate.
                        # Exactly 30 years means the 30-year period has not expired yet.
                        # Expiry occurs when academic_session_start is strictly AFTER completion_dt + 30 calendar years.
                        thirty_year_expiry = add_calendar_years(completion_dt, 30)
                        is_after_30_years = academic_session_start > thirty_year_expiry
                        elapsed_days = (academic_session_start - completion_dt).days
                        elapsed_years_approx = elapsed_days / 365.25

                        if not is_after_30_years and not has_major_mod:
                            # 30-year period has NOT expired and no major modifications: Stability Cert NOT MANDATORY!
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Structural Stability Certificate Not Required (< 30 Years)",
                                explanation=f"Building completion date is {completion_dt.strftime('%Y-%m-%d')} (30-year period expires on {thirty_year_expiry.strftime('%Y-%m-%d')}). Structural Stability Certificate is mandated only after the expiry of 30 years under APH Clause 2.14.6.",
                                expected_value=f"Academic Session Start <= 30-Year Expiry Date ({thirty_year_expiry.strftime('%Y-%m-%d')})",
                                observed_value=f"Completed {completion_dt.strftime('%Y-%m-%d')} (Expires {thirty_year_expiry.strftime('%Y-%m-%d')})",
                                document_id=bcc_info["document"].id,
                                document_version_id=bcc_info["version"].id,
                                evidence_page_number=completion_field.page_number,
                                evidence_bounding_box_json=json.dumps(completion_field.bounding_box),
                                evidence_raw_text=completion_field.raw_value,
                                evidence_confidence=completion_field.confidence,
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1
                        else:
                            # 30 years expired OR major modifications: Mandatory!
                            if has_major_mod:
                                trigger_desc = "Major structural modification reported (requires stability assessment and building plan revalidation)"
                                title_desc = "Missing Mandatory Structural Stability Certificate & Plan Revalidation (Major Modifications Reported)"
                            else:
                                trigger_desc = f"Building completed on {completion_dt.strftime('%Y-%m-%d')} (30-year period expired on {thirty_year_expiry.strftime('%Y-%m-%d')})"
                                title_desc = "Missing Mandatory Structural Stability Certificate (Building Age >= 30 Years)"

                            if not struct_info or not struct_info["version"]:
                                f = Finding(
                                    validation_run_id=run.id,
                                    application_id=app.id,
                                    rule_version_id=version.id,
                                    rule_code=code,
                                    rule_title=rule.title,
                                    category=rule.category,
                                    severity="DEFICIENCY",
                                    outcome="DEFICIENCY_DETECTED",
                                    title=title_desc,
                                    explanation=f"{trigger_desc}. AICTE APH Chapter II, Clause 2.14.6 mandates structural stability certification by an empanelled structural engineer (valid for 5 years) and revalidated building plan where modifications occurred.",
                                    expected_value="Certified Structural Stability from Empanelled Engineer (and Plan Revalidation if modified)",
                                    observed_value="Document Not Uploaded",
                                    document_id=struct_info["document"].id if struct_info else None,
                                    verification_status="MISMATCH",
                                    recommended_action=version.recommended_action
                                )
                                findings.append(f)
                                deficiencies += 1
                            else:
                                # Inspect 5-year validity and soundness
                                cert_date_field = struct_info["fields"].get("certificate_date") or struct_info["fields"].get("issue_date")
                                cert_dt = parse_date_safely(cert_date_field.normalized_value) if cert_date_field and cert_date_field.normalized_value not in ["ABSENT", None, ""] else None

                                cert_valid_until = add_calendar_years(cert_dt, 5) if cert_dt else None
                                is_expired = cert_valid_until is not None and academic_session_start > cert_valid_until

                                reg_field = struct_info["fields"].get("engineer_registration_number")
                                sound_field = struct_info["fields"].get("structural_soundness_certified")
                                is_sound = sound_field and ("TRUE" in sound_field.normalized_value.upper() or "SOUND" in sound_field.normalized_value.upper())
                                has_reg = reg_field and len(reg_field.normalized_value.strip()) > 2

                                if not cert_dt:
                                    f = Finding(
                                        validation_run_id=run.id,
                                        application_id=app.id,
                                        rule_version_id=version.id,
                                        rule_code=code,
                                        rule_title=rule.title,
                                        category=rule.category,
                                        severity="WARNING",
                                        outcome="UNABLE_TO_EVALUATE",
                                        title="Structural Stability Certificate Date Inconclusive",
                                        explanation="Structural Stability Certificate is uploaded, but certificate issue date could not be parsed to verify the 5-year validity limit under APH Clause 2.14.6.",
                                        expected_value="Legible Stability Certificate Issue Date",
                                        observed_value="Date Unparseable",
                                        document_id=struct_info["document"].id,
                                        document_version_id=struct_info["version"].id,
                                        verification_status="UNVERIFIED",
                                        recommended_action="Submit legible certificate showing clear issue date."
                                    )
                                    findings.append(f)
                                    unable_count += 1
                                elif is_expired:
                                    f = Finding(
                                        validation_run_id=run.id,
                                        application_id=app.id,
                                        rule_version_id=version.id,
                                        rule_code=code,
                                        rule_title=rule.title,
                                        category=rule.category,
                                        severity="DEFICIENCY",
                                        outcome="DEFICIENCY_DETECTED",
                                        title="Expired Structural Stability Certificate (> 5 Years Old)",
                                        explanation=f"Structural Stability Certificate was issued on {cert_dt.strftime('%Y-%m-%d')} (5-year validity expired on {cert_valid_until.strftime('%Y-%m-%d')}), exceeding the 5-year maximum validity period under AICTE APH Clause 2.14.6.",
                                        expected_value=f"Certificate Issued Within 5 Years of Session Start (Valid through at least {academic_session_start.strftime('%Y-%m-%d')})",
                                        observed_value=f"Issued on {cert_dt.strftime('%Y-%m-%d')} (Expired on {cert_valid_until.strftime('%Y-%m-%d')})",
                                        document_id=struct_info["document"].id,
                                        document_version_id=struct_info["version"].id,
                                        evidence_page_number=cert_date_field.page_number if cert_date_field else 1,
                                        evidence_bounding_box_json=json.dumps(cert_date_field.bounding_box) if cert_date_field else None,
                                        evidence_raw_text=cert_date_field.raw_value if cert_date_field else None,
                                        evidence_confidence=cert_date_field.confidence if cert_date_field else 1.0,
                                        verification_status="MISMATCH",
                                        recommended_action="Obtain and upload renewed structural stability certification from an empanelled structural engineer."
                                    )
                                    findings.append(f)
                                    deficiencies += 1
                                elif not has_reg or not is_sound:
                                    f = Finding(
                                        validation_run_id=run.id,
                                        application_id=app.id,
                                        rule_version_id=version.id,
                                        rule_code=code,
                                        rule_title=rule.title,
                                        category=rule.category,
                                        severity="DEFICIENCY",
                                        outcome="DEFICIENCY_DETECTED",
                                        title="Structural Stability Certification Incomplete",
                                        explanation="Structural engineer license registration number missing or affirmative soundness certification statement absent.",
                                        expected_value="Empanelled Engineer Registration No. & Affirmative Stability Declaration",
                                        observed_value=f"Reg: {reg_field.raw_value if reg_field else 'None'}, Sound: {sound_field.raw_value if sound_field else 'None'}",
                                        document_id=struct_info["document"].id,
                                        document_version_id=struct_info["version"].id,
                                        evidence_page_number=reg_field.page_number if reg_field else 1,
                                        evidence_bounding_box_json=json.dumps(reg_field.bounding_box) if reg_field else None,
                                        evidence_raw_text=reg_field.raw_value if reg_field else None,
                                        evidence_confidence=reg_field.confidence if reg_field else 1.0,
                                        verification_status="MISMATCH",
                                        recommended_action=version.recommended_action
                                    )
                                    findings.append(f)
                                    deficiencies += 1
                                else:
                                    status_title = "Structural Stability & Modification Assessment Verified" if has_major_mod else "Structural Stability Verified"
                                    explanation_text = f"Certificate confirmed by empanelled structural engineer (Reg: {reg_field.normalized_value}) certifying building stability (valid until {cert_valid_until.strftime('%Y-%m-%d')})."
                                    if has_major_mod:
                                        explanation_text += " Note: For major modifications, revalidated building plan must also be checked during human scrutiny."

                                    f = Finding(
                                        validation_run_id=run.id,
                                        application_id=app.id,
                                        rule_version_id=version.id,
                                        rule_code=code,
                                        rule_title=rule.title,
                                        category=rule.category,
                                        severity="INFO",
                                        outcome="NO_ISSUE_DETECTED",
                                        title=status_title,
                                        explanation=explanation_text,
                                        expected_value=f"Empanelled Engineer Stability Certification Valid through {academic_session_start.strftime('%Y-%m-%d')}",
                                        observed_value=f"Registration No. {reg_field.normalized_value} (Valid until {cert_valid_until.strftime('%Y-%m-%d')})",
                                        document_id=struct_info["document"].id,
                                        document_version_id=struct_info["version"].id,
                                        evidence_page_number=reg_field.page_number,
                                        evidence_bounding_box_json=json.dumps(reg_field.bounding_box),
                                        evidence_raw_text=reg_field.raw_value,
                                        evidence_confidence=reg_field.confidence,
                                        verification_status="VERIFIED_INTERNAL",
                                        recommended_action="No remediation needed."
                                    )
                                    findings.append(f)
                                    passed += 1

            # -------------------------------------------------------------
            # Rule 5: RULE-EOA-FSR-005 (Faculty-to-Student Ratio Compliance)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-FSR-005":
                doc_info = doc_data.get("FACULTY_ROSTER")
                total_intake = app.total_intake_applied or 720

                # Statutory programme-specific norms per APH Annexure-5
                PROGRAMME_FSR_NORMS = {
                    "ENGINEERING_TECHNOLOGY": 20.0,     # APH Annexure-5 Section 5.2 (UG Engineering 1:20)
                    "ENGINEERING_PG": 15.0,             # APH Annexure-5 Section 5.3 (PG Engineering 1:15)
                    "M_TECH": 15.0,                     # APH Annexure-5 Section 5.3 (M.Tech 1:15)
                    "POLYTECHNIC_DIPLOMA": 25.0,        # APH Annexure-5 Section 5.1 (Diploma 1:25)
                    "MANAGEMENT": 20.0,                 # APH Annexure-5 Section 5.2 / Table 5.2 (MBA/PGDM 1:20)
                    "MANAGEMENT_STUDIES": 20.0,
                    "MBA": 20.0,
                    "PGDM": 20.0,
                    "MCA": 20.0,                        # APH Annexure-5 Section 5.2 / Table 5.2 (MCA 1:20)
                    "COMPUTER_APPLICATIONS": 20.0,
                    "HMCT": 20.0,                       # APH Annexure-5 Section 5.2 (UG Hotel Management 1:20)
                    "HOTEL_MANAGEMENT": 20.0,
                    "PLANNING": 16.0,                   # APH Annexure-5 Section 5.2 (Planning 1:16)
                    "DESIGN": 10.0,                     # APH Annexure-5 Section 5.2 (Design 1:10)
                    "APPLIED_ARTS": 10.0,               # APH Annexure-5 Section 5.2 (Applied Arts 1:10)
                    "PHARMACY": 15.0,                   # Pharmacy Council of India (PCI) Regulations (1:15)
                    "ARCHITECTURE": 10.0,               # Council of Architecture (CoA) Regulations (1:10)
                    "ARCHITECTURE_PLANNING": 10.0,
                }
                inst_category = getattr(institution, "category", "ENGINEERING_TECHNOLOGY")
                cfg_norms = params.get("programme_norms", {})

                if inst_category not in PROGRAMME_FSR_NORMS and inst_category not in cfg_norms:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="INFO",
                        outcome="NOT_APPLICABLE",
                        title=f"FSR Not Applicable to {inst_category}",
                        explanation=f"Institution category '{inst_category}' is not an AICTE technical education discipline governed by APH Annexure-5 faculty ratio norms.",
                        expected_value="AICTE Technical Discipline Category",
                        observed_value=f"Category: {inst_category}",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="NOT_APPLICABLE",
                        recommended_action="No faculty-to-student ratio evaluation required for non-technical category."
                    )
                    findings.append(f)
                    passed += 1
                    continue

                # Check configured norms in rule params or fallback to statutory map
                max_fsr = cfg_norms.get(inst_category, PROGRAMME_FSR_NORMS.get(inst_category, 20.0))
                section_ref = "Section 5.1" if (max_fsr == 25.0 or "DIPLOMA" in inst_category) else ("Section 5.3" if max_fsr == 15.0 and "ENGINEERING" in inst_category else "Section 5.2")

                if not doc_info or not doc_info["version"]:
                    min_faculty = math.ceil(total_intake / max_fsr)
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="DEFICIENCY",
                        outcome="DEFICIENCY_DETECTED",
                        title="Missing Certified Faculty Cadre Roster",
                        explanation=f"Faculty Roster document is missing. AICTE APH Annexure-5 {section_ref} mandates FSR <= 1:{max_fsr:.1f} for {inst_category} (min {min_faculty} faculty for {total_intake} students).",
                        expected_value=f"FSR <= 1:{max_fsr:.1f} (Min {min_faculty} Faculty)",
                        observed_value="Document Not Uploaded",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="MISMATCH",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    deficiencies += 1
                else:
                    fac_field = doc_info["fields"].get("total_qualified_faculty_count")
                    if not fac_field:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Faculty Count Inconclusive",
                            explanation="Faculty Roster is uploaded, but the total qualified faculty count could not be parsed with certainty from extraction tokens.",
                            expected_value=f"FSR <= 1:{max_fsr:.1f} (Min {math.ceil(total_intake/max_fsr)} Faculty)",
                            observed_value="Count Unparseable",
                            document_id=doc_info["document"].id,
                            document_version_id=doc_info["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action="Submit structured cadre roster with clear numerical total count."
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        if fac_field.normalized_value == "ABSENT" or not fac_field.normalized_value:
                            fac_count = None
                        else:
                            try:
                                fac_count = int(float(fac_field.normalized_value))
                            except (ValueError, TypeError):
                                fac_count = None

                        if fac_count is None:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="WARNING",
                                outcome="UNABLE_TO_EVALUATE",
                                title="Faculty Count Inconclusive",
                                explanation="Faculty Roster is uploaded, but the total qualified faculty count could not be parsed with certainty from extraction tokens.",
                                expected_value=f"FSR <= 1:{max_fsr:.1f} (Min {math.ceil(total_intake/max_fsr)} Faculty)",
                                observed_value="Count Unparseable",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                verification_status="UNVERIFIED",
                                recommended_action="Submit structured cadre roster with clear numerical total count."
                            )
                            findings.append(f)
                            unable_count += 1
                        elif fac_count <= 0:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Zero or Invalid Faculty Count",
                                explanation="Extracted faculty count is zero or invalid, which violates mandatory cadre norms.",
                                expected_value=f"Min {math.ceil(total_intake/max_fsr)} Faculty",
                                observed_value="0 Faculty",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=fac_field.page_number,
                                evidence_bounding_box_json=json.dumps(fac_field.bounding_box),
                                evidence_raw_text=fac_field.raw_value,
                                evidence_confidence=fac_field.confidence,
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            computed_fsr = total_intake / fac_count
                            min_required = math.ceil(total_intake / max_fsr)

                            if computed_fsr > max_fsr:
                                f = Finding(
                                    validation_run_id=run.id,
                                    application_id=app.id,
                                    rule_version_id=version.id,
                                    rule_code=code,
                                    rule_title=rule.title,
                                    category=rule.category,
                                    severity="DEFICIENCY",
                                    outcome="DEFICIENCY_DETECTED",
                                    title="Faculty-to-Student Ratio (FSR) Deficit",
                                    explanation=f"Computed FSR of 1:{computed_fsr:.1f} ({fac_count} faculty for {total_intake} students) violates AICTE APH Annexure-5 {section_ref} norm of 1:{max_fsr:.1f} for {inst_category}. Shortfall of {min_required - fac_count} faculty members.",
                                    expected_value=f"FSR <= 1:{max_fsr:.1f} (Min {min_required} Faculty)",
                                    observed_value=f"FSR 1:{computed_fsr:.1f} ({fac_count} Faculty)",
                                    document_id=doc_info["document"].id,
                                    document_version_id=doc_info["version"].id,
                                    evidence_page_number=fac_field.page_number,
                                    evidence_bounding_box_json=json.dumps(fac_field.bounding_box),
                                    evidence_raw_text=fac_field.raw_value,
                                    evidence_confidence=fac_field.confidence,
                                    verification_status="MISMATCH",
                                    recommended_action=version.recommended_action
                                )
                                findings.append(f)
                                deficiencies += 1
                            else:
                                f = Finding(
                                    validation_run_id=run.id,
                                    application_id=app.id,
                                    rule_version_id=version.id,
                                    rule_code=code,
                                    rule_title=rule.title,
                                    category=rule.category,
                                    severity="INFO",
                                    outcome="NO_ISSUE_DETECTED",
                                    title="Faculty-to-Student Ratio Compliant",
                                    explanation=f"Computed FSR of 1:{computed_fsr:.1f} ({fac_count} faculty for {total_intake} students) satisfies AICTE APH Annexure-5 {section_ref} norm of 1:{max_fsr:.1f} for {inst_category}.",
                                    expected_value=f"FSR <= 1:{max_fsr:.1f}",
                                    observed_value=f"FSR 1:{computed_fsr:.1f} ({fac_count} Faculty)",
                                    document_id=doc_info["document"].id,
                                    document_version_id=doc_info["version"].id,
                                    evidence_page_number=fac_field.page_number,
                                    evidence_bounding_box_json=json.dumps(fac_field.bounding_box),
                                    evidence_raw_text=fac_field.raw_value,
                                    evidence_confidence=fac_field.confidence,
                                    verification_status="VERIFIED_INTERNAL",
                                    recommended_action="No remediation needed."
                                )
                                findings.append(f)
                                passed += 1

            # -------------------------------------------------------------
            # Rule 6: RULE-EOA-CROSS-006 (Land Title Deed vs Land Use Survey Match)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-CROSS-006":
                doc1 = doc_data.get("LAND_TITLE_DEED")
                doc2 = doc_data.get("LAND_USE_CERTIFICATE")

                if not doc1 or not doc1["version"] or not doc2 or not doc2["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="WARNING",
                        outcome="UNABLE_TO_EVALUATE",
                        title="Survey Cross-Matching Incomplete (Missing Document)",
                        explanation="Cross-matching survey numbers requires both Land Title Deed and Land Use Certificate to be uploaded.",
                        expected_value="Both Title Deed & Land Use Conversion Orders Uploaded",
                        observed_value=f"Title: {'Uploaded' if doc1 and doc1['version'] else 'Missing'}, Land Use: {'Uploaded' if doc2 and doc2['version'] else 'Missing'}",
                        document_id=doc1["document"].id if doc1 else None,
                        verification_status="UNVERIFIED",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    unable_count += 1
                else:
                    f1 = doc1["fields"].get("survey_numbers_list") or doc1["fields"].get("survey_numbers") or doc1["fields"].get("survey_number")
                    f2 = doc2["fields"].get("survey_numbers_list") or doc2["fields"].get("survey_number") or doc2["fields"].get("survey_numbers")

                    if not f1 or not f2 or f1.normalized_value == "ABSENT" or f2.normalized_value == "ABSENT":
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Survey Numbers Not Extracted for Cross-Match",
                            explanation="Survey numbers could not be parsed from one or both uploaded land documents.",
                            expected_value="Survey / Khasra Numbers on Both Certificates",
                            observed_value=f"Title: {f1.raw_value if f1 else 'Missing'}, Land Use: {f2.raw_value if f2 else 'Missing'}",
                            document_id=doc1["document"].id,
                            document_version_id=doc1["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action="Ensure survey numbers are clearly legible in both documents."
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        s1_set = normalize_survey_set(f1.normalized_value)
                        s2_set = normalize_survey_set(f2.normalized_value)

                        # Secondary evidence bundle
                        sec_evidence = {
                            "document_type": "LAND_USE_CERTIFICATE",
                            "document_id": doc2["document"].id,
                            "document_version_id": doc2["version"].id,
                            "page_number": f2.page_number,
                            "bounding_box": f2.bounding_box,
                            "raw_text": f2.raw_value,
                            "normalized_value": f2.normalized_value,
                            "confidence": f2.confidence
                        }

                        if not s1_set.issubset(s2_set):
                            missing_surveys = s1_set - s2_set
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="WARNING",
                                outcome="ADVISORY_WARNING",
                                title="Survey Number Consistency Check — Discrepancy Flagged for Review",
                                explanation=f"Land Title Deed lists survey numbers {sorted(list(s1_set))}, while Land Use Certificate references {sorted(list(s2_set))}. Unmatched survey numbers: {sorted(list(missing_surveys))}. Consistency check flags this discrepancy for scrutiny committee review to confirm whether an updated conversion order or clerical variance applies.",
                                expected_value=f"Land Use Certificate covering all Title Deed surveys: {sorted(list(s1_set))}",
                                observed_value=f"Land Use Certificate covers: {sorted(list(s2_set))}",
                                document_id=doc1["document"].id,
                                document_version_id=doc1["version"].id,
                                evidence_page_number=f1.page_number,
                                evidence_bounding_box_json=json.dumps(f1.bounding_box),
                                evidence_raw_text=f1.raw_value,
                                evidence_confidence=f1.confidence,
                                evidence_secondary_json=json.dumps(sec_evidence),
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            warnings += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Survey Numbers Reconciled Across Documents",
                                explanation=f"Survey numbers {sorted(list(s1_set))} in Land Title Deed match approved conversion in Land Use Certificate.",
                                expected_value=f"Matching survey numbers: {sorted(list(s1_set))}",
                                observed_value=f"Consistent survey numbers: {sorted(list(s2_set))}",
                                document_id=doc1["document"].id,
                                document_version_id=doc1["version"].id,
                                evidence_page_number=f1.page_number,
                                evidence_bounding_box_json=json.dumps(f1.bounding_box),
                                evidence_raw_text=f1.raw_value,
                                evidence_confidence=f1.confidence,
                                evidence_secondary_json=json.dumps(sec_evidence),
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

            # -------------------------------------------------------------
            # Rule 7: RULE-EOA-CROSS-007 (Sanctioned vs Completed Built-Up Area)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-CROSS-007":
                doc1 = doc_data.get("APPROVED_BUILDING_PLAN")
                doc2 = doc_data.get("BUILDING_COMPLETION")

                if not doc1 or not doc1["version"] or not doc2 or not doc2["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="WARNING",
                        outcome="UNABLE_TO_EVALUATE",
                        title="Built-up Area Cross-Match Incomplete (Missing Document)",
                        explanation="Comparing sanctioned vs completed built-up area requires both Approved Building Plan and Building Completion Certificate.",
                        expected_value="Both Building Plan & Completion Certificate Uploaded",
                        observed_value=f"Plan: {'Uploaded' if doc1 and doc1['version'] else 'Missing'}, Completion: {'Uploaded' if doc2 and doc2['version'] else 'Missing'}",
                        document_id=doc1["document"].id if doc1 else None,
                        verification_status="UNVERIFIED",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    unable_count += 1
                else:
                    f1 = doc1["fields"].get("sanctioned_builtup_area_sqm") or doc1["fields"].get("total_built_up_area_sqm") or doc1["fields"].get("built_up_area_sqm")
                    f2 = doc2["fields"].get("completed_builtup_area_sqm") or doc2["fields"].get("built_up_area_sqm") or doc2["fields"].get("total_built_up_area_sqm")

                    if not f1 or not f2 or f1.normalized_value == "ABSENT" or f2.normalized_value == "ABSENT":
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Built-up Area Values Inconclusive",
                            explanation="Built-up area figures could not be extracted from one or both uploaded building documents.",
                            expected_value="Instructional Area in Square Meters",
                            observed_value=f"Plan: {f1.raw_value if f1 else 'Missing'}, Completion: {f2.raw_value if f2 else 'Missing'}",
                            document_id=doc1["document"].id,
                            document_version_id=doc1["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action=version.recommended_action
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        try:
                            a1 = float(f1.normalized_value)
                            a2 = float(f2.normalized_value)
                        except (ValueError, TypeError):
                            a1, a2 = 0.0, 0.0

                        sec_evidence = {
                            "document_type": "BUILDING_COMPLETION",
                            "document_id": doc2["document"].id,
                            "document_version_id": doc2["version"].id,
                            "page_number": f2.page_number,
                            "bounding_box": f2.bounding_box,
                            "raw_text": f2.raw_value,
                            "normalized_value": f2.normalized_value,
                            "confidence": f2.confidence
                        }

                        if a1 > 0 and (a2 < a1 * params.get("min_ratio", 0.90)):
                            shortfall_pct = ((a1 - a2) / a1) * 100
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Constructed Built-Up Area Shortfall",
                                explanation=f"Completed area ({a2:.1f} Sq.m) is {shortfall_pct:.1f}% below sanctioned area ({a1:.1f} Sq.m), exceeding the allowable 10% tolerance under APH Appendix 4.3.",
                                expected_value=f">= {a1 * 0.90:.1f} Sq.m (90% of Sanctioned {a1:.1f} Sq.m)",
                                observed_value=f"{a2:.1f} Sq.m ({shortfall_pct:.1f}% Shortfall)",
                                document_id=doc1["document"].id,
                                document_version_id=doc1["version"].id,
                                evidence_page_number=f1.page_number,
                                evidence_bounding_box_json=json.dumps(f1.bounding_box),
                                evidence_raw_text=f1.raw_value,
                                evidence_confidence=f1.confidence,
                                evidence_secondary_json=json.dumps(sec_evidence),
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Built-Up Area Reconciled",
                                explanation=f"Completed area ({a2:.1f} Sq.m) matches sanctioned plan area ({a1:.1f} Sq.m) within statutory tolerance.",
                                expected_value=f"Sanctioned Plan Area: {a1:.1f} Sq.m",
                                observed_value=f"Completed Area: {a2:.1f} Sq.m",
                                document_id=doc1["document"].id,
                                document_version_id=doc1["version"].id,
                                evidence_page_number=f1.page_number,
                                evidence_bounding_box_json=json.dumps(f1.bounding_box),
                                evidence_raw_text=f1.raw_value,
                                evidence_confidence=f1.confidence,
                                evidence_secondary_json=json.dumps(sec_evidence),
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

            # -------------------------------------------------------------
            # Rule 8: RULE-EOA-PREV-008 (Previous Year Intake Baseline)
            # -------------------------------------------------------------
            elif code == "RULE-EOA-PREV-008":
                doc_info = doc_data.get("PREV_AICTE_APPROVAL")
                applied_intake = app.total_intake_applied or 720

                if not doc_info or not doc_info["version"]:
                    f = Finding(
                        validation_run_id=run.id,
                        application_id=app.id,
                        rule_version_id=version.id,
                        rule_code=code,
                        rule_title=rule.title,
                        category=rule.category,
                        severity="DEFICIENCY",
                        outcome="DEFICIENCY_DETECTED",
                        title="Missing Previous AICTE Approval Letter",
                        explanation="Previous Academic Year AICTE Approval Extension Letter has not been uploaded for baseline intake verification.",
                        expected_value="Previous AICTE EoA Letter",
                        observed_value="Document Not Uploaded",
                        document_id=doc_info["document"].id if doc_info else None,
                        verification_status="MISMATCH",
                        recommended_action=version.recommended_action
                    )
                    findings.append(f)
                    deficiencies += 1
                else:
                    prev_field = doc_info["fields"].get("approved_total_intake")
                    if not prev_field:
                        f = Finding(
                            validation_run_id=run.id,
                            application_id=app.id,
                            rule_version_id=version.id,
                            rule_code=code,
                            rule_title=rule.title,
                            category=rule.category,
                            severity="WARNING",
                            outcome="UNABLE_TO_EVALUATE",
                            title="Previous Sanctioned Intake Inconclusive",
                            explanation="Previous approval letter is uploaded, but sanctioned intake seats could not be parsed with certainty from extraction tokens.",
                            expected_value=f"Baseline intake seats <= {applied_intake}",
                            observed_value="Intake Unparseable",
                            document_id=doc_info["document"].id,
                            document_version_id=doc_info["version"].id,
                            verification_status="UNVERIFIED",
                            recommended_action=version.recommended_action
                        )
                        findings.append(f)
                        unable_count += 1
                    else:
                        try:
                            prev_intake = int(prev_field.normalized_value)
                        except (ValueError, TypeError):
                            prev_intake = 0

                        if applied_intake > prev_intake and prev_intake > 0:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="DEFICIENCY",
                                outcome="DEFICIENCY_DETECTED",
                                title="Applied Intake Exceeds Previous Sanction Baseline",
                                explanation=f"Current applied intake of {applied_intake} seats exceeds previously approved intake of {prev_intake} seats. Standard EoA applications cannot expand intake without formal expansion sanction.",
                                expected_value=f"Applied Intake <= Previously Approved ({prev_intake} Seats)",
                                observed_value=f"{applied_intake} Seats Applied",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=prev_field.page_number,
                                evidence_bounding_box_json=json.dumps(prev_field.bounding_box),
                                evidence_raw_text=prev_field.raw_value,
                                evidence_confidence=prev_field.confidence,
                                verification_status="MISMATCH",
                                recommended_action=version.recommended_action
                            )
                            findings.append(f)
                            deficiencies += 1
                        else:
                            f = Finding(
                                validation_run_id=run.id,
                                application_id=app.id,
                                rule_version_id=version.id,
                                rule_code=code,
                                rule_title=rule.title,
                                category=rule.category,
                                severity="INFO",
                                outcome="NO_ISSUE_DETECTED",
                                title="Applied Intake Within Previous Sanction Baseline",
                                explanation=f"Applied intake of {applied_intake} seats is consistent with previously approved capacity ({prev_intake} seats).",
                                expected_value=f"Intake <= {prev_intake} Seats",
                                observed_value=f"{applied_intake} Seats",
                                document_id=doc_info["document"].id,
                                document_version_id=doc_info["version"].id,
                                evidence_page_number=prev_field.page_number,
                                evidence_bounding_box_json=json.dumps(prev_field.bounding_box),
                                evidence_raw_text=prev_field.raw_value,
                                evidence_confidence=prev_field.confidence,
                                verification_status="VERIFIED_INTERNAL",
                                recommended_action="No remediation needed."
                            )
                            findings.append(f)
                            passed += 1

        # Persist all findings
        for f in findings:
            self.db.add(f)

        # Update run summary
        total_checks = len(findings)
        summary = {
            "deficiencies": deficiencies,
            "warnings": warnings,
            "passed": passed,
            "unable_to_evaluate": unable_count,
            "total_checks": total_checks,
            "completed_at": utc_now().isoformat()
        }

        run.total_checks = total_checks
        run.deficiencies_count = deficiencies
        run.warnings_count = warnings
        run.passed_count = passed
        run.unable_to_evaluate_count = unable_count
        run.summary_json = json.dumps(summary)
        run.completed_at = utc_now()
        run.status = "COMPLETED"

        # Update application lifecycle state
        if deficiencies > 0:
            app.status = "DEFICIENCIES_DETECTED"
        else:
            app.status = "FINDINGS_AVAILABLE"

        self.db.commit()
        self.db.refresh(run)

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=triggered_by_user_id,
            actor_role="INSTITUTION",
            action="VALIDATION_RUN_COMPLETED",
            entity_type="APPLICATION",
            entity_id=app.id,
            payload={
                "validation_run_id": run.id,
                "run_number": run.run_number,
                "deficiencies_count": deficiencies,
                "warnings_count": warnings,
                "passed_count": passed,
                "unable_to_evaluate_count": unable_count,
                "total_checks": total_checks
            }
        )

        return run, findings
