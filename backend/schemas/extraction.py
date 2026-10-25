# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Intelligent Document Processing (IDP) Schemas (backend/schemas/extraction.py)

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class BoundingBox(BaseModel):
    ymin: Optional[float] = None
    xmin: Optional[float] = None
    ymax: Optional[float] = None
    xmax: Optional[float] = None


class ExtractedFieldResponse(BaseModel):
    id: str
    processing_run_id: str
    document_id: str
    document_version_id: str
    field_key: str
    field_label: str
    raw_value: str
    normalized_value: str
    data_type: str
    page_number: int
    bounding_box: Optional[BoundingBox] = None
    confidence: float
    extraction_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPageResponse(BaseModel):
    id: str
    document_version_id: str
    page_number: int
    extraction_method: str
    text_content: str
    confidence: float
    char_count: int
    word_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentProcessingStatusResponse(BaseModel):
    run_id: str
    document_id: str
    document_version_id: str
    status: str
    processor_version: str
    extraction_method: str
    pages_processed: int
    pages_digital: int
    pages_ocr: int
    average_confidence: float
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    fields_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentExtractionResultResponse(BaseModel):
    document_id: str
    document_version_id: str
    version_number: int
    document_type: str
    status: str
    processing_run: Optional[DocumentProcessingStatusResponse] = None
    extracted_fields: List[ExtractedFieldResponse] = []
    pages: Optional[List[DocumentPageResponse]] = None


class ReprocessRequest(BaseModel):
    force: bool = False
