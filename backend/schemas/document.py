# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Document & Checklist Schemas (backend/schemas/document.py)

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class DocumentVersionResponse(BaseModel):
    id: str
    version_number: int
    file_name: str
    file_size_bytes: int
    file_hash_sha256: str
    mime_type: str
    page_count: int
    is_scanned: bool
    upload_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    title: str
    is_mandatory: bool
    status: str
    created_at: datetime
    current_version: Optional[DocumentVersionResponse] = None
    versions: List[DocumentVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ChecklistResponse(BaseModel):
    application_id: str
    total_slots: int = 8
    uploaded_slots: int = 0
    pending_slots: int = 8
    checklist: List[DocumentResponse]


class DocumentUploadResponse(BaseModel):
    document_id: str
    document_type: str = ""
    version_number: int
    file_name: str
    file_hash_sha256: str
    file_size_bytes: int
    status: str
    message: str
