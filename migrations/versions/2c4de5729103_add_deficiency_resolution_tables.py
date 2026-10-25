"""add_deficiency_resolution_tables

Revision ID: 2c4de5729103
Revises: 1b3bf7540531
Create Date: 2026-10-24 15:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c4de5729103'
down_revision: Union[str, Sequence[str], None] = '1b3bf7540531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with deficiency resolution tables and finding acknowledgement columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add columns to findings table if not present
    finding_cols = [c['name'] for c in inspector.get_columns('findings')] if 'findings' in existing_tables else []
    with op.batch_alter_table('findings') as batch_op:
        if 'acknowledged_at' not in finding_cols:
            batch_op.add_column(sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        if 'acknowledged_by_user_id' not in finding_cols:
            batch_op.add_column(sa.Column('acknowledged_by_user_id', sa.String(length=36), nullable=True))

    # 2. Create correction_submissions table if not present
    if 'correction_submissions' not in existing_tables:
        op.create_table(
            'correction_submissions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('finding_id', sa.String(length=36), nullable=False),
            sa.Column('application_id', sa.String(length=36), nullable=False),
            sa.Column('cycle_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
            sa.Column('response_text', sa.Text(), nullable=False),
            sa.Column('response_category', sa.String(length=50), nullable=False, server_default='DOCUMENT_REPLACEMENT'),
            sa.Column('document_id', sa.String(length=36), nullable=True),
            sa.Column('document_version_id', sa.String(length=36), nullable=True),
            sa.Column('initial_validation_run_id', sa.String(length=36), nullable=True),
            sa.Column('revalidation_run_id', sa.String(length=36), nullable=True),
            sa.Column('revalidation_status', sa.String(length=50), nullable=True),
            sa.Column('resolution_outcome', sa.String(length=50), nullable=True),
            sa.Column('comparison_notes', sa.Text(), nullable=True),
            sa.Column('reviewer_disposition', sa.String(length=50), nullable=True),
            sa.Column('reviewer_notes', sa.Text(), nullable=True),
            sa.Column('reviewed_by_user_id', sa.String(length=36), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['initial_validation_run_id'], ['validation_runs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['revalidation_run_id'], ['validation_runs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_correction_submissions_application_id'), 'correction_submissions', ['application_id'], unique=False)
        op.create_index(op.f('ix_correction_submissions_finding_id'), 'correction_submissions', ['finding_id'], unique=False)
        op.create_index(op.f('ix_correction_submissions_status'), 'correction_submissions', ['status'], unique=False)
        op.create_index(op.f('ix_correction_submissions_user_id'), 'correction_submissions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'correction_submissions' in existing_tables:
        op.drop_index(op.f('ix_correction_submissions_user_id'), table_name='correction_submissions')
        op.drop_index(op.f('ix_correction_submissions_status'), table_name='correction_submissions')
        op.drop_index(op.f('ix_correction_submissions_finding_id'), table_name='correction_submissions')
        op.drop_index(op.f('ix_correction_submissions_application_id'), table_name='correction_submissions')
        op.drop_table('correction_submissions')

    with op.batch_alter_table('findings') as batch_op:
        batch_op.drop_column('acknowledged_by_user_id')
        batch_op.drop_column('acknowledged_at')
