"""
Gamification Module - Pydantic Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================
# ENUMS (as string literals for validation)
# ============================================================

BADGE_CATEGORIES = ["time", "skills", "projects", "training", "leadership", "special"]
BADGE_RARITIES = ["common", "rare", "epic", "legendary"]
ACHIEVEMENT_TYPES = [
    "hours_logged",
    "projects_completed",
    "tasks_completed",
    "skills_acquired",
    "trainings_completed",
    "consecutive_days",
    "volunteer_referred",
    "custom",
]
POINTS_EVENT_TYPES = [
    "hours_logged",
    "task_completed",
    "project_completed",
    "training_completed",
    "skill_certified",
    "achievement_earned",
    "badge_earned",
    "volunteer_referred",
    "manual_adjustment",
]
LEADERBOARD_TYPES = ["points", "hours", "projects"]
LEADERBOARD_TIMEFRAMES = ["all_time", "monthly", "weekly"]


# ============================================================
# BADGE SCHEMAS
# ============================================================


class BadgeBase(BaseModel):
    """Base badge schema with common fields."""

    name: str = Field(..., max_length=100, description="Badge name")
    description: str = Field(..., description="Badge description")
    category: str = Field(..., description="Badge category")
    icon_url: Optional[str] = Field(None, max_length=255, description="URL to badge icon")
    color: Optional[str] = Field(None, max_length=7, description="Hex color code (e.g., #4CAF50)")
    rarity: str = Field(..., description="Badge rarity level")
    points_value: int = Field(..., ge=0, description="Points awarded when earned")
    is_active: bool = Field(True, description="Whether badge is currently available")
    is_secret: bool = Field(False, description="Hidden until earned")

    @field_validator("category")
    def validate_category(cls, v):
        if v not in BADGE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(BADGE_CATEGORIES)}")
        return v

    @field_validator("rarity")
    def validate_rarity(cls, v):
        if v not in BADGE_RARITIES:
            raise ValueError(f"Rarity must be one of: {', '.join(BADGE_RARITIES)}")
        return v

    @field_validator("color")
    def validate_color(cls, v):
        if v and not v.startswith("#"):
            raise ValueError("Color must be a hex code starting with #")
        if v and len(v) != 7:
            raise ValueError("Color must be 7 characters (e.g., #4CAF50)")
        return v


class BadgeCreate(BadgeBase):
    """Schema for creating a new badge."""

    pass


class BadgeUpdate(BaseModel):
    """Schema for updating a badge (all fields optional)."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=7)
    rarity: Optional[str] = None
    points_value: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_secret: Optional[bool] = None

    @field_validator("category")
    def validate_category(cls, v):
        if v and v not in BADGE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(BADGE_CATEGORIES)}")
        return v

    @field_validator("rarity")
    def validate_rarity(cls, v):
        if v and v not in BADGE_RARITIES:
            raise ValueError(f"Rarity must be one of: {', '.join(BADGE_RARITIES)}")
        return v


class Badge(BadgeBase):
    """Complete badge schema for responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BadgeSummary(BaseModel):
    """Summary badge schema for list views."""

    id: int
    name: str
    category: str
    rarity: str
    color: Optional[str]
    icon_url: Optional[str]
    points_value: int
    is_secret: bool

    class Config:
        from_attributes = True


# ============================================================
# VOLUNTEER BADGE SCHEMAS
# ============================================================


class VolunteerBadgeBase(BaseModel):
    """Base volunteer badge schema."""

    earned_reason: Optional[str] = Field(None, description="Context about how badge was earned")
    is_showcased: bool = Field(False, description="Display on volunteer's profile")


class VolunteerBadgeAward(BaseModel):
    """Schema for manually awarding a badge."""

    badge_id: int = Field(..., description="ID of badge to award")
    earned_reason: Optional[str] = Field(None, description="Reason for manual award")


class VolunteerBadge(VolunteerBadgeBase):
    """Complete volunteer badge schema."""

    id: int
    volunteer_id: int
    badge_id: int
    earned_at: datetime
    awarded_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class VolunteerBadgeWithDetails(VolunteerBadge):
    """Volunteer badge with full badge details."""

    badge: BadgeSummary


class BadgeShowcaseToggle(BaseModel):
    """Schema for toggling badge showcase."""

    is_showcased: bool = Field(..., description="Whether to showcase badge")


class VolunteerBadgeCollection(BaseModel):
    """Collection of badges for a volunteer."""

    total_badges: int
    showcased_badges: List[str]
    badges: List[VolunteerBadgeWithDetails]


# ============================================================
# ACHIEVEMENT SCHEMAS
# ============================================================


class AchievementBase(BaseModel):
    """Base achievement schema."""

    name: str = Field(..., max_length=100, description="Achievement name")
    description: str = Field(..., description="Achievement description")
    achievement_type: str = Field(..., description="Type of achievement")
    criteria: Dict[str, Any] = Field(..., description="Achievement criteria (JSON)")
    points_reward: int = Field(..., ge=0, description="Points awarded when achieved")
    badge_id: Optional[int] = Field(None, description="Badge awarded upon completion")
    is_repeatable: bool = Field(False, description="Can be earned multiple times")
    tracks_progress: bool = Field(True, description="Show progress to volunteer")
    is_active: bool = Field(True, description="Currently available")
    is_secret: bool = Field(False, description="Hidden until earned")

    @field_validator("achievement_type")
    def validate_achievement_type(cls, v):
        if v not in ACHIEVEMENT_TYPES:
            raise ValueError(f"Achievement type must be one of: {', '.join(ACHIEVEMENT_TYPES)}")
        return v


class AchievementCreate(AchievementBase):
    """Schema for creating a new achievement."""

    pass


class AchievementUpdate(BaseModel):
    """Schema for updating an achievement (all fields optional)."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    achievement_type: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points_reward: Optional[int] = Field(None, ge=0)
    badge_id: Optional[int] = None
    is_repeatable: Optional[bool] = None
    tracks_progress: Optional[bool] = None
    is_active: Optional[bool] = None
    is_secret: Optional[bool] = None

    @field_validator("achievement_type")
    def validate_achievement_type(cls, v):
        if v and v not in ACHIEVEMENT_TYPES:
            raise ValueError(f"Achievement type must be one of: {', '.join(ACHIEVEMENT_TYPES)}")
        return v


class Achievement(AchievementBase):
    """Complete achievement schema for responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementSummary(BaseModel):
    """Summary achievement schema for list views."""

    id: int
    name: str
    achievement_type: str
    points_reward: int
    is_repeatable: bool
    is_secret: bool

    class Config:
        from_attributes = True


# ============================================================
# VOLUNTEER ACHIEVEMENT SCHEMAS
# ============================================================


class VolunteerAchievementBase(BaseModel):
    """Base volunteer achievement schema."""

    current_progress: Decimal = Field(default=Decimal("0"), description="Current progress value")
    target_progress: Decimal = Field(..., description="Target value from criteria")
    is_completed: bool = Field(False, description="Whether achievement is completed")
    times_completed: int = Field(0, ge=0, description="Count for repeatable achievements")


class VolunteerAchievement(VolunteerAchievementBase):
    """Complete volunteer achievement schema."""

    id: int
    volunteer_id: int
    achievement_id: int
    completed_at: Optional[datetime] = None
    started_at: datetime
    last_progress_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AchievementProgress(BaseModel):
    """Achievement progress for a volunteer with details."""

    id: int
    name: str
    description: str
    achievement_type: str
    points_reward: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    current_progress: Decimal
    target_progress: Decimal
    progress_percentage: float = Field(description="Calculated progress percentage")
    times_completed: int
    badge: Optional[BadgeSummary] = None

    class Config:
        from_attributes = True


class VolunteerAchievementProgress(BaseModel):
    """Collection of achievement progress for a volunteer."""

    total_achievements: int
    completed: int
    in_progress: int
    achievements: List[AchievementProgress]


# ============================================================
# POINTS SCHEMAS
# ============================================================


class VolunteerPointsBase(BaseModel):
    """Base volunteer points schema."""

    total_points: int = Field(0, ge=0, description="All-time total points")
    current_points: int = Field(0, ge=0, description="Current balance (same as total for cumulative)")
    rank: Optional[int] = Field(None, ge=1, description="Current rank position")
    rank_percentile: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentile ranking")
    current_streak_days: int = Field(0, ge=0, description="Current consecutive active days")
    longest_streak_days: int = Field(0, ge=0, description="Best streak ever")
    last_activity_date: Optional[datetime] = Field(None, description="Last activity date")


class VolunteerPoints(VolunteerPointsBase):
    """Complete volunteer points schema."""

    id: int
    volunteer_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class PointsHistoryEntry(BaseModel):
    """Single points history entry."""

    id: int
    points_change: int = Field(..., description="Points added/removed (can be negative)")
    event_type: str = Field(..., description="Type of event")
    description: str = Field(..., description="Human-readable description")
    reference_id: Optional[int] = Field(None, description="ID of related entity")
    reference_type: Optional[str] = Field(None, description="Type of related entity")
    balance_after: int = Field(..., description="Points balance after this change")
    awarded_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PointsSummary(VolunteerPoints):
    """Points summary with recent history."""

    recent_history: List[PointsHistoryEntry] = Field(default_factory=list)


class PointsAwardRequest(BaseModel):
    """Schema for manually awarding points."""

    points: int = Field(..., description="Points to award (can be negative)")
    event_type: str = Field(default="manual_adjustment", description="Event type")
    description: str = Field(..., min_length=1, description="Reason for award")
    reference_id: Optional[int] = Field(None, description="Related entity ID")
    reference_type: Optional[str] = Field(None, description="Related entity type")

    @field_validator("event_type")
    def validate_event_type(cls, v):
        if v not in POINTS_EVENT_TYPES:
            raise ValueError(f"Event type must be one of: {', '.join(POINTS_EVENT_TYPES)}")
        return v


class PointsAwardResponse(BaseModel):
    """Response after awarding points."""

    volunteer_id: int
    points_change: int
    new_balance: int
    event_type: str
    description: str
    created_at: datetime


class StreakInfo(BaseModel):
    """Volunteer streak information."""

    volunteer_id: int
    current_streak_days: int
    longest_streak_days: int
    last_activity_date: Optional[datetime]
    is_active_today: bool


# ============================================================
# LEADERBOARD SCHEMAS
# ============================================================


class LeaderboardRanking(BaseModel):
    """Single ranking entry in a leaderboard."""

    volunteer_id: int
    rank: int
    value: int | Decimal
    volunteer_name: str
    volunteer_avatar: Optional[str] = None


class LeaderboardBase(BaseModel):
    """Base leaderboard schema."""

    leaderboard_type: str = Field(..., description="Type of leaderboard")
    timeframe: str = Field(..., description="Timeframe for leaderboard")
    period_start: Optional[datetime] = Field(None, description="Period start date")
    period_end: Optional[datetime] = Field(None, description="Period end date")

    @field_validator("leaderboard_type")
    def validate_leaderboard_type(cls, v):
        if v not in LEADERBOARD_TYPES:
            raise ValueError(f"Leaderboard type must be one of: {', '.join(LEADERBOARD_TYPES)}")
        return v

    @field_validator("timeframe")
    def validate_timeframe(cls, v):
        if v not in LEADERBOARD_TIMEFRAMES:
            raise ValueError(f"Timeframe must be one of: {', '.join(LEADERBOARD_TIMEFRAMES)}")
        return v


class Leaderboard(LeaderboardBase):
    """Complete leaderboard schema."""

    id: int
    rankings: List[LeaderboardRanking]
    generated_at: datetime
    is_current: bool
    total_participants: int
    average_value: Optional[Decimal] = None
    median_value: Optional[Decimal] = None

    class Config:
        from_attributes = True


class VolunteerLeaderboardPosition(BaseModel):
    """Volunteer's position in a leaderboard."""

    volunteer_id: int
    leaderboard_type: str
    timeframe: str
    rank: Optional[int] = None
    value: Optional[int | Decimal] = None
    total_participants: int
    percentile: Optional[Decimal] = None


# ============================================================
# STATISTICS SCHEMAS
# ============================================================


class GamificationStats(BaseModel):
    """Overall gamification statistics (admin view)."""

    total_badges: int
    total_achievements: int
    total_points_awarded: int
    total_badges_earned: int
    total_achievements_completed: int
    active_volunteers: int
    avg_points_per_volunteer: Decimal
    most_earned_badge: Optional[BadgeSummary] = None
    most_completed_achievement: Optional[AchievementSummary] = None


class VolunteerGamificationSummary(BaseModel):
    """Complete gamification summary for a volunteer."""

    volunteer_id: int
    points: VolunteerPointsBase
    badges_earned: int
    achievements_completed: int
    recent_badges: List[VolunteerBadgeWithDetails]
    achievement_progress: List[AchievementProgress]
    leaderboard_positions: List[VolunteerLeaderboardPosition]


# ============================================================
# UTILITY SCHEMAS
# ============================================================


class BadgeCategoryList(BaseModel):
    """List of available badge categories."""

    categories: List[str] = Field(default_factory=lambda: BADGE_CATEGORIES)


class AchievementTypeList(BaseModel):
    """List of available achievement types."""

    types: List[str] = Field(default_factory=lambda: ACHIEVEMENT_TYPES)


class GlobalRanking(BaseModel):
    """Global ranking entry."""

    rank: int
    volunteer_id: int
    volunteer_name: str
    volunteer_avatar: Optional[str]
    total_points: int
    badges_count: int
    achievements_count: int
