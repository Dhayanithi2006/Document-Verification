"""deactivate_unsupported_draft_bank_rule

Revision ID: 5a7c92b84102
Revises: 3f8a1279b401
Create Date: 2026-10-24 20:55:00.000000

"""
import json
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a7c92b84102'
down_revision: Union[str, Sequence[str], None] = '3f8a1279b401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Safely deactivates unsupported RULE-DRAFT-BANK-009 and logs audit event."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'regulatory_rules' in existing_tables:
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. Deactivate in regulatory_rules
        conn.execute(
            sa.text(
                "UPDATE regulatory_rules "
                "SET status = 'DRAFT_MISSING_OFFICIAL_SOURCE', is_active = 0, updated_at = :now "
                "WHERE rule_code = 'RULE-DRAFT-BANK-009'"
            ),
            {"now": datetime.now(timezone.utc)}
        )

        # 2. Deactivate versions
        conn.execute(
            sa.text(
                "UPDATE regulatory_rule_versions "
                "SET is_active = 0 "
                "WHERE rule_id IN (SELECT id FROM regulatory_rules WHERE rule_code = 'RULE-DRAFT-BANK-009')"
            )
        )

        # 3. Insert audit event if audit_events table exists
        if 'audit_events' in existing_tables:
            result = conn.execute(
                sa.text("SELECT id FROM regulatory_rules WHERE rule_code = 'RULE-DRAFT-BANK-009'")
            ).fetchone()
            
            rule_id = result[0] if result else "unknown"
            event_id = str(uuid.uuid4())
            payload = json.dumps({
                "rule_code": "RULE-DRAFT-BANK-009",
                "action": "DEACTIVATE",
                "reason": "Deactivated in Step 4 regulatory correction: No matching evaluation logic implemented and regional state board official source remains unverified per APH audit."
            })
            
            conn.execute(
                sa.text(
                    "INSERT INTO audit_events (id, action, actor_user_id, actor_role, entity_type, entity_id, payload_json, ip_address, created_at) "
                    "VALUES (:id, 'REGULATORY_RULE_DEACTIVATED', 'system_migration', 'ADMIN', 'REGULATORY_RULE', :entity_id, :payload, '127.0.0.1', :created_at)"
                ),
                {
                    "id": event_id,
                    "entity_id": rule_id,
                    "payload": payload,
                    "created_at": datetime.now(timezone.utc)
                }
            )


def downgrade() -> None:
    """Revert deactivation of RULE-DRAFT-BANK-009."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'regulatory_rules' in existing_tables:
        conn.execute(
            sa.text(
                "UPDATE regulatory_rules "
                "SET status = 'APPROVED_FOR_PROTOTYPE_USE', is_active = 1, updated_at = :now "
                "WHERE rule_code = 'RULE-DRAFT-BANK-009'"
            ),
            {"now": datetime.now(timezone.utc)}
        )
        conn.execute(
            sa.text(
                "UPDATE regulatory_rule_versions "
                "SET is_active = 1 "
                "WHERE rule_id IN (SELECT id FROM regulatory_rules WHERE rule_code = 'RULE-DRAFT-BANK-009')"
            )
        )
