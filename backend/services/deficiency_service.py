# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Deficiency Resolution, Corrective Actions & Revalidation Service (backend/services/deficiency_service.py)

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.core.database import utc_now
from backend.core.deps import verify_institution_access
from backend.models.user import User
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.regulatory import RegulatoryRule, ValidationRun, Finding
from backend.models.deficiency import CorrectionSubmission
from backend.models.audit import AuditEvent
from backend.models.extraction import DocumentProcessingRun
from backend.schemas.deficiency import (
    CorrectionDraftRequest,
    CorrectionSubmitRequest,
    CorrectionSubmissionResponse,
    DeficiencyItemResponse,
    ApplicationDeficienciesResponse,
    ComparisonItem,
    RevalidationResponse,
    TimelineEvent,
    FindingHistoryResponse,
)
from backend.schemas.regulatory import FindingEvidence
from backend.services.audit_service import create_audit_event
from backend.services.regulatory_engine import RegulatoryEngine
from backend.services.extraction_service import DocumentProcessingPipeline

logger = logging.getLogger("aicte-deficiency-service")


class DeficiencyService:
    def __init__(self, db: Session):
        self.db = db

    def _parse_evidence(self, finding: Finding) -> FindingEvidence:
        """Parses stored JSON evidence or secondary evidence into standard FindingEvidence schema."""
        ev = FindingEvidence(
            document_id=finding.document_id,
            document_version_id=finding.document_version_id,
            page_number=finding.evidence_page_number,
            confidence=finding.evidence_confidence if finding.evidence_confidence is not None else 1.0,
            raw_text=finding.evidence_raw_text,
        )
        if finding.evidence_bounding_box_json:
            try:
                ev.bounding_box = json.loads(finding.evidence_bounding_box_json)
            except Exception:
                pass
        if finding.evidence_secondary_json:
            try:
                ev.secondary_evidence = json.loads(finding.evidence_secondary_json)
            except Exception:
                pass
        return ev

    def get_application_deficiencies(
        self, application_id: str, current_user: User
    ) -> ApplicationDeficienciesResponse:
        """
        Retrieves all actionable findings (deficiencies and warnings) for an authorized application.
        Integrates active response drafts, latest submissions, and lifecycle status.
        Enforces strict tenant isolation.
        """
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        # Retrieve the latest validation run for the application
        latest_run = (
            self.db.query(ValidationRun)
            .filter(ValidationRun.application_id == application_id)
            .order_by(ValidationRun.run_number.desc())
            .first()
        )

        latest_run_id = latest_run.id if latest_run else None

        # Fetch actionable findings: findings in latest run, plus any unresolved findings from earlier runs
        actionable_outcomes = ["DEFICIENCY_DETECTED", "ADVISORY_WARNING"]
        query = self.db.query(Finding).filter(
            Finding.application_id == application_id,
            Finding.severity.in_(["DEFICIENCY", "WARNING"]),
            Finding.outcome.in_(actionable_outcomes),
        )

        if latest_run_id:
            # Prefer findings from the latest run, or unresolved findings from prior runs
            query = query.filter(
                or_(
                    Finding.validation_run_id == latest_run_id,
                    Finding.status.in_(["OPEN", "ACKNOWLEDGED", "RESPONSE_IN_PROGRESS", "CORRECTION_SUBMITTED", "AWAITING_REVIEW"]),
                )
            )

        findings = query.order_by(Finding.created_at.desc()).all()

        # Deduplicate findings by rule_code to prevent duplicate deficiency items across runs
        deduped_findings: Dict[str, Finding] = {}
        for f in findings:
            existing = deduped_findings.get(f.rule_code)
            if not existing:
                deduped_findings[f.rule_code] = f
            else:
                if (f.status in ["AWAITING_REVIEW", "CORRECTION_SUBMITTED", "RESPONSE_IN_PROGRESS"] and existing.status not in ["AWAITING_REVIEW", "CORRECTION_SUBMITTED"]) or f.correction_submissions:
                    deduped_findings[f.rule_code] = f

        findings = list(deduped_findings.values())

        items: List[DeficiencyItemResponse] = []
        acknowledged_count = 0
        in_progress_count = 0
        submitted_count = 0
        awaiting_review_count = 0
        resolved_count = 0

        for f in findings:
            # Query active submissions for this finding or rule
            submissions = (
                self.db.query(CorrectionSubmission)
                .filter(
                    CorrectionSubmission.application_id == application_id,
                    or_(
                        CorrectionSubmission.finding_id == f.id,
                        CorrectionSubmission.finding.has(Finding.rule_code == f.rule_code)
                    )
                )
                .order_by(CorrectionSubmission.cycle_number.desc(), CorrectionSubmission.created_at.desc())
                .all()
            )

            active_draft = next((s for s in submissions if s.status == "DRAFT"), None)
            latest_submission = next((s for s in submissions if s.status == "SUBMITTED"), None)

            # Determine composite resolution status
            if f.status == "AWAITING_REVIEW" or (latest_submission and latest_submission.resolution_outcome == "CONDITION_CLEARED"):
                res_status = "AWAITING_REVIEW"
                awaiting_review_count += 1
            elif f.status == "RESOLVED":
                res_status = "RESOLVED"
                resolved_count += 1
            elif latest_submission and latest_submission.status == "SUBMITTED":
                res_status = "CORRECTION_SUBMITTED"
                submitted_count += 1
            elif active_draft:
                res_status = "RESPONSE_IN_PROGRESS"
                in_progress_count += 1
            elif f.acknowledged_at or f.status == "ACKNOWLEDGED":
                res_status = "ACKNOWLEDGED"
                acknowledged_count += 1
            else:
                res_status = "OPEN"

            doc_title = None
            if f.document_id:
                doc = self.db.query(Document).filter(Document.id == f.document_id).first()
                if doc:
                    doc_title = doc.title or doc.document_type

            draft_resp = CorrectionSubmissionResponse.model_validate(active_draft) if active_draft else None
            sub_resp = CorrectionSubmissionResponse.model_validate(latest_submission) if latest_submission else None

            official_src = f.rule_version.rule.official_source if f.rule_version and f.rule_version.rule else None

            items.append(
                DeficiencyItemResponse(
                    id=f.id,
                    validation_run_id=f.validation_run_id,
                    application_id=f.application_id,
                    rule_code=f.rule_code,
                    rule_title=f.rule_title,
                    official_source=official_src,
                    category=f.category,
                    severity=f.severity,
                    outcome=f.outcome,
                    status=f.status,
                    title=f.title,
                    explanation=f.explanation,
                    expected_value=f.expected_value,
                    observed_value=f.observed_value,
                    evidence=self._parse_evidence(f),
                    verification_status=f.verification_status,
                    recommended_action=f.recommended_action,
                    created_at=f.created_at,
                    acknowledged_at=f.acknowledged_at,
                    resolved_at=f.resolved_at,
                    resolution_status=res_status,
                    active_draft=draft_resp,
                    latest_submission=sub_resp,
                    document_title=doc_title,
                )
            )

        return ApplicationDeficienciesResponse(
            application_id=app.id,
            application_status=app.status,
            total_deficiencies=len(items),
            actionable_count=len(items),
            acknowledged_count=acknowledged_count + in_progress_count + submitted_count + awaiting_review_count + resolved_count,
            in_progress_count=in_progress_count,
            submitted_count=submitted_count,
            awaiting_review_count=awaiting_review_count,
            resolved_count=resolved_count,
            latest_validation_run_id=latest_run_id,
            deficiencies=items,
        )

    def acknowledge_finding(self, finding_id: str, current_user: User) -> DeficiencyItemResponse:
        """
        Marks an actionable finding as formally reviewed and acknowledged by the applicant.
        Does not resolve the finding; establishes traceability of applicant awareness.
        """
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

        app = self.db.query(Application).filter(Application.id == finding.application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        if not finding.acknowledged_at:
            finding.acknowledged_at = utc_now()
            finding.acknowledged_by_user_id = current_user.id
            if finding.status == "OPEN":
                finding.status = "ACKNOWLEDGED"

            self.db.commit()
            self.db.refresh(finding)

            create_audit_event(
                db=self.db,
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                action="FINDING_ACKNOWLEDGED",
                entity_type="finding",
                entity_id=finding.id,
                payload={
                    "application_id": app.id,
                    "rule_code": finding.rule_code,
                    "acknowledged_at": finding.acknowledged_at.isoformat(),
                },
            )

        # Retrieve any submission
        submissions = (
            self.db.query(CorrectionSubmission)
            .filter(CorrectionSubmission.finding_id == finding.id)
            .order_by(CorrectionSubmission.cycle_number.desc())
            .all()
        )
        active_draft = next((s for s in submissions if s.status == "DRAFT"), None)
        latest_submission = next((s for s in submissions if s.status == "SUBMITTED"), None)

        res_status = "ACKNOWLEDGED"
        if active_draft:
            res_status = "RESPONSE_IN_PROGRESS"
        elif latest_submission:
            res_status = "CORRECTION_SUBMITTED"

        official_src = finding.rule_version.rule.official_source if finding.rule_version and finding.rule_version.rule else None

        return DeficiencyItemResponse(
            id=finding.id,
            validation_run_id=finding.validation_run_id,
            application_id=finding.application_id,
            rule_code=finding.rule_code,
            rule_title=finding.rule_title,
            official_source=official_src,
            category=finding.category,
            severity=finding.severity,
            outcome=finding.outcome,
            status=finding.status,
            title=finding.title,
            explanation=finding.explanation,
            expected_value=finding.expected_value,
            observed_value=finding.observed_value,
            evidence=self._parse_evidence(finding),
            verification_status=finding.verification_status,
            recommended_action=finding.recommended_action,
            created_at=finding.created_at,
            acknowledged_at=finding.acknowledged_at,
            resolved_at=finding.resolved_at,
            resolution_status=res_status,
            active_draft=CorrectionSubmissionResponse.model_validate(active_draft) if active_draft else None,
            latest_submission=CorrectionSubmissionResponse.model_validate(latest_submission) if latest_submission else None,
        )

    def get_draft_response(self, finding_id: str, current_user: User) -> Optional[CorrectionSubmissionResponse]:
        """Retrieves the active draft response or latest submission for a finding."""
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

        app = self.db.query(Application).filter(Application.id == finding.application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        submission = (
            self.db.query(CorrectionSubmission)
            .filter(CorrectionSubmission.finding_id == finding_id)
            .order_by(CorrectionSubmission.cycle_number.desc(), CorrectionSubmission.created_at.desc())
            .first()
        )
        if not submission:
            return None

        return CorrectionSubmissionResponse.model_validate(submission)

    def save_draft_response(
        self, finding_id: str, payload: CorrectionDraftRequest, current_user: User
    ) -> CorrectionSubmissionResponse:
        """
        Saves or updates a draft corrective response for an actionable finding.
        Validates referenced documents belong to the application.
        """
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

        app = self.db.query(Application).filter(Application.id == finding.application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        # Application lifecycle check: cannot edit locked/withdrawn applications
        if app.status in ["APPROVED", "REJECTED", "WITHDRAWN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit corrections for an application in '{app.status}' status."
            )

        # Document reference validation
        if payload.document_id:
            doc = self.db.query(Document).filter(
                Document.id == payload.document_id,
                Document.application_id == app.id
            ).first()
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced supporting document does not belong to this application."
                )
            if payload.document_version_id:
                doc_ver = self.db.query(DocumentVersion).filter(
                    DocumentVersion.id == payload.document_version_id,
                    DocumentVersion.document_id == doc.id
                ).first()
                if not doc_ver:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Referenced document version does not belong to the selected document."
                    )

        # Check for existing DRAFT in the current cycle
        draft = (
            self.db.query(CorrectionSubmission)
            .filter(
                CorrectionSubmission.finding_id == finding_id,
                CorrectionSubmission.status == "DRAFT"
            )
            .order_by(CorrectionSubmission.cycle_number.desc())
            .first()
        )

        if draft:
            draft.response_text = payload.response_text
            draft.response_category = payload.response_category
            draft.document_id = payload.document_id
            draft.document_version_id = payload.document_version_id
            draft.updated_at = utc_now()
        else:
            # Workflow Guard: cannot create correction draft for a resolved finding
            if finding.status == "RESOLVED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot create or update a correction draft for a resolved finding."
                )

            # Determine cycle number and inspect latest submission
            last_sub = (
                self.db.query(CorrectionSubmission)
                .filter(CorrectionSubmission.finding_id == finding_id)
                .order_by(CorrectionSubmission.cycle_number.desc(), CorrectionSubmission.created_at.desc())
                .first()
            )

            if last_sub and last_sub.status == "SUBMITTED":
                if last_sub.reviewer_disposition != "RETURNED_FOR_CORRECTION":
                    # 1. Guard against draft creation while awaiting revalidation
                    if last_sub.revalidation_status in ["PENDING", None]:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"A correction submission for cycle {last_sub.cycle_number} is currently "
                                "awaiting revalidation. A new draft cannot be created until "
                                "revalidation is executed or the submission is formally returned for correction."
                            )
                        )

                    # 2. Guard against draft creation while awaiting reviewer disposition
                    if (
                        last_sub.resolution_outcome == "CONDITION_CLEARED"
                        or finding.status == "AWAITING_REVIEW"
                        or last_sub.reviewer_disposition == "PENDING_REVIEW"
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"A correction submission for cycle {last_sub.cycle_number} has been revalidated "
                                "and is currently awaiting reviewer disposition. A new draft cannot be created."
                            )
                        )

            if finding.status == "AWAITING_REVIEW":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot save correction draft while finding is awaiting reviewer disposition."
                )

            next_cycle = (last_sub.cycle_number + 1) if last_sub else 1

            draft = CorrectionSubmission(
                finding_id=finding.id,
                application_id=app.id,
                cycle_number=next_cycle,
                user_id=current_user.id,
                status="DRAFT",
                response_text=payload.response_text,
                response_category=payload.response_category,
                document_id=payload.document_id,
                document_version_id=payload.document_version_id,
                initial_validation_run_id=finding.validation_run_id,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            self.db.add(draft)

        if finding.status in ["OPEN", "ACKNOWLEDGED"]:
            finding.status = "RESPONSE_IN_PROGRESS"

        self.db.commit()
        self.db.refresh(draft)

        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="CORRECTION_DRAFT_SAVED",
            entity_type="correction_submission",
            entity_id=draft.id,
            payload={
                "finding_id": finding.id,
                "application_id": app.id,
                "cycle_number": draft.cycle_number,
                "document_id": draft.document_id,
            },
        )

        return CorrectionSubmissionResponse.model_validate(draft)

    def submit_correction(
        self, finding_id: str, payload: CorrectionSubmitRequest, current_user: User
    ) -> CorrectionSubmissionResponse:
        """
        Formally submits an applicant's corrective response.
        Enforces immutable submission timestamp, transitions finding to CORRECTION_SUBMITTED,
        and prepares the submission for controlled revalidation.
        """
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

        app = self.db.query(Application).filter(Application.id == finding.application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        if app.status in ["APPROVED", "REJECTED", "WITHDRAWN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit corrections for an application in '{app.status}' status."
            )

        # Document validation
        if payload.document_id:
            doc = self.db.query(Document).filter(
                Document.id == payload.document_id,
                Document.application_id == app.id
            ).first()
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced supporting document does not belong to this application."
                )
            if payload.document_version_id:
                doc_ver = self.db.query(DocumentVersion).filter(
                    DocumentVersion.id == payload.document_version_id,
                    DocumentVersion.document_id == doc.id
                ).first()
                if not doc_ver:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Referenced document version does not belong to the selected document."
                    )

        # Retrieve active DRAFT or create fresh submission
        draft = (
            self.db.query(CorrectionSubmission)
            .filter(
                CorrectionSubmission.finding_id == finding_id,
                CorrectionSubmission.status == "DRAFT"
            )
            .order_by(CorrectionSubmission.cycle_number.desc())
            .first()
        )

        now = utc_now()
        if draft:
            draft.response_text = payload.response_text
            draft.response_category = payload.response_category
            draft.document_id = payload.document_id
            draft.document_version_id = payload.document_version_id
            draft.status = "SUBMITTED"
            draft.submitted_at = now
            draft.updated_at = now
            draft.revalidation_status = "PENDING"
            submission = draft
        else:
            # Workflow Guard: cannot submit correction for a resolved finding
            if finding.status == "RESOLVED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot submit corrections for a resolved finding."
                )

            last_sub = (
                self.db.query(CorrectionSubmission)
                .filter(CorrectionSubmission.finding_id == finding_id)
                .order_by(CorrectionSubmission.cycle_number.desc(), CorrectionSubmission.created_at.desc())
                .first()
            )

            if last_sub and last_sub.status == "SUBMITTED":
                if last_sub.reviewer_disposition != "RETURNED_FOR_CORRECTION":
                    # 1. Guard against submission while previous cycle is awaiting revalidation
                    if last_sub.revalidation_status in ["PENDING", None]:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"A correction submission for cycle {last_sub.cycle_number} is currently "
                                "awaiting revalidation. An additional submission cannot be created until "
                                "revalidation is executed or the submission is formally returned for correction."
                            )
                        )

                    # 2. Guard against submission while awaiting reviewer disposition
                    if (
                        last_sub.resolution_outcome == "CONDITION_CLEARED"
                        or finding.status == "AWAITING_REVIEW"
                        or last_sub.reviewer_disposition == "PENDING_REVIEW"
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"A correction submission for cycle {last_sub.cycle_number} has been revalidated "
                                "and is currently awaiting reviewer disposition. An additional submission cannot be created."
                            )
                        )

            if finding.status == "AWAITING_REVIEW":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot submit correction while finding is awaiting reviewer disposition."
                )

            next_cycle = (last_sub.cycle_number + 1) if last_sub else 1

            submission = CorrectionSubmission(
                finding_id=finding.id,
                application_id=app.id,
                cycle_number=next_cycle,
                user_id=current_user.id,
                status="SUBMITTED",
                response_text=payload.response_text,
                response_category=payload.response_category,
                document_id=payload.document_id,
                document_version_id=payload.document_version_id,
                initial_validation_run_id=finding.validation_run_id,
                revalidation_status="PENDING",
                created_at=now,
                updated_at=now,
                submitted_at=now,
            )
            self.db.add(submission)

        # Mark any earlier submitted responses in prior cycles as SUPERSEDED
        self.db.query(CorrectionSubmission).filter(
            CorrectionSubmission.finding_id == finding_id,
            CorrectionSubmission.id != submission.id,
            CorrectionSubmission.status == "SUBMITTED"
        ).update({"status": "SUPERSEDED"}, synchronize_session=False)

        # Transition finding state
        finding.status = "CORRECTION_SUBMITTED"

        self.db.commit()
        self.db.refresh(submission)

        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="CORRECTION_SUBMITTED",
            entity_type="correction_submission",
            entity_id=submission.id,
            payload={
                "finding_id": finding.id,
                "application_id": app.id,
                "cycle_number": submission.cycle_number,
                "document_id": submission.document_id,
                "document_version_id": submission.document_version_id,
            },
        )

        return CorrectionSubmissionResponse.model_validate(submission)

    def revalidate_application(
        self, application_id: str, current_user: User
    ) -> RevalidationResponse:
        """
        Executes controlled revalidation by invoking the actual P7 RegulatoryEngine.
        Selects latest active document versions (v2/v3) and their structured extraction evidence.
        Computes delta comparison against prior findings and updates submission resolution states.
        Maintains decision-support boundary: automated outcomes do not replace authorized human reviewers.
        """
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        # Check for un-extracted attached documents: if any submitted correction references a document version
        # that hasn't completed P6 extraction, ensure extraction runs first
        submitted_corrections = (
            self.db.query(CorrectionSubmission)
            .filter(
                CorrectionSubmission.application_id == application_id,
                CorrectionSubmission.status == "SUBMITTED",
            )
            .all()
        )

        idp_service = DocumentProcessingPipeline(self.db)
        for sub in submitted_corrections:
            if sub.document_version_id:
                has_run = (
                    self.db.query(DocumentProcessingRun)
                    .filter(
                        DocumentProcessingRun.document_version_id == sub.document_version_id,
                        DocumentProcessingRun.status.in_(["COMPLETED", "COMPLETED_WITH_WARNINGS"])
                    )
                    .first()
                )
                if not has_run:
                    ver = self.db.query(DocumentVersion).filter(DocumentVersion.id == sub.document_version_id).first()
                    if ver:
                        try:
                            logger.info(f"Processing attached document version {ver.id} before revalidation...")
                            idp_service.process_document(document_id=ver.document_id, version_number=ver.version_number, current_user=current_user)
                        except Exception as e:
                            logger.warning(f"Pre-revalidation IDP processing failed for version {ver.id}: {e}")

        # Map prior actionable findings for delta comparison
        prior_findings = (
            self.db.query(Finding)
            .filter(
                Finding.application_id == application_id,
                Finding.severity.in_(["DEFICIENCY", "WARNING"]),
            )
            .all()
        )
        prior_finding_map: Dict[str, Finding] = {f.rule_code: f for f in prior_findings}

        # Invoke real P7 RegulatoryEngine
        engine = RegulatoryEngine(self.db)
        new_run, new_findings = engine.evaluate_application(
            application_id=application_id,
            triggered_by_user_id=current_user.id,
            trigger_type="CORRECTION_REVALIDATION",
        )

        new_finding_map: Dict[str, Finding] = {f.rule_code: f for f in new_findings}

        comparison_items: List[ComparisonItem] = []
        cleared_count = 0
        persisting_count = 0
        new_count = 0

        # Evaluate what happened to prior actionable findings
        for rule_code, old_f in prior_finding_map.items():
            new_f = new_finding_map.get(rule_code)

            # Locate relevant correction submission by finding_id or rule_code
            sub = next((s for s in submitted_corrections if s.finding_id == old_f.id or (s.finding and s.finding.rule_code == rule_code)), None)

            if new_f and new_f.outcome == "DEFICIENCY_DETECTED":
                # Condition persists
                persisting_count += 1
                status_change = "PERSISTS"
                details = f"Rule check re-evaluated: condition still detected. Observed '{new_f.observed_value}', expected '{new_f.expected_value}'."
                if sub:
                    sub.revalidation_run_id = new_run.id
                    sub.revalidation_status = "COMPLETED"
                    sub.resolution_outcome = "CONDITION_PERSISTS"
                    sub.comparison_notes = details

            elif (new_f and new_f.outcome == "NO_ISSUE_DETECTED") or (new_f is None):
                # Condition cleared!
                cleared_count += 1
                status_change = "CLEARED"
                details = f"Rule check re-evaluated: requirement is now satisfied under latest evidence."
                if sub:
                    sub.revalidation_run_id = new_run.id
                    sub.revalidation_status = "COMPLETED"
                    sub.resolution_outcome = "CONDITION_CLEARED"
                    sub.reviewer_disposition = "PENDING_REVIEW"
                    sub.comparison_notes = details
                # Mark finding as resolved in automated pre-scrutiny; awaiting formal reviewer signoff
                old_f.status = "AWAITING_REVIEW"
                old_f.resolved_at = utc_now()
            else:
                # Ambiguous or unable to evaluate
                status_change = "UNCHANGED"
                details = f"Outcome: {new_f.outcome if new_f else 'NOT_EVALUATED'}."
                if sub:
                    sub.revalidation_run_id = new_run.id
                    sub.revalidation_status = "COMPLETED"
                    sub.resolution_outcome = "NEEDS_HUMAN_REVIEW"
                    sub.comparison_notes = details

            comparison_items.append(
                ComparisonItem(
                    finding_id=old_f.id,
                    rule_code=rule_code,
                    rule_title=old_f.rule_title,
                    previous_outcome=old_f.outcome,
                    latest_outcome=new_f.outcome if new_f else "NO_ISSUE_DETECTED",
                    status_change=status_change,
                    previous_observed_value=old_f.observed_value,
                    latest_observed_value=new_f.observed_value if new_f else "COMPLIANT",
                    details=details,
                )
            )

        # Check for newly surfaced findings not present in prior findings
        for rule_code, new_f in new_finding_map.items():
            if rule_code not in prior_finding_map and new_f.outcome == "DEFICIENCY_DETECTED":
                new_count += 1
                comparison_items.append(
                    ComparisonItem(
                        finding_id=new_f.id,
                        rule_code=rule_code,
                        rule_title=new_f.rule_title,
                        previous_outcome="NONE",
                        latest_outcome=new_f.outcome,
                        status_change="NEW",
                        previous_observed_value=None,
                        latest_observed_value=new_f.observed_value,
                        details=f"New deficiency surfaced during revalidation: {new_f.explanation}",
                    )
                )

        self.db.commit()

        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="APPLICATION_REVALIDATED",
            entity_type="validation_run",
            entity_id=new_run.id,
            payload={
                "application_id": application_id,
                "run_number": new_run.run_number,
                "cleared_count": cleared_count,
                "persisting_count": persisting_count,
                "new_count": new_count,
            },
        )

        return RevalidationResponse(
            application_id=app.id,
            validation_run_id=new_run.id,
            run_number=new_run.run_number,
            status=new_run.status,
            total_checks=len(new_findings),
            findings_cleared=cleared_count,
            findings_persisting=persisting_count,
            new_findings=new_count,
            comparison=comparison_items,
        )

    def get_finding_history(self, finding_id: str, current_user: User) -> FindingHistoryResponse:
        """
        Retrieves the complete, immutable chronological timeline for a deficiency finding.
        Combines finding discovery, applicant acknowledgement, draft updates, submissions,
        revalidation executions, and forensic audit records.
        """
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

        app = self.db.query(Application).filter(Application.id == finding.application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        verify_institution_access(app, current_user)

        events: List[TimelineEvent] = []

        # 1. Initial Finding Identification
        events.append(
            TimelineEvent(
                event_type="FINDING_IDENTIFIED",
                timestamp=finding.created_at,
                actor="System Regulatory Engine",
                actor_role="SYSTEM",
                description=f"Pre-scrutiny finding detected under {finding.rule_code}: '{finding.title}'",
                details={
                    "severity": finding.severity,
                    "outcome": finding.outcome,
                    "observed_value": finding.observed_value,
                    "expected_value": finding.expected_value,
                },
            )
        )

        # 2. Finding Acknowledgement
        if finding.acknowledged_at:
            events.append(
                TimelineEvent(
                    event_type="ACKNOWLEDGED",
                    timestamp=finding.acknowledged_at,
                    actor=finding.acknowledged_by_user_id or "Applicant",
                    actor_role="INSTITUTION",
                    description="Applicant reviewed and acknowledged the deficiency finding.",
                    details={"status": "ACKNOWLEDGED"},
                )
            )

        # 3. Submissions & Drafts
        submissions = (
            self.db.query(CorrectionSubmission)
            .filter(CorrectionSubmission.finding_id == finding_id)
            .order_by(CorrectionSubmission.created_at.asc())
            .all()
        )

        for s in submissions:
            # Draft creation
            events.append(
                TimelineEvent(
                    event_type="DRAFT_SAVED",
                    timestamp=s.created_at,
                    actor=s.user_id,
                    actor_role="INSTITUTION",
                    description=f"Cycle {s.cycle_number} draft response prepared.",
                    details={
                        "response_category": s.response_category,
                        "document_id": s.document_id,
                        "document_version_id": s.document_version_id,
                    },
                )
            )

            # Formal Submission
            if s.submitted_at:
                events.append(
                    TimelineEvent(
                        event_type="CORRECTION_SUBMITTED",
                        timestamp=s.submitted_at,
                        actor=s.user_id,
                        actor_role="INSTITUTION",
                        description=f"Cycle {s.cycle_number} formal response submitted: {s.response_text[:80]}...",
                        details={
                            "cycle_number": s.cycle_number,
                            "response_category": s.response_category,
                            "status": s.status,
                            "document_version_id": s.document_version_id,
                        },
                    )
                )

            # Revalidation Event
            if s.revalidation_run_id:
                reval_run = self.db.query(ValidationRun).filter(ValidationRun.id == s.revalidation_run_id).first()
                events.append(
                    TimelineEvent(
                        event_type="REVALIDATION_RUN",
                        timestamp=reval_run.completed_at or reval_run.started_at if reval_run else s.updated_at,
                        actor="Regulatory Rule Engine",
                        actor_role="SYSTEM",
                        description=f"Automated revalidation completed. Outcome: {s.resolution_outcome or 'COMPLETED'}",
                        details={
                            "revalidation_run_id": s.revalidation_run_id,
                            "resolution_outcome": s.resolution_outcome,
                            "notes": s.comparison_notes,
                        },
                    )
                )

            # Reviewer Disposition / Handoff
            if s.reviewer_disposition:
                events.append(
                    TimelineEvent(
                        event_type="REVIEWER_DISPOSITION",
                        timestamp=s.reviewed_at or s.updated_at,
                        actor=s.reviewed_by_user_id or "AICTE Scrutiny Committee",
                        actor_role="REVIEWER",
                        description=f"Reviewer disposition recorded: {s.reviewer_disposition}",
                        details={
                            "disposition": s.reviewer_disposition,
                            "notes": s.reviewer_notes,
                        },
                    )
                )

        # Sort timeline chronologically
        events.sort(key=lambda x: x.timestamp)

        return FindingHistoryResponse(
            finding_id=finding.id,
            application_id=app.id,
            history=events,
        )
