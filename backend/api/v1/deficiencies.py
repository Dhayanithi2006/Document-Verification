# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Deficiency Resolution & Corrective Actions Endpoints (backend/api/v1/deficiencies.py)

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, verify_institution_access
from backend.models.user import User
from backend.models.application import Application
from backend.models.regulatory import Finding
from backend.models.document import Document
from backend.schemas.deficiency import (
    CorrectionDraftRequest,
    CorrectionSubmitRequest,
    CorrectionSubmissionResponse,
    DeficiencyItemResponse,
    ApplicationDeficienciesResponse,
    RevalidationResponse,
    FindingHistoryResponse,
)
from backend.services.deficiency_service import DeficiencyService
from backend.services.document_service import save_uploaded_document
from backend.services.extraction_service import DocumentProcessingPipeline

router = APIRouter(tags=["Deficiency Resolution & Revalidation"])


@router.get(
    "/applications/{application_id}/deficiencies",
    response_model=ApplicationDeficienciesResponse,
    summary="List Actionable Deficiencies for Application"
)
def list_application_deficiencies(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all actionable regulatory findings for an authorized application,
    including applicant draft responses, submitted evidence, and revalidation state.
    Strict tenant isolation is enforced.
    """
    service = DeficiencyService(db)
    return service.get_application_deficiencies(application_id, current_user)


@router.post(
    "/findings/{finding_id}/acknowledge",
    response_model=DeficiencyItemResponse,
    summary="Acknowledge Deficiency Finding"
)
def acknowledge_finding(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks an identified finding as formally acknowledged by the applicant institution.
    Establishes traceability without altering the regulatory non-compliance status.
    """
    service = DeficiencyService(db)
    return service.acknowledge_finding(finding_id, current_user)


@router.get(
    "/findings/{finding_id}/response",
    response_model=Optional[CorrectionSubmissionResponse],
    summary="Get Active Correction Draft or Latest Submission"
)
def get_finding_response(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the current draft corrective response or latest submission for a finding.
    """
    service = DeficiencyService(db)
    return service.get_draft_response(finding_id, current_user)


@router.put(
    "/findings/{finding_id}/response",
    response_model=CorrectionSubmissionResponse,
    summary="Save Correction Draft Response"
)
def save_draft_response(
    finding_id: str,
    payload: CorrectionDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates an applicant's draft correction response, including explanation
    and supporting document references, without formal submission.
    """
    service = DeficiencyService(db)
    return service.save_draft_response(finding_id, payload, current_user)


@router.post(
    "/findings/{finding_id}/submit",
    response_model=CorrectionSubmissionResponse,
    summary="Submit Formal Corrective Response"
)
def submit_correction(
    finding_id: str,
    payload: CorrectionSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Formally submits a corrective response for a finding. Transitions finding status to
    CORRECTION_SUBMITTED and makes the application eligible for controlled revalidation.
    """
    service = DeficiencyService(db)
    return service.submit_correction(finding_id, payload, current_user)


@router.post(
    "/applications/{application_id}/revalidate",
    response_model=RevalidationResponse,
    summary="Execute Controlled Revalidation"
)
def revalidate_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes controlled regulatory revalidation using the real P7 RegulatoryEngine.
    Selects latest uploaded document versions (v2/v3), re-runs active AICTE rules,
    computes before-versus-after delta outcomes, and updates submission resolution states.
    Automated outcomes do not replace authorized human reviewers.
    """
    service = DeficiencyService(db)
    return service.revalidate_application(application_id, current_user)


@router.get(
    "/findings/{finding_id}/history",
    response_model=FindingHistoryResponse,
    summary="Get Full Chronological Finding History"
)
def get_finding_history(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the complete, immutable chronological audit trail for a single finding,
    including detection, acknowledgement, draft edits, submissions, revalidations,
    and reviewer observations.
    """
    service = DeficiencyService(db)
    return service.get_finding_history(finding_id, current_user)


@router.post(
    "/findings/{finding_id}/resolve",
    summary="Multipart Document Replacement and Immediate Revalidation (Bridge API)"
)
async def resolve_finding_with_document(
    finding_id: str,
    request: Request,
    remarks: str = Form(...),
    response_category: str = Form("DOCUMENT_REPLACEMENT"),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bridge endpoint supporting direct replacement document upload (v2/v3),
    immediate IDP extraction, submission, and revalidation.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

    app = db.query(Application).filter(Application.id == finding.application_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    verify_institution_access(app, current_user)

    doc_id = None
    doc_ver_id = None
    new_version_num = 1

    if file:
        # Determine document type from finding or existing document
        doc_type = "GENERAL_SUPPORTING_DOCUMENT"
        if finding.document_id:
            existing_doc = db.query(Document).filter(Document.id == finding.document_id).first()
            if existing_doc:
                doc_type = existing_doc.document_type

        ip_addr = request.client.host if request.client else "127.0.0.1"
        new_version = await save_uploaded_document(
            db=db,
            application=app,
            document_type=doc_type,
            file=file,
            current_user=current_user,
            ip_address=ip_addr
        )
        doc_id = new_version.document_id
        doc_ver_id = new_version.id
        new_version_num = new_version.version_number

        # Process document through IDP pipeline
        idp_service = DocumentProcessingPipeline(db)
        try:
            idp_service.process_document(document_id=new_version.document_id, version_number=new_version.version_number, current_user=current_user)
        except Exception as e:
            # Document saved; processing warning logged
            pass

    # Submit correction
    service = DeficiencyService(db)
    sub = service.submit_correction(
        finding_id=finding_id,
        payload=CorrectionSubmitRequest(
            response_text=remarks,
            response_category=response_category,
            document_id=doc_id,
            document_version_id=doc_ver_id
        ),
        current_user=current_user
    )

    # Trigger revalidation
    reval = service.revalidate_application(app.id, current_user)

    return {
        "finding_id": finding.id,
        "submission_id": sub.id,
        "status": "CORRECTION_SUBMITTED",
        "new_version_number": new_version_num,
        "revalidation": reval,
        "message": "Corrected version uploaded and revalidation executed successfully."
    }
