# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Step 4.1: Migration & Rule-Deactivation Governance Verification
# tests/backend/test_migration_governance.py

import os
import json
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import get_db, Base
from backend.core.security import create_access_token
from backend.core.config import settings
from backend.models.user import User
from backend.models.institution import Institution
from backend.models.application import Application
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, Finding
from backend.models.audit import AuditEvent
from backend.services.regulatory_engine import RegulatoryEngine, seed_regulatory_rules

DISPOSABLE_DB_PATH = Path("data/disposable_migration_test.db")
DISPOSABLE_DB_URL = f"sqlite:///{DISPOSABLE_DB_PATH}"


@pytest.fixture(scope="module")
def disposable_db():
    """Sets up a disposable isolated database strictly separate from live data/aicte.db."""
    if DISPOSABLE_DB_PATH.exists():
        try:
            DISPOSABLE_DB_PATH.unlink()
        except Exception:
            pass

    engine = create_engine(
        DISPOSABLE_DB_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Configure Alembic to point to the disposable database URL
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DISPOSABLE_DB_URL)

    yield {
        "engine": engine,
        "sessionmaker": TestingSession,
        "alembic_cfg": alembic_cfg,
        "path": DISPOSABLE_DB_PATH
    }

    # Teardown: close engine and remove disposable db
    engine.dispose()
    if DISPOSABLE_DB_PATH.exists():
        try:
            DISPOSABLE_DB_PATH.unlink()
        except Exception:
            pass


def test_migration_governance_full_lifecycle(disposable_db):
    """
    Executes the comprehensive 8-point migration and rule deactivation governance audit
    prescribed in Step 4.1 against an isolated, disposable database copy.
    """
    engine = disposable_db["engine"]
    SessionMaker = disposable_db["sessionmaker"]
    alembic_cfg = disposable_db["alembic_cfg"]

    # -------------------------------------------------------------------------
    # Baseline: Run migration up to 3f8a1279b401 (state before bank rule deactivation)
    # -------------------------------------------------------------------------
    command.upgrade(alembic_cfg, "3f8a1279b401")
    
    session = SessionMaker()
    try:
        # Seed initial rules, including active RULE-DRAFT-BANK-009 in pre-deactivation state
        rule = RegulatoryRule(
            id=str(uuid.uuid4()),
            rule_code="RULE-DRAFT-BANK-009",
            title="Joint Fixed Deposit (FDR) Lien Period Check",
            category="FINANCIAL_NORMS",
            official_source="State Technical Board Bylaws (Unverified Regional Amendment)",
            status="APPROVED_FOR_PROTOTYPE_USE",
            is_active=True
        )
        session.add(rule)
        session.flush()

        ver = RegulatoryRuleVersion(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            version_number=1,
            severity="WARNING",
            description="Pre-deactivation active draft bank rule.",
            parameters_json=json.dumps({"min_lien_years": 8}),
            recommended_action="Awaiting regional board clarification.",
            is_active=True
        )
        session.add(ver)
        session.commit()

        # Confirm baseline pre-migration state
        pre_rule = session.query(RegulatoryRule).filter_by(rule_code="RULE-DRAFT-BANK-009").first()
        assert pre_rule is not None
        assert pre_rule.is_active is True
        assert pre_rule.status == "APPROVED_FOR_PROTOTYPE_USE"
    finally:
        session.close()

    # -------------------------------------------------------------------------
    # 1. Apply Migration 5a7c92b84102 and Verify Post-Migration State
    # -------------------------------------------------------------------------
    command.upgrade(alembic_cfg, "5a7c92b84102")

    session = SessionMaker()
    try:
        migrated_rule = session.query(RegulatoryRule).filter_by(rule_code="RULE-DRAFT-BANK-009").first()
        assert migrated_rule is not None
        assert migrated_rule.is_active is False
        assert migrated_rule.status == "DRAFT_MISSING_OFFICIAL_SOURCE"

        migrated_ver = session.query(RegulatoryRuleVersion).filter_by(rule_id=migrated_rule.id).first()
        assert migrated_ver is not None
        assert migrated_ver.is_active is False

        # Verify migration generated expected audit event
        mig_audit = session.query(AuditEvent).filter_by(
            action="REGULATORY_RULE_DEACTIVATED",
            actor_user_id="system_migration"
        ).first()
        assert mig_audit is not None
        assert mig_audit.entity_id == migrated_rule.id
        payload = json.loads(mig_audit.payload_json)
        assert payload["rule_code"] == "RULE-DRAFT-BANK-009"
        assert payload["action"] == "DEACTIVATE"
        assert "Step 4 regulatory correction" in payload["reason"]

        # ---------------------------------------------------------------------
        # 2. Confirm RULE-DRAFT-BANK-009 is Inactive and Not Enforced
        # ---------------------------------------------------------------------
        active_rules = session.query(RegulatoryRule).filter_by(is_active=True).all()
        active_codes = {r.rule_code for r in active_rules}
        assert "RULE-DRAFT-BANK-009" not in active_codes

        # ---------------------------------------------------------------------
        # 3. Restart or Run Seed Process and Verify it Does Not Reactivate Rule
        # ---------------------------------------------------------------------
        seed_regulatory_rules(session)
        session.commit()

        post_seed_rule = session.query(RegulatoryRule).filter_by(rule_code="RULE-DRAFT-BANK-009").first()
        assert post_seed_rule.is_active is False
        assert post_seed_rule.status == "DRAFT_MISSING_OFFICIAL_SOURCE"

        post_seed_ver = session.query(RegulatoryRuleVersion).filter_by(rule_id=post_seed_rule.id).first()
        assert post_seed_ver.is_active is False

        # ---------------------------------------------------------------------
        # 4. Check Migration Behavior on an Already-Correct State (Idempotency)
        # ---------------------------------------------------------------------
        # Calling upgrade on the current head should execute idempotently without error
        command.upgrade(alembic_cfg, "head")

        post_idempotent_rule = session.query(RegulatoryRule).filter_by(rule_code="RULE-DRAFT-BANK-009").first()
        assert post_idempotent_rule.is_active is False
        assert post_idempotent_rule.status == "DRAFT_MISSING_OFFICIAL_SOURCE"

    finally:
        session.close()

    # -------------------------------------------------------------------------
    # 5. Verify Admin Deactivation Endpoint Rejects Unauthorized Roles
    # 6. Verify Successful Deactivation Records the Expected Audit Event
    # 7. Check Behavior of Repeated Deactivation Requests
    # -------------------------------------------------------------------------
    def override_get_db():
        s = SessionMaker()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        # Create users in disposable database
        sess = SessionMaker()
        inst = Institution(
            id="inst_disp_01",
            name="Disposable Test Institution",
            aicte_permanent_id="1-DISP-01",
            district="Bangalore Urban",
            state="Karnataka",
            category="ENGINEERING_TECHNOLOGY"
        )
        sess.add(inst)
        sess.flush()

        applicant = User(
            id=str(uuid.uuid4()),
            email="applicant_test@institution.test",
            password_hash="hash",
            full_name="Applicant Test",
            role="INSTITUTION",
            is_active=True,
            institution_id="inst_disp_01"
        )
        reviewer = User(
            id=str(uuid.uuid4()),
            email="reviewer_test@reviewer.test",
            password_hash="hash",
            full_name="Reviewer Test",
            role="REVIEWER",
            is_active=True
        )
        admin = User(
            id=str(uuid.uuid4()),
            email="admin_test@platform.test",
            password_hash="hash",
            full_name="Admin Test",
            role="ADMIN",
            is_active=True
        )
        sess.add_all([applicant, reviewer, admin])
        sess.commit()

        applicant_id = str(applicant.id)
        applicant_email = str(applicant.email)
        applicant_role = str(applicant.role)

        reviewer_id = str(reviewer.id)
        reviewer_email = str(reviewer.email)
        reviewer_role = str(reviewer.role)

        admin_id = str(admin.id)
        admin_email = str(admin.email)
        admin_role = str(admin.role)

        sess.close()

        applicant_token = create_access_token({"sub": applicant_id, "email": applicant_email, "role": applicant_role})
        reviewer_token = create_access_token({"sub": reviewer_id, "email": reviewer_email, "role": reviewer_role})
        admin_token = create_access_token({"sub": admin_id, "email": admin_email, "role": admin_role})

        app_headers = {"Authorization": f"Bearer {applicant_token}"}
        rev_headers = {"Authorization": f"Bearer {reviewer_token}"}
        adm_headers = {"Authorization": f"Bearer {admin_token}"}

        # 5. RBAC checks on /api/v1/rules/{rule_code}/deactivate
        # Unauthenticated -> 401
        res_unauth = client.post("/api/v1/rules/RULE-DRAFT-BANK-009/deactivate")
        assert res_unauth.status_code == 401

        # APPLICANT role -> 403 Forbidden
        res_applicant = client.post("/api/v1/rules/RULE-DRAFT-BANK-009/deactivate", headers=app_headers)
        assert res_applicant.status_code == 403

        # REVIEWER role -> 403 Forbidden
        res_reviewer = client.post("/api/v1/rules/RULE-DRAFT-BANK-009/deactivate", headers=rev_headers)
        assert res_reviewer.status_code == 403

        # 6. Admin authorized deactivation
        res_admin = client.post(
            "/api/v1/rules/RULE-DRAFT-BANK-009/deactivate?reason=Admin+governance+audit+pass",
            headers=adm_headers
        )
        assert res_admin.status_code == 200
        adm_data = res_admin.json()
        assert adm_data["is_active"] is False
        assert adm_data["status"] == "DRAFT_MISSING_OFFICIAL_SOURCE"

        # Verify audit event in database
        sess = SessionMaker()
        admin_audit = sess.query(AuditEvent).filter_by(
            action="REGULATORY_RULE_DEACTIVATED",
            actor_user_id=admin_id
        ).first()
        assert admin_audit is not None
        assert admin_audit.actor_role == "ADMIN"
        assert admin_audit.entity_type == "REGULATORY_RULE"
        audit_payload = json.loads(admin_audit.payload_json)
        assert audit_payload["reason"] == "Admin governance audit pass"
        assert audit_payload["rule_code"] == "RULE-DRAFT-BANK-009"
        initial_audit_count = sess.query(AuditEvent).count()
        sess.close()

        # 7. Repeated deactivation requests (idempotency check)
        res_repeat = client.post(
            "/api/v1/rules/RULE-DRAFT-BANK-009/deactivate?reason=Repeated+admin+deactivation",
            headers=adm_headers
        )
        assert res_repeat.status_code == 200
        repeat_data = res_repeat.json()
        assert repeat_data["is_active"] is False

        # Verify repeat records append-only audit event without crashing or corrupting state
        sess = SessionMaker()
        repeat_audit_count = sess.query(AuditEvent).count()
        assert repeat_audit_count == initial_audit_count + 1
        sess.close()

    finally:
        app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # 8. Check Downgrade Implementation and History Preservation
    # -------------------------------------------------------------------------
    # Revert migration 5a7c92b84102 to down_revision 3f8a1279b401
    command.downgrade(alembic_cfg, "3f8a1279b401")

    session = SessionMaker()
    try:
        downgraded_rule = session.query(RegulatoryRule).filter_by(rule_code="RULE-DRAFT-BANK-009").first()
        assert downgraded_rule is not None
        assert downgraded_rule.is_active is True
        assert downgraded_rule.status == "APPROVED_FOR_PROTOTYPE_USE"

        downgraded_ver = session.query(RegulatoryRuleVersion).filter_by(rule_id=downgraded_rule.id).first()
        assert downgraded_ver is not None
        assert downgraded_ver.is_active is True

        # CRITICAL GOVERNANCE AUDIT CHECK:
        # Verify that downgrade did NOT delete prior audit event records (append-only audit history)
        prior_audits = session.query(AuditEvent).filter_by(action="REGULATORY_RULE_DEACTIVATED").all()
        assert len(prior_audits) >= 2, "Audit events must remain intact after schema downgrade"

    finally:
        session.close()
