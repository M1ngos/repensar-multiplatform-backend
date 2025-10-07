# volunteers.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional
from datetime import date

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.volunteer import Volunteer
from app.crud.volunteer import (
    volunteer_crud, volunteer_skill_crud, volunteer_time_log_crud, volunteer_stats_crud
)
from app.schemas.volunteer import (
    # Volunteer schemas
    VolunteerRegistration, VolunteerCreate, VolunteerUpdate, 
    VolunteerProfile, Volunteer as VolunteerSchema, VolunteerSummary, VolunteerStats,
    
    # Skill schemas
    VolunteerSkill, VolunteerSkillAssignmentCreate, VolunteerSkillAssignmentUpdate,
    VolunteerSkillAssignment,
    
    # Time tracking schemas
    VolunteerTimeLogCreate, VolunteerTimeLogUpdate, VolunteerTimeLogApproval,
    VolunteerTimeLog
)

router = APIRouter(
    prefix="/volunteers",
    tags=["volunteers"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# ========================================
# VOLUNTEER PROFILE ENDPOINTS
# ========================================

@router.post("/register", response_model=dict)
def register_volunteer(
    registration_data: VolunteerRegistration,
    db: Session = Depends(get_db)
):
    """Register a new volunteer with user account creation."""
    from app.core.auth import get_password_hash, create_user_with_type
    from app.crud.volunteer import volunteer_skill_crud
    
    try:
        # Create user account
        user_data = {
            "name": registration_data.name,
            "email": registration_data.email,
            "password_hash": get_password_hash(registration_data.password),
            "phone": registration_data.phone,
            "user_type": "volunteer"
        }
        
        user = create_user_with_type(db, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate volunteer ID
        volunteer_count = len(volunteer_crud.get_volunteers(db))
        volunteer_id = f"VLT{volunteer_count + 1:03d}"
        
        # Create volunteer profile
        volunteer_data = VolunteerCreate(
            user_id=user.id,
            volunteer_id=volunteer_id,
            date_of_birth=registration_data.date_of_birth,
            gender=registration_data.gender,
            address=registration_data.address,
            city=registration_data.city,
            postal_code=registration_data.postal_code,
            emergency_contact_name=registration_data.emergency_contact_name,
            emergency_contact_phone=registration_data.emergency_contact_phone,
            emergency_contact_relationship=registration_data.emergency_contact_relationship,
            availability=registration_data.availability,
            joined_date=date.today(),
            motivation=registration_data.motivation
        )
        
        volunteer = volunteer_crud.create_volunteer(db, volunteer_data)
        
        # Assign skills if provided
        for skill_id in registration_data.skill_ids:
            skill_assignment = VolunteerSkillAssignmentCreate(skill_id=skill_id)
            volunteer_skill_crud.assign_skill_to_volunteer(db, volunteer.id, skill_assignment)
        
        return {
            "message": "Volunteer registered successfully",
            "volunteer_id": volunteer.volunteer_id,
            "user_id": user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/", response_model=List[VolunteerSummary])
def get_volunteers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(active|inactive|suspended)$"),
    skill_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of volunteers with filtering options."""
    try:
        volunteers = volunteer_crud.get_volunteers(
            db, skip=skip, limit=limit, status=status, skill_id=skill_id, search=search
        )
        
        # Convert to summary format with additional info
        volunteer_summaries = []
        for volunteer in volunteers:
            # Get user info
            user_info = volunteer_crud.get_volunteer_profile_with_details(db, volunteer.id)
            if user_info:
                user = user_info["user"]
                skills_count = len(user_info["skills"])
                
                # Get recent activity (last time log)
                recent_logs = volunteer_time_log_crud.get_volunteer_time_logs(
                    db, volunteer.id, limit=1
                )
                recent_activity = recent_logs[0].created_at if recent_logs else None
                
                summary = VolunteerSummary(
                    id=volunteer.id,
                    volunteer_id=volunteer.volunteer_id,
                    name=user.name,
                    email=user.email,
                    volunteer_status=volunteer.volunteer_status,
                    total_hours_contributed=float(volunteer.total_hours_contributed),
                    joined_date=volunteer.joined_date,
                    skills_count=skills_count,
                    recent_activity=recent_activity
                )
                volunteer_summaries.append(summary)
        
        return volunteer_summaries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteers: {str(e)}"
        )

@router.get("/stats", response_model=VolunteerStats)
def get_volunteer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get volunteer statistics dashboard."""
    try:
        stats = volunteer_stats_crud.get_volunteer_stats(db)
        return VolunteerStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer stats: {str(e)}"
        )

@router.get("/{volunteer_id}", response_model=VolunteerProfile)
def get_volunteer_profile(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed volunteer profile."""
    try:
        profile_data = volunteer_crud.get_volunteer_profile_with_details(db, volunteer_id)
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        volunteer = profile_data["volunteer"]
        user = profile_data["user"]
        skills = profile_data["skills"]
        
        # Build profile response
        profile = VolunteerProfile(
            **volunteer.model_dump(),
            name=user.name,
            email=user.email,
            phone=user.phone,
            skills=[
                VolunteerSkillAssignment(
                    **skill_assignment.model_dump(),
                    skill=VolunteerSkill(**skill.model_dump())
                )
                for skill_assignment, skill in skills
            ]
        )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer profile: {str(e)}"
        )

@router.put("/{volunteer_id}", response_model=VolunteerSchema)
def update_volunteer_profile(
    volunteer_id: int,
    update_data: VolunteerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update volunteer profile."""
    try:
        # Check if volunteer exists
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        # Check permissions (volunteer can only update their own profile, or admin/staff)
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this volunteer profile"
            )
        
        updated_volunteer = volunteer_crud.update_volunteer(db, volunteer_id, update_data)
        if not updated_volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update volunteer"
            )
        
        return VolunteerSchema(**updated_volunteer.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update volunteer profile: {str(e)}"
        )

@router.delete("/{volunteer_id}", response_model=dict)
def deactivate_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate volunteer (soft delete)."""
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "project_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to deactivate volunteers"
            )
        
        success = volunteer_crud.delete_volunteer(db, volunteer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        return {"message": "Volunteer deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate volunteer: {str(e)}"
        )

# ========================================
# VOLUNTEER SKILLS ENDPOINTS
# ========================================

@router.get("/skills/available", response_model=List[VolunteerSkill])
def get_available_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get list of available volunteer skills."""
    try:
        skills = volunteer_skill_crud.get_skills(db, skip=skip, limit=limit)
        return [VolunteerSkill(**skill.model_dump()) for skill in skills]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skills: {str(e)}"
        )

@router.get("/{volunteer_id}/skills", response_model=List[VolunteerSkillAssignment])
def get_volunteer_skills(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get skills for a specific volunteer."""
    try:
        skills = volunteer_skill_crud.get_volunteer_skills(db, volunteer_id)
        return [VolunteerSkillAssignment(**skill.model_dump()) for skill in skills]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer skills: {str(e)}"
        )

@router.post("/{volunteer_id}/skills", response_model=VolunteerSkillAssignment)
def assign_skill_to_volunteer(
    volunteer_id: int,
    skill_assignment: VolunteerSkillAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a skill to a volunteer."""
    try:
        # Check if volunteer exists
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        # Check if skill exists
        skill = volunteer_skill_crud.get_skill(db, skill_assignment.skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify volunteer skills"
            )
        
        assignment = volunteer_skill_crud.assign_skill_to_volunteer(
            db, volunteer_id, skill_assignment
        )
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill already assigned to volunteer"
            )
        
        return VolunteerSkillAssignment(**assignment.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign skill: {str(e)}"
        )

@router.put("/{volunteer_id}/skills/{skill_id}", response_model=VolunteerSkillAssignment)
def update_volunteer_skill(
    volunteer_id: int,
    skill_id: int,
    update_data: VolunteerSkillAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update volunteer skill assignment."""
    try:
        # Check permissions
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify volunteer skills"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_assignment = volunteer_skill_crud.update_volunteer_skill(
            db, volunteer_id, skill_id, update_dict
        )
        
        if not updated_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill assignment not found"
            )
        
        return VolunteerSkillAssignment(**updated_assignment.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill assignment: {str(e)}"
        )

@router.delete("/{volunteer_id}/skills/{skill_id}", response_model=dict)
def remove_skill_from_volunteer(
    volunteer_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove skill assignment from volunteer."""
    try:
        # Check permissions
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify volunteer skills"
            )
        
        success = volunteer_skill_crud.remove_skill_from_volunteer(
            db, volunteer_id, skill_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill assignment not found"
            )
        
        return {"message": "Skill removed from volunteer successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove skill: {str(e)}"
        )

# ========================================
# VOLUNTEER TIME TRACKING ENDPOINTS
# ========================================

@router.get("/{volunteer_id}/hours", response_model=List[VolunteerTimeLog])
def get_volunteer_hours(
    volunteer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    approved_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get volunteer time logs."""
    try:
        # Check permissions
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        if (current_user.user_type.name not in ["admin", "staff_member", "project_manager"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view volunteer hours"
            )
        
        time_logs = volunteer_time_log_crud.get_volunteer_time_logs(
            db, volunteer_id, skip=skip, limit=limit, 
            start_date=start_date, end_date=end_date, approved_only=approved_only
        )
        
        return [VolunteerTimeLog(**log.model_dump()) for log in time_logs]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer hours: {str(e)}"
        )

@router.post("/{volunteer_id}/hours", response_model=VolunteerTimeLog)
def log_volunteer_hours(
    volunteer_id: int,
    time_log_data: VolunteerTimeLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log volunteer hours."""
    try:
        # Check if volunteer exists
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        # Check permissions (volunteer can log their own hours, staff can log for anyone)
        if (current_user.user_type.name not in ["admin", "staff_member", "project_manager"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to log hours for this volunteer"
            )
        
        # Set volunteer_id in the data
        time_log_data.volunteer_id = volunteer_id
        
        time_log = volunteer_time_log_crud.create_time_log(db, time_log_data)
        return VolunteerTimeLog(**time_log.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log volunteer hours: {str(e)}"
        )

@router.put("/hours/{time_log_id}", response_model=VolunteerTimeLog)
def update_volunteer_hours(
    time_log_id: int,
    update_data: VolunteerTimeLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update volunteer time log."""
    try:
        # Check if time log exists
        time_log = volunteer_time_log_crud.get_time_log(db, time_log_id)
        if not time_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time log not found"
            )
        
        # Get volunteer info
        volunteer = volunteer_crud.get_volunteer(db, time_log.volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this time log"
            )
        
        # Don't allow updates to approved time logs unless admin
        if time_log.approved and current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update approved time log"
            )
        
        updated_log = volunteer_time_log_crud.update_time_log(db, time_log_id, update_data)
        if not updated_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update time log"
            )
        
        return VolunteerTimeLog(**updated_log.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update time log: {str(e)}"
        )

@router.post("/hours/{time_log_id}/approve", response_model=VolunteerTimeLog)
def approve_volunteer_hours(
    time_log_id: int,
    approval_data: VolunteerTimeLogApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject volunteer time log."""
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "staff_member", "project_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to approve time logs"
            )
        
        approved_log = volunteer_time_log_crud.approve_time_log(
            db, time_log_id, current_user.id, approval_data
        )
        
        if not approved_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time log not found"
            )
        
        return VolunteerTimeLog(**approved_log.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve time log: {str(e)}"
        )

@router.delete("/hours/{time_log_id}", response_model=dict)
def delete_volunteer_hours(
    time_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete volunteer time log."""
    try:
        # Check if time log exists
        time_log = volunteer_time_log_crud.get_time_log(db, time_log_id)
        if not time_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time log not found"
            )
        
        # Get volunteer info
        volunteer = volunteer_crud.get_volunteer(db, time_log.volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin", "staff_member"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this time log"
            )
        
        # Don't allow deletion of approved time logs unless admin
        if time_log.approved and current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete approved time log"
            )
        
        success = volunteer_time_log_crud.delete_time_log(db, time_log_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to delete time log"
            )
        
        return {"message": "Time log deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete time log: {str(e)}"
        )

@router.get("/{volunteer_id}/hours/summary", response_model=dict)
def get_volunteer_hours_summary(
    volunteer_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get volunteer hours summary."""
    try:
        # Check permissions
        volunteer = volunteer_crud.get_volunteer(db, volunteer_id)
        if not volunteer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer not found"
            )
        
        if (current_user.user_type.name not in ["admin", "staff_member", "project_manager"] and 
            volunteer.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view volunteer hours summary"
            )
        
        summary = volunteer_time_log_crud.get_volunteer_hours_summary(db, volunteer_id, year)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hours summary: {str(e)}"
        )