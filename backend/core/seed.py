# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Development & Testing Synthetic Seeder (backend/core/seed.py)

from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.core.security import get_password_hash
from backend.models.institution import Institution
from backend.models.user import User
from backend.models.application import Application


def seed_synthetic_data(db: Session) -> None:
    """Idempotently seeds synthetic institutions, demo accounts, and baseline applications
    strictly for testing and demonstration in development mode.
    """
    if settings.ENVIRONMENT == "production":
        return

    # 1. Seed Synthetic Institutions
    inst1 = db.query(Institution).filter(Institution.aicte_permanent_id == "1-10972412").first()
    if not inst1:
        inst1 = Institution(
            id="inst_01",
            aicte_permanent_id="1-10972412",
            name="Apex Institute of Technology & Management (Synthetic Demo)",
            category="ENGINEERING_TECHNOLOGY",
            state="Karnataka",
            district="Bengaluru Urban",
            is_rural=False
        )
        db.add(inst1)

    inst2 = db.query(Institution).filter(Institution.aicte_permanent_id == "1-20485913").first()
    if not inst2:
        inst2 = Institution(
            id="inst_02",
            aicte_permanent_id="1-20485913",
            name="National Polytechnic & Science Academy (Synthetic Demo)",
            category="POLYTECHNIC_DIPLOMA",
            state="Tamil Nadu",
            district="Coimbatore",
            is_rural=True
        )
        db.add(inst2)

    db.commit()

    # 2. Seed Synthetic Accounts
    users_data = [
        {
            "id": "usr_inst_01",
            "email": "applicant@institution.test",
            "password": "Password123!",
            "full_name": "Dr. R. K. Sharma",
            "role": "INSTITUTION",
            "institution_id": "inst_01",
            "is_active": True
        },
        {
            "id": "usr_inst_02",
            "email": "applicant2@institution2.test",
            "password": "Password123!",
            "full_name": "Dr. M. S. Sundaram",
            "role": "INSTITUTION",
            "institution_id": "inst_02",
            "is_active": True
        },
        {
            "id": "usr_rev_104",
            "email": "reviewer@reviewer.test",
            "password": "ReviewerPass123!",
            "full_name": "Prof. K. S. Krishnan",
            "role": "REVIEWER",
            "institution_id": None,
            "is_active": True
        },
        {
            "id": "usr_adm_001",
            "email": "admin@platform.test",
            "password": "AdminPass123!",
            "full_name": "Platform System Administrator (Synthetic)",
            "role": "ADMIN",
            "institution_id": None,
            "is_active": True
        },
        {
            "id": "usr_inactive",
            "email": "inactive@institution.test",
            "password": "Password123!",
            "full_name": "Inactive Account Demo",
            "role": "INSTITUTION",
            "institution_id": "inst_01",
            "is_active": False
        }
    ]

    for u in users_data:
        existing_user = db.query(User).filter((User.id == u["id"]) | (User.email == u["email"])).first()
        if not existing_user:
            user = User(
                id=u["id"],
                email=u["email"],
                password_hash=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                institution_id=u["institution_id"],
                is_active=u["is_active"]
            )
            db.add(user)
        else:
            existing_user.id = u["id"]
            existing_user.email = u["email"]
            existing_user.password_hash = get_password_hash(u["password"])
            existing_user.full_name = u["full_name"]
            existing_user.role = u["role"]
            existing_user.institution_id = u["institution_id"]
            existing_user.is_active = u["is_active"]

    db.commit()

    # 3. Seed Synthetic Applications (For testing tenant isolation)
    app1 = db.query(Application).filter(Application.application_number == "AICTE-EOA-2026-9812").first()
    if not app1:
        app1 = Application(
            id="app_9812",
            application_number="AICTE-EOA-2026-9812",
            institution_id="inst_01",
            academic_year="2026-2027",
            application_type="EOA",
            status="FINDINGS_AVAILABLE",
            total_intake_applied=720
        )
        db.add(app1)

    app2 = db.query(Application).filter(Application.application_number == "AICTE-EOA-2026-9813").first()
    if not app2:
        app2 = Application(
            id="app_9813",
            application_number="AICTE-EOA-2026-9813",
            institution_id="inst_02",
            academic_year="2026-2027",
            application_type="EOA",
            status="REVALIDATED",
            total_intake_applied=480
        )
        db.add(app2)
    db.commit()

    # 4. Seed Checklist Slots for Demo Applications
    from backend.models.document import Document
    from backend.services.document_service import initialize_application_checklist

    if not db.query(Document).filter(Document.application_id == "app_9812").first():
        initialize_application_checklist(db, "app_9812")
    if not db.query(Document).filter(Document.application_id == "app_9813").first():
        initialize_application_checklist(db, "app_9813")
