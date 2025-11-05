"""Create uploaded files table

Revision ID: 006
Revises: 005
Create Date: 2025-11-05 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Create uploaded_files table for file storage."""
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('storage_backend', sa.String(length=20), nullable=False),
        sa.Column('bucket_name', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('volunteer_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
    )

    # Indexes for queries
    op.create_index('ix_uploaded_files_uploaded_by_id', 'uploaded_files', ['uploaded_by_id'])
    op.create_index('ix_uploaded_files_project_id', 'uploaded_files', ['project_id'])
    op.create_index('ix_uploaded_files_task_id', 'uploaded_files', ['task_id'])
    op.create_index('ix_uploaded_files_category', 'uploaded_files', ['category'])
    op.create_index('ix_uploaded_files_created_at', 'uploaded_files', ['created_at'])


def downgrade():
    """Drop uploaded_files table."""
    op.drop_index('ix_uploaded_files_created_at', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_category', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_task_id', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_project_id', table_name='uploaded_files')
    op.drop_index('ix_uploaded_files_uploaded_by_id', table_name='uploaded_files')
    op.drop_table('uploaded_files')
