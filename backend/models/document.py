# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Document & Version Relational Models (backend/models/document.py)

import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    application = relationship("Application", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    processing_runs = relationship("DocumentProcessingRun", back_populates="document", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document {self.document_type} ({self.status})>"


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    page_count = Column(Integer, nullable=False, default=0)
    is_scanned = Column(Boolean, nullable=False, default=False)
    upload_timestamp = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    document = relationship("Document", back_populates="versions")
    processing_runs = relationship("DocumentProcessingRun", back_populates="version", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="version", cascade="all, delete-orphan")
    pages = relationship("DocumentPage", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
    )

    def __repr__(self) -> str:
        return f"<DocumentVersion {self.document_id} v{self.version_number}>"
