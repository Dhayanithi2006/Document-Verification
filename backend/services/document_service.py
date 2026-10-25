# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Document & Upload Service (backend/services/document_service.py)

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.user import User
from backend.services.audit_service import create_audit_event

# Statutory 8 Mandatory Documents for EoA Applications
MANDATORY_EOA_DOCUMENTS = [
    {
        "document_type": "LAND_TITLE_DEED",
        "title": "Land Title Deed / Registered Lease Deed",
        "is_mandatory": True,
    },
    {
        "document_type": "LAND_USE_CERTIFICATE",
        "title": "Land Use Certificate / Non-Agricultural (NA) Order",
        "is_mandatory": True,
    },
    {
        "document_type": "APPROVED_BUILDING_PLAN",
        "title": "Approved Building Master Plan & Blueprints",
        "is_mandatory": True,
    },
    {
        "document_type": "BUILDING_COMPLETION",
        "title": "Building Completion / Occupancy Certificate",
        "is_mandatory": True,
    },
    {
        "document_type": "FIRE_SAFETY_NOC",
        "title": "Fire Safety Certificate / No-Objection Certificate",
        "is_mandatory": True,
    },
    {
        "document_type": "STRUCTURAL_STABILITY",
        "title": "Structural Stability & Soundness Certificate",
        "is_mandatory": False,
    },
    {
        "document_type": "PREV_AICTE_APPROVAL",
        "title": "Previous AICTE Approval / EoA Letter",
        "is_mandatory": True,
    },
    {
        "document_type": "FACULTY_ROSTER",
        "title": "Faculty Roster & Cadre Distribution",
        "is_mandatory": True,
    },
]


def initialize_application_checklist(db: Session, application_id: str) -> None:
    """Initializes the 8 mandatory document checklist slots in PENDING state."""
    for item in MANDATORY_EOA_DOCUMENTS:
        doc = Document(
            application_id=application_id,
            document_type=item["document_type"],
            title=item["title"],
            is_mandatory=item["is_mandatory"],
            status="PENDING",
        )
        db.add(doc)
    db.commit()


def validate_pdf_content(file_bytes: bytes, filename: str) -> Tuple[int, str]:
    """Validates that uploaded content is a genuine, non-empty PDF file.
    
    Checks:
    1. Minimum length.
    2. Magic-byte signature (%PDF-).
    3. Maximum upload size (15MB).
    4. Calculates cryptographic SHA-256 hash.
    5. Estimates page count safely.
    """
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Uploaded file is empty (0 bytes). Please upload a valid document."
        )

    # Magic-byte signature verification
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid file signature: Content does not begin with standard PDF magic-bytes (%PDF-). Disallowed or corrupted file."
        )

    # Size limit check
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum permissible size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Compute SHA-256 hash
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    # Estimate page count safely
    page_count = 1
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        page_count = len(reader.pages)
    except Exception:
        # Fallback if reader fails to parse header but bytes are valid
        page_count = 1

    return page_count, sha256


async def save_uploaded_document(
    db: Session,
    application: Application,
    document_type: str,
    file: UploadFile,
    current_user: User,
    ip_address: str = "127.0.0.1"
) -> DocumentVersion:
    """Securely validates, stores on private disk, and persists document version metadata."""
    # Validate filename extension
    original_filename = Path(file.filename or "uploaded.pdf").name
    ext = Path(original_filename).suffix.lower()
    if ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Disallowed file format. Only PDF (.pdf) documents are permitted."
        )

    # Read content safely
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file stream: {str(e)}"
        )

    # Validate PDF content & signatures
    page_count, file_hash = validate_pdf_content(content, original_filename)

    # Find or create logical Document slot
    doc = db.query(Document).filter(
        Document.application_id == application.id,
        Document.document_type == document_type
    ).first()

    if not doc:
        # Check if type is among mandatory list to get title
        item_meta = next((m for m in MANDATORY_EOA_DOCUMENTS if m["document_type"] == document_type), None)
        title = item_meta["title"] if item_meta else document_type.replace("_", " ").title()
        doc = Document(
            application_id=application.id,
            document_type=document_type,
            title=title,
            is_mandatory=True if item_meta else False,
            status="PENDING"
        )
        db.add(doc)
        db.flush()

    # Determine next version number
    version_num = len(doc.versions) + 1

    # Safe private storage path (never use untrusted client filename on disk)
    storage_root = Path(settings.STORAGE_DIR)
    app_storage_dir = storage_root / application.institution_id / application.id
    app_storage_dir.mkdir(parents=True, exist_ok=True)

    safe_file_name = f"{document_type}_v{version_num}_{file_hash[:8]}.pdf"
    file_disk_path = app_storage_dir / safe_file_name
    relative_path = str(file_disk_path.relative_to(Path(".")) if file_disk_path.is_relative_to(Path(".")) else file_disk_path)

    # Write file to disk
    try:
        with open(file_disk_path, "wb") as f:
            f.write(content)
    except Exception as write_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist document to private storage: {str(write_err)}"
        )

    # Persist version record atomically
    try:
        version = DocumentVersion(
            document_id=doc.id,
            version_number=version_num,
            file_name=original_filename,
            file_path=relative_path,
            file_size_bytes=len(content),
            file_hash_sha256=file_hash,
            mime_type="application/pdf",
            page_count=page_count,
            is_scanned=False,
        )
        db.add(version)

        # Update document status
        doc.status = "UPLOADED"
        db.commit()
        db.refresh(version)
    except Exception as db_err:
        db.rollback()
        # Compensating cleanup: delete untracked file
        if file_disk_path.exists():
            file_disk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database persistence failed: {str(db_err)}"
        )

    # Record Audit Event
    create_audit_event(
        db=db,
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="DOCUMENT_UPLOADED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        payload={
            "document_type": document_type,
            "version_number": version_num,
            "file_name": original_filename,
            "file_size_bytes": len(content),
            "file_hash_sha256": file_hash,
            "application_id": application.id
        },
        ip_address=ip_address
    )

    return version
