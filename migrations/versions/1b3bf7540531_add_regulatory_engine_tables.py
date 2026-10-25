"""add_regulatory_engine_tables

Revision ID: 1b3bf7540531
Revises: 49c653bc3216
Create Date: 2026-10-24 15:19:52.022163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b3bf7540531'
down_revision: Union[str, Sequence[str], None] = '49c653bc3216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'regulatory_rules' not in existing_tables:
        op.create_table(
            'regulatory_rules',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('rule_code', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),
            sa.Column('official_source', sa.String(length=512), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='APPROVED_FOR_PROTOTYPE_USE'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_regulatory_rules_rule_code', 'regulatory_rules', ['rule_code'], unique=True)
        op.create_index('ix_regulatory_rules_category', 'regulatory_rules', ['category'])

    if 'regulatory_rule_versions' not in existing_tables:
        op.create_table(
            'regulatory_rule_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('rule_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('parameters_json', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=False, server_default='DEFICIENCY'),
            sa.Column('recommended_action', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('approved_by_user_id', sa.String(length=36), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['rule_id'], ['regulatory_rules.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_regulatory_rule_versions_rule_id', 'regulatory_rule_versions', ['rule_id'])

    if 'validation_runs' not in existing_tables:
        op.create_table(
            'validation_runs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('application_id', sa.String(length=36), nullable=False),
            sa.Column('run_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('triggered_by_user_id', sa.String(length=36), nullable=False),
            sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default='INITIAL_PRE_SCRUTINY'),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
            sa.Column('total_checks', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('deficiencies_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('warnings_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('passed_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('unable_to_evaluate_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('summary_json', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_validation_runs_application_id', 'validation_runs', ['application_id'])
        op.create_index('ix_validation_runs_status', 'validation_runs', ['status'])

    if 'findings' not in existing_tables:
        op.create_table(
            'findings',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('validation_run_id', sa.String(length=36), nullable=False),
            sa.Column('application_id', sa.String(length=36), nullable=False),
            sa.Column('rule_version_id', sa.String(length=36), nullable=False),
            sa.Column('rule_code', sa.String(length=50), nullable=False),
            sa.Column('rule_title', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=False, server_default='DEFICIENCY'),
            sa.Column('outcome', sa.String(length=50), nullable=False, server_default='DEFICIENCY_DETECTED'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('explanation', sa.Text(), nullable=False),
            sa.Column('expected_value', sa.Text(), nullable=True),
            sa.Column('observed_value', sa.Text(), nullable=True),
            sa.Column('document_id', sa.String(length=36), nullable=True),
            sa.Column('document_version_id', sa.String(length=36), nullable=True),
            sa.Column('evidence_page_number', sa.Integer(), nullable=True),
            sa.Column('evidence_bounding_box_json', sa.Text(), nullable=True),
            sa.Column('evidence_raw_text', sa.Text(), nullable=True),
            sa.Column('evidence_confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('evidence_secondary_json', sa.Text(), nullable=True),
            sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='VERIFIED_INTERNAL'),
            sa.Column('recommended_action', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['validation_run_id'], ['validation_runs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['rule_version_id'], ['regulatory_rule_versions.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_findings_validation_run_id', 'findings', ['validation_run_id'])
        op.create_index('ix_findings_application_id', 'findings', ['application_id'])
        op.create_index('ix_findings_rule_code', 'findings', ['rule_code'])
        op.create_index('ix_findings_category', 'findings', ['category'])
        op.create_index('ix_findings_severity', 'findings', ['severity'])
        op.create_index('ix_findings_outcome', 'findings', ['outcome'])
        op.create_index('ix_findings_status', 'findings', ['status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('findings')
    op.drop_table('validation_runs')
    op.drop_table('regulatory_rule_versions')
    op.drop_table('regulatory_rules')
