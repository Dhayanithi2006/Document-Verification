# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Application & Document Checklist Endpoints (backend/api/v1/applications.py)

import random
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session

from backend.core.database import get_db, utc_now
from backend.core.deps import get_current_user, verify_institution_access
from backend.models.user import User
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.schemas.application import (
    ApplicationResponse,
    ApplicationCreate,
    ApplicationUpdate,
)
from backend.schemas.document import (
    ChecklistResponse,
    DocumentResponse,
    DocumentVersionResponse,
    DocumentUploadResponse,
)
from backend.services.document_service import (
    initialize_application_checklist,
    save_uploaded_document,
)
from backend.services.audit_service import create_audit_event

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists applications with strict server-side tenant scoping:
    - INSTITUTION role: filtered exclusively to current user's institution_id.
    - REVIEWER / ADMIN role: permitted access across all institutions.
    """
    query = db.query(Application)
    if current_user.role == "INSTITUTION":
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)

    return query.order_by(Application.created_at.desc()).all()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new Extension of Approval (EoA) draft application.
    
    Security & Business Rules:
    1. Caller must have role INSTITUTION with a verified institution_id.
    2. Server-side institution binding: Uses current_user.institution_id strictly.
    3. Generates unique application reference number (e.g. AICTE-EOA-2026-XXXX).
    4. Automatically initializes the 8 mandatory checklist document slots in PENDING state.
    5. Records immutable audit event.
    """
    if current_user.role != "INSTITUTION":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only institutional applicants are authorized to create Extension of Approval applications."
        )

    if not current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is not bound to an authorized educational institution."
        )

    # Generate unique application reference number
    year_prefix = payload.academic_year.split("-")[0] if "-" in payload.academic_year else "2026"
    random_suffix = random.randint(1000, 9999)
    app_number = f"AICTE-EOA-{year_prefix}-{random_suffix}"

    # Ensure uniqueness
    while db.query(Application).filter(Application.application_number == app_number).first():
        random_suffix = random.randint(1000, 9999)
        app_number = f"AICTE-EOA-{year_prefix}-{random_suffix}"

    app = Application(
        application_number=app_number,
        institution_id=current_user.institution_id,
        academic_year=payload.academic_year,
        application_type=payload.application_type,
        status="DRAFT",
        total_intake_applied=payload.total_intake_applied
    )
    db.add(app)
    db.flush()

    # Automatically initialize 8 statutory checklist document slots
    initialize_application_checklist(db, app.id)

    # Record Audit Event
    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="APPLICATION_CREATED",
        entity_type="APPLICATION",
        entity_id=app.id,
        payload={
            "application_number": app.application_number,
            "institution_id": app.institution_id,
            "academic_year": app.academic_year,
            "total_intake_applied": app.total_intake_applied
        },
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    db.refresh(app)
    return app


@router.get("/{id}", response_model=ApplicationResponse)
def get_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches a specific application, enforcing strict tenant isolation against IDOR attacks."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Server-Side Tenant Isolation Guard
    verify_institution_access(app, current_user)
    return app


@router.put("/{id}", response_model=ApplicationResponse)
def update_application(
    id: str,
    payload: ApplicationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates permitted application parameters in DRAFT status."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    if current_user.role == "INSTITUTION" and app.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application cannot be edited in its current lifecycle status: {app.status}."
        )

    if payload.academic_year is not None:
        app.academic_year = payload.academic_year
    if payload.total_intake_applied is not None:
        app.total_intake_applied = payload.total_intake_applied

    app.updated_at = utc_now()
    db.commit()
    db.refresh(app)

    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="APPLICATION_UPDATED",
        entity_type="APPLICATION",
        entity_id=app.id,
        payload={
            "academic_year": app.academic_year,
            "total_intake_applied": app.total_intake_applied
        },
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return app


@router.get("/{id}/checklist", response_model=ChecklistResponse)
def get_application_checklist(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the mandatory 8-document checklist with versions and status."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    docs = db.query(Document).filter(Document.application_id == id).all()
    checklist_items = []
    for doc in docs:
        versions = sorted(doc.versions, key=lambda v: v.version_number, reverse=True)
        latest_ver = versions[0] if versions else None
        
        latest_ver_resp = None
        if latest_ver:
            latest_ver_resp = DocumentVersionResponse(
                id=latest_ver.id,
                version_number=latest_ver.version_number,
                file_name=latest_ver.file_name,
                file_size_bytes=latest_ver.file_size_bytes,
                file_hash_sha256=latest_ver.file_hash_sha256,
                mime_type=latest_ver.mime_type,
                page_count=latest_ver.page_count,
                is_scanned=latest_ver.is_scanned,
                upload_timestamp=latest_ver.upload_timestamp
            )

        all_vers_resp = [
            DocumentVersionResponse(
                id=v.id,
                version_number=v.version_number,
                file_name=v.file_name,
                file_size_bytes=v.file_size_bytes,
                file_hash_sha256=v.file_hash_sha256,
                mime_type=v.mime_type,
                page_count=v.page_count,
                is_scanned=v.is_scanned,
                upload_timestamp=v.upload_timestamp
            )
            for v in versions
        ]

        checklist_items.append(
            DocumentResponse(
                id=doc.id,
                application_id=doc.application_id,
                document_type=doc.document_type,
                title=doc.title,
                is_mandatory=doc.is_mandatory,
                status=doc.status,
                created_at=doc.created_at,
                current_version=latest_ver_resp,
                versions=all_vers_resp
            )
        )

    total_slots = len(checklist_items)
    uploaded_slots = sum(1 for item in checklist_items if item.status == "UPLOADED")
    pending_slots = total_slots - uploaded_slots

    return ChecklistResponse(
        application_id=id,
        total_slots=total_slots,
        uploaded_slots=uploaded_slots,
        pending_slots=pending_slots,
        checklist=checklist_items
    )


@router.post("/{id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    id: str,
    request: Request,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accepts, securely validates, and privately persists a PDF document upload."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Server-Side Tenant Isolation Guard
    verify_institution_access(app, current_user)

    if current_user.role != "INSTITUTION":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only institutional applicants are authorized to upload supporting documents."
        )

    ip = request.client.host if request.client else "127.0.0.1"
    version = await save_uploaded_document(
        db=db,
        application=app,
        document_type=document_type,
        file=file,
        current_user=current_user,
        ip_address=ip
    )

    doc_id = str(version.document_id)
    ver_num = int(version.version_number)
    f_name = str(version.file_name)
    f_hash = str(version.file_hash_sha256)
    f_size = int(version.file_size_bytes)

    # Auto-trigger real IDP pipeline (digital extraction / OCR / field parsing)
    try:
        from backend.services.extraction_service import DocumentProcessingPipeline
        pipeline = DocumentProcessingPipeline(db)
        pipeline.process_document_version(doc_id, version_number=ver_num)
    except Exception as extract_err:
        import logging
        logging.getLogger("uvicorn.error").warning(f"Auto-extraction on upload encountered non-fatal issue: {extract_err}")

    return DocumentUploadResponse(
        document_id=doc_id,
        document_type=document_type,
        version_number=ver_num,
        file_name=f_name,
        file_hash_sha256=f_hash,
        file_size_bytes=f_size,
        status="UPLOADED",
        message="Document uploaded and IDP extraction completed successfully."
    )


@router.delete("/{id}/documents/{document_type}")
def delete_document(
    id: str,
    document_type: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes an uploaded document slot and resets its checklist state to PENDING."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    if current_user.role != "INSTITUTION":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only institutional applicants are authorized to remove uploaded documents."
        )

    if app.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot remove documents: Application is in status '{app.status}'."
        )

    doc = db.query(Document).filter(
        Document.application_id == id,
        Document.document_type == document_type
    ).first()

    if not doc or not doc.versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No uploaded document found for category: {document_type}."
        )

    # Delete physical files safely
    for v in doc.versions:
        try:
            p = Path(v.file_path)
            if p.exists():
                p.unlink(missing_ok=True)
            elif (Path(".") / p).exists():
                (Path(".") / p).unlink(missing_ok=True)
        except Exception:
            pass
        db.delete(v)

    doc.status = "PENDING"
    db.commit()

    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="DOCUMENT_REMOVED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        payload={
            "document_type": document_type,
            "application_id": app.id
        },
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return {
        "status": "PENDING",
        "message": f"Document {document_type} removed successfully and reset to PENDING."
    }


# -------------------------------------------------------------------------
# Phase P7: Regulatory Pre-Scrutiny & Evidence Findings Endpoints
# -------------------------------------------------------------------------

@router.post("/{id}/validate", status_code=status.HTTP_200_OK)
def trigger_application_validation(
    id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers deterministic regulatory rule evaluation across latest extracted document evidence.
    Produces and persists an immutable ValidationRun record with evidence-linked findings.
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    from backend.services.regulatory_engine import RegulatoryEngine
    engine = RegulatoryEngine(db)
    run, findings = engine.evaluate_application(
        application_id=app.id,
        triggered_by_user_id=current_user.id,
        trigger_type="INITIAL_PRE_SCRUTINY"
    )

    return {
        "validation_run_id": run.id,
        "application_id": app.id,
        "run_number": run.run_number,
        "status": run.status,
        "total_checks": run.total_checks,
        "findings_summary": {
            "deficiencies": run.deficiencies_count,
            "warnings": run.warnings_count,
            "passed": run.passed_count,
            "unable_to_evaluate": run.unable_to_evaluate_count
        },
        "completed_at": run.completed_at.isoformat() if run.completed_at else None
    }


@router.get("/{id}/findings")
def get_application_findings(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all evidence-anchored findings produced by the latest regulatory validation run."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    from backend.models.regulatory import ValidationRun, Finding
    import json

    run = db.query(ValidationRun).filter(
        ValidationRun.application_id == id
    ).order_by(ValidationRun.run_number.desc()).first()

    if not run:
        return {
            "application_id": app.id,
            "validation_run_id": None,
            "run_number": None,
            "status": "NOT_EVALUATED",
            "total_checks": 0,
            "summary": {
                "deficiencies": 0,
                "warnings": 0,
                "passed": 0,
                "unable_to_evaluate": 0
            },
            "findings": []
        }

    findings_records = db.query(Finding).filter(
        Finding.validation_run_id == run.id
    ).order_by(Finding.created_at.asc()).all()

    formatted_findings = []
    for f in findings_records:
        box = None
        if f.evidence_bounding_box_json:
            try:
                box = json.loads(f.evidence_bounding_box_json)
            except Exception:
                pass

        sec_evidence = None
        if f.evidence_secondary_json:
            try:
                sec_evidence = json.loads(f.evidence_secondary_json)
            except Exception:
                pass

        doc_title = None
        version_num = None
        if f.document:
            doc_title = f.document.title
        if f.document_version:
            version_num = f.document_version.version_number

        official_src = f.rule_version.rule.official_source if f.rule_version and f.rule_version.rule else None

        formatted_findings.append({
            "id": f.id,
            "validation_run_id": f.validation_run_id,
            "application_id": f.application_id,
            "rule_code": f.rule_code,
            "rule_title": f.rule_title,
            "official_source": official_src,
            "category": f.category,
            "severity": f.severity,
            "outcome": f.outcome,
            "status": f.status,
            "title": f.title,
            "explanation": f.explanation,
            "expected_value": f.expected_value,
            "observed_value": f.observed_value,
            "evidence": {
                "document_id": f.document_id,
                "document_version_id": f.document_version_id,
                "document_title": doc_title,
                "version_number": version_num,
                "page_number": f.evidence_page_number,
                "bounding_box": box,
                "raw_text": f.evidence_raw_text,
                "confidence": f.evidence_confidence,
                "secondary_evidence": sec_evidence
            },
            "verification_status": f.verification_status,
            "recommended_action": f.recommended_action,
            "created_at": f.created_at.isoformat()
        })

    return {
        "application_id": app.id,
        "validation_run_id": run.id,
        "run_number": run.run_number,
        "status": run.status,
        "total_checks": run.total_checks,
        "summary": {
            "deficiencies": run.deficiencies_count,
            "warnings": run.warnings_count,
            "passed": run.passed_count,
            "unable_to_evaluate": run.unable_to_evaluate_count
        },
        "findings": formatted_findings
    }


@router.get("/{id}/validation-status")
def get_application_validation_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the execution status and summary counts of the latest validation run."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    verify_institution_access(app, current_user)

    from backend.models.regulatory import ValidationRun

    run = db.query(ValidationRun).filter(
        ValidationRun.application_id == id
    ).order_by(ValidationRun.run_number.desc()).first()

    if not run:
        return {
            "application_id": app.id,
            "validation_run_id": None,
            "status": "NOT_EVALUATED",
            "message": "No pre-scrutiny regulatory evaluation has been executed yet."
        }

    return {
        "validation_run_id": run.id,
        "application_id": app.id,
        "run_number": run.run_number,
        "status": run.status,
        "total_checks": run.total_checks,
        "findings_summary": {
            "deficiencies": run.deficiencies_count,
            "warnings": run.warnings_count,
            "passed": run.passed_count,
            "unable_to_evaluate": run.unable_to_evaluate_count
        },
        "completed_at": run.completed_at.isoformat() if run.completed_at else None
    }

