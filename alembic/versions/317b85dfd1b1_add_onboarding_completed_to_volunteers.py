"""add_onboarding_completed_to_volunteers

Revision ID: 317b85dfd1b1
Revises: 012
Create Date: 2026-03-09 16:19:35.451190

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "317b85dfd1b1"
down_revision: Union[str, Sequence[str], None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "volunteers",
        sa.Column(
            "onboarding_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    op.drop_column("volunteers", "onboarding_completed")
