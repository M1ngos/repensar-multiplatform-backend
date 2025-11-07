"""seed_initial_user_types

Revision ID: cd04f478e6b0
Revises: 006
Create Date: 2025-11-07 13:14:46.347100

Seeds the initial user types required by the system:
- admin: Full system access
- project_manager: Manage projects, tasks, and volunteers
- staff_member: Staff operations and volunteer management
- volunteer: Limited volunteer access
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, Sequence[str], None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial user types with permissions and dashboard configurations."""

    # Create table reference
    user_types_table = sa.table(
        'user_types',
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('permissions', JSONB),
        sa.column('dashboard_config', JSONB)
    )

    # Define user types with their permissions and dashboard configs
    user_types_data = [
        {
            'name': 'admin',
            'description': 'Administrator with full system access',
            'permissions': {
                'users': {'create': True, 'read': True, 'update': True, 'delete': True},
                'projects': {'create': True, 'read': True, 'update': True, 'delete': True},
                'tasks': {'create': True, 'read': True, 'update': True, 'delete': True},
                'volunteers': {'create': True, 'read': True, 'update': True, 'delete': True},
                'resources': {'create': True, 'read': True, 'update': True, 'delete': True},
                'reports': {'create': True, 'read': True, 'update': True, 'delete': True},
                'analytics': {'read': True},
                'system': {'configure': True, 'manage_users': True}
            },
            'dashboard_config': {
                'widgets': ['overview', 'projects', 'tasks', 'volunteers', 'reports', 'analytics'],
                'default_view': 'overview'
            }
        },
        {
            'name': 'project_manager',
            'description': 'Project manager with project and volunteer management capabilities',
            'permissions': {
                'users': {'create': False, 'read': True, 'update': False, 'delete': False},
                'projects': {'create': True, 'read': True, 'update': True, 'delete': False},
                'tasks': {'create': True, 'read': True, 'update': True, 'delete': True},
                'volunteers': {'create': False, 'read': True, 'update': True, 'delete': False},
                'resources': {'create': True, 'read': True, 'update': True, 'delete': False},
                'reports': {'create': True, 'read': True, 'update': False, 'delete': False},
                'analytics': {'read': True},
                'time_logs': {'approve': True}
            },
            'dashboard_config': {
                'widgets': ['my_projects', 'tasks', 'volunteers', 'reports'],
                'default_view': 'my_projects'
            }
        },
        {
            'name': 'staff_member',
            'description': 'Staff member with operational and volunteer management capabilities',
            'permissions': {
                'users': {'create': False, 'read': True, 'update': False, 'delete': False},
                'projects': {'create': False, 'read': True, 'update': False, 'delete': False},
                'tasks': {'create': False, 'read': True, 'update': True, 'delete': False},
                'volunteers': {'create': True, 'read': True, 'update': True, 'delete': False},
                'resources': {'create': False, 'read': True, 'update': True, 'delete': False},
                'reports': {'create': False, 'read': True, 'update': False, 'delete': False},
                'time_logs': {'approve': True}
            },
            'dashboard_config': {
                'widgets': ['tasks', 'volunteers', 'time_logs'],
                'default_view': 'tasks'
            }
        },
        {
            'name': 'volunteer',
            'description': 'Volunteer with limited access to assigned tasks and personal information',
            'permissions': {
                'users': {'create': False, 'read': False, 'update': False, 'delete': False},
                'projects': {'create': False, 'read': True, 'update': False, 'delete': False},
                'tasks': {'create': False, 'read': True, 'update': False, 'delete': False},
                'volunteers': {'create': False, 'read': False, 'update': False, 'delete': False},
                'resources': {'create': False, 'read': False, 'update': False, 'delete': False},
                'reports': {'create': False, 'read': False, 'update': False, 'delete': False},
                'own_profile': {'read': True, 'update': True},
                'own_tasks': {'read': True},
                'time_logs': {'create': True, 'read': True, 'update': True}
            },
            'dashboard_config': {
                'widgets': ['my_tasks', 'my_hours', 'available_tasks'],
                'default_view': 'my_tasks'
            }
        }
    ]

    # Insert user types
    op.bulk_insert(user_types_table, user_types_data)


def downgrade() -> None:
    """Remove seeded user types."""

    # Delete only the user types we created
    op.execute("""
        DELETE FROM user_types
        WHERE name IN ('admin', 'project_manager', 'staff_member', 'volunteer')
    """)
