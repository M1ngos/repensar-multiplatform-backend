"""Create gamification tables

Revision ID: 009
Revises: 008
Create Date: 2025-11-07 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """Create gamification tables for badges, achievements, and points."""

    # Create badges table
    op.create_table(
        'badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False, server_default='special'),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('rarity', sa.String(length=20), nullable=False, server_default='common'),
        sa.Column('points_value', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_badges_name', 'badges', ['name'])
    op.create_index('ix_badges_category', 'badges', ['category'])
    op.create_index('ix_badges_is_active', 'badges', ['is_active'])

    # Create achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('achievement_type', sa.String(length=30), nullable=False, server_default='custom'),
        sa.Column('criteria', JSON, nullable=False),
        sa.Column('points_reward', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('badge_id', sa.Integer(), nullable=True),
        sa.Column('is_repeatable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tracks_progress', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id']),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_achievements_name', 'achievements', ['name'])
    op.create_index('ix_achievements_achievement_type', 'achievements', ['achievement_type'])
    op.create_index('ix_achievements_is_active', 'achievements', ['is_active'])

    # Create volunteer_badges table
    op.create_table(
        'volunteer_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False),
        sa.Column('earned_reason', sa.Text(), nullable=True),
        sa.Column('awarded_by_id', sa.Integer(), nullable=True),
        sa.Column('is_showcased', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id']),
        sa.ForeignKeyConstraint(['awarded_by_id'], ['users.id']),
    )
    op.create_index('ix_volunteer_badges_volunteer_id', 'volunteer_badges', ['volunteer_id'])
    op.create_index('ix_volunteer_badges_badge_id', 'volunteer_badges', ['badge_id'])
    op.create_index('ix_volunteer_badges_earned_at', 'volunteer_badges', ['earned_at'])

    # Create volunteer_achievements table
    op.create_table(
        'volunteer_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('current_progress', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('target_progress', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('times_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_progress_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id']),
    )
    op.create_index('ix_volunteer_achievements_volunteer_id', 'volunteer_achievements', ['volunteer_id'])
    op.create_index('ix_volunteer_achievements_achievement_id', 'volunteer_achievements', ['achievement_id'])
    op.create_index('ix_volunteer_achievements_is_completed', 'volunteer_achievements', ['is_completed'])
    op.create_index('ix_volunteer_achievements_completed_at', 'volunteer_achievements', ['completed_at'])

    # Create volunteer_points table
    op.create_table(
        'volunteer_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('rank_percentile', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('current_streak_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
        sa.UniqueConstraint('volunteer_id'),
    )
    op.create_index('ix_volunteer_points_volunteer_id', 'volunteer_points', ['volunteer_id'])
    op.create_index('ix_volunteer_points_total_points', 'volunteer_points', ['total_points'])
    op.create_index('ix_volunteer_points_rank', 'volunteer_points', ['rank'])

    # Create points_history table
    op.create_table(
        'points_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('volunteer_points_id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('points_change', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('awarded_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_points_id'], ['volunteer_points.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
        sa.ForeignKeyConstraint(['awarded_by_id'], ['users.id']),
    )
    op.create_index('ix_points_history_volunteer_points_id', 'points_history', ['volunteer_points_id'])
    op.create_index('ix_points_history_volunteer_id', 'points_history', ['volunteer_id'])
    op.create_index('ix_points_history_event_type', 'points_history', ['event_type'])
    op.create_index('ix_points_history_created_at', 'points_history', ['created_at'])

    # Create leaderboards table
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('leaderboard_type', sa.String(length=50), nullable=False),
        sa.Column('timeframe', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('rankings', JSON, nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('total_participants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('median_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_leaderboards_leaderboard_type', 'leaderboards', ['leaderboard_type'])
    op.create_index('ix_leaderboards_timeframe', 'leaderboards', ['timeframe'])
    op.create_index('ix_leaderboards_period_start', 'leaderboards', ['period_start'])
    op.create_index('ix_leaderboards_generated_at', 'leaderboards', ['generated_at'])
    op.create_index('ix_leaderboards_is_current', 'leaderboards', ['is_current'])


def downgrade():
    """Drop gamification tables."""
    op.drop_index('ix_leaderboards_is_current', table_name='leaderboards')
    op.drop_index('ix_leaderboards_generated_at', table_name='leaderboards')
    op.drop_index('ix_leaderboards_period_start', table_name='leaderboards')
    op.drop_index('ix_leaderboards_timeframe', table_name='leaderboards')
    op.drop_index('ix_leaderboards_leaderboard_type', table_name='leaderboards')
    op.drop_table('leaderboards')

    op.drop_index('ix_points_history_created_at', table_name='points_history')
    op.drop_index('ix_points_history_event_type', table_name='points_history')
    op.drop_index('ix_points_history_volunteer_id', table_name='points_history')
    op.drop_index('ix_points_history_volunteer_points_id', table_name='points_history')
    op.drop_table('points_history')

    op.drop_index('ix_volunteer_points_rank', table_name='volunteer_points')
    op.drop_index('ix_volunteer_points_total_points', table_name='volunteer_points')
    op.drop_index('ix_volunteer_points_volunteer_id', table_name='volunteer_points')
    op.drop_table('volunteer_points')

    op.drop_index('ix_volunteer_achievements_completed_at', table_name='volunteer_achievements')
    op.drop_index('ix_volunteer_achievements_is_completed', table_name='volunteer_achievements')
    op.drop_index('ix_volunteer_achievements_achievement_id', table_name='volunteer_achievements')
    op.drop_index('ix_volunteer_achievements_volunteer_id', table_name='volunteer_achievements')
    op.drop_table('volunteer_achievements')

    op.drop_index('ix_volunteer_badges_earned_at', table_name='volunteer_badges')
    op.drop_index('ix_volunteer_badges_badge_id', table_name='volunteer_badges')
    op.drop_index('ix_volunteer_badges_volunteer_id', table_name='volunteer_badges')
    op.drop_table('volunteer_badges')

    op.drop_index('ix_achievements_is_active', table_name='achievements')
    op.drop_index('ix_achievements_achievement_type', table_name='achievements')
    op.drop_index('ix_achievements_name', table_name='achievements')
    op.drop_table('achievements')

    op.drop_index('ix_badges_is_active', table_name='badges')
    op.drop_index('ix_badges_category', table_name='badges')
    op.drop_index('ix_badges_name', table_name='badges')
    op.drop_table('badges')
