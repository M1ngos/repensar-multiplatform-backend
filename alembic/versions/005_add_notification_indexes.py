"""Add indexes for notification performance

Revision ID: 005
Revises: 004
Create Date: 2025-11-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add indexes on notifications table for query performance.

    These indexes optimize:
    - User notification queries (by user_id + is_read + created_at)
    - Notification cleanup (by expires_at)
    - Project/task-related notification queries
    """

    # Composite index for user notification queries (most common query pattern)
    # Covers: WHERE user_id = X AND is_read = false ORDER BY created_at DESC
    op.create_index(
        'ix_notifications_user_read_created',
        'notifications',
        ['user_id', 'is_read', 'created_at'],
        unique=False
    )

    # Index for notification cleanup queries
    # Covers: WHERE expires_at <= NOW() AND expires_at IS NOT NULL
    op.create_index(
        'ix_notifications_expires_at',
        'notifications',
        ['expires_at'],
        unique=False
    )

    # Index for project-related notification queries
    op.create_index(
        'ix_notifications_project_id',
        'notifications',
        ['related_project_id'],
        unique=False
    )

    # Index for task-related notification queries
    op.create_index(
        'ix_notifications_task_id',
        'notifications',
        ['related_task_id'],
        unique=False
    )


def downgrade():
    """Remove notification performance indexes."""

    op.drop_index('ix_notifications_user_read_created', table_name='notifications')
    op.drop_index('ix_notifications_expires_at', table_name='notifications')
    op.drop_index('ix_notifications_project_id', table_name='notifications')
    op.drop_index('ix_notifications_task_id', table_name='notifications')
