# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Administrator Management Service (backend/services/admin_service.py)

from typing import List, Optional, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.core.security import get_password_hash
from backend.models.user import User
from backend.models.institution import Institution
from backend.models.application import Application
from backend.models.regulatory import Finding
from backend.models.audit import AuditEvent
from backend.schemas.admin import (
    AdminOverviewMetrics,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AdminUserResponse,
    AdminInstitutionResponse,
    AdminInstitutionUpdateRequest,
    AdminAuditEventResponse,
)
from backend.services.audit_service import create_audit_event


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview_metrics(self) -> AdminOverviewMetrics:
        """Computes live system overview metrics from the real relational database."""
        users = self.db.query(User).all()
        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active)
        inactive_users = total_users - active_users
        total_reviewers = sum(1 for u in users if u.role == "REVIEWER")

        total_institutions = self.db.query(Institution).count()
        applications = self.db.query(Application).all()
        total_applications = len(applications)

        # Status breakdowns
        status_map: Dict[str, int] = {}
        review_status_map: Dict[str, int] = {}
        for a in applications:
            st = a.status or "DRAFT"
            status_map[st] = status_map.get(st, 0) + 1
            rst = a.review_status or "UNASSIGNED"
            review_status_map[rst] = review_status_map.get(rst, 0) + 1

        total_findings = self.db.query(Finding).count()
        total_audit_events = self.db.query(AuditEvent).count()

        return AdminOverviewMetrics(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            total_reviewers=total_reviewers,
            total_institutions=total_institutions,
            total_applications=total_applications,
            applications_by_status=status_map,
            applications_by_review_status=review_status_map,
            total_findings=total_findings,
            total_audit_events=total_audit_events,
        )

    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AdminUserResponse]:
        """Lists users with optional filtering and institution metadata."""
        query = self.db.query(User).outerjoin(Institution, User.institution_id == Institution.id)

        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.email.ilike(term),
                    User.full_name.ilike(term),
                    Institution.name.ilike(term),
                )
            )

        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        return [
            AdminUserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                institution_id=u.institution_id,
                institution_name=u.institution.name if u.institution else None,
                is_active=u.is_active,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
            )
            for u in users
        ]

    def create_user(
        self, payload: AdminUserCreateRequest, current_user: User
    ) -> AdminUserResponse:
        """Provisions a new user account with hashed credentials and strict role validation."""
        existing = self.db.query(User).filter(User.email == payload.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user account with this email address already exists.",
            )

        valid_roles = ("INSTITUTION", "REVIEWER", "ADMIN")
        if payload.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user role '{payload.role}'. Must be one of {valid_roles}.",
            )

        if payload.role == "INSTITUTION" and not payload.institution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institution applicant accounts must be bound to an authorized educational institution.",
            )

        if payload.institution_id:
            inst = self.db.query(Institution).filter(Institution.id == payload.institution_id).first()
            if not inst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified institution does not exist.",
                )

        import uuid
        new_user_id = str(uuid.uuid4())
        new_user = User(
            id=new_user_id,
            email=payload.email.lower().strip(),
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name.strip(),
            role=payload.role,
            institution_id=payload.institution_id if payload.role == "INSTITUTION" else None,
            is_active=payload.is_active,
        )
        self.db.add(new_user)

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="USER_PROVISIONED",
            entity_type="USER",
            entity_id=new_user.id,
            payload={
                "email": new_user.email,
                "role": new_user.role,
                "institution_id": new_user.institution_id,
                "is_active": new_user.is_active,
            },
        )

        self.db.commit()
        self.db.refresh(new_user)

        return AdminUserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            institution_id=new_user.institution_id,
            institution_name=new_user.institution.name if new_user.institution else None,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login_at=new_user.last_login_at,
        )

    def update_user(
        self, user_id: str, payload: AdminUserUpdateRequest, current_user: User
    ) -> AdminUserResponse:
        """Updates user account parameters, role, or active status with safety checks against self-lockout."""
        target_user = self.db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found.",
            )

        # Prevent administrator self-lockout or self-demotion
        if target_user.id == current_user.id:
            if payload.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Administrators cannot deactivate their own active account session.",
                )
            if payload.role and payload.role != "ADMIN":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Administrators cannot demote their own administrative role.",
                )

        if payload.role is not None:
            valid_roles = ("INSTITUTION", "REVIEWER", "ADMIN")
            if payload.role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user role '{payload.role}'.",
                )
            target_user.role = payload.role

        if payload.full_name is not None:
            target_user.full_name = payload.full_name.strip()

        if payload.institution_id is not None:
            if payload.institution_id:
                inst = self.db.query(Institution).filter(Institution.id == payload.institution_id).first()
                if not inst:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Specified institution does not exist.",
                    )
            target_user.institution_id = payload.institution_id

        if payload.is_active is not None:
            target_user.is_active = payload.is_active

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="USER_UPDATED",
            entity_type="USER",
            entity_id=target_user.id,
            payload={
                "updated_role": target_user.role,
                "is_active": target_user.is_active,
                "institution_id": target_user.institution_id,
            },
        )

        self.db.commit()
        self.db.refresh(target_user)

        return AdminUserResponse(
            id=target_user.id,
            email=target_user.email,
            full_name=target_user.full_name,
            role=target_user.role,
            institution_id=target_user.institution_id,
            institution_name=target_user.institution.name if target_user.institution else None,
            is_active=target_user.is_active,
            created_at=target_user.created_at,
            last_login_at=target_user.last_login_at,
        )

    def list_institutions(
        self, search: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[AdminInstitutionResponse]:
        """Lists educational institutions with application counts."""
        query = self.db.query(Institution)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Institution.name.ilike(term),
                    Institution.aicte_permanent_id.ilike(term),
                    Institution.district.ilike(term),
                    Institution.state.ilike(term),
                )
            )

        institutions = query.order_by(Institution.name.asc()).offset(skip).limit(limit).all()

        results = []
        for inst in institutions:
            app_count = self.db.query(Application).filter(Application.institution_id == inst.id).count()
            user_count = self.db.query(User).filter(User.institution_id == inst.id).count()
            results.append(
                AdminInstitutionResponse(
                    id=inst.id,
                    aicte_permanent_id=inst.aicte_permanent_id,
                    name=inst.name,
                    category=inst.category,
                    state=inst.state,
                    district=inst.district,
                    is_rural=inst.is_rural,
                    created_at=inst.created_at,
                    applications_count=app_count,
                    users_count=user_count,
                )
            )
        return results

    def update_institution(
        self, institution_id: str, payload: AdminInstitutionUpdateRequest, current_user: User
    ) -> AdminInstitutionResponse:
        """Updates non-sensitive institutional metadata."""
        inst = self.db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Institution not found.",
            )

        if payload.name is not None:
            inst.name = payload.name.strip()
        if payload.category is not None:
            inst.category = payload.category.strip()
        if payload.state is not None:
            inst.state = payload.state.strip()
        if payload.district is not None:
            inst.district = payload.district.strip()
        if payload.is_rural is not None:
            inst.is_rural = payload.is_rural

        # Audit Event
        create_audit_event(
            db=self.db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="INSTITUTION_UPDATED",
            entity_type="INSTITUTION",
            entity_id=inst.id,
            payload={
                "name": inst.name,
                "category": inst.category,
                "state": inst.state,
                "district": inst.district,
                "is_rural": inst.is_rural,
            },
        )

        self.db.commit()
        self.db.refresh(inst)

        app_count = self.db.query(Application).filter(Application.institution_id == inst.id).count()
        user_count = self.db.query(User).filter(User.institution_id == inst.id).count()

        return AdminInstitutionResponse(
            id=inst.id,
            aicte_permanent_id=inst.aicte_permanent_id,
            name=inst.name,
            category=inst.category,
            state=inst.state,
            district=inst.district,
            is_rural=inst.is_rural,
            created_at=inst.created_at,
            applications_count=app_count,
            users_count=user_count,
        )

    def list_audit_events(
        self,
        action: Optional[str] = None,
        actor_role: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AdminAuditEventResponse]:
        """Queries the immutable security audit log with role-aware inspection."""
        query = self.db.query(AuditEvent)

        if action:
            query = query.filter(AuditEvent.action == action)
        if actor_role:
            query = query.filter(AuditEvent.actor_role == actor_role)
        if entity_type:
            query = query.filter(AuditEvent.entity_type == entity_type)

        events = query.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit).all()

        results = []
        for e in events:
            actor_user = self.db.query(User).filter(User.id == e.actor_user_id).first()
            results.append(
                AdminAuditEventResponse(
                    id=e.id,
                    actor_user_id=e.actor_user_id,
                    actor_email=actor_user.email if actor_user else None,
                    actor_role=e.actor_role,
                    action=e.action,
                    entity_type=e.entity_type,
                    entity_id=e.entity_id,
                    payload_json=e.payload_json,
                    ip_address=e.ip_address,
                    created_at=e.created_at,
                )
            )
        return results
