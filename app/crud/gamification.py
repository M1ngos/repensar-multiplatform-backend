"""
Gamification Module - CRUD Operations
"""

from sqlmodel import Session, select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.gamification import (
    Badge,
    Achievement,
    VolunteerBadge,
    VolunteerAchievement,
    VolunteerPoints,
    PointsHistory,
    Leaderboard,
)
from app.schemas.gamification import (
    BadgeCreate,
    BadgeUpdate,
    AchievementCreate,
    AchievementUpdate,
    PointsAwardRequest,
)


# ============================================================
# BADGE CRUD
# ============================================================


class BadgeCRUD:
    """CRUD operations for badges."""

    def create_badge(self, db: Session, data: BadgeCreate) -> Badge:
        """Create a new badge."""
        badge = Badge(**data.model_dump())
        db.add(badge)
        db.commit()
        db.refresh(badge)
        return badge

    def get_badge(self, db: Session, badge_id: int) -> Optional[Badge]:
        """Get badge by ID."""
        return db.get(Badge, badge_id)

    def get_badge_by_name(self, db: Session, name: str) -> Optional[Badge]:
        """Get badge by name."""
        statement = select(Badge).where(Badge.name == name)
        return db.exec(statement).first()

    def get_badges(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        rarity: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_secret: bool = False,
    ) -> List[Badge]:
        """Get list of badges with filters."""
        query = select(Badge)

        if category:
            query = query.where(Badge.category == category)
        if rarity:
            query = query.where(Badge.rarity == rarity)
        if is_active is not None:
            query = query.where(Badge.is_active == is_active)
        if not include_secret:
            query = query.where(Badge.is_secret == False)

        query = query.offset(skip).limit(limit).order_by(Badge.created_at.desc())
        return list(db.exec(query).all())

    def count_badges(
        self,
        db: Session,
        category: Optional[str] = None,
        rarity: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count badges with filters."""
        query = select(func.count(Badge.id))

        if category:
            query = query.where(Badge.category == category)
        if rarity:
            query = query.where(Badge.rarity == rarity)
        if is_active is not None:
            query = query.where(Badge.is_active == is_active)

        return db.exec(query).one()

    def update_badge(self, db: Session, badge_id: int, data: BadgeUpdate) -> Optional[Badge]:
        """Update a badge."""
        badge = db.get(Badge, badge_id)
        if not badge:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(badge, field, value)

        badge.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(badge)
        return badge

    def delete_badge(self, db: Session, badge_id: int) -> bool:
        """Soft delete a badge (set is_active to False)."""
        badge = db.get(Badge, badge_id)
        if not badge:
            return False

        badge.is_active = False
        badge.updated_at = datetime.utcnow()
        db.commit()
        return True


# ============================================================
# ACHIEVEMENT CRUD
# ============================================================


class AchievementCRUD:
    """CRUD operations for achievements."""

    def create_achievement(self, db: Session, data: AchievementCreate) -> Achievement:
        """Create a new achievement."""
        achievement = Achievement(**data.model_dump())
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement

    def get_achievement(self, db: Session, achievement_id: int) -> Optional[Achievement]:
        """Get achievement by ID."""
        return db.get(Achievement, achievement_id)

    def get_achievement_by_name(self, db: Session, name: str) -> Optional[Achievement]:
        """Get achievement by name."""
        statement = select(Achievement).where(Achievement.name == name)
        return db.exec(statement).first()

    def get_achievements(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        achievement_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_secret: bool = False,
    ) -> List[Achievement]:
        """Get list of achievements with filters."""
        query = select(Achievement)

        if achievement_type:
            query = query.where(Achievement.achievement_type == achievement_type)
        if is_active is not None:
            query = query.where(Achievement.is_active == is_active)
        if not include_secret:
            query = query.where(Achievement.is_secret == False)

        query = query.offset(skip).limit(limit).order_by(Achievement.created_at.desc())
        return list(db.exec(query).all())

    def count_achievements(
        self,
        db: Session,
        achievement_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count achievements with filters."""
        query = select(func.count(Achievement.id))

        if achievement_type:
            query = query.where(Achievement.achievement_type == achievement_type)
        if is_active is not None:
            query = query.where(Achievement.is_active == is_active)

        return db.exec(query).one()

    def update_achievement(
        self, db: Session, achievement_id: int, data: AchievementUpdate
    ) -> Optional[Achievement]:
        """Update an achievement."""
        achievement = db.get(Achievement, achievement_id)
        if not achievement:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(achievement, field, value)

        achievement.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(achievement)
        return achievement

    def delete_achievement(self, db: Session, achievement_id: int) -> bool:
        """Soft delete an achievement (set is_active to False)."""
        achievement = db.get(Achievement, achievement_id)
        if not achievement:
            return False

        achievement.is_active = False
        achievement.updated_at = datetime.utcnow()
        db.commit()
        return True


# ============================================================
# VOLUNTEER BADGE CRUD
# ============================================================


class VolunteerBadgeCRUD:
    """CRUD operations for volunteer badges."""

    def award_badge(
        self,
        db: Session,
        volunteer_id: int,
        badge_id: int,
        earned_reason: Optional[str] = None,
        awarded_by_id: Optional[int] = None,
    ) -> VolunteerBadge:
        """Award a badge to a volunteer."""
        volunteer_badge = VolunteerBadge(
            volunteer_id=volunteer_id,
            badge_id=badge_id,
            earned_at=datetime.utcnow(),
            earned_reason=earned_reason,
            awarded_by_id=awarded_by_id,
            is_showcased=False,
        )
        db.add(volunteer_badge)
        db.commit()
        db.refresh(volunteer_badge)
        return volunteer_badge

    def has_badge(self, db: Session, volunteer_id: int, badge_id: int) -> bool:
        """Check if volunteer already has a badge."""
        statement = select(VolunteerBadge).where(
            and_(VolunteerBadge.volunteer_id == volunteer_id, VolunteerBadge.badge_id == badge_id)
        )
        return db.exec(statement).first() is not None

    def get_volunteer_badge(
        self, db: Session, volunteer_id: int, badge_id: int
    ) -> Optional[VolunteerBadge]:
        """Get a specific volunteer badge."""
        statement = select(VolunteerBadge).where(
            and_(VolunteerBadge.volunteer_id == volunteer_id, VolunteerBadge.badge_id == badge_id)
        )
        return db.exec(statement).first()

    def get_volunteer_badges(
        self, db: Session, volunteer_id: int, showcased_only: bool = False
    ) -> List[VolunteerBadge]:
        """Get all badges earned by a volunteer."""
        query = select(VolunteerBadge).where(VolunteerBadge.volunteer_id == volunteer_id)

        if showcased_only:
            query = query.where(VolunteerBadge.is_showcased == True)

        query = query.order_by(VolunteerBadge.earned_at.desc())
        return list(db.exec(query).all())

    def toggle_showcase(
        self, db: Session, volunteer_id: int, badge_id: int, is_showcased: bool
    ) -> Optional[VolunteerBadge]:
        """Toggle badge showcase status."""
        volunteer_badge = self.get_volunteer_badge(db, volunteer_id, badge_id)
        if not volunteer_badge:
            return None

        volunteer_badge.is_showcased = is_showcased
        db.commit()
        db.refresh(volunteer_badge)
        return volunteer_badge

    def count_volunteer_badges(self, db: Session, volunteer_id: int) -> int:
        """Count total badges earned by a volunteer."""
        query = select(func.count(VolunteerBadge.id)).where(
            VolunteerBadge.volunteer_id == volunteer_id
        )
        return db.exec(query).one()


# ============================================================
# VOLUNTEER ACHIEVEMENT CRUD
# ============================================================


class VolunteerAchievementCRUD:
    """CRUD operations for volunteer achievements."""

    def get_or_create_progress(
        self, db: Session, volunteer_id: int, achievement_id: int
    ) -> VolunteerAchievement:
        """Get or create achievement progress for a volunteer."""
        statement = select(VolunteerAchievement).where(
            and_(
                VolunteerAchievement.volunteer_id == volunteer_id,
                VolunteerAchievement.achievement_id == achievement_id,
            )
        )
        progress = db.exec(statement).first()

        if not progress:
            # Get achievement to extract target from criteria
            achievement = db.get(Achievement, achievement_id)
            if not achievement:
                raise ValueError(f"Achievement {achievement_id} not found")

            # Extract target from criteria
            target = self._extract_target_from_criteria(achievement)

            progress = VolunteerAchievement(
                volunteer_id=volunteer_id,
                achievement_id=achievement_id,
                current_progress=Decimal("0"),
                target_progress=target,
                is_completed=False,
                times_completed=0,
                started_at=datetime.utcnow(),
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)

        return progress

    def _extract_target_from_criteria(self, achievement: Achievement) -> Decimal:
        """Extract target value from achievement criteria."""
        criteria = achievement.criteria
        if "hours_required" in criteria:
            return Decimal(str(criteria["hours_required"]))
        elif "projects_required" in criteria:
            return Decimal(str(criteria["projects_required"]))
        elif "tasks_required" in criteria:
            return Decimal(str(criteria["tasks_required"]))
        elif "skills_required" in criteria:
            return Decimal(str(criteria["skills_required"]))
        elif "trainings_required" in criteria:
            return Decimal(str(criteria["trainings_required"]))
        elif "days_required" in criteria:
            return Decimal(str(criteria["days_required"]))
        elif "volunteers_required" in criteria:
            return Decimal(str(criteria["volunteers_required"]))
        else:
            return Decimal("1")  # Default target

    def update_progress(
        self, db: Session, volunteer_id: int, achievement_id: int, new_value: Decimal
    ) -> VolunteerAchievement:
        """Update achievement progress."""
        progress = self.get_or_create_progress(db, volunteer_id, achievement_id)
        progress.current_progress = new_value
        progress.last_progress_at = datetime.utcnow()

        # Check if completed
        if not progress.is_completed and progress.current_progress >= progress.target_progress:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            progress.times_completed += 1

        db.commit()
        db.refresh(progress)
        return progress

    def increment_progress(
        self, db: Session, volunteer_id: int, achievement_id: int, increment: Decimal
    ) -> VolunteerAchievement:
        """Increment achievement progress."""
        progress = self.get_or_create_progress(db, volunteer_id, achievement_id)
        progress.current_progress += increment
        progress.last_progress_at = datetime.utcnow()

        # Check if completed
        if not progress.is_completed and progress.current_progress >= progress.target_progress:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            progress.times_completed += 1

        db.commit()
        db.refresh(progress)
        return progress

    def complete_achievement(
        self, db: Session, volunteer_id: int, achievement_id: int
    ) -> VolunteerAchievement:
        """Mark achievement as completed."""
        progress = self.get_or_create_progress(db, volunteer_id, achievement_id)

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            progress.times_completed += 1
            progress.current_progress = progress.target_progress
        else:
            # For repeatable achievements
            achievement = db.get(Achievement, achievement_id)
            if achievement and achievement.is_repeatable:
                progress.times_completed += 1
                progress.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(progress)
        return progress

    def get_volunteer_achievements(
        self, db: Session, volunteer_id: int, completed_only: bool = False
    ) -> List[VolunteerAchievement]:
        """Get all achievement progress for a volunteer."""
        query = select(VolunteerAchievement).where(
            VolunteerAchievement.volunteer_id == volunteer_id
        )

        if completed_only:
            query = query.where(VolunteerAchievement.is_completed == True)

        query = query.order_by(VolunteerAchievement.started_at.desc())
        return list(db.exec(query).all())

    def count_completed_achievements(self, db: Session, volunteer_id: int) -> int:
        """Count completed achievements for a volunteer."""
        query = select(func.count(VolunteerAchievement.id)).where(
            and_(
                VolunteerAchievement.volunteer_id == volunteer_id,
                VolunteerAchievement.is_completed == True,
            )
        )
        return db.exec(query).one()


# ============================================================
# POINTS CRUD
# ============================================================


class PointsCRUD:
    """CRUD operations for volunteer points."""

    def get_or_create_points(self, db: Session, volunteer_id: int) -> VolunteerPoints:
        """Get or create points record for a volunteer."""
        statement = select(VolunteerPoints).where(VolunteerPoints.volunteer_id == volunteer_id)
        points = db.exec(statement).first()

        if not points:
            points = VolunteerPoints(
                volunteer_id=volunteer_id,
                total_points=0,
                current_points=0,
                rank=None,
                rank_percentile=None,
                current_streak_days=0,
                longest_streak_days=0,
                last_activity_date=None,
                updated_at=datetime.utcnow(),
            )
            db.add(points)
            db.commit()
            db.refresh(points)

        return points

    def award_points(
        self,
        db: Session,
        volunteer_id: int,
        points_change: int,
        event_type: str,
        description: str,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        awarded_by_id: Optional[int] = None,
    ) -> PointsHistory:
        """Award points to a volunteer and create history entry."""
        points_record = self.get_or_create_points(db, volunteer_id)

        # Update points (cumulative - both total and current increase)
        points_record.total_points += points_change
        points_record.current_points += points_change
        points_record.updated_at = datetime.utcnow()

        # Create history entry
        history = PointsHistory(
            volunteer_points_id=points_record.id,
            volunteer_id=volunteer_id,
            points_change=points_change,
            event_type=event_type,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type,
            balance_after=points_record.current_points,
            awarded_by_id=awarded_by_id,
            created_at=datetime.utcnow(),
        )

        db.add(history)
        db.commit()
        db.refresh(points_record)
        db.refresh(history)

        return history

    def get_points(self, db: Session, volunteer_id: int) -> Optional[VolunteerPoints]:
        """Get points record for a volunteer."""
        statement = select(VolunteerPoints).where(VolunteerPoints.volunteer_id == volunteer_id)
        return db.exec(statement).first()

    def get_points_history(
        self, db: Session, volunteer_id: int, skip: int = 0, limit: int = 50
    ) -> List[PointsHistory]:
        """Get points history for a volunteer."""
        query = (
            select(PointsHistory)
            .where(PointsHistory.volunteer_id == volunteer_id)
            .order_by(PointsHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.exec(query).all())

    def update_streak(
        self, db: Session, volunteer_id: int, activity_date: Optional[datetime] = None
    ) -> VolunteerPoints:
        """Update activity streak for a volunteer."""
        if activity_date is None:
            activity_date = datetime.utcnow()

        points_record = self.get_or_create_points(db, volunteer_id)
        today = activity_date.date()

        if points_record.last_activity_date:
            last_date = points_record.last_activity_date.date()
            days_diff = (today - last_date).days

            if days_diff == 0:
                # Same day, no change
                pass
            elif days_diff == 1:
                # Consecutive day, increment streak
                points_record.current_streak_days += 1
                if points_record.current_streak_days > points_record.longest_streak_days:
                    points_record.longest_streak_days = points_record.current_streak_days
            else:
                # Streak broken, reset
                points_record.current_streak_days = 1
        else:
            # First activity
            points_record.current_streak_days = 1
            points_record.longest_streak_days = 1

        points_record.last_activity_date = activity_date
        points_record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(points_record)
        return points_record

    def update_rankings(self, db: Session) -> int:
        """Update rankings for all volunteers. Returns count of updated records."""
        # Get all volunteers ordered by total points
        statement = (
            select(VolunteerPoints)
            .order_by(desc(VolunteerPoints.total_points), VolunteerPoints.volunteer_id)
        )
        all_points = list(db.exec(statement).all())

        total_volunteers = len(all_points)
        if total_volunteers == 0:
            return 0

        # Update ranks and percentiles
        for rank, points_record in enumerate(all_points, start=1):
            points_record.rank = rank
            # Percentile: (number of people below / total) * 100
            people_below = total_volunteers - rank
            points_record.rank_percentile = Decimal(
                str(round((people_below / total_volunteers) * 100, 2))
            )
            points_record.updated_at = datetime.utcnow()

        db.commit()
        return total_volunteers

    def get_top_volunteers(
        self, db: Session, limit: int = 100, min_points: int = 0
    ) -> List[VolunteerPoints]:
        """Get top volunteers by points."""
        query = (
            select(VolunteerPoints)
            .where(VolunteerPoints.total_points >= min_points)
            .order_by(desc(VolunteerPoints.total_points))
            .limit(limit)
        )
        return list(db.exec(query).all())


# ============================================================
# LEADERBOARD CRUD
# ============================================================


class LeaderboardCRUD:
    """CRUD operations for leaderboards."""

    def create_leaderboard(
        self,
        db: Session,
        leaderboard_type: str,
        timeframe: str,
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        rankings: List[Dict[str, Any]],
        total_participants: int,
        average_value: Optional[Decimal] = None,
        median_value: Optional[Decimal] = None,
    ) -> Leaderboard:
        """Create a new leaderboard snapshot."""
        # Mark existing leaderboards of same type/timeframe as not current
        statement = select(Leaderboard).where(
            and_(
                Leaderboard.leaderboard_type == leaderboard_type,
                Leaderboard.timeframe == timeframe,
                Leaderboard.is_current == True,
            )
        )
        existing = db.exec(statement).all()
        for lb in existing:
            lb.is_current = False

        # Create new leaderboard
        leaderboard = Leaderboard(
            leaderboard_type=leaderboard_type,
            timeframe=timeframe,
            period_start=period_start,
            period_end=period_end,
            rankings=rankings,
            generated_at=datetime.utcnow(),
            is_current=True,
            total_participants=total_participants,
            average_value=average_value,
            median_value=median_value,
        )

        db.add(leaderboard)
        db.commit()
        db.refresh(leaderboard)
        return leaderboard

    def get_current_leaderboard(
        self, db: Session, leaderboard_type: str, timeframe: str
    ) -> Optional[Leaderboard]:
        """Get current leaderboard for a type and timeframe."""
        statement = select(Leaderboard).where(
            and_(
                Leaderboard.leaderboard_type == leaderboard_type,
                Leaderboard.timeframe == timeframe,
                Leaderboard.is_current == True,
            )
        )
        return db.exec(statement).first()

    def get_leaderboard(self, db: Session, leaderboard_id: int) -> Optional[Leaderboard]:
        """Get leaderboard by ID."""
        return db.get(Leaderboard, leaderboard_id)

    def get_leaderboards(
        self,
        db: Session,
        leaderboard_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        current_only: bool = True,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Leaderboard]:
        """Get list of leaderboards with filters."""
        query = select(Leaderboard)

        if leaderboard_type:
            query = query.where(Leaderboard.leaderboard_type == leaderboard_type)
        if timeframe:
            query = query.where(Leaderboard.timeframe == timeframe)
        if current_only:
            query = query.where(Leaderboard.is_current == True)

        query = query.offset(skip).limit(limit).order_by(Leaderboard.generated_at.desc())
        return list(db.exec(query).all())

    def delete_old_leaderboards(self, db: Session, days_to_keep: int = 30) -> int:
        """Delete leaderboards older than specified days (keep current ones)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        statement = select(Leaderboard).where(
            and_(Leaderboard.generated_at < cutoff_date, Leaderboard.is_current == False)
        )
        old_leaderboards = db.exec(statement).all()

        count = 0
        for lb in old_leaderboards:
            db.delete(lb)
            count += 1

        db.commit()
        return count


# ============================================================
# SINGLETON INSTANCES
# ============================================================

badge_crud = BadgeCRUD()
achievement_crud = AchievementCRUD()
volunteer_badge_crud = VolunteerBadgeCRUD()
volunteer_achievement_crud = VolunteerAchievementCRUD()
points_crud = PointsCRUD()
leaderboard_crud = LeaderboardCRUD()
