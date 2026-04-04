"""Add communication tables (messaging, announcements, email digest)

Revision ID: 016
Revises: 015_add_user_preferences
Create Date: 2026-04-02

Note: Tables already exist in DB (created manually). This migration
stamps them as applied and ensures they exist with correct schema.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision: str = "016_add_communication"
down_revision: Union[str, None] = "015_add_user_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ensure communication tables exist."""

    # Create conversations table if not exists
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversations_type", "conversations", ["type"], if_not_exists=True
    )
    op.create_index(
        "ix_conversations_is_active", "conversations", ["is_active"], if_not_exists=True
    )
    op.create_index(
        "ix_conversations_last_message_at",
        "conversations",
        ["last_message_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversations_created_at",
        "conversations",
        ["created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversations_project_id",
        "conversations",
        ["project_id"],
        if_not_exists=True,
    )

    # Create conversation_participants table
    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_read_at", sa.DateTime(), nullable=True),
        sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "notifications_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversation_participants_conversation_id",
        "conversation_participants",
        ["conversation_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversation_participants_user_id",
        "conversation_participants",
        ["user_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_conversation_participants_is_active",
        "conversation_participants",
        ["is_active"],
        if_not_exists=True,
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "message_type",
            sa.String(length=20),
            nullable=False,
            server_default="direct",
        ),
        sa.Column("reply_to_id", sa.Integer(), nullable=True),
        sa.Column("attachments", JSON, nullable=True),
        sa.Column("is_edited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("edited_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reply_to_id"], ["messages.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_messages_conversation_id",
        "messages",
        ["conversation_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_messages_sender_id", "messages", ["sender_id"], if_not_exists=True
    )
    op.create_index(
        "ix_messages_created_at", "messages", ["created_at"], if_not_exists=True
    )

    # Create message_read_receipts table
    op.create_table(
        "message_read_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_message_read_receipts_message_id",
        "message_read_receipts",
        ["message_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_message_read_receipts_user_id",
        "message_read_receipts",
        ["user_id"],
        if_not_exists=True,
    )

    # Create announcements table
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("target_user_types", JSON, nullable=True),
        sa.Column("target_project_ids", JSON, nullable=True),
        sa.Column("target_user_ids", JSON, nullable=True),
        sa.Column("publish_at", sa.DateTime(), nullable=False),
        sa.Column("expire_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attachments", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_announcements_title", "announcements", ["title"], if_not_exists=True
    )
    op.create_index(
        "ix_announcements_publish_at",
        "announcements",
        ["publish_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_announcements_expire_at", "announcements", ["expire_at"], if_not_exists=True
    )
    op.create_index(
        "ix_announcements_is_published",
        "announcements",
        ["is_published"],
        if_not_exists=True,
    )

    # Create announcement_reads table
    op.create_table(
        "announcement_reads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("announcement_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["announcement_id"], ["announcements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        if_not_exists=True,
    )
    op.create_index(
        "ix_announcement_reads_announcement_id",
        "announcement_reads",
        ["announcement_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_announcement_reads_user_id",
        "announcement_reads",
        ["user_id"],
        if_not_exists=True,
    )

    # Create email_digest_preferences table
    op.create_table(
        "email_digest_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "frequency", sa.String(length=20), nullable=False, server_default="daily"
        ),
        sa.Column("preferred_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column(
            "include_messages", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_announcements", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_task_updates", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "include_project_updates",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("last_digest_sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_email_digest_preferences_user_id",
        "email_digest_preferences",
        ["user_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    """Drop communication tables."""
    op.drop_index(
        "ix_email_digest_preferences_user_id",
        table_name="email_digest_preferences",
        if_exists=True,
    )
    op.drop_table("email_digest_preferences", if_exists=True)

    op.drop_index(
        "ix_announcement_reads_user_id", table_name="announcement_reads", if_exists=True
    )
    op.drop_index(
        "ix_announcement_reads_announcement_id",
        table_name="announcement_reads",
        if_exists=True,
    )
    op.drop_table("announcement_reads", if_exists=True)

    op.drop_index(
        "ix_announcements_is_published", table_name="announcements", if_exists=True
    )
    op.drop_index(
        "ix_announcements_expire_at", table_name="announcements", if_exists=True
    )
    op.drop_index(
        "ix_announcements_publish_at", table_name="announcements", if_exists=True
    )
    op.drop_index("ix_announcements_title", table_name="announcements", if_exists=True)
    op.drop_table("announcements", if_exists=True)

    op.drop_index(
        "ix_message_read_receipts_user_id",
        table_name="message_read_receipts",
        if_exists=True,
    )
    op.drop_index(
        "ix_message_read_receipts_message_id",
        table_name="message_read_receipts",
        if_exists=True,
    )
    op.drop_table("message_read_receipts", if_exists=True)

    op.drop_index("ix_messages_created_at", table_name="messages", if_exists=True)
    op.drop_index("ix_messages_sender_id", table_name="messages", if_exists=True)
    op.drop_index("ix_messages_conversation_id", table_name="messages", if_exists=True)
    op.drop_table("messages", if_exists=True)

    op.drop_index(
        "ix_conversation_participants_is_active",
        table_name="conversation_participants",
        if_exists=True,
    )
    op.drop_index(
        "ix_conversation_participants_user_id",
        table_name="conversation_participants",
        if_exists=True,
    )
    op.drop_index(
        "ix_conversation_participants_conversation_id",
        table_name="conversation_participants",
        if_exists=True,
    )
    op.drop_table("conversation_participants", if_exists=True)

    op.drop_index(
        "ix_conversations_project_id", table_name="conversations", if_exists=True
    )
    op.drop_index(
        "ix_conversations_created_at", table_name="conversations", if_exists=True
    )
    op.drop_index(
        "ix_conversations_last_message_at", table_name="conversations", if_exists=True
    )
    op.drop_index(
        "ix_conversations_is_active", table_name="conversations", if_exists=True
    )
    op.drop_index("ix_conversations_type", table_name="conversations", if_exists=True)
    op.drop_table("conversations", if_exists=True)
