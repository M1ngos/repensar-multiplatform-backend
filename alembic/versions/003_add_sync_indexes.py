"""Add indexes for sync optimization

Revision ID: 003
Revises: 002
Create Date: 2025-10-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add indexes on updated_at/created_at/assigned_at fields for sync performance.

    These indexes optimize the incremental sync queries which filter
    by timestamp (e.g., WHERE updated_at > '2025-10-27T10:00:00Z').
    """

    # Volunteers and related tables
    op.create_index('ix_volunteers_updated_at', 'volunteers', ['updated_at'], unique=False)
    op.create_index('ix_volunteer_skills_created_at', 'volunteer_skills', ['created_at'], unique=False)

    # Projects and related tables
    op.create_index('ix_projects_updated_at', 'projects', ['updated_at'], unique=False)
    op.create_index('ix_project_teams_assigned_at', 'project_teams', ['assigned_at'], unique=False)
    op.create_index('ix_milestones_updated_at', 'milestones', ['updated_at'], unique=False)
    op.create_index('ix_environmental_metrics_updated_at', 'environmental_metrics', ['updated_at'], unique=False)

    # Tasks
    op.create_index('ix_tasks_updated_at', 'tasks', ['updated_at'], unique=False)

    # Note: Other indexes may be added as needed for entity types that support sync


def downgrade():
    """Remove sync optimization indexes."""

    # Volunteers and related tables
    op.drop_index('ix_volunteers_updated_at', table_name='volunteers')
    op.drop_index('ix_volunteer_skills_created_at', table_name='volunteer_skills')

    # Projects and related tables
    op.drop_index('ix_projects_updated_at', table_name='projects')
    op.drop_index('ix_project_teams_assigned_at', table_name='project_teams')
    op.drop_index('ix_milestones_updated_at', table_name='milestones')
    op.drop_index('ix_environmental_metrics_updated_at', table_name='environmental_metrics')

    # Tasks
    op.drop_index('ix_tasks_updated_at', table_name='tasks')
