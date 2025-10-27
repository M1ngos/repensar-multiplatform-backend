"""Create sync tables for offline-first support

Revision ID: 004
Revises: 003
Create Date: 2025-10-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'  # Depends on sync indexes
branch_labels = None
depends_on = None


def upgrade():
    """
    Create sync tables:
    - devices: Track registered client devices
    - device_sync_states: Track per-device, per-entity sync state
    - sync_conflicts: Log sync conflicts for debugging
    """

    # Create devices table
    op.create_table(
        'devices',
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_name', sa.String(length=200), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('app_version', sa.String(length=50), nullable=True),
        sa.Column('push_token', sa.String(length=500), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('device_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_devices_user_id', 'devices', ['user_id'])
    op.create_index('ix_devices_is_active', 'devices', ['is_active'])
    op.create_index('ix_devices_last_sync_at', 'devices', ['last_sync_at'])

    # Create device_sync_states table
    op.create_table(
        'device_sync_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced_version', sa.Integer(), nullable=True),
        sa.Column('sync_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.device_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_id', 'entity_type', name='uq_device_entity_type')
    )
    op.create_index('ix_device_sync_states_device_id', 'device_sync_states', ['device_id'])
    op.create_index('ix_device_sync_states_entity_type', 'device_sync_states', ['entity_type'])
    op.create_index('ix_device_sync_states_last_synced_at', 'device_sync_states', ['last_synced_at'])

    # Create sync_conflicts table
    op.create_table(
        'sync_conflicts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('client_version', sa.Integer(), nullable=True),
        sa.Column('server_version', sa.Integer(), nullable=True),
        sa.Column('client_timestamp', sa.DateTime(), nullable=True),
        sa.Column('server_timestamp', sa.DateTime(), nullable=True),
        sa.Column('client_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('server_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('resolution', sa.String(length=50), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('conflict_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_sync_conflicts_device_id', 'sync_conflicts', ['device_id'])
    op.create_index('ix_sync_conflicts_user_id', 'sync_conflicts', ['user_id'])
    op.create_index('ix_sync_conflicts_entity_type', 'sync_conflicts', ['entity_type'])
    op.create_index('ix_sync_conflicts_resolved_at', 'sync_conflicts', ['resolved_at'])
    op.create_index('ix_sync_conflicts_created_at', 'sync_conflicts', ['created_at'])


def downgrade():
    """Remove sync tables"""
    op.drop_index('ix_sync_conflicts_created_at', table_name='sync_conflicts')
    op.drop_index('ix_sync_conflicts_resolved_at', table_name='sync_conflicts')
    op.drop_index('ix_sync_conflicts_entity_type', table_name='sync_conflicts')
    op.drop_index('ix_sync_conflicts_user_id', table_name='sync_conflicts')
    op.drop_index('ix_sync_conflicts_device_id', table_name='sync_conflicts')
    op.drop_table('sync_conflicts')

    op.drop_index('ix_device_sync_states_last_synced_at', table_name='device_sync_states')
    op.drop_index('ix_device_sync_states_entity_type', table_name='device_sync_states')
    op.drop_index('ix_device_sync_states_device_id', table_name='device_sync_states')
    op.drop_table('device_sync_states')

    op.drop_index('ix_devices_last_sync_at', table_name='devices')
    op.drop_index('ix_devices_is_active', table_name='devices')
    op.drop_index('ix_devices_user_id', table_name='devices')
    op.drop_table('devices')
