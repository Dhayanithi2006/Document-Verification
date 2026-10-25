# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Regulatory Rules & Findings Endpoints (backend/api/v1/regulatory.py)

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db, utc_now
from backend.core.deps import get_current_user, require_admin, verify_institution_access
from backend.models.user import User
from backend.models.application import Application
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, Finding
from backend.services.audit_service import create_audit_event
from backend.services.regulatory_engine import seed_regulatory_rules

router = APIRouter(tags=["Regulatory Rules & Findings"])


@router.get("/rules")
def list_regulatory_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all regulatory rules from the APH compliance catalogue, including approval status."""
    seed_regulatory_rules(db)
    rules = db.query(RegulatoryRule).order_by(RegulatoryRule.rule_code.asc()).all()

    results = []
    for r in rules:
        latest_version = db.query(RegulatoryRuleVersion).filter(
            RegulatoryRuleVersion.rule_id == r.id
        ).order_by(RegulatoryRuleVersion.version_number.desc()).first()

        params = {}
        if latest_version and latest_version.parameters_json:
            try:
                params = json.loads(latest_version.parameters_json)
            except Exception:
                pass

        results.append({
            "id": r.id,
            "rule_code": r.rule_code,
            "title": r.title,
            "category": r.category,
            "official_source": r.official_source,
            "status": r.status,
            "is_active": r.is_active,
            "current_version": {
                "version_number": latest_version.version_number if latest_version else 1,
                "severity": latest_version.severity if latest_version else "DEFICIENCY",
                "description": latest_version.description if latest_version else "",
                "parameters": params,
                "recommended_action": latest_version.recommended_action if latest_version else "",
                "is_active": latest_version.is_active if latest_version else True,
                "approved_at": latest_version.approved_at.isoformat() if latest_version and latest_version.approved_at else None
            }
        })

    return results


@router.get("/rules/{rule_code}")
def get_regulatory_rule_detail(
    rule_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full versioned rule definition and official clause metadata."""
    seed_regulatory_rules(db)
    rule = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulatory rule not found.")

    versions = db.query(RegulatoryRuleVersion).filter(
        RegulatoryRuleVersion.rule_id == rule.id
    ).order_by(RegulatoryRuleVersion.version_number.desc()).all()

    version_list = []
    for v in versions:
        params = {}
        if v.parameters_json:
            try:
                params = json.loads(v.parameters_json)
            except Exception:
                pass
        version_list.append({
            "version_number": v.version_number,
            "severity": v.severity,
            "description": v.description,
            "parameters": params,
            "recommended_action": v.recommended_action,
            "is_active": v.is_active,
            "approved_at": v.approved_at.isoformat() if v.approved_at else None
        })

    return {
        "id": rule.id,
        "rule_code": rule.rule_code,
        "title": rule.title,
        "category": rule.category,
        "official_source": rule.official_source,
        "status": rule.status,
        "is_active": rule.is_active,
        "versions": version_list
    }


@router.post("/rules/{rule_code}/activate")
def activate_regulatory_rule(
    rule_code: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to activate a verified regulatory rule for automated enforcement."""
    rule = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulatory rule not found.")

    rule.status = "APPROVED_FOR_PROTOTYPE_USE"
    rule.is_active = True
    rule.updated_at = utc_now()

    latest_version = db.query(RegulatoryRuleVersion).filter(
        RegulatoryRuleVersion.rule_id == rule.id
    ).order_by(RegulatoryRuleVersion.version_number.desc()).first()

    if latest_version:
        latest_version.is_active = True
        latest_version.approved_by_user_id = current_user.id
        latest_version.approved_at = utc_now()

    db.commit()
    return {
        "rule_code": rule.rule_code,
        "status": rule.status,
        "is_active": rule.is_active,
        "message": f"Rule {rule_code} activated successfully for automated regulatory enforcement."
    }


@router.post("/rules/{rule_code}/deactivate")
def deactivate_regulatory_rule(
    rule_code: str,
    reason: Optional[str] = "Deactivated due to missing official statutory source or unimplemented evaluation logic.",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to safely deactivate an unverified or draft regulatory rule."""
    rule = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulatory rule not found.")

    rule.status = "DRAFT_MISSING_OFFICIAL_SOURCE"
    rule.is_active = False
    rule.updated_at = utc_now()

    latest_version = db.query(RegulatoryRuleVersion).filter(
        RegulatoryRuleVersion.rule_id == rule.id
    ).order_by(RegulatoryRuleVersion.version_number.desc()).first()

    if latest_version:
        latest_version.is_active = False

    create_audit_event(
        db=db,
        action="REGULATORY_RULE_DEACTIVATED",
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        entity_type="REGULATORY_RULE",
        entity_id=rule.id,
        payload={
            "rule_code": rule.rule_code,
            "action": "DEACTIVATE",
            "reason": reason
        }
    )

    db.commit()
    return {
        "rule_code": rule.rule_code,
        "status": rule.status,
        "is_active": rule.is_active,
        "message": f"Rule {rule_code} deactivated successfully."
    }


@router.get("/findings/{id}")
def get_finding_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full evidence provenance and cross-matching details for a specific finding."""
    finding = db.query(Finding).filter(Finding.id == id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

    # Multi-tenant IDOR check
    app = db.query(Application).filter(Application.id == finding.application_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    verify_institution_access(app, current_user)

    box = None
    if finding.evidence_bounding_box_json:
        try:
            box = json.loads(finding.evidence_bounding_box_json)
        except Exception:
            pass

    sec_evidence = None
    if finding.evidence_secondary_json:
        try:
            sec_evidence = json.loads(finding.evidence_secondary_json)
        except Exception:
            pass

    doc_title = finding.document.title if finding.document else None
    version_num = finding.document_version.version_number if finding.document_version else None
    official_src = finding.rule_version.rule.official_source if finding.rule_version and finding.rule_version.rule else None

    return {
        "id": finding.id,
        "validation_run_id": finding.validation_run_id,
        "application_id": finding.application_id,
        "rule_code": finding.rule_code,
        "rule_title": finding.rule_title,
        "official_source": official_src,
        "category": finding.category,
        "severity": finding.severity,
        "outcome": finding.outcome,
        "status": finding.status,
        "title": finding.title,
        "explanation": finding.explanation,
        "expected_value": finding.expected_value,
        "observed_value": finding.observed_value,
        "evidence": {
            "document_id": finding.document_id,
            "document_version_id": finding.document_version_id,
            "document_title": doc_title,
            "version_number": version_num,
            "page_number": finding.evidence_page_number,
            "bounding_box": box,
            "raw_text": finding.evidence_raw_text,
            "confidence": finding.evidence_confidence,
            "secondary_evidence": sec_evidence
        },
        "verification_status": finding.verification_status,
        "recommended_action": finding.recommended_action,
        "created_at": finding.created_at.isoformat()
    }
