"""Add OAuth fields to users table

Revision ID: 002
Revises: 001
Create Date: 2025-10-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add OAuth fields to users table for Google Sign In support."""
    # Make password_hash nullable (for OAuth users)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=True)

    # Add OAuth provider fields
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(length=500), nullable=True))

    # Create index for OAuth provider lookups
    op.create_index('ix_users_oauth_provider_id', 'users', ['oauth_provider', 'oauth_provider_id'])


def downgrade():
    """Remove OAuth fields from users table."""
    # Drop index
    op.drop_index('ix_users_oauth_provider_id', table_name='users')

    # Remove OAuth columns
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'oauth_provider')

    # Make password_hash not nullable again
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=False)
