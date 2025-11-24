"""
Gamification Service - Business Logic and Event Handling
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from statistics import median
from sqlmodel import Session, select, func

from app.crud.gamification import (
    badge_crud,
    achievement_crud,
    volunteer_badge_crud,
    volunteer_achievement_crud,
    points_crud,
    leaderboard_crud,
)
from app.models.gamification import (
    Badge,
    Achievement,
    VolunteerPoints,
    VolunteerAchievement,
)
from app.models.user import User
from app.services.event_bus import EventType, get_event_bus
from app.services.notification_service import NotificationService
from app.models.analytics import NotificationType

logger = logging.getLogger(__name__)


# ============================================================
# POINTS AWARD VALUES
# ============================================================

POINTS_CONFIG = {
    "hours_logged": 5,  # 5 points per hour
    "task_completed": 25,  # Base task completion
    "project_completed": 100,  # Project completion
    "training_completed": 25,  # Training completion
    "skill_certified": 50,  # Skill certification
    "volunteer_referred": 50,  # Referral bonus
    "badge_earned": 0,  # Badge points come from badge.points_value
    "achievement_earned": 0,  # Achievement points come from achievement.points_reward
}


# ============================================================
# CORE GAMIFICATION SERVICE
# ============================================================


class GamificationService:
    """Service for gamification business logic."""

    # ========================================
    # POINTS MANAGEMENT
    # ========================================

    @staticmethod
    def award_points(
        db: Session,
        volunteer_id: int,
        points_change: int,
        event_type: str,
        description: str,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        awarded_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Award points to a volunteer and create history entry.
        Returns the points history entry and updated balance.
        """
        try:
            # Award points and create history
            history = points_crud.award_points(
                db=db,
                volunteer_id=volunteer_id,
                points_change=points_change,
                event_type=event_type,
                description=description,
                reference_id=reference_id,
                reference_type=reference_type,
                awarded_by_id=awarded_by_id,
            )

            # Update streak
            points_crud.update_streak(db, volunteer_id)

            logger.info(
                f"Awarded {points_change} points to volunteer {volunteer_id} for {event_type}"
            )

            return {
                "volunteer_id": volunteer_id,
                "points_change": points_change,
                "new_balance": history.balance_after,
                "event_type": event_type,
                "description": description,
            }

        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            raise

    @staticmethod
    async def award_points_for_event(
        db: Session,
        volunteer_id: int,
        event_type: str,
        multiplier: float = 1.0,
        description: Optional[str] = None,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
    ):
        """Award points based on event type with optional multiplier."""
        base_points = POINTS_CONFIG.get(event_type, 0)
        points = int(base_points * multiplier)

        if points > 0:
            desc = description or f"Earned points for {event_type.replace('_', ' ')}"
            GamificationService.award_points(
                db=db,
                volunteer_id=volunteer_id,
                points_change=points,
                event_type=event_type,
                description=desc,
                reference_id=reference_id,
                reference_type=reference_type,
            )

            # Check for point-based achievements
            await GamificationService.check_achievements(db, volunteer_id)

    # ========================================
    # BADGE MANAGEMENT
    # ========================================

    @staticmethod
    async def award_badge(
        db: Session,
        volunteer_id: int,
        badge_id: int,
        earned_reason: Optional[str] = None,
        awarded_by_id: Optional[int] = None,
        skip_points: bool = False,
    ) -> Dict[str, Any]:
        """Award a badge to a volunteer if they don't already have it."""
        # Check if already earned
        if volunteer_badge_crud.has_badge(db, volunteer_id, badge_id):
            return {"status": "already_earned", "badge_id": badge_id}

        # Get badge details
        badge = badge_crud.get_badge(db, badge_id)
        if not badge or not badge.is_active:
            raise ValueError(f"Badge {badge_id} not found or inactive")

        # Award badge
        volunteer_badge = volunteer_badge_crud.award_badge(
            db=db,
            volunteer_id=volunteer_id,
            badge_id=badge_id,
            earned_reason=earned_reason,
            awarded_by_id=awarded_by_id,
        )

        # Award points for badge if not skipped
        if not skip_points and badge.points_value > 0:
            GamificationService.award_points(
                db=db,
                volunteer_id=volunteer_id,
                points_change=badge.points_value,
                event_type="badge_earned",
                description=f"Earned badge: {badge.name}",
                reference_id=badge_id,
                reference_type="badge",
            )

        logger.info(f"Awarded badge '{badge.name}' to volunteer {volunteer_id}")

        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.BADGE_EARNED,
                {
                    "volunteer_id": volunteer_id,
                    "badge_id": badge_id,
                    "badge_name": badge.name,
                    "points_awarded": badge.points_value,
                },
                user_id=volunteer_id,
            )
        except Exception as e:
            logger.error(f"Failed to publish badge earned event: {e}")

        # Send notification
        try:
            await NotificationService.create_notification(
                db=db,
                user_id=volunteer_id,
                title=f"Badge Earned: {badge.name}",
                message=f"Congratulations! You've earned the '{badge.name}' badge and {badge.points_value} points!",
                notification_type=NotificationType.achievement,
            )
        except Exception as e:
            logger.error(f"Failed to send badge notification: {e}")

        return {
            "status": "awarded",
            "badge_id": badge_id,
            "badge_name": badge.name,
            "points_awarded": badge.points_value,
        }

    # ========================================
    # ACHIEVEMENT MANAGEMENT
    # ========================================

    @staticmethod
    async def check_achievements(db: Session, volunteer_id: int):
        """Check and update all achievements for a volunteer."""
        try:
            # Get all active achievements
            achievements = achievement_crud.get_achievements(db, is_active=True, limit=1000)

            for achievement in achievements:
                await GamificationService._check_single_achievement(
                    db, volunteer_id, achievement
                )

        except Exception as e:
            logger.error(f"Error checking achievements for volunteer {volunteer_id}: {e}")

    @staticmethod
    async def _check_single_achievement(
        db: Session, volunteer_id: int, achievement: Achievement
    ):
        """Check a single achievement for a volunteer."""
        try:
            # Get or create progress
            progress = volunteer_achievement_crud.get_or_create_progress(
                db, volunteer_id, achievement.id
            )

            # Skip if already completed and not repeatable
            if progress.is_completed and not achievement.is_repeatable:
                return

            # Calculate current progress based on achievement type
            current_value = await GamificationService._calculate_achievement_progress(
                db, volunteer_id, achievement
            )

            # Update progress
            was_completed = progress.is_completed
            progress = volunteer_achievement_crud.update_progress(
                db, volunteer_id, achievement.id, current_value
            )

            # Check if newly completed
            if progress.is_completed and not was_completed:
                await GamificationService._complete_achievement(db, volunteer_id, achievement)

        except Exception as e:
            logger.error(
                f"Error checking achievement {achievement.id} for volunteer {volunteer_id}: {e}"
            )

    @staticmethod
    async def _calculate_achievement_progress(
        db: Session, volunteer_id: int, achievement: Achievement
    ) -> Decimal:
        """Calculate current progress for an achievement."""
        achievement_type = achievement.achievement_type
        criteria = achievement.criteria

        try:
            if achievement_type == "hours_logged":
                # Get total hours from time logs
                # This would need integration with time tracking module
                # For now, we'll use a placeholder
                from app.models.time_tracking import TimeLog

                statement = (
                    select(func.sum(TimeLog.hours))
                    .where(TimeLog.volunteer_id == volunteer_id)
                    .where(TimeLog.status == "approved")
                )
                result = db.exec(statement).first()
                return Decimal(str(result or 0))

            elif achievement_type == "projects_completed":
                # Get completed projects count
                # This would need integration with project module
                from app.models.project import ProjectMember

                statement = (
                    select(func.count(ProjectMember.id))
                    .where(ProjectMember.user_id == volunteer_id)
                    .where(ProjectMember.role.in_(["member", "lead"]))
                )
                result = db.exec(statement).first()
                return Decimal(str(result or 0))

            elif achievement_type == "tasks_completed":
                # Get completed tasks count
                # This would need integration with task module
                from app.models.tasks import Task

                statement = (
                    select(func.count(Task.id))
                    .where(Task.assigned_to_id == volunteer_id)
                    .where(Task.status == "completed")
                )
                result = db.exec(statement).first()
                return Decimal(str(result or 0))

            elif achievement_type == "skills_acquired":
                # Get certified skills count
                from app.models.skill import VolunteerSkill

                statement = (
                    select(func.count(VolunteerSkill.id))
                    .where(VolunteerSkill.user_id == volunteer_id)
                    .where(VolunteerSkill.is_certified == True)
                )
                result = db.exec(statement).first()
                return Decimal(str(result or 0))

            elif achievement_type == "trainings_completed":
                # Get completed trainings count
                # This would need integration with training module
                # Placeholder for now
                return Decimal("0")

            elif achievement_type == "consecutive_days":
                # Get current streak
                points_record = points_crud.get_points(db, volunteer_id)
                if points_record:
                    return Decimal(str(points_record.current_streak_days))
                return Decimal("0")

            elif achievement_type == "volunteer_referred":
                # Count referred volunteers
                # This would need referral tracking
                # Placeholder for now
                return Decimal("0")

            else:
                # Custom or unknown type
                return Decimal("0")

        except Exception as e:
            logger.error(f"Error calculating achievement progress: {e}")
            return Decimal("0")

    @staticmethod
    async def _complete_achievement(db: Session, volunteer_id: int, achievement: Achievement):
        """Handle achievement completion - award points and badge."""
        logger.info(
            f"Volunteer {volunteer_id} completed achievement '{achievement.name}'"
        )

        # Award points
        if achievement.points_reward > 0:
            GamificationService.award_points(
                db=db,
                volunteer_id=volunteer_id,
                points_change=achievement.points_reward,
                event_type="achievement_earned",
                description=f"Completed achievement: {achievement.name}",
                reference_id=achievement.id,
                reference_type="achievement",
            )

        # Award badge if specified
        if achievement.badge_id:
            await GamificationService.award_badge(
                db=db,
                volunteer_id=volunteer_id,
                badge_id=achievement.badge_id,
                earned_reason=f"Completed achievement: {achievement.name}",
                skip_points=True,  # Badge points already awarded separately
            )

        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.ACHIEVEMENT_COMPLETED,
                {
                    "volunteer_id": volunteer_id,
                    "achievement_id": achievement.id,
                    "achievement_name": achievement.name,
                    "points_awarded": achievement.points_reward,
                },
                user_id=volunteer_id,
            )
        except Exception as e:
            logger.error(f"Failed to publish achievement completed event: {e}")

        # Send notification
        try:
            await NotificationService.create_notification(
                db=db,
                user_id=volunteer_id,
                title=f"Achievement Unlocked: {achievement.name}",
                message=f"Congratulations! You've completed '{achievement.name}' and earned {achievement.points_reward} points!",
                notification_type=NotificationType.achievement,
            )
        except Exception as e:
            logger.error(f"Failed to send achievement notification: {e}")

    # ========================================
    # LEADERBOARD MANAGEMENT
    # ========================================

    @staticmethod
    def generate_points_leaderboard(
        db: Session, timeframe: str = "all_time"
    ) -> Dict[str, Any]:
        """Generate points leaderboard for a timeframe."""
        period_start, period_end = GamificationService._get_timeframe_dates(timeframe)

        if timeframe == "all_time":
            # Use VolunteerPoints directly for all-time
            statement = (
                select(VolunteerPoints)
                .where(VolunteerPoints.total_points > 0)
                .order_by(VolunteerPoints.total_points.desc())
                .limit(100)
            )
            volunteers_points = list(db.exec(statement).all())
            rankings = []

            for rank, vp in enumerate(volunteers_points, start=1):
                # Get volunteer info
                volunteer = db.get(User, vp.volunteer_id)
                if volunteer:
                    rankings.append(
                        {
                            "volunteer_id": vp.volunteer_id,
                            "rank": rank,
                            "value": vp.total_points,
                            "volunteer_name": volunteer.full_name,
                            "volunteer_avatar": volunteer.profile_picture_url,
                        }
                    )

        else:
            # For weekly/monthly, aggregate from points history
            from app.models.gamification import PointsHistory

            statement = (
                select(
                    PointsHistory.volunteer_id,
                    func.sum(PointsHistory.points_change).label("total_points"),
                )
                .where(PointsHistory.created_at >= period_start)
                .where(PointsHistory.created_at <= period_end)
                .group_by(PointsHistory.volunteer_id)
                .order_by(func.sum(PointsHistory.points_change).desc())
                .limit(100)
            )

            results = db.exec(statement).all()
            rankings = []

            for rank, result in enumerate(results, start=1):
                volunteer = db.get(User, result[0])
                if volunteer:
                    rankings.append(
                        {
                            "volunteer_id": result[0],
                            "rank": rank,
                            "value": int(result[1]),
                            "volunteer_name": volunteer.full_name,
                            "volunteer_avatar": volunteer.profile_picture_url,
                        }
                    )

        # Calculate statistics
        total_participants = len(rankings)
        values = [r["value"] for r in rankings]
        average_value = Decimal(str(sum(values) / total_participants)) if values else None
        median_value = Decimal(str(median(values))) if values else None

        # Create leaderboard
        leaderboard = leaderboard_crud.create_leaderboard(
            db=db,
            leaderboard_type="points",
            timeframe=timeframe,
            period_start=period_start,
            period_end=period_end,
            rankings=rankings,
            total_participants=total_participants,
            average_value=average_value,
            median_value=median_value,
        )

        logger.info(
            f"Generated points leaderboard for {timeframe} with {total_participants} participants"
        )

        return {
            "leaderboard_id": leaderboard.id,
            "type": "points",
            "timeframe": timeframe,
            "participants": total_participants,
        }

    @staticmethod
    def generate_hours_leaderboard(
        db: Session, timeframe: str = "all_time"
    ) -> Dict[str, Any]:
        """Generate hours leaderboard for a timeframe."""
        period_start, period_end = GamificationService._get_timeframe_dates(timeframe)

        try:
            from app.models.time_tracking import TimeLog

            statement = (
                select(
                    TimeLog.volunteer_id,
                    func.sum(TimeLog.hours).label("total_hours"),
                )
                .where(TimeLog.status == "approved")
            )

            if period_start and period_end:
                statement = statement.where(TimeLog.date >= period_start.date()).where(
                    TimeLog.date <= period_end.date()
                )

            statement = (
                statement.group_by(TimeLog.volunteer_id)
                .order_by(func.sum(TimeLog.hours).desc())
                .limit(100)
            )

            results = db.exec(statement).all()
            rankings = []

            for rank, result in enumerate(results, start=1):
                volunteer = db.get(User, result[0])
                if volunteer:
                    rankings.append(
                        {
                            "volunteer_id": result[0],
                            "rank": rank,
                            "value": float(result[1]),
                            "volunteer_name": volunteer.full_name,
                            "volunteer_avatar": volunteer.profile_picture_url,
                        }
                    )

            total_participants = len(rankings)
            values = [r["value"] for r in rankings]
            average_value = Decimal(str(sum(values) / total_participants)) if values else None
            median_value = Decimal(str(median(values))) if values else None

            leaderboard = leaderboard_crud.create_leaderboard(
                db=db,
                leaderboard_type="hours",
                timeframe=timeframe,
                period_start=period_start,
                period_end=period_end,
                rankings=rankings,
                total_participants=total_participants,
                average_value=average_value,
                median_value=median_value,
            )

            return {
                "leaderboard_id": leaderboard.id,
                "type": "hours",
                "timeframe": timeframe,
                "participants": total_participants,
            }

        except Exception as e:
            logger.error(f"Error generating hours leaderboard: {e}")
            # Return empty leaderboard on error
            leaderboard = leaderboard_crud.create_leaderboard(
                db=db,
                leaderboard_type="hours",
                timeframe=timeframe,
                period_start=period_start,
                period_end=period_end,
                rankings=[],
                total_participants=0,
            )
            return {
                "leaderboard_id": leaderboard.id,
                "type": "hours",
                "timeframe": timeframe,
                "participants": 0,
            }

    @staticmethod
    def generate_projects_leaderboard(
        db: Session, timeframe: str = "all_time"
    ) -> Dict[str, Any]:
        """Generate projects leaderboard for a timeframe."""
        period_start, period_end = GamificationService._get_timeframe_dates(timeframe)

        try:
            from app.models.project import ProjectMember

            statement = (
                select(
                    ProjectMember.user_id,
                    func.count(ProjectMember.project_id).label("total_projects"),
                )
            )

            if period_start and period_end:
                statement = statement.where(
                    ProjectMember.created_at >= period_start
                ).where(ProjectMember.created_at <= period_end)

            statement = (
                statement.group_by(ProjectMember.user_id)
                .order_by(func.count(ProjectMember.project_id).desc())
                .limit(100)
            )

            results = db.exec(statement).all()
            rankings = []

            for rank, result in enumerate(results, start=1):
                volunteer = db.get(User, result[0])
                if volunteer:
                    rankings.append(
                        {
                            "volunteer_id": result[0],
                            "rank": rank,
                            "value": int(result[1]),
                            "volunteer_name": volunteer.full_name,
                            "volunteer_avatar": volunteer.profile_picture_url,
                        }
                    )

            total_participants = len(rankings)
            values = [r["value"] for r in rankings]
            average_value = Decimal(str(sum(values) / total_participants)) if values else None
            median_value = Decimal(str(median(values))) if values else None

            leaderboard = leaderboard_crud.create_leaderboard(
                db=db,
                leaderboard_type="projects",
                timeframe=timeframe,
                period_start=period_start,
                period_end=period_end,
                rankings=rankings,
                total_participants=total_participants,
                average_value=average_value,
                median_value=median_value,
            )

            return {
                "leaderboard_id": leaderboard.id,
                "type": "projects",
                "timeframe": timeframe,
                "participants": total_participants,
            }

        except Exception as e:
            logger.error(f"Error generating projects leaderboard: {e}")
            leaderboard = leaderboard_crud.create_leaderboard(
                db=db,
                leaderboard_type="projects",
                timeframe=timeframe,
                period_start=period_start,
                period_end=period_end,
                rankings=[],
                total_participants=0,
            )
            return {
                "leaderboard_id": leaderboard.id,
                "type": "projects",
                "timeframe": timeframe,
                "participants": 0,
            }

    @staticmethod
    def update_all_leaderboards(db: Session) -> int:
        """Update all leaderboards (all types and timeframes)."""
        count = 0
        types = ["points", "hours", "projects"]
        timeframes = ["all_time", "weekly", "monthly"]

        for lb_type in types:
            for timeframe in timeframes:
                try:
                    if lb_type == "points":
                        GamificationService.generate_points_leaderboard(db, timeframe)
                    elif lb_type == "hours":
                        GamificationService.generate_hours_leaderboard(db, timeframe)
                    elif lb_type == "projects":
                        GamificationService.generate_projects_leaderboard(db, timeframe)
                    count += 1
                except Exception as e:
                    logger.error(f"Error generating {lb_type}/{timeframe} leaderboard: {e}")

        # Update volunteer rankings
        points_crud.update_rankings(db)

        logger.info(f"Updated {count} leaderboards")
        return count

    @staticmethod
    def _get_timeframe_dates(timeframe: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end dates for a timeframe."""
        now = datetime.utcnow()

        if timeframe == "weekly":
            # Current week (Monday to Sunday)
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return start, end

        elif timeframe == "monthly":
            # Current month
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(seconds=1)
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(seconds=1)
            return start, end

        else:  # all_time
            return None, None


# ============================================================
# EVENT SUBSCRIBERS
# ============================================================


async def on_task_completed(event_payload: Dict[str, Any]):
    """Handle task completed event."""
    try:
        from app.database.engine import get_db

        data = event_payload.get("data", {})
        volunteer_id = data.get("assigned_to_id")

        if not volunteer_id:
            return

        db_gen = get_db()
        db = next(db_gen)
        try:
            await GamificationService.award_points_for_event(
                db=db,
                volunteer_id=volunteer_id,
                event_type="task_completed",
                description=f"Completed task: {data.get('task_name', 'Unknown')}",
                reference_id=data.get("task_id"),
                reference_type="task",
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error in task completed event handler: {e}")


async def on_timelog_approved(event_payload: Dict[str, Any]):
    """Handle time log approved event."""
    try:
        from app.database.engine import get_db

        data = event_payload.get("data", {})
        volunteer_id = data.get("volunteer_id")
        hours = data.get("hours", 0)

        if not volunteer_id or hours <= 0:
            return

        db_gen = get_db()
        db = next(db_gen)
        try:
            await GamificationService.award_points_for_event(
                db=db,
                volunteer_id=volunteer_id,
                event_type="hours_logged",
                multiplier=float(hours),
                description=f"Logged {hours} hours of volunteer work",
                reference_id=data.get("timelog_id"),
                reference_type="timelog",
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error in timelog approved event handler: {e}")


async def on_training_completed(event_payload: Dict[str, Any]):
    """Handle training completed event."""
    try:
        from app.database.engine import get_db

        data = event_payload.get("data", {})
        volunteer_id = data.get("volunteer_id")

        if not volunteer_id:
            return

        db_gen = get_db()
        db = next(db_gen)
        try:
            await GamificationService.award_points_for_event(
                db=db,
                volunteer_id=volunteer_id,
                event_type="training_completed",
                description=f"Completed training: {data.get('training_name', 'Unknown')}",
                reference_id=data.get("training_id"),
                reference_type="training",
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error in training completed event handler: {e}")


async def on_skill_added(event_payload: Dict[str, Any]):
    """Handle skill added event (certified)."""
    try:
        from app.database.engine import get_db

        data = event_payload.get("data", {})
        volunteer_id = data.get("volunteer_id")
        is_certified = data.get("is_certified", False)

        if not volunteer_id or not is_certified:
            return

        db_gen = get_db()
        db = next(db_gen)
        try:
            await GamificationService.award_points_for_event(
                db=db,
                volunteer_id=volunteer_id,
                event_type="skill_certified",
                description=f"Certified in skill: {data.get('skill_name', 'Unknown')}",
                reference_id=data.get("skill_id"),
                reference_type="skill",
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error in skill added event handler: {e}")


def initialize_gamification_events():
    """Initialize event subscriptions for gamification."""
    try:
        event_bus = get_event_bus()

        # Subscribe to relevant events
        event_bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)
        event_bus.subscribe(EventType.TIMELOG_APPROVED, on_timelog_approved)
        event_bus.subscribe(EventType.TRAINING_COMPLETED, on_training_completed)
        event_bus.subscribe(EventType.SKILL_ADDED, on_skill_added)

        logger.info("Gamification event subscriptions initialized")

    except Exception as e:
        logger.error(f"Failed to initialize gamification events: {e}")
