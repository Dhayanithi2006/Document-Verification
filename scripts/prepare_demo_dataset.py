# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Curated Demo Dataset Generator (scripts/prepare_demo_dataset.py)

import os
import sys
import shutil
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base, utc_now
from backend.core.security import get_password_hash
from backend.models.institution import Institution
from backend.models.user import User
from backend.models.application import Application
from backend.models.document import Document, DocumentVersion
from backend.models.regulatory import RegulatoryRule, RegulatoryRuleVersion, ValidationRun, Finding
from backend.models.deficiency import CorrectionSubmission
from backend.models.reviewer import ReviewerObservation
from backend.models.audit import AuditEvent
from backend.services.document_service import initialize_application_checklist
from backend.services.regulatory_engine import seed_regulatory_rules

DEMO_DB_FILE = "data/demo.db"
DEMO_STORAGE_DIR = "storage/demo_documents"

def generate_valid_pdf_content(title: str, body: str) -> bytes:
    """Generates a minimal valid PDF-1.4 file with standard trailer and catalog."""
    stream_content = f"BT /F1 12 Tf 72 712 Td ({title}) Tj 0 -20 Td ({body}) Tj ET".encode('latin1')
    stream_len = len(stream_content)
    pdf = (
        b"%PDF-1.4\n"
        b"%\xe2\xe3\xcf\xd3\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(stream_len).encode('ascii') + b" >>\nstream\n"
        + stream_content + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000015 00000 n \n0000000068 00000 n \n0000000125 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n500\n%%EOF\n"
    )
    return pdf

def prepare_demo_environment():
    print(f"==================================================")
    print(f"PREPARING CURATED DEMO ENVIRONMENT: {DEMO_DB_FILE}")
    print(f"==================================================")

    # 1. Clean existing demo database and storage if present (Never touches data/aicte.db)
    if os.path.exists(DEMO_DB_FILE):
        os.remove(DEMO_DB_FILE)
        print(f"Removed previous {DEMO_DB_FILE}")
    for ext in ["-wal", "-shm"]:
        if os.path.exists(DEMO_DB_FILE + ext):
            os.remove(DEMO_DB_FILE + ext)

    if os.path.exists(DEMO_STORAGE_DIR):
        shutil.rmtree(DEMO_STORAGE_DIR)
        print(f"Cleaned previous {DEMO_STORAGE_DIR}")
    os.makedirs(DEMO_STORAGE_DIR, exist_ok=True)

    # 2. Initialize Database Engine and Tables
    engine = create_engine(f"sqlite:///./{DEMO_DB_FILE}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 3. Seed Institutions
        inst1 = Institution(
            id="inst_01",
            aicte_permanent_id="1-10972412",
            name="Apex Institute of Technology & Management (Synthetic Demo)",
            category="ENGINEERING_TECHNOLOGY",
            state="Karnataka",
            district="Bengaluru Urban",
            is_rural=False
        )
        inst2 = Institution(
            id="inst_02",
            aicte_permanent_id="1-20485913",
            name="National Polytechnic & Science Academy (Synthetic Demo)",
            category="POLYTECHNIC_DIPLOMA",
            state="Tamil Nadu",
            district="Coimbatore",
            is_rural=True
        )
        db.add_all([inst1, inst2])
        db.commit()
        print("-> Seeded Institutions: inst_01, inst_02")

        # 4. Seed Presentation Users
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
        db.commit()
        print("-> Seeded Users: applicant, reviewer, admin, applicant2, inactive")

        # 5. Seed Regulatory Rules
        seed_regulatory_rules(db)
        print("-> Seeded 10 Regulatory Rules (8 active, 2 draft)")

        # 6. Seed Presentation Applications
        now = utc_now()
        app1 = Application(
            id="app_9812",
            application_number="AICTE-EOA-2026-9812",
            institution_id="inst_01",
            academic_year="2026-2027",
            application_type="EOA",
            status="DEFICIENCIES_DETECTED",
            total_intake_applied=720,
            assigned_reviewer_id="usr_rev_104",
            assigned_at=now,
            review_status="UNDER_SCRUTINY",
            created_at=now,
            updated_at=now
        )
        app2 = Application(
            id="app_9813",
            application_number="AICTE-EOA-2026-9813",
            institution_id="inst_02",
            academic_year="2026-2027",
            application_type="EOA",
            status="DRAFT",
            total_intake_applied=480,
            created_at=now,
            updated_at=now
        )
        db.add_all([app1, app2])
        db.commit()
        print("-> Seeded Applications: app_9812 (inst_01), app_9813 (inst_02)")

        # 7. Initialize Document Checklists
        initialize_application_checklist(db, "app_9812")
        initialize_application_checklist(db, "app_9813")
        print("-> Initialized Checklist Slots")

        # 8. Seed Synthetic Documents for app_9812
        app_storage = os.path.join(DEMO_STORAGE_DIR, "inst_01", "app_9812")
        os.makedirs(app_storage, exist_ok=True)

        doc_seeds = [
            ("LAND_TITLE_DEED", "Registered Land Title Deed (Sy No 142/1, 142/2)", "LAND_TITLE_DEED_v1.pdf", "Registered Sale Deed dated 12-05-2004. Total land 5.25 Acres."),
            ("BUILDING_COMPLETION", "Provisional Building Completion Certificate", "BUILDING_COMPLETION_v1.pdf", "Provisional Building Completion Certificate issued by BBMP. Phase-1 Complete."),
            ("LAND_USE_CERTIFICATE", "Competent Authority Land Use Certificate", "LAND_USE_CERTIFICATE_v1.pdf", "Land Conversion Order No. LCO-2005-992 Educational Use Permitted.")
        ]

        doc_version_map = {}
        for doc_type, title, filename, body in doc_seeds:
            pdf_bytes = generate_valid_pdf_content(title, body)
            sha256 = hashlib.sha256(pdf_bytes).hexdigest()
            file_path = os.path.join(app_storage, filename)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            doc = db.query(Document).filter(Document.application_id == "app_9812", Document.document_type == doc_type).first()
            if doc:
                doc.status = "UPLOADED"
                doc.title = title
                ver = DocumentVersion(
                    document_id=doc.id,
                    version_number=1,
                    file_name=filename,
                    file_path=file_path,
                    file_size_bytes=len(pdf_bytes),
                    file_hash_sha256=sha256,
                    mime_type="application/pdf",
                    page_count=1,
                    is_scanned=False,
                    upload_timestamp=now
                )
                db.add(ver)
                db.flush()
                doc_version_map[doc_type] = (doc, ver)

        db.commit()
        print(f"-> Seeded synthetic documents in {app_storage}")

        # 9. Seed Initial Validation Run and Representative Findings
        vrun = ValidationRun(
            application_id="app_9812",
            run_number=1,
            triggered_by_user_id="usr_inst_01",
            trigger_type="INITIAL_PRE_SCRUTINY",
            status="COMPLETED",
            total_checks=8,
            passed_count=5,
            deficiencies_count=2,
            warnings_count=1,
            unable_to_evaluate_count=0,
            summary_json=json.dumps({"passed": 5, "deficiencies": 2, "warnings": 1}),
            started_at=now,
            completed_at=now
        )
        db.add(vrun)
        db.flush()

        # Rule versions
        r_bcc = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == "RULE-EOA-BCC-002").first()
        rv_bcc = db.query(RegulatoryRuleVersion).filter(RegulatoryRuleVersion.rule_id == r_bcc.id).first()

        r_fire = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == "RULE-EOA-FIRE-003").first()
        rv_fire = db.query(RegulatoryRuleVersion).filter(RegulatoryRuleVersion.rule_id == r_fire.id).first()

        r_cross = db.query(RegulatoryRule).filter(RegulatoryRule.rule_code == "RULE-EOA-CROSS-006").first()
        rv_cross = db.query(RegulatoryRuleVersion).filter(RegulatoryRuleVersion.rule_id == r_cross.id).first()

        doc_bcc, ver_bcc = doc_version_map["BUILDING_COMPLETION"]
        doc_land, ver_land = doc_version_map["LAND_TITLE_DEED"]
        doc_fire = db.query(Document).filter(Document.application_id == "app_9812", Document.document_type == "FIRE_SAFETY_NOC").first()

        f1 = Finding(
            id="find_bcc_002",
            validation_run_id=vrun.id,
            application_id="app_9812",
            rule_version_id=rv_bcc.id,
            rule_code="RULE-EOA-BCC-002",
            rule_title=r_bcc.title,
            category=r_bcc.category,
            severity="DEFICIENCY",
            outcome="FAILED",
            status="OPEN",
            title="Provisional Completion Certificate Requires Municipal OC",
            explanation="Uploaded certificate indicates provisional status. AICTE APH Chapter II Clause 2.3.2 allows provisional certificates for max 2 academic years; permanent Occupancy Certificate is required.",
            expected_value="Permanent Occupancy Certificate (Full Completion)",
            observed_value="Provisional Completion (Phase-1)",
            document_id=doc_bcc.id,
            document_version_id=ver_bcc.id,
            evidence_page_number=1,
            evidence_confidence=0.95,
            verification_status="AUTOMATED_CHECK",
            recommended_action=rv_bcc.recommended_action,
            created_at=now
        )

        f2 = Finding(
            id="find_fire_003",
            validation_run_id=vrun.id,
            application_id="app_9812",
            rule_version_id=rv_fire.id,
            rule_code="RULE-EOA-FIRE-003",
            rule_title=r_fire.title,
            category=r_fire.category,
            severity="DEFICIENCY",
            outcome="FAILED",
            status="OPEN",
            title="Mandatory Fire Safety Certificate (NOC) Missing",
            explanation="Fire Safety Certificate has not been uploaded. AICTE APH Appendix 4 mandates a valid NOC from the State Fire Services Department.",
            expected_value="Valid Fire Safety NOC Uploaded",
            observed_value="Slot Pending / Unuploaded",
            document_id=doc_fire.id if doc_fire else None,
            evidence_confidence=1.0,
            verification_status="AUTOMATED_CHECK",
            recommended_action=rv_fire.recommended_action,
            created_at=now
        )

        f3 = Finding(
            id="find_cross_006",
            validation_run_id=vrun.id,
            application_id="app_9812",
            rule_version_id=rv_cross.id,
            rule_code="RULE-EOA-CROSS-006",
            rule_title=r_cross.title,
            category=r_cross.category,
            severity="WARNING",
            outcome="FAILED",
            status="OPEN",
            title="Khasra / Survey Number Cross-Document Reconciliation Advisory",
            explanation="Survey number Sy No 142/1 is referenced in Land Deed, but municipal records cite Khata No 89. Please ensure Khata extract is included.",
            expected_value="Consistent Survey / Khata Numbers",
            observed_value="Sy No 142/1 vs Khata 89",
            document_id=doc_land.id,
            document_version_id=ver_land.id,
            evidence_page_number=1,
            evidence_confidence=0.88,
            verification_status="AUTOMATED_CHECK",
            recommended_action="Ensure Khata extract references primary survey number.",
            created_at=now
        )

        db.add_all([f1, f2, f3])
        db.commit()
        print("-> Seeded Validation Run & 3 Representative Findings (2 blocking deficiencies, 1 warning)")

        # 10. Seed Actionable Correction Draft
        f1.acknowledged_at = now
        f1.acknowledged_by_user_id = "usr_inst_01"

        corr_draft = CorrectionSubmission(
            id="corr_bcc_draft",
            finding_id=f1.id,
            application_id="app_9812",
            cycle_number=1,
            user_id="usr_inst_01",
            status="DRAFT",
            response_text="The municipal planning authority has issued final Occupancy Certificate No. BBMP/OC/2026/8912. The scanned copy is uploaded as replacement evidence.",
            response_category="NEW_DOCUMENT_EVIDENCE",
            document_id=doc_bcc.id,
            document_version_id=ver_bcc.id,
            initial_validation_run_id=vrun.id,
            created_at=now,
            updated_at=now
        )
        db.add(corr_draft)
        db.commit()
        print("-> Seeded Actionable Correction Draft for Finding f1")

        # 11. Seed Baseline Audit Events
        audit_records = [
            ("usr_inst_01", "INSTITUTION", "APPLICATION_CREATED", "APPLICATION", "app_9812", {"application_number": "AICTE-EOA-2026-9812", "intake": 720}),
            ("usr_inst_01", "INSTITUTION", "DOCUMENT_UPLOADED", "DOCUMENT", doc_bcc.id, {"type": "BUILDING_COMPLETION", "file": "BUILDING_COMPLETION_v1.pdf"}),
            ("usr_inst_01", "INSTITUTION", "VALIDATION_RUN_COMPLETED", "APPLICATION", "app_9812", {"run_number": 1, "deficiencies": 2, "warnings": 1}),
            ("usr_adm_001", "ADMIN", "APPLICATION_REVIEWER_ASSIGNED", "APPLICATION", "app_9812", {"reviewer_id": "usr_rev_104"}),
            ("usr_inst_01", "INSTITUTION", "FINDING_ACKNOWLEDGED", "finding", f1.id, {"finding_id": f1.id, "rule_code": "RULE-EOA-BCC-002"}),
            ("usr_inst_01", "INSTITUTION", "CORRECTION_DRAFT_SAVED", "correction_submission", corr_draft.id, {"finding_id": f1.id})
        ]

        for actor, role, action, etype, eid, payload in audit_records:
            ev = AuditEvent(
                actor_user_id=actor,
                actor_role=role,
                action=action,
                entity_type=etype,
                entity_id=eid,
                payload_json=json.dumps(payload),
                ip_address="127.0.0.1",
                created_at=now
            )
            db.add(ev)
        db.commit()
        print(f"-> Seeded {len(audit_records)} Representative Audit Events")

        # 12. Final Stats
        users_count = db.query(User).count()
        apps_count = db.query(Application).count()
        docs_count = db.query(Document).count()
        findings_count = db.query(Finding).count()
        audits_count = db.query(AuditEvent).count()
        print(f"\n==================================================")
        print(f"DEMO ENVIRONMENT PREPARATION COMPLETE:")
        print(f"  Database: {DEMO_DB_FILE} ({os.path.getsize(DEMO_DB_FILE)} bytes)")
        print(f"  Storage: {DEMO_STORAGE_DIR}")
        print(f"  Users: {users_count}")
        print(f"  Applications: {apps_count}")
        print(f"  Documents: {docs_count}")
        print(f"  Findings: {findings_count}")
        print(f"  Audit Events: {audits_count}")
        print(f"==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    prepare_demo_environment()
