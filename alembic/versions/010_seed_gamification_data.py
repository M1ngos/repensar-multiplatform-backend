"""Seed initial gamification data

Revision ID: 010
Revises: 009
Create Date: 2025-11-07 16:00:00.000000

Seeds initial badges and achievements to bootstrap the gamification system.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, Sequence[str], None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial badges and achievements."""

    # Create table references
    badges_table = sa.table(
        'badges',
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('category', sa.String),
        sa.column('icon_url', sa.String),
        sa.column('color', sa.String),
        sa.column('rarity', sa.String),
        sa.column('points_value', sa.Integer),
        sa.column('is_active', sa.Boolean),
        sa.column('is_secret', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )

    achievements_table = sa.table(
        'achievements',
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('achievement_type', sa.String),
        sa.column('criteria', JSON),
        sa.column('points_reward', sa.Integer),
        sa.column('badge_id', sa.Integer),
        sa.column('is_repeatable', sa.Boolean),
        sa.column('tracks_progress', sa.Boolean),
        sa.column('is_active', sa.Boolean),
        sa.column('is_secret', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )

    now = datetime.utcnow()

    # Seed Badges
    badges_data = [
        # Time-based badges
        {
            'name': 'First Step',
            'description': 'Completed your first hour of volunteer work',
            'category': 'time',
            'color': '#4CAF50',
            'rarity': 'common',
            'points_value': 10,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Dedicated Volunteer',
            'description': 'Contributed 50 hours of volunteer work',
            'category': 'time',
            'color': '#2196F3',
            'rarity': 'rare',
            'points_value': 50,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Century Club',
            'description': 'Reached 100 hours of volunteer service',
            'category': 'time',
            'color': '#9C27B0',
            'rarity': 'epic',
            'points_value': 100,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Hero of the Community',
            'description': 'Contributed over 500 hours of volunteer work',
            'category': 'time',
            'color': '#FF9800',
            'rarity': 'legendary',
            'points_value': 500,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Project-based badges
        {
            'name': 'Project Pioneer',
            'description': 'Completed your first project',
            'category': 'projects',
            'color': '#4CAF50',
            'rarity': 'common',
            'points_value': 25,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Multi-Tasker',
            'description': 'Participated in 5 different projects',
            'category': 'projects',
            'color': '#2196F3',
            'rarity': 'rare',
            'points_value': 75,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Skill-based badges
        {
            'name': 'Quick Learner',
            'description': 'Acquired your first certified skill',
            'category': 'skills',
            'color': '#4CAF50',
            'rarity': 'common',
            'points_value': 20,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Jack of All Trades',
            'description': 'Certified in 5 different skills',
            'category': 'skills',
            'color': '#9C27B0',
            'rarity': 'epic',
            'points_value': 100,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Training badges
        {
            'name': 'Trained and Ready',
            'description': 'Completed your first training',
            'category': 'training',
            'color': '#4CAF50',
            'rarity': 'common',
            'points_value': 15,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Lifelong Learner',
            'description': 'Completed 10 trainings',
            'category': 'training',
            'color': '#2196F3',
            'rarity': 'rare',
            'points_value': 80,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Leadership badges
        {
            'name': 'Mentor',
            'description': 'Helped onboard a new volunteer',
            'category': 'leadership',
            'color': '#FF9800',
            'rarity': 'rare',
            'points_value': 50,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Special/streak badges
        {
            'name': 'Consistent Contributor',
            'description': 'Volunteered for 7 consecutive days',
            'category': 'special',
            'color': '#FF5722',
            'rarity': 'rare',
            'points_value': 60,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Month of Service',
            'description': 'Volunteered for 30 consecutive days',
            'category': 'special',
            'color': '#FF9800',
            'rarity': 'epic',
            'points_value': 150,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
    ]

    # Insert badges
    op.bulk_insert(badges_table, badges_data)

    # Seed Achievements (linked to badges)
    # Note: Badge IDs will be 1-13 based on insertion order above
    achievements_data = [
        # Hours-based achievements
        {
            'name': 'First Hour',
            'description': 'Log your first hour of volunteer work',
            'achievement_type': 'hours_logged',
            'criteria': {'hours_required': 1},
            'points_reward': 10,
            'badge_id': 1,  # First Step badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': '10 Hour Milestone',
            'description': 'Contribute 10 hours of volunteer work',
            'achievement_type': 'hours_logged',
            'criteria': {'hours_required': 10},
            'points_reward': 25,
            'badge_id': None,
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': '50 Hour Milestone',
            'description': 'Contribute 50 hours of volunteer work',
            'achievement_type': 'hours_logged',
            'criteria': {'hours_required': 50},
            'points_reward': 50,
            'badge_id': 2,  # Dedicated Volunteer badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': '100 Hour Milestone',
            'description': 'Reach 100 hours of volunteer service',
            'achievement_type': 'hours_logged',
            'criteria': {'hours_required': 100},
            'points_reward': 100,
            'badge_id': 3,  # Century Club badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': '500 Hour Legend',
            'description': 'Contribute 500 hours of volunteer work',
            'achievement_type': 'hours_logged',
            'criteria': {'hours_required': 500},
            'points_reward': 500,
            'badge_id': 4,  # Hero of the Community badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Project-based achievements
        {
            'name': 'First Project Complete',
            'description': 'Successfully complete your first project',
            'achievement_type': 'projects_completed',
            'criteria': {'projects_required': 1},
            'points_reward': 25,
            'badge_id': 5,  # Project Pioneer badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': '5 Projects Milestone',
            'description': 'Participate in 5 different projects',
            'achievement_type': 'projects_completed',
            'criteria': {'projects_required': 5},
            'points_reward': 75,
            'badge_id': 6,  # Multi-Tasker badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Task-based achievements
        {
            'name': 'Task Master',
            'description': 'Complete 10 tasks',
            'achievement_type': 'tasks_completed',
            'criteria': {'tasks_required': 10},
            'points_reward': 30,
            'badge_id': None,
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Task Champion',
            'description': 'Complete 50 tasks',
            'achievement_type': 'tasks_completed',
            'criteria': {'tasks_required': 50},
            'points_reward': 100,
            'badge_id': None,
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Skills achievements
        {
            'name': 'First Skill Certified',
            'description': 'Get certified in your first skill',
            'achievement_type': 'skills_acquired',
            'criteria': {'skills_required': 1, 'certified': True},
            'points_reward': 20,
            'badge_id': 7,  # Quick Learner badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Multi-Skilled',
            'description': 'Get certified in 5 different skills',
            'achievement_type': 'skills_acquired',
            'criteria': {'skills_required': 5, 'certified': True},
            'points_reward': 100,
            'badge_id': 8,  # Jack of All Trades badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Training achievements
        {
            'name': 'First Training Complete',
            'description': 'Complete your first training',
            'achievement_type': 'trainings_completed',
            'criteria': {'trainings_required': 1},
            'points_reward': 15,
            'badge_id': 9,  # Trained and Ready badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Training Enthusiast',
            'description': 'Complete 10 trainings',
            'achievement_type': 'trainings_completed',
            'criteria': {'trainings_required': 10},
            'points_reward': 80,
            'badge_id': 10,  # Lifelong Learner badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Streak achievements
        {
            'name': 'Week Warrior',
            'description': 'Volunteer for 7 consecutive days',
            'achievement_type': 'consecutive_days',
            'criteria': {'days_required': 7},
            'points_reward': 60,
            'badge_id': 12,  # Consistent Contributor badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
        {
            'name': 'Monthly Marathon',
            'description': 'Volunteer for 30 consecutive days',
            'achievement_type': 'consecutive_days',
            'criteria': {'days_required': 30},
            'points_reward': 150,
            'badge_id': 13,  # Month of Service badge
            'is_repeatable': False,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },

        # Referral achievement
        {
            'name': 'Recruiter',
            'description': 'Refer a new volunteer who completes onboarding',
            'achievement_type': 'volunteer_referred',
            'criteria': {'volunteers_required': 1},
            'points_reward': 50,
            'badge_id': 11,  # Mentor badge
            'is_repeatable': True,
            'tracks_progress': True,
            'is_active': True,
            'is_secret': False,
            'created_at': now,
            'updated_at': now
        },
    ]

    # Insert achievements
    op.bulk_insert(achievements_table, achievements_data)


def downgrade() -> None:
    """Remove seeded gamification data."""

    # Delete seeded achievements and badges
    op.execute("DELETE FROM achievements WHERE achievement_type IN ('hours_logged', 'projects_completed', 'tasks_completed', 'skills_acquired', 'trainings_completed', 'consecutive_days', 'volunteer_referred')")
    op.execute("DELETE FROM badges WHERE category IN ('time', 'projects', 'skills', 'training', 'leadership', 'special')")
