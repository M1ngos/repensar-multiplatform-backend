# app/models/gamification.py
from sqlmodel import SQLModel, Field, Relationship, Column, Text, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class BadgeCategory(str, Enum):
    """Categories for organizing badges"""
    TIME = "time"  # Time-based achievements (hours logged)
    SKILLS = "skills"  # Skill-related achievements
    PROJECTS = "projects"  # Project completion achievements
    TRAINING = "training"  # Training completion achievements
    LEADERSHIP = "leadership"  # Leadership and mentoring
    SPECIAL = "special"  # Special event badges


class AchievementType(str, Enum):
    """Types of achievements based on trigger conditions"""
    HOURS_LOGGED = "hours_logged"
    PROJECTS_COMPLETED = "projects_completed"
    TASKS_COMPLETED = "tasks_completed"
    SKILLS_ACQUIRED = "skills_acquired"
    TRAININGS_COMPLETED = "trainings_completed"
    CONSECUTIVE_DAYS = "consecutive_days"
    VOLUNTEER_REFERRED = "volunteer_referred"
    CUSTOM = "custom"


class PointsEventType(str, Enum):
    """Types of events that award points"""
    HOURS_LOGGED = "hours_logged"
    TASK_COMPLETED = "task_completed"
    PROJECT_COMPLETED = "project_completed"
    TRAINING_COMPLETED = "training_completed"
    SKILL_CERTIFIED = "skill_certified"
    ACHIEVEMENT_EARNED = "achievement_earned"
    BADGE_EARNED = "badge_earned"
    VOLUNTEER_REFERRED = "volunteer_referred"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class Badge(SQLModel, table=True):
    """Badge definitions - what badges exist in the system"""
    __tablename__ = "badges"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: str = Field(sa_column=Column(Text))
    category: str = Field(max_length=30, default=BadgeCategory.SPECIAL, index=True)

    # Visual
    icon_url: Optional[str] = Field(default=None, max_length=500)  # URL to badge icon/image
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color code

    # Rarity/prestige
    rarity: str = Field(default="common", max_length=20)  # "common", "rare", "epic", "legendary"
    points_value: int = Field(default=10, ge=0)  # Points awarded when badge is earned

    # Availability
    is_active: bool = Field(default=True, index=True)
    is_secret: bool = Field(default=False)  # Hidden until earned

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    volunteer_badges: List["VolunteerBadge"] = Relationship(back_populates="badge")


class Achievement(SQLModel, table=True):
    """Achievement definitions with criteria"""
    __tablename__ = "achievements"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: str = Field(sa_column=Column(Text))
    achievement_type: str = Field(max_length=30, default=AchievementType.CUSTOM, index=True)

    # Criteria (stored as JSON for flexibility)
    # Example: {"hours_required": 100, "project_count": 5}
    criteria: Dict[str, Any] = Field(sa_column=Column(JSON))

    # Rewards
    points_reward: int = Field(default=50, ge=0)
    badge_id: Optional[int] = Field(default=None, foreign_key="badges.id")  # Optional badge to award

    # Progress tracking
    is_repeatable: bool = Field(default=False)  # Can be earned multiple times
    tracks_progress: bool = Field(default=True)  # Whether to show progress (e.g., 50/100 hours)

    # Availability
    is_active: bool = Field(default=True, index=True)
    is_secret: bool = Field(default=False)  # Hidden until earned

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    volunteer_achievements: List["VolunteerAchievement"] = Relationship(back_populates="achievement")


class VolunteerBadge(SQLModel, table=True):
    """Badges earned by volunteers"""
    __tablename__ = "volunteer_badges"

    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    badge_id: int = Field(foreign_key="badges.id", index=True)

    earned_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Context about how it was earned
    earned_reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    awarded_by_id: Optional[int] = Field(default=None, foreign_key="users.id")  # For manual awards

    # Display preferences
    is_showcased: bool = Field(default=False)  # Whether volunteer displays this on profile

    # Relationships
    badge: Badge = Relationship(back_populates="volunteer_badges")


class VolunteerAchievement(SQLModel, table=True):
    """Achievements earned by volunteers"""
    __tablename__ = "volunteer_achievements"

    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)
    achievement_id: int = Field(foreign_key="achievements.id", index=True)

    # Progress tracking
    current_progress: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)
    target_progress: Decimal = Field(max_digits=10, decimal_places=2)  # From achievement criteria

    # Completion
    is_completed: bool = Field(default=False, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)
    times_completed: int = Field(default=0, ge=0)  # For repeatable achievements

    # Tracking
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_progress_at: Optional[datetime] = Field(default=None)

    # Relationships
    achievement: Achievement = Relationship(back_populates="volunteer_achievements")


class VolunteerPoints(SQLModel, table=True):
    """Current points balance for each volunteer"""
    __tablename__ = "volunteer_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", unique=True, index=True)

    # Points tracking
    total_points: int = Field(default=0, ge=0, index=True)  # All-time total
    current_points: int = Field(default=0, ge=0)  # Current balance (if points can be spent)

    # Ranking (updated periodically)
    rank: Optional[int] = Field(default=None, index=True)
    rank_percentile: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2)

    # Streaks
    current_streak_days: int = Field(default=0, ge=0)  # Current consecutive active days
    longest_streak_days: int = Field(default=0, ge=0)  # Best streak ever
    last_activity_date: Optional[datetime] = Field(default=None)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    points_history: List["PointsHistory"] = Relationship(back_populates="volunteer_points")


class PointsHistory(SQLModel, table=True):
    """Audit trail for points changes"""
    __tablename__ = "points_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_points_id: int = Field(foreign_key="volunteer_points.id", index=True)
    volunteer_id: int = Field(foreign_key="volunteers.id", index=True)

    # Change details
    points_change: int = Field(...)  # Can be positive or negative
    event_type: str = Field(max_length=30, index=True)  # PointsEventType

    # Context
    description: str = Field(max_length=500)
    reference_id: Optional[int] = Field(default=None)  # ID of related entity (task, project, etc.)
    reference_type: Optional[str] = Field(default=None, max_length=50)  # Type of entity

    # Balance after change
    balance_after: int = Field(ge=0)

    awarded_by_id: Optional[int] = Field(default=None, foreign_key="users.id")  # For manual awards
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    volunteer_points: VolunteerPoints = Relationship(back_populates="points_history")


class Leaderboard(SQLModel, table=True):
    """Cached leaderboard snapshots for performance"""
    __tablename__ = "leaderboards"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Leaderboard type and timeframe
    leaderboard_type: str = Field(max_length=50, index=True)  # "points", "hours", "projects"
    timeframe: str = Field(max_length=20, index=True)  # "all_time", "monthly", "weekly"

    # Time period
    period_start: Optional[datetime] = Field(default=None, index=True)
    period_end: Optional[datetime] = Field(default=None)

    # Rankings (stored as JSON for flexibility)
    # Example: [{"volunteer_id": 1, "rank": 1, "value": 1500, "volunteer_name": "John"}]
    rankings: List[Dict[str, Any]] = Field(sa_column=Column(JSON))

    # Cache metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    is_current: bool = Field(default=True, index=True)

    # Statistics
    total_participants: int = Field(default=0, ge=0)
    average_value: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    median_value: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)