# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Reviewer Scrutiny Service (backend/services/reviewer_service.py)

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from backend.models.application import Application
from backend.models.institution import Institution
from backend.models.user import User
from backend.models.document import Document, DocumentVersion
from backend.models.regulatory import Finding, ValidationRun, RegulatoryRule, RegulatoryRuleVersion
from backend.models.deficiency import CorrectionSubmission
from backend.models.reviewer import ReviewerObservation
from backend.schemas.reviewer import (
    ReviewerQueueItemResponse,
    ReviewerQueueMetrics,
    ReviewerQueueResponse,
    ReviewerObservationResponse,
    ReviewerObservationCreate,
    ReviewerScrutinyDetailResponse,
)
from backend.services.audit_service import create_audit_event


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewerService:
    def __init__(self, db: Session):
        self.db = db

    def _build_queue_item(self, app: Application) -> ReviewerQueueItemResponse:
        """Constructs an enriched ReviewerQueueItemResponse from an Application record."""
        inst = app.institution
        assigned_user = app.assigned_reviewer

        # Findings summary for latest state
        findings = self.db.query(Finding).filter(Finding.application_id == app.id).all()
        
        # Deduplicate findings by rule_code to get latest status per rule
        rules_map: Dict[str, Finding] = {}
        for f in findings:
            if f.rule_code not in rules_map or f.created_at > rules_map[f.rule_code].created_at:
                rules_map[f.rule_code] = f
        
        active_findings = list(rules_map.values())
        deficiencies_count = sum(1 for f in active_findings if f.severity == "DEFICIENCY" and f.status != "RESOLVED")
        warnings_count = sum(1 for f in active_findings if f.severity == "WARNING" and f.status != "RESOLVED")
        awaiting_review_count = sum(1 for f in active_findings if f.status == "AWAITING_REVIEW")
        
        # Active submissions count
        submissions = self.db.query(CorrectionSubmission).filter(
            CorrectionSubmission.application_id == app.id,
            CorrectionSubmission.status == "SUBMITTED"
        ).all()
        correction_submitted_count = len(submissions)

        # Pre-scrutiny score calculation: 100 - (deficiencies * 15 + warnings * 5)
        raw_score = 100 - (deficiencies_count * 15 + warnings_count * 5)
        pre_scrutiny_score = max(0, min(100, raw_score))

        return ReviewerQueueItemResponse(
            id=app.id,
            application_number=app.application_number,
            institution_id=app.institution_id,
            institution_name=inst.name if inst else "Unknown Institution",
            aicte_permanent_id=inst.aicte_permanent_id if inst else "N/A",
            state=inst.state if inst else "N/A",
            district=inst.district if inst else "N/A",
            academic_year=app.academic_year,
            application_type=app.application_type,
            status=app.status,
            review_status=app.review_status or "UNASSIGNED",
            assigned_reviewer_id=app.assigned_reviewer_id,
            assigned_reviewer_name=assigned_user.full_name if assigned_user else None,
            assigned_at=app.assigned_at,
            deficiencies_count=deficiencies_count,
            warnings_count=warnings_count,
            awaiting_review_count=awaiting_review_count,
            correction_submitted_count=correction_submitted_count,
            pre_scrutiny_score=pre_scrutiny_score,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )

    def get_reviewer_queue(
        self,
        current_user: User,
        status_filter: Optional[str] = None,
        review_status_filter: Optional[str] = None,
        assigned_filter: Optional[str] = None,
        academic_year: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> ReviewerQueueResponse:
        """Retrieves paginated applications for authorised scrutiny with real-time metrics."""
        query = self.db.query(Application).join(Institution, Application.institution_id == Institution.id)

        # Search filter
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Application.application_number.ilike(term),
                    Institution.name.ilike(term),
                    Institution.aicte_permanent_id.ilike(term),
                    Institution.district.ilike(term),
                    Institution.state.ilike(term),
                )
            )

        if status_filter:
            query = query.filter(Application.status == status_filter)

        if review_status_filter:
            query = query.filter(Application.review_status == review_status_filter)

        if assigned_filter == "me":
            query = query.filter(Application.assigned_reviewer_id == current_user.id)
        elif assigned_filter == "unassigned":
            query = query.filter(Application.assigned_reviewer_id.is_(None))

        if academic_year:
            query = query.filter(Application.academic_year == academic_year)

        total = query.count()
        offset = (page - 1) * limit
        apps = query.order_by(Application.updated_at.desc()).offset(offset).limit(limit).all()

        items = [self._build_queue_item(app) for app in apps]

        # Calculate high-level queue metrics across all applications
        all_apps = self.db.query(Application).all()
        total_apps = len(all_apps)
        assigned_to_me = sum(1 for a in all_apps if a.assigned_reviewer_id == current_user.id)
        unassigned = sum(1 for a in all_apps if not a.assigned_reviewer_id)
        under_scrutiny = sum(1 for a in all_apps if a.review_status == "UNDER_SCRUTINY")
        awaiting_review = sum(1 for a in all_apps if a.review_status in ("ASSIGNED", "UNDER_SCRUTINY") or a.status == "FINDINGS_AVAILABLE")
        recommended_clear = sum(1 for a in all_apps if a.review_status == "PRE_SCRUTINY_RECOMMENDED_CLEAR")
        returned_for_correction = sum(1 for a in all_apps if a.review_status == "RETURNED_FOR_CORRECTION")

        metrics = ReviewerQueueMetrics(
            total_applications=total_apps,
            assigned_to_me=assigned_to_me,
            unassigned=unassigned,
            under_scrutiny=under_scrutiny,
            awaiting_review=awaiting_review,
            recommended_clear=recommended_clear,
            returned_for_correction=returned_for_correction,
        )

        return ReviewerQueueResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            metrics=metrics,
        )

    def get_scrutiny_case_details(
        self, application_id: str, current_user: User
    ) -> ReviewerScrutinyDetailResponse:
        """Retrieves full scrutiny case summary, checklist, findings, submissions, and observations."""
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or inaccessible.",
            )

        # Transition review_status to UNDER_SCRUTINY if assigned to current reviewer and unstarted
        if app.assigned_reviewer_id == current_user.id and app.review_status in ("UNASSIGNED", "ASSIGNED"):
            app.review_status = "UNDER_SCRUTINY"
            self.db.commit()
            self.db.refresh(app)

        app_item = self._build_queue_item(app)

        # 1. Statutory Checklist
        docs = self.db.query(Document).filter(Document.application_id == app.id).all()
        checklist_data = []
        for d in docs:
            cur_ver = max(d.versions, key=lambda v: v.version_number) if d.versions else None
            checklist_data.append({
                "id": d.id,
                "document_type": d.document_type,
                "title": d.title,
                "status": d.status,
                "version_number": cur_ver.version_number if cur_ver else 1,
                "is_scanned": cur_ver.is_scanned if cur_ver else False,
                "ocr_confidence": 1.0,
                "uploaded_at": cur_ver.upload_timestamp.isoformat() if cur_ver and cur_ver.upload_timestamp else None,
            })

        # 2. Findings (deduplicated by rule_code to present current state)
        findings = self.db.query(Finding).filter(Finding.application_id == app.id).all()
        findings_map: Dict[str, Finding] = {}
        for f in findings:
            if f.rule_code not in findings_map or f.created_at > findings_map[f.rule_code].created_at:
                findings_map[f.rule_code] = f
        
        findings_data = []
        for f in findings_map.values():
            rule_ver = f.rule_version
            official_source = "AICTE Approval Process Handbook (APH 2024-2027)"
            if rule_ver and rule_ver.rule and rule_ver.rule.official_source:
                official_source = rule_ver.rule.official_source

            findings_data.append({
                "id": f.id,
                "rule_code": f.rule_code,
                "rule_title": f.rule_title,
                "category": f.category,
                "severity": f.severity,
                "outcome": f.outcome,
                "status": f.status,
                "explanation": f.explanation,
                "expected_value": f.expected_value,
                "observed_value": f.observed_value,
                "official_source": official_source,
                "document_id": f.document_id,
                "document_version_id": f.document_version_id,
                "evidence_page_number": f.evidence_page_number,
                "evidence_bounding_box_json": f.evidence_bounding_box_json,
                "evidence_raw_text": f.evidence_raw_text,
                "evidence_secondary_json": f.evidence_secondary_json,
                "recommended_action": f.recommended_action,
                "acknowledged_at": f.acknowledged_at.isoformat() if f.acknowledged_at else None,
                "created_at": f.created_at.isoformat(),
            })

        # 3. Correction Submissions (P8 records)
        subs = self.db.query(CorrectionSubmission).filter(
            CorrectionSubmission.application_id == app.id
        ).order_by(CorrectionSubmission.cycle_number.desc(), CorrectionSubmission.created_at.desc()).all()

        subs_data = []
        for s in subs:
            subs_data.append({
                "id": s.id,
                "finding_id": s.finding_id,
                "cycle_number": s.cycle_number,
                "status": s.status,
                "response_text": s.response_text,
                "response_category": s.response_category,
                "document_id": s.document_id,
                "document_version_id": s.document_version_id,
                "revalidation_status": s.revalidation_status,
                "resolution_outcome": s.resolution_outcome,
                "comparison_notes": s.comparison_notes,
                "reviewer_disposition": s.reviewer_disposition,
                "reviewer_notes": s.reviewer_notes,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "created_at": s.created_at.isoformat(),
            })

        # 4. Reviewer Observations
        observations = self.db.query(ReviewerObservation).filter(
            ReviewerObservation.application_id == app.id
        ).order_by(ReviewerObservation.created_at.desc()).all()

        obs_data = []
        for o in observations:
            rev_name = o.reviewer.full_name if o.reviewer else "Authorised Reviewer"
            obs_data.append(
                ReviewerObservationResponse(
                    id=o.id,
                    application_id=o.application_id,
                    finding_id=o.finding_id,
                    submission_id=o.submission_id,
                    reviewer_user_id=o.reviewer_user_id,
                    reviewer_name=rev_name,
                    decision=o.decision,
                    justification=o.justification,
                    is_internal_note=o.is_internal_note,
                    created_at=o.created_at,
                )
            )

        # 5. Revalidation Comparison
        reval_comparison = []
        for s in subs:
            if s.revalidation_run_id and s.resolution_outcome:
                reval_comparison.append({
                    "submission_id": s.id,
                    "finding_id": s.finding_id,
                    "cycle_number": s.cycle_number,
                    "resolution_outcome": s.resolution_outcome,
                    "comparison_notes": s.comparison_notes,
                    "revalidation_status": s.revalidation_status,
                })

        eligible_actions = [
            "ASSIGN_REVIEWER",
            "RECORD_OBSERVATION",
            "RECOMMEND_CLEAR",
            "RETURN_FOR_CORRECTION",
            "FURTHER_REVIEW_REQUIRED",
        ]

        return ReviewerScrutinyDetailResponse(
            application=app_item,
            checklist=checklist_data,
            findings=findings_data,
            correction_submissions=subs_data,
            observations=obs_data,
            revalidation_comparison=reval_comparison,
            eligible_actions=eligible_actions,
        )

    def assign_reviewer(
        self,
        application_id: str,
        target_reviewer_id: str,
        current_user: User,
        remarks: Optional[str] = None,
    ) -> ReviewerQueueItemResponse:
        """Assigns or reassigns an application to an active reviewer."""
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )

        target_user = self.db.query(User).filter(User.id == target_reviewer_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target reviewer user account not found.",
            )

        if not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign case to an inactive reviewer account.",
            )

        if target_user.role not in ("REVIEWER", "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target user role '{target_user.role}' is not eligible for scrutiny review assignment.",
            )

        previous_reviewer = app.assigned_reviewer_id
        app.assigned_reviewer_id = target_user.id
        app.assigned_at = utc_now()
        if app.review_status == "UNASSIGNED":
            app.review_status = "ASSIGNED"

        # Record observation if remarks provided
        if remarks:
            obs = ReviewerObservation(
                application_id=app.id,
                reviewer_user_id=current_user.id,
                decision="ASSIGNED",
                justification=remarks.strip(),
                is_internal_note=True,
            )
            self.db.add(obs)

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="APPLICATION_REVIEWER_ASSIGNED",
            entity_type="APPLICATION",
            entity_id=app.id,
            payload={
                "previous_reviewer_id": previous_reviewer,
                "assigned_reviewer_id": target_user.id,
                "assigned_reviewer_name": target_user.full_name,
                "remarks": remarks,
            },
        )

        self.db.commit()
        self.db.refresh(app)
        return self._build_queue_item(app)

    def record_scrutiny_observation(
        self,
        application_id: str,
        payload: ReviewerObservationCreate,
        current_user: User,
    ) -> ReviewerObservationResponse:
        """Records an official scrutiny observation or decision on a finding or application."""
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )

        finding = None
        if payload.finding_id:
            finding = self.db.query(Finding).filter(
                Finding.id == payload.finding_id,
                Finding.application_id == app.id
            ).first()
            if not finding:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target finding does not exist on this application.",
                )

        submission = None
        if payload.submission_id:
            submission = self.db.query(CorrectionSubmission).filter(
                CorrectionSubmission.id == payload.submission_id,
                CorrectionSubmission.application_id == app.id
            ).first()

        # Update finding & submission if decision relates to correction disposition
        if finding:
            # Query active submission for this finding
            if not submission:
                submission = self.db.query(CorrectionSubmission).filter(
                    CorrectionSubmission.finding_id == finding.id,
                    CorrectionSubmission.status == "SUBMITTED"
                ).order_by(CorrectionSubmission.created_at.desc()).first()

            if payload.decision == "ACCEPT_CORRECTION":
                finding.status = "RESOLVED"
                finding.resolved_at = utc_now()
                if submission:
                    submission.reviewer_disposition = "ACCEPTED"
                    submission.reviewer_notes = payload.justification
                    submission.reviewed_by_user_id = current_user.id
                    submission.reviewed_at = utc_now()

            elif payload.decision == "OVERRULE_DEFICIENCY":
                finding.status = "RESOLVED"
                finding.resolved_at = utc_now()
                if submission:
                    submission.reviewer_disposition = "OVERRULED"
                    submission.reviewer_notes = payload.justification
                    submission.reviewed_by_user_id = current_user.id
                    submission.reviewed_at = utc_now()

            elif payload.decision in ("CONCUR_DEFICIENCY", "REQUIRE_ADDITIONAL_EVIDENCE"):
                finding.status = "OPEN"
                if submission:
                    submission.reviewer_disposition = "RETURNED_FOR_CORRECTION"
                    submission.reviewer_notes = payload.justification
                    submission.reviewed_by_user_id = current_user.id
                    submission.reviewed_at = utc_now()

        # Update application review_status to UNDER_SCRUTINY if in earlier state
        if app.review_status in ("UNASSIGNED", "ASSIGNED"):
            app.review_status = "UNDER_SCRUTINY"

        obs = ReviewerObservation(
            application_id=app.id,
            finding_id=finding.id if finding else None,
            submission_id=submission.id if submission else None,
            reviewer_user_id=current_user.id,
            decision=payload.decision,
            justification=payload.justification.strip(),
            is_internal_note=payload.is_internal_note,
        )
        self.db.add(obs)

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="REVIEWER_OBSERVATION_RECORDED",
            entity_type="APPLICATION",
            entity_id=app.id,
            payload={
                "finding_id": finding.id if finding else None,
                "submission_id": submission.id if submission else None,
                "decision": payload.decision,
                "justification": payload.justification,
                "is_internal_note": payload.is_internal_note,
            },
        )

        self.db.commit()
        self.db.refresh(obs)

        return ReviewerObservationResponse(
            id=obs.id,
            application_id=obs.application_id,
            finding_id=obs.finding_id,
            submission_id=obs.submission_id,
            reviewer_user_id=obs.reviewer_user_id,
            reviewer_name=current_user.full_name,
            decision=obs.decision,
            justification=obs.justification,
            is_internal_note=obs.is_internal_note,
            created_at=obs.created_at,
        )

    def complete_prescrutiny_review(
        self,
        application_id: str,
        decision: str,
        remarks: str,
        current_user: User,
    ) -> ReviewerQueueItemResponse:
        """Completes a formal pre-scrutiny stage review recommendation.
        
        Advisory Boundary: Pre-scrutiny recommendations do not constitute official statutory AICTE approval.
        """
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )

        valid_decisions = (
            "PRE_SCRUTINY_RECOMMENDED_CLEAR",
            "RETURNED_FOR_CORRECTION",
            "FURTHER_REVIEW_REQUIRED",
        )
        if decision not in valid_decisions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision '{decision}'. Must be one of {valid_decisions}.",
            )

        # Precondition check for PRE_SCRUTINY_RECOMMENDED_CLEAR
        if decision == "PRE_SCRUTINY_RECOMMENDED_CLEAR":
            findings = self.db.query(Finding).filter(Finding.application_id == app.id).all()
            rules_map: Dict[str, Finding] = {}
            for f in findings:
                if f.rule_code not in rules_map or f.created_at > rules_map[f.rule_code].created_at:
                    rules_map[f.rule_code] = f
            
            blocking = [f for f in rules_map.values() if f.severity == "DEFICIENCY" and f.status != "RESOLVED"]
            if blocking:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot recommend pre-scrutiny clearance: {len(blocking)} blocking deficiency finding(s) remain open. Each deficiency must be resolved by valid evidence or explicitly overruled.",
                )
            app.review_status = "PRE_SCRUTINY_RECOMMENDED_CLEAR"
            app.status = "REVIEWED"

        elif decision == "RETURNED_FOR_CORRECTION":
            app.review_status = "RETURNED_FOR_CORRECTION"
            app.status = "RETURNED_FOR_CORRECTION"

        elif decision == "FURTHER_REVIEW_REQUIRED":
            app.review_status = "FURTHER_REVIEW_REQUIRED"

        app.overall_reviewer_remarks = remarks.strip()
        app.scrutiny_completed_at = utc_now()

        # Create record in reviewer_observations
        obs = ReviewerObservation(
            application_id=app.id,
            reviewer_user_id=current_user.id,
            decision=decision,
            justification=remarks.strip(),
            is_internal_note=False,
        )
        self.db.add(obs)

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="PRE_SCRUTINY_REVIEW_COMPLETED",
            entity_type="APPLICATION",
            entity_id=app.id,
            payload={
                "decision": decision,
                "remarks": remarks,
                "review_status": app.review_status,
                "application_status": app.status,
            },
        )

        self.db.commit()
        self.db.refresh(app)
        return self._build_queue_item(app)
