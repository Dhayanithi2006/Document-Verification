# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Document Processing Runs, Extracted Fields & Provenance Models (backend/models/extraction.py)

import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class DocumentProcessingRun(Base):
    __tablename__ = "document_processing_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED
    processor_version = Column(String(50), nullable=False, default="idp-pipeline-v1.0.0")
    extraction_method = Column(String(50), nullable=False, default="HYBRID")    # DIGITAL_PDF_TEXT, OCR, HYBRID
    pages_processed = Column(Integer, nullable=False, default=0)
    pages_digital = Column(Integer, nullable=False, default=0)
    pages_ocr = Column(Integer, nullable=False, default=0)
    average_confidence = Column(Float, nullable=False, default=1.0)
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="processing_runs")
    version = relationship("DocumentVersion", back_populates="processing_runs")
    extracted_fields = relationship("ExtractedField", back_populates="processing_run", cascade="all, delete-orphan")

    @property
    def run_id(self) -> str:
        return self.id

    @property
    def fields_count(self) -> int:
        return len(self.extracted_fields) if self.extracted_fields else 0

    def __repr__(self) -> str:
        return f"<DocumentProcessingRun {self.id} (doc={self.document_id}, status={self.status})>"


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    processing_run_id = Column(String(36), ForeignKey("document_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    field_key = Column(String(100), nullable=False, index=True)  # e.g. "valid_until_date", "contiguous_land_area_acres"
    field_label = Column(String(255), nullable=False)            # e.g. "Fire NOC Expiry Date"
    raw_value = Column(String(512), nullable=False)              # Raw text snippet from document
    normalized_value = Column(String(512), nullable=False)       # Canonical normalized value (ISO date, float, clean text)
    data_type = Column(String(50), nullable=False)               # "DATE", "FLOAT", "INTEGER", "STRING", "BOOLEAN"
    
    page_number = Column(Integer, nullable=False, default=1)     # 1-indexed source page
    box_ymin = Column(Float, nullable=True)                      # Normalized spatial coordinates (0.0 to 1.0)
    box_xmin = Column(Float, nullable=True)
    box_ymax = Column(Float, nullable=True)
    box_xmax = Column(Float, nullable=True)
    
    confidence = Column(Float, nullable=False, default=1.0)      # Genuine token confidence (0.0 to 1.0)
    extraction_method = Column(String(50), nullable=False)       # "DIGITAL_PDF_TEXT", "OCR"
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    processing_run = relationship("DocumentProcessingRun", back_populates="extracted_fields")
    document = relationship("Document", back_populates="extracted_fields")
    version = relationship("DocumentVersion", back_populates="extracted_fields")

    @property
    def bounding_box(self):
        if self.box_ymin is not None and self.box_xmin is not None:
            return {
                "ymin": round(self.box_ymin, 4),
                "xmin": round(self.box_xmin, 4),
                "ymax": round(self.box_ymax, 4) if self.box_ymax is not None else round(self.box_ymin + 0.03, 4),
                "xmax": round(self.box_xmax, 4) if self.box_xmax is not None else round(self.box_xmin + 0.2, 4)
            }
        return None

    def __repr__(self) -> str:
        return f"<ExtractedField {self.field_key}={self.normalized_value} (conf={self.confidence:.2f})>"


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)                # 1-indexed
    extraction_method = Column(String(50), nullable=False)       # "DIGITAL_PDF_TEXT", "OCR"
    text_content = Column(Text, nullable=False, default="")      # Raw extracted page text
    confidence = Column(Float, nullable=False, default=1.0)
    char_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    version = relationship("DocumentVersion", back_populates="pages")

    def __repr__(self) -> str:
        return f"<DocumentPage doc_ver={self.document_version_id} p.{self.page_number} ({self.extraction_method})>"
