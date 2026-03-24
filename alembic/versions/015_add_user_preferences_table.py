"""Add user preferences table

Revision ID: 015_add_user_preferences
Revises: 317b85dfd1b1
Create Date: 2026-03-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "015_add_user_preferences"
down_revision: Union[str, None] = "317b85dfd1b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "email_task_assigned", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "email_task_completed", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "email_project_updates", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "email_weekly_digest", sa.Boolean(), nullable=True, server_default="false"
        ),
        sa.Column("in_app_all", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "in_app_task_updates", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "in_app_project_updates", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "in_app_gamification", sa.Boolean(), nullable=True, server_default="true"
        ),
        sa.Column(
            "theme", sa.String(length=20), nullable=True, server_default="system"
        ),
        sa.Column("compact_mode", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("show_tutorials", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("language", sa.String(length=10), nullable=True, server_default="en"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
