"""
Tests for Gamification Module
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from decimal import Decimal

from app.schemas.gamification import (
    # Badge schemas
    BadgeCreate,
    BadgeUpdate,
    Badge,
    BadgeSummary,
    # Achievement schemas
    AchievementCreate,
    AchievementUpdate,
    Achievement,
    # Points schemas
    PointsAwardRequest,
    PointsSummary,
    StreakInfo,
    # Leaderboard schemas
    Leaderboard,
    LeaderboardRanking,
)


# ============================================================
# BADGE SCHEMA TESTS
# ============================================================


class TestBadgeCreate:
    def test_badge_create_valid(self):
        """Test creating a valid badge"""
        badge = BadgeCreate(
            name="Test Badge",
            description="A test badge",
            category="time",
            rarity="common",
            points_value=10,
            is_active=True,
            is_secret=False,
        )
        assert badge.name == "Test Badge"
        assert badge.category == "time"
        assert badge.rarity == "common"
        assert badge.points_value == 10

    def test_badge_create_with_color(self):
        """Test creating badge with hex color"""
        badge = BadgeCreate(
            name="Test Badge",
            description="A test badge",
            category="time",
            color="#4CAF50",
            rarity="common",
            points_value=10,
        )
        assert badge.color == "#4CAF50"

    def test_badge_create_invalid_category(self):
        """Test that invalid category raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test Badge",
                description="A test badge",
                category="invalid_category",
                rarity="common",
                points_value=10,
            )

    def test_badge_create_invalid_rarity(self):
        """Test that invalid rarity raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test Badge",
                description="A test badge",
                category="time",
                rarity="invalid_rarity",
                points_value=10,
            )

    def test_badge_create_invalid_color_format(self):
        """Test that invalid color format raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test Badge",
                description="A test badge",
                category="time",
                color="blue",  # Should be hex like #4CAF50
                rarity="common",
                points_value=10,
            )

    def test_badge_create_negative_points(self):
        """Test that negative points raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test Badge",
                description="A test badge",
                category="time",
                rarity="common",
                points_value=-10,
            )


class TestBadgeUpdate:
    def test_badge_update_partial(self):
        """Test updating badge with partial data"""
        badge = BadgeUpdate(name="Updated Name")
        assert badge.name == "Updated Name"
        assert badge.description is None

    def test_badge_update_all_fields(self):
        """Test updating badge with all fields"""
        badge = BadgeUpdate(
            name="Updated Badge",
            description="Updated description",
            category="skills",
            rarity="rare",
            points_value=50,
            is_active=False,
        )
        assert badge.name == "Updated Badge"
        assert badge.category == "skills"
        assert badge.rarity == "rare"


# ============================================================
# ACHIEVEMENT SCHEMA TESTS
# ============================================================


class TestAchievementCreate:
    def test_achievement_create_valid(self):
        """Test creating a valid achievement"""
        achievement = AchievementCreate(
            name="First Hour",
            description="Log your first hour",
            achievement_type="hours_logged",
            criteria={"hours_required": 1},
            points_reward=10,
            is_repeatable=False,
            tracks_progress=True,
        )
        assert achievement.name == "First Hour"
        assert achievement.achievement_type == "hours_logged"
        assert achievement.criteria == {"hours_required": 1}
        assert achievement.points_reward == 10

    def test_achievement_create_with_badge(self):
        """Test creating achievement with badge"""
        achievement = AchievementCreate(
            name="Century Club",
            description="Reach 100 hours",
            achievement_type="hours_logged",
            criteria={"hours_required": 100},
            points_reward=100,
            badge_id=3,
        )
        assert achievement.badge_id == 3

    def test_achievement_create_invalid_type(self):
        """Test that invalid achievement type raises error"""
        with pytest.raises(ValidationError):
            AchievementCreate(
                name="Test Achievement",
                description="Test description",
                achievement_type="invalid_type",
                criteria={"value": 1},
                points_reward=10,
            )

    def test_achievement_create_repeatable(self):
        """Test creating repeatable achievement"""
        achievement = AchievementCreate(
            name="Volunteer Referral",
            description="Refer a volunteer",
            achievement_type="volunteer_referred",
            criteria={"volunteers_required": 1},
            points_reward=50,
            is_repeatable=True,
        )
        assert achievement.is_repeatable is True

    def test_achievement_create_secret(self):
        """Test creating secret achievement"""
        achievement = AchievementCreate(
            name="Secret Badge",
            description="Hidden until earned",
            achievement_type="custom",
            criteria={"custom": True},
            points_reward=100,
            is_secret=True,
        )
        assert achievement.is_secret is True


# ============================================================
# POINTS SCHEMA TESTS
# ============================================================


class TestPointsAwardRequest:
    def test_points_award_request_valid(self):
        """Test creating valid points award request"""
        request = PointsAwardRequest(
            points=100,
            event_type="manual_adjustment",
            description="Bonus for leadership",
        )
        assert request.points == 100
        assert request.event_type == "manual_adjustment"
        assert request.description == "Bonus for leadership"

    def test_points_award_request_negative_points(self):
        """Test awarding negative points (deduction)"""
        request = PointsAwardRequest(
            points=-50, event_type="manual_adjustment", description="Penalty"
        )
        assert request.points == -50

    def test_points_award_request_with_reference(self):
        """Test points award with reference"""
        request = PointsAwardRequest(
            points=25,
            event_type="task_completed",
            description="Completed task",
            reference_id=123,
            reference_type="task",
        )
        assert request.reference_id == 123
        assert request.reference_type == "task"

    def test_points_award_request_invalid_event_type(self):
        """Test that invalid event type raises error"""
        with pytest.raises(ValidationError):
            PointsAwardRequest(
                points=100, event_type="invalid_event", description="Test"
            )

    def test_points_award_request_empty_description(self):
        """Test that empty description raises error"""
        with pytest.raises(ValidationError):
            PointsAwardRequest(
                points=100, event_type="manual_adjustment", description=""
            )


class TestStreakInfo:
    def test_streak_info_valid(self):
        """Test creating streak info"""
        streak = StreakInfo(
            volunteer_id=123,
            current_streak_days=7,
            longest_streak_days=14,
            last_activity_date=datetime.utcnow(),
            is_active_today=True,
        )
        assert streak.volunteer_id == 123
        assert streak.current_streak_days == 7
        assert streak.longest_streak_days == 14
        assert streak.is_active_today is True

    def test_streak_info_no_activity(self):
        """Test streak info with no activity"""
        streak = StreakInfo(
            volunteer_id=123,
            current_streak_days=0,
            longest_streak_days=0,
            last_activity_date=None,
            is_active_today=False,
        )
        assert streak.current_streak_days == 0
        assert streak.last_activity_date is None


# ============================================================
# LEADERBOARD SCHEMA TESTS
# ============================================================


class TestLeaderboardRanking:
    def test_leaderboard_ranking_valid(self):
        """Test creating leaderboard ranking"""
        ranking = LeaderboardRanking(
            volunteer_id=123,
            rank=1,
            value=2500,
            volunteer_name="John Doe",
            volunteer_avatar="/avatars/123.jpg",
        )
        assert ranking.volunteer_id == 123
        assert ranking.rank == 1
        assert ranking.value == 2500

    def test_leaderboard_ranking_no_avatar(self):
        """Test ranking without avatar"""
        ranking = LeaderboardRanking(
            volunteer_id=123,
            rank=1,
            value=2500,
            volunteer_name="John Doe",
        )
        assert ranking.volunteer_avatar is None


class TestLeaderboard:
    def test_leaderboard_valid(self):
        """Test creating leaderboard"""
        rankings = [
            {
                "volunteer_id": 123,
                "rank": 1,
                "value": 2500,
                "volunteer_name": "John Doe",
                "volunteer_avatar": None,
            }
        ]

        leaderboard = Leaderboard(
            id=1,
            leaderboard_type="points",
            timeframe="all_time",
            period_start=None,
            period_end=None,
            rankings=rankings,
            generated_at=datetime.utcnow(),
            is_current=True,
            total_participants=100,
            average_value=Decimal("500.0"),
            median_value=Decimal("450.0"),
        )
        assert leaderboard.leaderboard_type == "points"
        assert leaderboard.timeframe == "all_time"
        assert leaderboard.total_participants == 100
        assert len(leaderboard.rankings) == 1

    def test_leaderboard_invalid_type(self):
        """Test that invalid leaderboard type raises error"""
        with pytest.raises(ValidationError):
            Leaderboard(
                id=1,
                leaderboard_type="invalid_type",
                timeframe="all_time",
                rankings=[],
                generated_at=datetime.utcnow(),
                is_current=True,
                total_participants=0,
            )

    def test_leaderboard_invalid_timeframe(self):
        """Test that invalid timeframe raises error"""
        with pytest.raises(ValidationError):
            Leaderboard(
                id=1,
                leaderboard_type="points",
                timeframe="invalid_timeframe",
                rankings=[],
                generated_at=datetime.utcnow(),
                is_current=True,
                total_participants=0,
            )


# ============================================================
# VALIDATION TESTS
# ============================================================


class TestSchemaValidations:
    def test_badge_category_validation(self):
        """Test all valid badge categories"""
        valid_categories = [
            "time",
            "skills",
            "projects",
            "training",
            "leadership",
            "special",
        ]

        for category in valid_categories:
            badge = BadgeCreate(
                name=f"Test {category}",
                description="Test",
                category=category,
                rarity="common",
                points_value=10,
            )
            assert badge.category == category

    def test_badge_rarity_validation(self):
        """Test all valid badge rarities"""
        valid_rarities = ["common", "rare", "epic", "legendary"]

        for rarity in valid_rarities:
            badge = BadgeCreate(
                name=f"Test {rarity}",
                description="Test",
                category="time",
                rarity=rarity,
                points_value=10,
            )
            assert badge.rarity == rarity

    def test_achievement_type_validation(self):
        """Test all valid achievement types"""
        valid_types = [
            "hours_logged",
            "projects_completed",
            "tasks_completed",
            "skills_acquired",
            "trainings_completed",
            "consecutive_days",
            "volunteer_referred",
            "custom",
        ]

        for achievement_type in valid_types:
            achievement = AchievementCreate(
                name=f"Test {achievement_type}",
                description="Test",
                achievement_type=achievement_type,
                criteria={"value": 1},
                points_reward=10,
            )
            assert achievement.achievement_type == achievement_type

    def test_points_event_type_validation(self):
        """Test all valid points event types"""
        valid_event_types = [
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

        for event_type in valid_event_types:
            request = PointsAwardRequest(
                points=10, event_type=event_type, description="Test"
            )
            assert request.event_type == event_type

    def test_leaderboard_type_validation(self):
        """Test all valid leaderboard types"""
        valid_types = ["points", "hours", "projects"]

        for lb_type in valid_types:
            leaderboard = Leaderboard(
                id=1,
                leaderboard_type=lb_type,
                timeframe="all_time",
                rankings=[],
                generated_at=datetime.utcnow(),
                is_current=True,
                total_participants=0,
            )
            assert leaderboard.leaderboard_type == lb_type

    def test_leaderboard_timeframe_validation(self):
        """Test all valid leaderboard timeframes"""
        valid_timeframes = ["all_time", "monthly", "weekly"]

        for timeframe in valid_timeframes:
            leaderboard = Leaderboard(
                id=1,
                leaderboard_type="points",
                timeframe=timeframe,
                rankings=[],
                generated_at=datetime.utcnow(),
                is_current=True,
                total_participants=0,
            )
            assert leaderboard.timeframe == timeframe


# ============================================================
# EDGE CASES
# ============================================================


class TestEdgeCases:
    def test_badge_max_length_name(self):
        """Test badge name max length"""
        long_name = "A" * 100
        badge = BadgeCreate(
            name=long_name,
            description="Test",
            category="time",
            rarity="common",
            points_value=10,
        )
        assert len(badge.name) == 100

    def test_badge_name_too_long(self):
        """Test that badge name exceeding max length raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="A" * 101,
                description="Test",
                category="time",
                rarity="common",
                points_value=10,
            )

    def test_color_validation_missing_hash(self):
        """Test color without # raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test",
                description="Test",
                category="time",
                color="4CAF50",
                rarity="common",
                points_value=10,
            )

    def test_color_validation_wrong_length(self):
        """Test color with wrong length raises error"""
        with pytest.raises(ValidationError):
            BadgeCreate(
                name="Test",
                description="Test",
                category="time",
                color="#4CAF",
                rarity="common",
                points_value=10,
            )

    def test_achievement_criteria_complex(self):
        """Test achievement with complex criteria"""
        achievement = AchievementCreate(
            name="Certified Expert",
            description="Get 5 certified skills",
            achievement_type="skills_acquired",
            criteria={"skills_required": 5, "certified": True},
            points_reward=100,
        )
        assert achievement.criteria["skills_required"] == 5
        assert achievement.criteria["certified"] is True

    def test_zero_points_award(self):
        """Test awarding zero points is valid"""
        request = PointsAwardRequest(
            points=0, event_type="manual_adjustment", description="No points awarded"
        )
        assert request.points == 0

    def test_large_points_value(self):
        """Test very large points value"""
        request = PointsAwardRequest(
            points=1000000,
            event_type="manual_adjustment",
            description="Million point bonus",
        )
        assert request.points == 1000000

    def test_empty_leaderboard_rankings(self):
        """Test leaderboard with no participants"""
        leaderboard = Leaderboard(
            id=1,
            leaderboard_type="points",
            timeframe="weekly",
            rankings=[],
            generated_at=datetime.utcnow(),
            is_current=True,
            total_participants=0,
            average_value=None,
            median_value=None,
        )
        assert len(leaderboard.rankings) == 0
        assert leaderboard.total_participants == 0


# ============================================================
# INTEGRATION SCENARIO TESTS
# ============================================================


class TestIntegrationScenarios:
    def test_volunteer_progression_scenario(self):
        """Test a complete volunteer progression scenario"""
        # Create a simple badge
        badge = BadgeCreate(
            name="First Step",
            description="First hour logged",
            category="time",
            rarity="common",
            points_value=10,
        )

        # Create corresponding achievement
        achievement = AchievementCreate(
            name="First Hour",
            description="Log your first hour",
            achievement_type="hours_logged",
            criteria={"hours_required": 1},
            points_reward=10,
            badge_id=1,
        )

        # Award points for the hour
        points_award = PointsAwardRequest(
            points=5,
            event_type="hours_logged",
            description="Logged 1 hour of work",
            reference_id=1,
            reference_type="timelog",
        )

        assert badge.points_value == 10
        assert achievement.points_reward == 10
        assert points_award.points == 5

    def test_leaderboard_creation_scenario(self):
        """Test creating a leaderboard with multiple volunteers"""
        rankings = [
            {
                "volunteer_id": 1,
                "rank": 1,
                "value": 1000,
                "volunteer_name": "Alice",
                "volunteer_avatar": None,
            },
            {
                "volunteer_id": 2,
                "rank": 2,
                "value": 800,
                "volunteer_name": "Bob",
                "volunteer_avatar": None,
            },
            {
                "volunteer_id": 3,
                "rank": 3,
                "value": 600,
                "volunteer_name": "Charlie",
                "volunteer_avatar": None,
            },
        ]

        leaderboard = Leaderboard(
            id=1,
            leaderboard_type="points",
            timeframe="monthly",
            period_start=datetime(2025, 11, 1),
            period_end=datetime(2025, 11, 30),
            rankings=rankings,
            generated_at=datetime.utcnow(),
            is_current=True,
            total_participants=3,
            average_value=Decimal("800.0"),
            median_value=Decimal("800.0"),
        )

        assert len(leaderboard.rankings) == 3
        assert leaderboard.rankings[0]["rank"] == 1
        assert leaderboard.rankings[0]["value"] == 1000

    def test_streak_tracking_scenario(self):
        """Test tracking volunteer activity streaks"""
        # Start with no streak
        streak_start = StreakInfo(
            volunteer_id=123,
            current_streak_days=0,
            longest_streak_days=0,
            last_activity_date=None,
            is_active_today=False,
        )

        # After 7 days of activity
        streak_week = StreakInfo(
            volunteer_id=123,
            current_streak_days=7,
            longest_streak_days=7,
            last_activity_date=datetime.utcnow(),
            is_active_today=True,
        )

        # After breaking streak but having had a 30-day streak before
        streak_broken = StreakInfo(
            volunteer_id=123,
            current_streak_days=1,
            longest_streak_days=30,
            last_activity_date=datetime.utcnow(),
            is_active_today=True,
        )

        assert streak_start.current_streak_days == 0
        assert streak_week.current_streak_days == 7
        assert streak_broken.longest_streak_days == 30
        assert streak_broken.current_streak_days == 1
