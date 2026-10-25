# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Regulatory Rule Engine & Findings Schemas (backend/schemas/regulatory.py)

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class FindingEvidence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: Optional[str] = None
    document_version_id: Optional[str] = None
    document_title: Optional[str] = None
    page_number: Optional[int] = None
    bounding_box: Optional[Dict[str, float]] = None
    raw_text: Optional[str] = None
    confidence: float = 1.0
    secondary_evidence: Optional[Dict[str, Any]] = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    validation_run_id: str
    application_id: str
    rule_code: str
    rule_title: str
    official_source: Optional[str] = None
    category: str
    severity: str  # "DEFICIENCY", "WARNING", "INFO"
    outcome: str   # "DEFICIENCY_DETECTED", "ADVISORY_WARNING", "NO_ISSUE_DETECTED", "UNABLE_TO_EVALUATE"
    status: str    # "OPEN", "CORRECTION_SUBMITTED", "RESOLVED"
    title: str
    explanation: str
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    evidence: FindingEvidence
    verification_status: str
    recommended_action: str
    created_at: datetime


class ValidationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    validation_run_id: str
    application_id: str
    run_number: int
    status: str
    total_checks: int
    findings_summary: Dict[str, Any]
    completed_at: Optional[datetime] = None


class ApplicationFindingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    validation_run_id: Optional[str] = None
    run_number: Optional[int] = None
    status: str
    total_checks: int
    summary: Dict[str, Any]
    findings: List[FindingResponse]


class RegulatoryRuleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_number: int
    severity: str
    description: str
    parameters: Dict[str, Any]
    recommended_action: str
    is_active: bool
    approved_at: Optional[datetime] = None


class RegulatoryRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_code: str
    title: str
    category: str
    official_source: str
    status: str
    is_active: bool
    current_version: RegulatoryRuleVersionResponse
