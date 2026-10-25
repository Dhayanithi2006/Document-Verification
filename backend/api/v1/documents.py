# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Secure Document Streaming Endpoints (backend/api/v1/documents.py)

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, verify_institution_access
from backend.models.user import User
from backend.models.document import Document, DocumentVersion
from backend.models.application import Application
from backend.services.audit_service import create_audit_event

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{document_id}/versions/{version}/file")
def get_document_file(
    document_id: str,
    version: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely streams an uploaded PDF document binary for authorized viewing.
    
    Security Controls:
    1. Caller must be authenticated.
    2. Tenant isolation: Caller's institution must match document's owning institution.
    3. Prevents path traversal and unrestricted file access.
    4. Sets X-Content-Type-Options: nosniff and inline disposition.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    # Fetch associated application to verify tenant access
    app = db.query(Application).filter(Application.id == doc.application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated application not found."
        )

    # Server-Side Tenant Isolation Guard (404 mask)
    verify_institution_access(app, current_user)

    # Fetch specific version
    doc_version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.version_number == version
    ).first()

    if not doc_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} of this document does not exist."
        )

    physical_path = Path(doc_version.file_path)
    if not physical_path.exists():
        # Check relative to workspace root
        if not (Path(".") / physical_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical document file is unavailable in storage."
            )
        physical_path = Path(".") / physical_path

    # Record Audit Event
    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="DOCUMENT_VIEWED",
        entity_type="DOCUMENT_VERSION",
        entity_id=doc_version.id,
        payload={
            "document_id": doc.id,
            "version_number": version,
            "file_name": doc_version.file_name,
            "application_id": app.id
        },
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    headers = {
        "Content-Disposition": f'inline; filename="{doc_version.file_name}"',
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-cache"
    }

    return FileResponse(
        path=str(physical_path),
        media_type="application/pdf",
        headers=headers
    )


from typing import Optional, List
from fastapi import Query
from backend.models.extraction import DocumentProcessingRun, ExtractedField, DocumentPage
from backend.schemas.extraction import (
    DocumentProcessingStatusResponse,
    DocumentExtractionResultResponse,
    ExtractedFieldResponse,
    DocumentPageResponse
)
from backend.services.extraction_service import DocumentProcessingPipeline


def _get_authorized_document_and_app(document_id: str, current_user: User, db: Session):
    """Helper to fetch document and associated application with strict tenant isolation enforcement."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    app = db.query(Application).filter(Application.id == doc.application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated application not found."
        )

    verify_institution_access(app, current_user)
    return doc, app


@router.post("/{document_id}/process", response_model=DocumentProcessingStatusResponse)
def process_document(
    document_id: str,
    request: Request,
    version: Optional[int] = Query(None, description="Document version number to process. Defaults to latest version."),
    force: bool = Query(False, description="Force reprocessing even if already completed."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers real IDP extraction (digital PDF text extraction, OCR, field extraction)
    for an authorized uploaded document version.
    
    Security Controls:
    1. Caller must be authenticated.
    2. Tenant isolation: Institutions cannot process other institutions' documents.
    3. Safe execution bounded with deterministic error recovery.
    """
    doc, app = _get_authorized_document_and_app(document_id, current_user, db)

    if version is not None:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        ).first()
        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} of document {document_id} not found."
            )
    else:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No uploaded versions exist for this document slot."
            )

    pipeline = DocumentProcessingPipeline(db)
    run = pipeline.process_document_version(
        document_id=document_id,
        version_number=target_version.version_number,
        force_reprocess=force
    )

    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="DOCUMENT_PROCESSED",
        entity_type="DOCUMENT_PROCESSING_RUN",
        entity_id=run.id,
        payload={
            "document_id": doc.id,
            "version_number": target_version.version_number,
            "status": run.status,
            "pages_processed": run.pages_processed,
            "extraction_method": run.extraction_method,
            "application_id": app.id
        },
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return run


@router.get("/{document_id}/processing-status", response_model=DocumentProcessingStatusResponse)
@router.get("/{document_id}/status", response_model=DocumentProcessingStatusResponse)
def get_processing_status(
    document_id: str,
    version: Optional[int] = Query(None, description="Document version number. Defaults to latest version."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves current processing run status and summary metrics for an authorized document."""
    doc, app = _get_authorized_document_and_app(document_id, current_user, db)

    if version is not None:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        ).first()
    else:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded versions exist for this document slot."
        )

    run = db.query(DocumentProcessingRun).filter(
        DocumentProcessingRun.document_version_id == target_version.id
    ).order_by(DocumentProcessingRun.created_at.desc()).first()

    if not run:
        return DocumentProcessingStatusResponse(
            run_id="",
            document_id=doc.id,
            document_version_id=target_version.id,
            status="NOT_PROCESSED",
            processor_version="idp-pipeline-v1.0.0",
            extraction_method="UNKNOWN",
            pages_processed=0,
            pages_digital=0,
            pages_ocr=0,
            average_confidence=0.0,
            error_message=None,
            created_at=target_version.upload_timestamp,
            completed_at=None,
            fields_count=0
        )

    return run


@router.get("/{document_id}/extracted-fields", response_model=DocumentExtractionResultResponse)
def get_extracted_fields(
    document_id: str,
    version: Optional[int] = Query(None, description="Document version number. Defaults to latest version."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves structured extracted fields with provenance and spatial coordinates (API_CONTRACT Section 4.3)."""
    doc, app = _get_authorized_document_and_app(document_id, current_user, db)

    if version is not None:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        ).first()
    else:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded versions exist for this document slot."
        )

    run = db.query(DocumentProcessingRun).filter(
        DocumentProcessingRun.document_version_id == target_version.id
    ).order_by(DocumentProcessingRun.created_at.desc()).first()

    if not run:
        return DocumentExtractionResultResponse(
            document_id=doc.id,
            document_version_id=target_version.id,
            version_number=target_version.version_number,
            document_type=doc.document_type,
            status="NOT_PROCESSED",
            processing_run=None,
            extracted_fields=[]
        )

    fields = db.query(ExtractedField).filter(
        ExtractedField.processing_run_id == run.id
    ).all()

    field_responses = [
        ExtractedFieldResponse.model_validate(f) for f in fields
    ]
    run_response = DocumentProcessingStatusResponse.model_validate(run)

    return DocumentExtractionResultResponse(
        document_id=doc.id,
        document_version_id=target_version.id,
        version_number=target_version.version_number,
        document_type=doc.document_type,
        status=run.status,
        processing_run=run_response,
        extracted_fields=field_responses
    )


@router.get("/{document_id}/pages", response_model=List[DocumentPageResponse])
def get_document_pages(
    document_id: str,
    version: Optional[int] = Query(None, description="Document version number. Defaults to latest version."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves page-level extracted text and extraction method details."""
    doc, app = _get_authorized_document_and_app(document_id, current_user, db)

    if version is not None:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        ).first()
    else:
        target_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded versions exist for this document slot."
        )

    pages = db.query(DocumentPage).filter(
        DocumentPage.document_version_id == target_version.id
    ).order_by(DocumentPage.page_number.asc()).all()

    return [DocumentPageResponse.model_validate(p) for p in pages]

