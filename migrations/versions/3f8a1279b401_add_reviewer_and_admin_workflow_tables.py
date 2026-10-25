"""add_reviewer_and_admin_workflow_tables

Revision ID: 3f8a1279b401
Revises: 2c4de5729103
Create Date: 2026-10-24 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f8a1279b401'
down_revision: Union[str, Sequence[str], None] = '2c4de5729103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with reviewer observations table and application assignment columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add reviewer columns to applications table if not present
    app_cols = [c['name'] for c in inspector.get_columns('applications')] if 'applications' in existing_tables else []
    with op.batch_alter_table('applications') as batch_op:
        if 'assigned_reviewer_id' not in app_cols:
            batch_op.add_column(sa.Column('assigned_reviewer_id', sa.String(length=36), nullable=True))
        if 'assigned_at' not in app_cols:
            batch_op.add_column(sa.Column('assigned_at', sa.DateTime(), nullable=True))
        if 'review_status' not in app_cols:
            batch_op.add_column(sa.Column('review_status', sa.String(length=50), nullable=False, server_default='UNASSIGNED'))
        if 'overall_reviewer_remarks' not in app_cols:
            batch_op.add_column(sa.Column('overall_reviewer_remarks', sa.String(length=2048), nullable=True))
        if 'scrutiny_completed_at' not in app_cols:
            batch_op.add_column(sa.Column('scrutiny_completed_at', sa.DateTime(), nullable=True))

    # 2. Create reviewer_observations table if not present
    if 'reviewer_observations' not in existing_tables:
        op.create_table(
            'reviewer_observations',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('application_id', sa.String(length=36), sa.ForeignKey('applications.id', name='fk_rev_obs_application_id', ondelete='CASCADE'), nullable=False),
            sa.Column('finding_id', sa.String(length=36), sa.ForeignKey('findings.id', name='fk_rev_obs_finding_id', ondelete='SET NULL'), nullable=True),
            sa.Column('submission_id', sa.String(length=36), sa.ForeignKey('correction_submissions.id', name='fk_rev_obs_submission_id', ondelete='SET NULL'), nullable=True),
            sa.Column('reviewer_user_id', sa.String(length=36), sa.ForeignKey('users.id', name='fk_rev_obs_reviewer_id', ondelete='RESTRICT'), nullable=False),
            sa.Column('decision', sa.String(length=50), nullable=False),
            sa.Column('justification', sa.Text(), nullable=False),
            sa.Column('is_internal_note', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('idx_reviewer_obs_app_id', 'reviewer_observations', ['application_id'])
        op.create_index('idx_reviewer_obs_finding_id', 'reviewer_observations', ['finding_id'])
        op.create_index('idx_reviewer_obs_reviewer_id', 'reviewer_observations', ['reviewer_user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'reviewer_observations' in existing_tables:
        op.drop_table('reviewer_observations')

    app_cols = [c['name'] for c in inspector.get_columns('applications')] if 'applications' in existing_tables else []
    with op.batch_alter_table('applications') as batch_op:
        for col in ['scrutiny_completed_at', 'overall_reviewer_remarks', 'review_status', 'assigned_at', 'assigned_reviewer_id']:
            if col in app_cols:
                batch_op.drop_column(col)
