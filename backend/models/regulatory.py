# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Regulatory Rule Engine & Findings Relational Models (backend/models/regulatory.py)

import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base, utc_now


class RegulatoryRule(Base):
    """Catalog of regulatory compliance rules based on the AICTE Approval Process Handbook."""
    __tablename__ = "regulatory_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "RULE-EOA-FIRE-003"
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # "MANDATORY_SAFETY_CERTIFICATE", "LAND_NORMS", etc.
    official_source = Column(String(512), nullable=False)  # e.g. "AICTE APH 2024-2027 Clause 2.3.4 & NBC Part IV"
    status = Column(String(50), nullable=False, default="APPROVED_FOR_PROTOTYPE_USE")  # 'APPROVED_FOR_PROTOTYPE_USE', 'DRAFT_MISSING_OFFICIAL_SOURCE', 'RETIRED'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    versions = relationship("RegulatoryRuleVersion", back_populates="rule", cascade="all, delete-orphan", order_by="RegulatoryRuleVersion.version_number.desc()")

    def __repr__(self) -> str:
        return f"<RegulatoryRule {self.rule_code} ({self.status})>"


class RegulatoryRuleVersion(Base):
    """Immutable versioned definition of a regulatory compliance rule."""
    __tablename__ = "regulatory_rule_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("regulatory_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
    parameters_json = Column(Text, nullable=False)  # JSON serialized parameters
    severity = Column(String(50), nullable=False, default="DEFICIENCY")  # "DEFICIENCY", "WARNING", "INFO"
    recommended_action = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    approved_by_user_id = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    rule = relationship("RegulatoryRule", back_populates="versions")
    findings = relationship("Finding", back_populates="rule_version")

    def __repr__(self) -> str:
        return f"<RegulatoryRuleVersion {self.rule_id} v{self.version_number}>"


class ValidationRun(Base):
    """Audit record for a regulatory cross-matching pre-scrutiny evaluation run."""
    __tablename__ = "validation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number = Column(Integer, nullable=False, default=1)
    triggered_by_user_id = Column(String(36), nullable=False)
    trigger_type = Column(String(50), nullable=False, default="INITIAL_PRE_SCRUTINY")  # "INITIAL_PRE_SCRUTINY", "REVALIDATION"
    started_at = Column(DateTime, nullable=False, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="COMPLETED", index=True)  # 'RUNNING', 'COMPLETED', 'FAILED'
    total_checks = Column(Integer, nullable=False, default=0)
    deficiencies_count = Column(Integer, nullable=False, default=0)
    warnings_count = Column(Integer, nullable=False, default=0)
    passed_count = Column(Integer, nullable=False, default=0)
    unable_to_evaluate_count = Column(Integer, nullable=False, default=0)
    summary_json = Column(Text, nullable=True)

    # Relationships
    application = relationship("Application", backref="validation_runs")
    findings = relationship("Finding", back_populates="validation_run", cascade="all, delete-orphan", order_by="Finding.created_at.asc()")

    def __repr__(self) -> str:
        return f"<ValidationRun {self.id} App:{self.application_id} Run#{self.run_number}>"


class Finding(Base):
    """Evidence-anchored explainable pre-scrutiny finding produced by the rule engine."""
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    validation_run_id = Column(String(36), ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_version_id = Column(String(36), ForeignKey("regulatory_rule_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    rule_code = Column(String(50), nullable=False, index=True)  # e.g. "RULE-EOA-FIRE-003"
    rule_title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, default="DEFICIENCY", index=True)  # "DEFICIENCY", "WARNING", "INFO"
    outcome = Column(String(50), nullable=False, default="DEFICIENCY_DETECTED", index=True)  # 'DEFICIENCY_DETECTED', 'ADVISORY_WARNING', 'NO_ISSUE_DETECTED', 'UNABLE_TO_EVALUATE', 'NEEDS_HUMAN_REVIEW'
    status = Column(String(50), nullable=False, default="OPEN", index=True)  # 'OPEN', 'CORRECTION_SUBMITTED', 'RESOLVED', 'REJECTED'
    
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    expected_value = Column(Text, nullable=True)
    observed_value = Column(Text, nullable=True)
    
    # Primary Source Document Evidence
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_page_number = Column(Integer, nullable=True)
    evidence_bounding_box_json = Column(Text, nullable=True)  # JSON: {"ymin": 0.342, "xmin": 0.581, ...}
    evidence_raw_text = Column(Text, nullable=True)
    evidence_confidence = Column(Float, nullable=False, default=1.0)
    
    # Secondary Evidence for Cross-Document Consistency Matching
    evidence_secondary_json = Column(Text, nullable=True)  # JSON with doc 2 id, version, page, bounding_box, text, observed_value
    
    verification_status = Column(String(50), nullable=False, default="VERIFIED_INTERNAL")  # "VERIFIED_INTERNAL", "VERIFIED_SIMULATED", "MISMATCH", "UNVERIFIED"
    recommended_action = Column(Text, nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    validation_run = relationship("ValidationRun", back_populates="findings")
    rule_version = relationship("RegulatoryRuleVersion", back_populates="findings")
    document = relationship("Document")
    document_version = relationship("DocumentVersion")

    def __repr__(self) -> str:
        return f"<Finding {self.id} [{self.rule_code}] {self.severity} - {self.outcome}>"
