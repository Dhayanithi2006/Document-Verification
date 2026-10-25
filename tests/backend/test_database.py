# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Database & Model Tests (tests/backend/test_database.py)

import pytest
from sqlalchemy.exc import IntegrityError
from backend.models.institution import Institution
from backend.models.user import User
from backend.models.application import Application
from backend.core.security import get_password_hash


def test_user_institution_relationship(db_session):
    """Verifies relational linkage between User and Institution."""
    inst = db_session.query(Institution).filter(Institution.aicte_permanent_id == "1-10972412").first()
    assert inst is not None
    assert len(inst.users) > 0
    assert inst.users[0].institution_id == inst.id


def test_user_email_uniqueness_constraint(db_session):
    """Verifies that duplicate user emails are strictly blocked by database constraint."""
    dup_user = User(
        email="applicant@institution.test",  # Pre-existing email in seed
        password_hash=get_password_hash("SomePass123!"),
        full_name="Duplicate User",
        role="INSTITUTION",
        institution_id="inst_01"
    )
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_institution_permanent_id_uniqueness(db_session):
    """Verifies that duplicate AICTE permanent IDs are strictly rejected."""
    dup_inst = Institution(
        aicte_permanent_id="1-10972412",  # Pre-existing
        name="Duplicate College",
        category="ENGINEERING_TECHNOLOGY",
        state="Karnataka",
        district="Bengaluru Urban"
    )
    db_session.add(dup_inst)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
