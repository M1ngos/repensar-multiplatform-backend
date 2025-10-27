"""Add token_family column to users table

Revision ID: 001
Revises:
Create Date: 2025-01-07 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = '000'  # Depends on initial schema
branch_labels = None
depends_on = None


def upgrade():
    """Add token_family column to users table for JWT token rotation support."""
    op.add_column('users', sa.Column('token_family', sa.String(length=255), nullable=True))


def downgrade():
    """Remove token_family column from users table."""
    op.drop_column('users', 'token_family')
