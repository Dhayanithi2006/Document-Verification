"""add_extraction_tables

Revision ID: 49c653bc3216
Revises: f0151ad59202
Create Date: 2026-10-24 14:05:24.557458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49c653bc3216'
down_revision: Union[str, Sequence[str], None] = 'f0151ad59202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'document_processing_runs' not in existing_tables:
        op.create_table(
            'document_processing_runs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('document_id', sa.String(length=36), nullable=False),
            sa.Column('document_version_id', sa.String(length=36), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('processor_version', sa.String(length=50), nullable=False, server_default='idp-pipeline-v1.0.0'),
            sa.Column('extraction_method', sa.String(length=50), nullable=False, server_default='HYBRID'),
            sa.Column('pages_processed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('pages_digital', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('pages_ocr', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('average_confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('error_message', sa.String(length=512), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_document_processing_runs_document_id', 'document_processing_runs', ['document_id'])
        op.create_index('ix_document_processing_runs_document_version_id', 'document_processing_runs', ['document_version_id'])
        op.create_index('ix_document_processing_runs_status', 'document_processing_runs', ['status'])

    if 'document_pages' not in existing_tables:
        op.create_table(
            'document_pages',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('document_version_id', sa.String(length=36), nullable=False),
            sa.Column('page_number', sa.Integer(), nullable=False),
            sa.Column('extraction_method', sa.String(length=50), nullable=False),
            sa.Column('text_content', sa.Text(), nullable=False),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('char_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_document_pages_document_version_id', 'document_pages', ['document_version_id'])

    if 'extracted_fields' not in existing_tables:
        op.create_table(
            'extracted_fields',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('processing_run_id', sa.String(length=36), nullable=False),
            sa.Column('document_id', sa.String(length=36), nullable=False),
            sa.Column('document_version_id', sa.String(length=36), nullable=False),
            sa.Column('field_key', sa.String(length=100), nullable=False),
            sa.Column('field_label', sa.String(length=255), nullable=False),
            sa.Column('raw_value', sa.String(length=512), nullable=False),
            sa.Column('normalized_value', sa.String(length=512), nullable=False),
            sa.Column('data_type', sa.String(length=50), nullable=False),
            sa.Column('page_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('box_ymin', sa.Float(), nullable=True),
            sa.Column('box_xmin', sa.Float(), nullable=True),
            sa.Column('box_ymax', sa.Float(), nullable=True),
            sa.Column('box_xmax', sa.Float(), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('extraction_method', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['processing_run_id'], ['document_processing_runs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_extracted_fields_processing_run_id', 'extracted_fields', ['processing_run_id'])
        op.create_index('ix_extracted_fields_document_id', 'extracted_fields', ['document_id'])
        op.create_index('ix_extracted_fields_document_version_id', 'extracted_fields', ['document_version_id'])
        op.create_index('ix_extracted_fields_field_key', 'extracted_fields', ['field_key'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_extracted_fields_field_key', table_name='extracted_fields')
    op.drop_index('ix_extracted_fields_document_version_id', table_name='extracted_fields')
    op.drop_index('ix_extracted_fields_document_id', table_name='extracted_fields')
    op.drop_index('ix_extracted_fields_processing_run_id', table_name='extracted_fields')
    op.drop_table('extracted_fields')

    op.drop_index('ix_document_pages_document_version_id', table_name='document_pages')
    op.drop_table('document_pages')

    op.drop_index('ix_document_processing_runs_status', table_name='document_processing_runs')
    op.drop_index('ix_document_processing_runs_document_version_id', table_name='document_processing_runs')
    op.drop_index('ix_document_processing_runs_document_id', table_name='document_processing_runs')
    op.drop_table('document_processing_runs')
