"""
Gamification Module - API Routes
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional
from decimal import Decimal

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.gamification import (
    badge_crud,
    achievement_crud,
    volunteer_badge_crud,
    volunteer_achievement_crud,
    points_crud,
    leaderboard_crud,
)
from app.services.gamification_service import GamificationService
from app.schemas.gamification import (
    # Badge schemas
    Badge,
    BadgeCreate,
    BadgeUpdate,
    BadgeSummary,
    BadgeCategoryList,
    # Volunteer Badge schemas
    VolunteerBadgeAward,
    VolunteerBadgeWithDetails,
    BadgeShowcaseToggle,
    VolunteerBadgeCollection,
    # Achievement schemas
    Achievement,
    AchievementCreate,
    AchievementUpdate,
    AchievementSummary,
    AchievementTypeList,
    AchievementProgress,
    VolunteerAchievementProgress,
    # Points schemas
    PointsSummary,
    PointsHistoryEntry,
    PointsAwardRequest,
    PointsAwardResponse,
    StreakInfo,
    GlobalRanking,
    # Leaderboard schemas
    Leaderboard,
    VolunteerLeaderboardPosition,
    # Statistics schemas
    GamificationStats,
    VolunteerGamificationSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/gamification",
    tags=["gamification"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


# ============================================================
# BADGE ENDPOINTS
# ============================================================


@router.get("/badges", response_model=List[BadgeSummary])
async def list_badges(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rarity: Optional[str] = Query(None, description="Filter by rarity"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all badges with optional filters."""
    # Only show secret badges to admins
    include_secret = current_user.user_type.name == "admin"

    badges = badge_crud.get_badges(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        rarity=rarity,
        is_active=is_active,
        include_secret=include_secret,
    )
    return badges


@router.get("/badges/categories", response_model=BadgeCategoryList)
async def get_badge_categories(
    current_user: User = Depends(get_current_user),
):
    """Get list of available badge categories."""
    return BadgeCategoryList()


@router.get("/badges/{badge_id}", response_model=Badge)
async def get_badge(
    badge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get badge details by ID."""
    badge = badge_crud.get_badge(db, badge_id)
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found"
        )

    # Hide secret badges from non-admins who haven't earned it
    if badge.is_secret and current_user.user_type.name != "admin":
        has_badge = volunteer_badge_crud.has_badge(db, current_user.id, badge_id)
        if not has_badge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found"
            )

    return badge


@router.post("/badges", response_model=Badge, status_code=status.HTTP_201_CREATED)
async def create_badge(
    badge_data: BadgeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new badge (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create badges",
        )

    # Check for duplicate name
    existing = badge_crud.get_badge_by_name(db, badge_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Badge with name '{badge_data.name}' already exists",
        )

    badge = badge_crud.create_badge(db, badge_data)
    return badge


@router.put("/badges/{badge_id}", response_model=Badge)
async def update_badge(
    badge_id: int,
    badge_data: BadgeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a badge (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update badges",
        )

    badge = badge_crud.update_badge(db, badge_id, badge_data)
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found"
        )

    return badge


@router.delete("/badges/{badge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_badge(
    badge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete a badge (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete badges",
        )

    success = badge_crud.delete_badge(db, badge_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found"
        )

    return None


# ============================================================
# VOLUNTEER BADGE ENDPOINTS
# ============================================================


@router.get("/volunteers/{volunteer_id}/badges", response_model=VolunteerBadgeCollection)
async def get_volunteer_badges(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all badges earned by a volunteer."""
    # Volunteers can only view their own badges, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these badges",
        )

    volunteer_badges = volunteer_badge_crud.get_volunteer_badges(db, volunteer_id)
    total_badges = len(volunteer_badges)

    # Build response with badge details
    badges_with_details = []
    showcased_badges = []

    for vb in volunteer_badges:
        badge = badge_crud.get_badge(db, vb.badge_id)
        if badge:
            badge_detail = VolunteerBadgeWithDetails(
                id=vb.id,
                volunteer_id=vb.volunteer_id,
                badge_id=vb.badge_id,
                earned_at=vb.earned_at,
                earned_reason=vb.earned_reason,
                awarded_by_id=vb.awarded_by_id,
                is_showcased=vb.is_showcased,
                badge=BadgeSummary(
                    id=badge.id,
                    name=badge.name,
                    category=badge.category,
                    rarity=badge.rarity,
                    color=badge.color,
                    icon_url=badge.icon_url,
                    points_value=badge.points_value,
                    is_secret=badge.is_secret,
                ),
            )
            badges_with_details.append(badge_detail)

            if vb.is_showcased:
                showcased_badges.append(badge.name)

    return VolunteerBadgeCollection(
        total_badges=total_badges,
        showcased_badges=showcased_badges,
        badges=badges_with_details,
    )


@router.post("/volunteers/{volunteer_id}/badges/award", response_model=dict)
async def award_badge_to_volunteer(
    volunteer_id: int,
    award_data: VolunteerBadgeAward,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually award a badge to a volunteer (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manually award badges",
        )

    try:
        result = await GamificationService.award_badge(
            db=db,
            volunteer_id=volunteer_id,
            badge_id=award_data.badge_id,
            earned_reason=award_data.earned_reason,
            awarded_by_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error awarding badge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to award badge",
        )


@router.put("/volunteers/{volunteer_id}/badges/{badge_id}/showcase")
async def toggle_badge_showcase(
    volunteer_id: int,
    badge_id: int,
    toggle_data: BadgeShowcaseToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle badge showcase status."""
    # Only the volunteer themselves can toggle showcase
    if current_user.id != volunteer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only showcase your own badges",
        )

    volunteer_badge = volunteer_badge_crud.toggle_showcase(
        db, volunteer_id, badge_id, toggle_data.is_showcased
    )
    if not volunteer_badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't earned this badge",
        )

    return {"message": "Badge showcase updated", "is_showcased": toggle_data.is_showcased}


# ============================================================
# ACHIEVEMENT ENDPOINTS
# ============================================================


@router.get("/achievements", response_model=List[AchievementSummary])
async def list_achievements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    achievement_type: Optional[str] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all achievements with optional filters."""
    # Only show secret achievements to admins
    include_secret = current_user.user_type.name == "admin"

    achievements = achievement_crud.get_achievements(
        db=db,
        skip=skip,
        limit=limit,
        achievement_type=achievement_type,
        is_active=is_active,
        include_secret=include_secret,
    )
    return achievements


@router.get("/achievements/types", response_model=AchievementTypeList)
async def get_achievement_types(
    current_user: User = Depends(get_current_user),
):
    """Get list of available achievement types."""
    return AchievementTypeList()


@router.get("/achievements/{achievement_id}", response_model=Achievement)
async def get_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get achievement details by ID."""
    achievement = achievement_crud.get_achievement(db, achievement_id)
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found"
        )

    # Hide secret achievements from non-admins who haven't completed it
    if achievement.is_secret and current_user.user_type.name != "admin":
        progress = volunteer_achievement_crud.get_or_create_progress(
            db, current_user.id, achievement_id
        )
        if not progress.is_completed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found"
            )

    return achievement


@router.post(
    "/achievements", response_model=Achievement, status_code=status.HTTP_201_CREATED
)
async def create_achievement(
    achievement_data: AchievementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new achievement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create achievements",
        )

    # Check for duplicate name
    existing = achievement_crud.get_achievement_by_name(db, achievement_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Achievement with name '{achievement_data.name}' already exists",
        )

    # Validate badge_id if provided
    if achievement_data.badge_id:
        badge = badge_crud.get_badge(db, achievement_data.badge_id)
        if not badge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Badge {achievement_data.badge_id} not found",
            )

    achievement = achievement_crud.create_achievement(db, achievement_data)
    return achievement


@router.put("/achievements/{achievement_id}", response_model=Achievement)
async def update_achievement(
    achievement_id: int,
    achievement_data: AchievementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an achievement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update achievements",
        )

    achievement = achievement_crud.update_achievement(db, achievement_id, achievement_data)
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found"
        )

    return achievement


@router.delete("/achievements/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete an achievement (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete achievements",
        )

    success = achievement_crud.delete_achievement(db, achievement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found"
        )

    return None


# ============================================================
# VOLUNTEER ACHIEVEMENT ENDPOINTS
# ============================================================


@router.get(
    "/volunteers/{volunteer_id}/achievements", response_model=VolunteerAchievementProgress
)
async def get_volunteer_achievements(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get achievement progress for a volunteer."""
    # Volunteers can only view their own progress, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this progress",
        )

    # Get all achievements
    all_achievements = achievement_crud.get_achievements(db, is_active=True, limit=1000)
    total_achievements = len(all_achievements)

    # Get volunteer's progress for each
    progress_list = []
    completed_count = 0
    in_progress_count = 0

    for achievement in all_achievements:
        # Skip secret achievements unless completed
        if achievement.is_secret:
            progress = volunteer_achievement_crud.get_or_create_progress(
                db, volunteer_id, achievement.id
            )
            if not progress.is_completed and current_user.user_type.name != "admin":
                continue

        progress = volunteer_achievement_crud.get_or_create_progress(
            db, volunteer_id, achievement.id
        )

        # Calculate progress percentage
        if progress.target_progress > 0:
            progress_pct = float(
                (progress.current_progress / progress.target_progress) * 100
            )
            progress_pct = min(progress_pct, 100.0)
        else:
            progress_pct = 0.0

        # Get badge if exists
        badge_summary = None
        if achievement.badge_id:
            badge = badge_crud.get_badge(db, achievement.badge_id)
            if badge:
                badge_summary = BadgeSummary(
                    id=badge.id,
                    name=badge.name,
                    category=badge.category,
                    rarity=badge.rarity,
                    color=badge.color,
                    icon_url=badge.icon_url,
                    points_value=badge.points_value,
                    is_secret=badge.is_secret,
                )

        achievement_progress = AchievementProgress(
            id=achievement.id,
            name=achievement.name,
            description=achievement.description,
            achievement_type=achievement.achievement_type,
            points_reward=achievement.points_reward,
            is_completed=progress.is_completed,
            completed_at=progress.completed_at,
            current_progress=progress.current_progress,
            target_progress=progress.target_progress,
            progress_percentage=progress_pct,
            times_completed=progress.times_completed,
            badge=badge_summary,
        )

        progress_list.append(achievement_progress)

        if progress.is_completed:
            completed_count += 1
        else:
            in_progress_count += 1

    return VolunteerAchievementProgress(
        total_achievements=total_achievements,
        completed=completed_count,
        in_progress=in_progress_count,
        achievements=progress_list,
    )


@router.get(
    "/volunteers/{volunteer_id}/achievements/{achievement_id}/progress",
    response_model=AchievementProgress,
)
async def get_achievement_progress(
    volunteer_id: int,
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific achievement progress for a volunteer."""
    # Volunteers can only view their own progress, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this progress",
        )

    achievement = achievement_crud.get_achievement(db, achievement_id)
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found"
        )

    progress = volunteer_achievement_crud.get_or_create_progress(
        db, volunteer_id, achievement_id
    )

    # Calculate progress percentage
    if progress.target_progress > 0:
        progress_pct = float((progress.current_progress / progress.target_progress) * 100)
        progress_pct = min(progress_pct, 100.0)
    else:
        progress_pct = 0.0

    # Get badge if exists
    badge_summary = None
    if achievement.badge_id:
        badge = badge_crud.get_badge(db, achievement.badge_id)
        if badge:
            badge_summary = BadgeSummary(
                id=badge.id,
                name=badge.name,
                category=badge.category,
                rarity=badge.rarity,
                color=badge.color,
                icon_url=badge.icon_url,
                points_value=badge.points_value,
                is_secret=badge.is_secret,
            )

    return AchievementProgress(
        id=achievement.id,
        name=achievement.name,
        description=achievement.description,
        achievement_type=achievement.achievement_type,
        points_reward=achievement.points_reward,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at,
        current_progress=progress.current_progress,
        target_progress=progress.target_progress,
        progress_percentage=progress_pct,
        times_completed=progress.times_completed,
        badge=badge_summary,
    )


# ============================================================
# POINTS ENDPOINTS
# ============================================================


@router.get("/volunteers/{volunteer_id}/points", response_model=PointsSummary)
async def get_volunteer_points(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get points summary for a volunteer."""
    # Volunteers can only view their own points, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these points",
        )

    points_record = points_crud.get_points(db, volunteer_id)
    if not points_record:
        points_record = points_crud.get_or_create_points(db, volunteer_id)

    # Get recent history
    recent_history = points_crud.get_points_history(db, volunteer_id, skip=0, limit=10)

    return PointsSummary(
        id=points_record.id,
        volunteer_id=points_record.volunteer_id,
        total_points=points_record.total_points,
        current_points=points_record.current_points,
        rank=points_record.rank,
        rank_percentile=points_record.rank_percentile,
        current_streak_days=points_record.current_streak_days,
        longest_streak_days=points_record.longest_streak_days,
        last_activity_date=points_record.last_activity_date,
        updated_at=points_record.updated_at,
        recent_history=[
            PointsHistoryEntry(
                id=h.id,
                points_change=h.points_change,
                event_type=h.event_type,
                description=h.description,
                reference_id=h.reference_id,
                reference_type=h.reference_type,
                balance_after=h.balance_after,
                awarded_by_id=h.awarded_by_id,
                created_at=h.created_at,
            )
            for h in recent_history
        ],
    )


@router.get("/volunteers/{volunteer_id}/points/history", response_model=List[PointsHistoryEntry])
async def get_points_history(
    volunteer_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full points history for a volunteer."""
    # Volunteers can only view their own history, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this history",
        )

    history = points_crud.get_points_history(db, volunteer_id, skip=skip, limit=limit)
    return history


@router.post("/volunteers/{volunteer_id}/points/award", response_model=PointsAwardResponse)
async def award_points_manually(
    volunteer_id: int,
    award_data: PointsAwardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually award points to a volunteer (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manually award points",
        )

    # Verify volunteer exists
    volunteer = db.get(User, volunteer_id)
    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer not found"
        )

    try:
        result = GamificationService.award_points(
            db=db,
            volunteer_id=volunteer_id,
            points_change=award_data.points,
            event_type=award_data.event_type,
            description=award_data.description,
            reference_id=award_data.reference_id,
            reference_type=award_data.reference_type,
            awarded_by_id=current_user.id,
        )

        # Check achievements after manual award
        await GamificationService.check_achievements(db, volunteer_id)

        return PointsAwardResponse(
            volunteer_id=result["volunteer_id"],
            points_change=result["points_change"],
            new_balance=result["new_balance"],
            event_type=result["event_type"],
            description=result["description"],
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Error awarding points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to award points",
        )


@router.get("/volunteers/{volunteer_id}/streak", response_model=StreakInfo)
async def get_volunteer_streak(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get streak information for a volunteer."""
    # Volunteers can only view their own streak, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this streak",
        )

    points_record = points_crud.get_points(db, volunteer_id)
    if not points_record:
        points_record = points_crud.get_or_create_points(db, volunteer_id)

    # Check if active today
    from datetime import datetime

    is_active_today = False
    if points_record.last_activity_date:
        today = datetime.utcnow().date()
        last_date = points_record.last_activity_date.date()
        is_active_today = today == last_date

    return StreakInfo(
        volunteer_id=volunteer_id,
        current_streak_days=points_record.current_streak_days,
        longest_streak_days=points_record.longest_streak_days,
        last_activity_date=points_record.last_activity_date,
        is_active_today=is_active_today,
    )


@router.get("/points/rankings", response_model=List[GlobalRanking])
async def get_global_rankings(
    limit: int = Query(100, ge=1, le=100, description="Max rankings to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get global rankings by points."""
    top_volunteers = points_crud.get_top_volunteers(db, limit=limit)

    rankings = []
    for vp in top_volunteers:
        volunteer = db.get(User, vp.volunteer_id)
        if volunteer:
            badges_count = volunteer_badge_crud.count_volunteer_badges(db, vp.volunteer_id)
            achievements_count = volunteer_achievement_crud.count_completed_achievements(
                db, vp.volunteer_id
            )

            rankings.append(
                GlobalRanking(
                    rank=vp.rank or 0,
                    volunteer_id=vp.volunteer_id,
                    volunteer_name=volunteer.full_name,
                    volunteer_avatar=volunteer.profile_picture_url,
                    total_points=vp.total_points,
                    badges_count=badges_count,
                    achievements_count=achievements_count,
                )
            )

    return rankings


# ============================================================
# LEADERBOARD ENDPOINTS
# ============================================================


@router.get("/leaderboards/{leaderboard_type}", response_model=Leaderboard)
async def get_leaderboard(
    leaderboard_type: str,
    timeframe: str = Query("all_time", description="all_time, weekly, or monthly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get leaderboard by type and timeframe."""
    leaderboard = leaderboard_crud.get_current_leaderboard(db, leaderboard_type, timeframe)
    if not leaderboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No leaderboard found for {leaderboard_type}/{timeframe}",
        )

    return leaderboard


@router.post("/leaderboards/generate", response_model=dict)
async def generate_leaderboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually generate/update all leaderboards (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can generate leaderboards",
        )

    try:
        count = GamificationService.update_all_leaderboards(db)
        return {"message": f"Successfully generated {count} leaderboards"}
    except Exception as e:
        logger.error(f"Error generating leaderboards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate leaderboards",
        )


@router.get(
    "/leaderboards/volunteer/{volunteer_id}/position",
    response_model=List[VolunteerLeaderboardPosition],
)
async def get_volunteer_leaderboard_positions(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get volunteer's position across all leaderboards."""
    # Volunteers can only view their own position, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these positions",
        )

    positions = []
    types = ["points", "hours", "projects"]
    timeframes = ["all_time", "weekly", "monthly"]

    for lb_type in types:
        for timeframe in timeframes:
            leaderboard = leaderboard_crud.get_current_leaderboard(db, lb_type, timeframe)
            if leaderboard:
                # Find volunteer in rankings
                volunteer_rank = None
                volunteer_value = None

                for ranking in leaderboard.rankings:
                    if ranking["volunteer_id"] == volunteer_id:
                        volunteer_rank = ranking["rank"]
                        volunteer_value = ranking["value"]
                        break

                # Calculate percentile if ranked
                percentile = None
                if volunteer_rank and leaderboard.total_participants > 0:
                    people_below = leaderboard.total_participants - volunteer_rank
                    percentile = Decimal(
                        str(round((people_below / leaderboard.total_participants) * 100, 2))
                    )

                positions.append(
                    VolunteerLeaderboardPosition(
                        volunteer_id=volunteer_id,
                        leaderboard_type=lb_type,
                        timeframe=timeframe,
                        rank=volunteer_rank,
                        value=volunteer_value,
                        total_participants=leaderboard.total_participants,
                        percentile=percentile,
                    )
                )

    return positions


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================


@router.get("/stats", response_model=GamificationStats)
async def get_gamification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get overall gamification statistics (admin only)."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view overall statistics",
        )

    # Count totals
    total_badges = badge_crud.count_badges(db, is_active=True)
    total_achievements = achievement_crud.count_achievements(db, is_active=True)

    # Total points awarded
    from app.models.gamification import PointsHistory

    statement = select(func.sum(PointsHistory.points_change)).where(
        PointsHistory.points_change > 0
    )
    total_points_awarded = db.exec(statement).first() or 0

    # Total badges earned
    statement = select(func.count(VolunteerBadge.id))
    total_badges_earned = db.exec(statement).first() or 0

    # Total achievements completed
    statement = select(func.count(VolunteerAchievement.id)).where(
        VolunteerAchievement.is_completed == True
    )
    total_achievements_completed = db.exec(statement).first() or 0

    # Active volunteers (with points)
    statement = select(func.count(VolunteerPoints.id)).where(
        VolunteerPoints.total_points > 0
    )
    active_volunteers = db.exec(statement).first() or 0

    # Average points per volunteer
    avg_points_per_volunteer = Decimal("0")
    if active_volunteers > 0:
        avg_points_per_volunteer = Decimal(str(total_points_awarded / active_volunteers))

    # Most earned badge
    statement = (
        select(VolunteerBadge.badge_id, func.count(VolunteerBadge.id).label("count"))
        .group_by(VolunteerBadge.badge_id)
        .order_by(func.count(VolunteerBadge.id).desc())
        .limit(1)
    )
    result = db.exec(statement).first()
    most_earned_badge = None
    if result:
        badge = badge_crud.get_badge(db, result[0])
        if badge:
            most_earned_badge = BadgeSummary(
                id=badge.id,
                name=badge.name,
                category=badge.category,
                rarity=badge.rarity,
                color=badge.color,
                icon_url=badge.icon_url,
                points_value=badge.points_value,
                is_secret=badge.is_secret,
            )

    # Most completed achievement
    statement = (
        select(
            VolunteerAchievement.achievement_id,
            func.count(VolunteerAchievement.id).label("count"),
        )
        .where(VolunteerAchievement.is_completed == True)
        .group_by(VolunteerAchievement.achievement_id)
        .order_by(func.count(VolunteerAchievement.id).desc())
        .limit(1)
    )
    result = db.exec(statement).first()
    most_completed_achievement = None
    if result:
        achievement = achievement_crud.get_achievement(db, result[0])
        if achievement:
            most_completed_achievement = AchievementSummary(
                id=achievement.id,
                name=achievement.name,
                achievement_type=achievement.achievement_type,
                points_reward=achievement.points_reward,
                is_repeatable=achievement.is_repeatable,
                is_secret=achievement.is_secret,
            )

    return GamificationStats(
        total_badges=total_badges,
        total_achievements=total_achievements,
        total_points_awarded=total_points_awarded,
        total_badges_earned=total_badges_earned,
        total_achievements_completed=total_achievements_completed,
        active_volunteers=active_volunteers,
        avg_points_per_volunteer=avg_points_per_volunteer,
        most_earned_badge=most_earned_badge,
        most_completed_achievement=most_completed_achievement,
    )


@router.get("/stats/volunteer/{volunteer_id}", response_model=VolunteerGamificationSummary)
async def get_volunteer_gamification_summary(
    volunteer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete gamification summary for a volunteer."""
    # Volunteers can only view their own summary, admins can view all
    if current_user.id != volunteer_id and current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this summary",
        )

    # Get points
    points_record = points_crud.get_points(db, volunteer_id)
    if not points_record:
        points_record = points_crud.get_or_create_points(db, volunteer_id)

    # Count badges and get recent ones
    badges_earned = volunteer_badge_crud.count_volunteer_badges(db, volunteer_id)
    volunteer_badges = volunteer_badge_crud.get_volunteer_badges(db, volunteer_id)
    recent_badges = []
    for vb in volunteer_badges[:5]:  # Last 5 badges
        badge = badge_crud.get_badge(db, vb.badge_id)
        if badge:
            recent_badges.append(
                VolunteerBadgeWithDetails(
                    id=vb.id,
                    volunteer_id=vb.volunteer_id,
                    badge_id=vb.badge_id,
                    earned_at=vb.earned_at,
                    earned_reason=vb.earned_reason,
                    awarded_by_id=vb.awarded_by_id,
                    is_showcased=vb.is_showcased,
                    badge=BadgeSummary(
                        id=badge.id,
                        name=badge.name,
                        category=badge.category,
                        rarity=badge.rarity,
                        color=badge.color,
                        icon_url=badge.icon_url,
                        points_value=badge.points_value,
                        is_secret=badge.is_secret,
                    ),
                )
            )

    # Count achievements
    achievements_completed = volunteer_achievement_crud.count_completed_achievements(
        db, volunteer_id
    )

    # Get achievement progress (top 5 in-progress)
    all_achievements = achievement_crud.get_achievements(db, is_active=True, limit=100)
    achievement_progress = []
    for achievement in all_achievements[:5]:
        progress = volunteer_achievement_crud.get_or_create_progress(
            db, volunteer_id, achievement.id
        )
        if not progress.is_completed:
            progress_pct = (
                float((progress.current_progress / progress.target_progress) * 100)
                if progress.target_progress > 0
                else 0.0
            )
            badge_summary = None
            if achievement.badge_id:
                badge = badge_crud.get_badge(db, achievement.badge_id)
                if badge:
                    badge_summary = BadgeSummary(
                        id=badge.id,
                        name=badge.name,
                        category=badge.category,
                        rarity=badge.rarity,
                        color=badge.color,
                        icon_url=badge.icon_url,
                        points_value=badge.points_value,
                        is_secret=badge.is_secret,
                    )
            achievement_progress.append(
                AchievementProgress(
                    id=achievement.id,
                    name=achievement.name,
                    description=achievement.description,
                    achievement_type=achievement.achievement_type,
                    points_reward=achievement.points_reward,
                    is_completed=False,
                    completed_at=None,
                    current_progress=progress.current_progress,
                    target_progress=progress.target_progress,
                    progress_percentage=progress_pct,
                    times_completed=0,
                    badge=badge_summary,
                )
            )

    # Get leaderboard positions
    leaderboard_positions = []
    for lb_type in ["points", "hours", "projects"]:
        for timeframe in ["all_time", "weekly", "monthly"]:
            leaderboard = leaderboard_crud.get_current_leaderboard(db, lb_type, timeframe)
            if leaderboard:
                volunteer_rank = None
                volunteer_value = None
                for ranking in leaderboard.rankings:
                    if ranking["volunteer_id"] == volunteer_id:
                        volunteer_rank = ranking["rank"]
                        volunteer_value = ranking["value"]
                        break

                percentile = None
                if volunteer_rank and leaderboard.total_participants > 0:
                    people_below = leaderboard.total_participants - volunteer_rank
                    percentile = Decimal(
                        str(round((people_below / leaderboard.total_participants) * 100, 2))
                    )

                leaderboard_positions.append(
                    VolunteerLeaderboardPosition(
                        volunteer_id=volunteer_id,
                        leaderboard_type=lb_type,
                        timeframe=timeframe,
                        rank=volunteer_rank,
                        value=volunteer_value,
                        total_participants=leaderboard.total_participants,
                        percentile=percentile,
                    )
                )

    return VolunteerGamificationSummary(
        volunteer_id=volunteer_id,
        points=points_record,
        badges_earned=badges_earned,
        achievements_completed=achievements_completed,
        recent_badges=recent_badges,
        achievement_progress=achievement_progress,
        leaderboard_positions=leaderboard_positions,
    )
