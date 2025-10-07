# app/crud/volunteer.py
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.models.volunteer import (
    Volunteer, VolunteerSkill, VolunteerSkillAssignment, 
    VolunteerTimeLog, VolunteerTraining, VolunteerTrainingRecord
)
from app.models.user import User
from app.schemas.volunteer import (
    VolunteerCreate, VolunteerUpdate, VolunteerSkillAssignmentCreate,
    VolunteerTimeLogCreate, VolunteerTimeLogUpdate, VolunteerTimeLogApproval
)

class VolunteerCRUD:
    
    def create_volunteer(self, db: Session, volunteer_data: VolunteerCreate) -> Volunteer:
        """Create a new volunteer profile."""
        volunteer = Volunteer(**volunteer_data.model_dump())
        db.add(volunteer)
        db.commit()
        db.refresh(volunteer)
        return volunteer
    
    def get_volunteer(self, db: Session, volunteer_id: int) -> Optional[Volunteer]:
        """Get volunteer by ID."""
        return db.exec(select(Volunteer).where(Volunteer.id == volunteer_id)).first()
    
    def get_volunteer_by_volunteer_id(self, db: Session, volunteer_id: str) -> Optional[Volunteer]:
        """Get volunteer by volunteer_id string."""
        return db.exec(select(Volunteer).where(Volunteer.volunteer_id == volunteer_id)).first()
    
    def get_volunteer_by_user_id(self, db: Session, user_id: int) -> Optional[Volunteer]:
        """Get volunteer by user ID."""
        return db.exec(select(Volunteer).where(Volunteer.user_id == user_id)).first()
    
    def get_volunteers(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        skill_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Volunteer]:
        """Get volunteers with optional filtering."""
        query = select(Volunteer).join(User, Volunteer.user_id == User.id)
        
        if status:
            query = query.where(Volunteer.volunteer_status == status)
        
        if skill_id:
            query = query.join(VolunteerSkillAssignment).where(
                VolunteerSkillAssignment.skill_id == skill_id
            )
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    Volunteer.volunteer_id.ilike(search_pattern)
                )
            )
        
        query = query.offset(skip).limit(limit)
        return db.exec(query).all()
    
    def update_volunteer(
        self, db: Session, volunteer_id: int, volunteer_data: VolunteerUpdate
    ) -> Optional[Volunteer]:
        """Update volunteer profile."""
        volunteer = self.get_volunteer(db, volunteer_id)
        if not volunteer:
            return None
        
        update_data = volunteer_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            for key, value in update_data.items():
                setattr(volunteer, key, value)
            
            db.add(volunteer)
            db.commit()
            db.refresh(volunteer)
        
        return volunteer
    
    def delete_volunteer(self, db: Session, volunteer_id: int) -> bool:
        """Delete volunteer profile (soft delete by setting status to inactive)."""
        volunteer = self.get_volunteer(db, volunteer_id)
        if not volunteer:
            return False
        
        volunteer.volunteer_status = "inactive"
        volunteer.updated_at = datetime.utcnow()
        db.add(volunteer)
        db.commit()
        return True
    
    def get_volunteer_profile_with_details(self, db: Session, volunteer_id: int) -> Optional[Dict]:
        """Get volunteer profile with user details and skills."""
        query = (
            select(Volunteer, User)
            .join(User, Volunteer.user_id == User.id)
            .where(Volunteer.id == volunteer_id)
        )
        result = db.exec(query).first()
        if not result:
            return None
        
        volunteer, user = result
        
        # Get skills
        skills_query = (
            select(VolunteerSkillAssignment, VolunteerSkill)
            .join(VolunteerSkill, VolunteerSkillAssignment.skill_id == VolunteerSkill.id)
            .where(VolunteerSkillAssignment.volunteer_id == volunteer_id)
        )
        skills = db.exec(skills_query).all()
        
        return {
            "volunteer": volunteer,
            "user": user,
            "skills": skills
        }

class VolunteerSkillCRUD:
    
    def get_skills(self, db: Session, skip: int = 0, limit: int = 100) -> List[VolunteerSkill]:
        """Get all volunteer skills."""
        query = select(VolunteerSkill).where(VolunteerSkill.is_active == True)
        return db.exec(query.offset(skip).limit(limit)).all()
    
    def get_skill(self, db: Session, skill_id: int) -> Optional[VolunteerSkill]:
        """Get skill by ID."""
        return db.exec(select(VolunteerSkill).where(VolunteerSkill.id == skill_id)).first()
    
    def assign_skill_to_volunteer(
        self, db: Session, volunteer_id: int, skill_assignment: VolunteerSkillAssignmentCreate
    ) -> Optional[VolunteerSkillAssignment]:
        """Assign a skill to a volunteer."""
        # Check if assignment already exists
        existing = db.exec(
            select(VolunteerSkillAssignment).where(
                and_(
                    VolunteerSkillAssignment.volunteer_id == volunteer_id,
                    VolunteerSkillAssignment.skill_id == skill_assignment.skill_id
                )
            )
        ).first()
        
        if existing:
            return None  # Already assigned
        
        assignment = VolunteerSkillAssignment(
            volunteer_id=volunteer_id,
            **skill_assignment.model_dump()
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def update_volunteer_skill(
        self, 
        db: Session, 
        volunteer_id: int, 
        skill_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[VolunteerSkillAssignment]:
        """Update volunteer skill assignment."""
        assignment = db.exec(
            select(VolunteerSkillAssignment).where(
                and_(
                    VolunteerSkillAssignment.volunteer_id == volunteer_id,
                    VolunteerSkillAssignment.skill_id == skill_id
                )
            )
        ).first()
        
        if not assignment:
            return None
        
        for key, value in update_data.items():
            setattr(assignment, key, value)
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def remove_skill_from_volunteer(
        self, db: Session, volunteer_id: int, skill_id: int
    ) -> bool:
        """Remove skill assignment from volunteer."""
        assignment = db.exec(
            select(VolunteerSkillAssignment).where(
                and_(
                    VolunteerSkillAssignment.volunteer_id == volunteer_id,
                    VolunteerSkillAssignment.skill_id == skill_id
                )
            )
        ).first()
        
        if not assignment:
            return False
        
        db.delete(assignment)
        db.commit()
        return True
    
    def get_volunteer_skills(self, db: Session, volunteer_id: int) -> List[VolunteerSkillAssignment]:
        """Get all skills for a volunteer."""
        query = (
            select(VolunteerSkillAssignment)
            .join(VolunteerSkill, VolunteerSkillAssignment.skill_id == VolunteerSkill.id)
            .where(VolunteerSkillAssignment.volunteer_id == volunteer_id)
        )
        return db.exec(query).all()

class VolunteerTimeLogCRUD:
    
    def create_time_log(
        self, db: Session, time_log_data: VolunteerTimeLogCreate
    ) -> VolunteerTimeLog:
        """Create a new time log entry."""
        time_log = VolunteerTimeLog(**time_log_data.model_dump())
        db.add(time_log)
        db.commit()
        db.refresh(time_log)
        return time_log
    
    def get_time_log(self, db: Session, time_log_id: int) -> Optional[VolunteerTimeLog]:
        """Get time log by ID."""
        return db.exec(select(VolunteerTimeLog).where(VolunteerTimeLog.id == time_log_id)).first()
    
    def get_volunteer_time_logs(
        self, 
        db: Session, 
        volunteer_id: int, 
        skip: int = 0, 
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        approved_only: bool = False
    ) -> List[VolunteerTimeLog]:
        """Get time logs for a volunteer."""
        query = select(VolunteerTimeLog).where(VolunteerTimeLog.volunteer_id == volunteer_id)
        
        if start_date:
            query = query.where(VolunteerTimeLog.date >= start_date)
        
        if end_date:
            query = query.where(VolunteerTimeLog.date <= end_date)
        
        if approved_only:
            query = query.where(VolunteerTimeLog.approved == True)
        
        query = query.order_by(VolunteerTimeLog.date.desc()).offset(skip).limit(limit)
        return db.exec(query).all()
    
    def update_time_log(
        self, db: Session, time_log_id: int, update_data: VolunteerTimeLogUpdate
    ) -> Optional[VolunteerTimeLog]:
        """Update time log entry."""
        time_log = self.get_time_log(db, time_log_id)
        if not time_log:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(time_log, key, value)
            
            db.add(time_log)
            db.commit()
            db.refresh(time_log)
        
        return time_log
    
    def approve_time_log(
        self, 
        db: Session, 
        time_log_id: int, 
        approved_by_id: int, 
        approval_data: VolunteerTimeLogApproval
    ) -> Optional[VolunteerTimeLog]:
        """Approve or reject time log entry."""
        time_log = self.get_time_log(db, time_log_id)
        if not time_log:
            return None
        
        time_log.approved = approval_data.approved
        time_log.approved_by_id = approved_by_id
        time_log.approved_at = datetime.utcnow()
        time_log.updated_at = datetime.utcnow()
        
        db.add(time_log)
        
        # Update volunteer total hours if approved
        if approval_data.approved:
            volunteer = db.exec(
                select(Volunteer).where(Volunteer.id == time_log.volunteer_id)
            ).first()
            if volunteer:
                volunteer.total_hours_contributed += time_log.hours
                volunteer.updated_at = datetime.utcnow()
                db.add(volunteer)
        
        db.commit()
        db.refresh(time_log)
        return time_log
    
    def delete_time_log(self, db: Session, time_log_id: int) -> bool:
        """Delete time log entry."""
        time_log = self.get_time_log(db, time_log_id)
        if not time_log:
            return False
        
        # If approved, subtract from volunteer total hours
        if time_log.approved:
            volunteer = db.exec(
                select(Volunteer).where(Volunteer.id == time_log.volunteer_id)
            ).first()
            if volunteer:
                volunteer.total_hours_contributed = max(
                    0, volunteer.total_hours_contributed - time_log.hours
                )
                volunteer.updated_at = datetime.utcnow()
                db.add(volunteer)
        
        db.delete(time_log)
        db.commit()
        return True
    
    def get_volunteer_hours_summary(
        self, db: Session, volunteer_id: int, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get volunteer hours summary."""
        query = select(VolunteerTimeLog).where(
            and_(
                VolunteerTimeLog.volunteer_id == volunteer_id,
                VolunteerTimeLog.approved == True
            )
        )
        
        if year:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            query = query.where(
                and_(
                    VolunteerTimeLog.date >= start_date,
                    VolunteerTimeLog.date <= end_date
                )
            )
        
        time_logs = db.exec(query).all()
        
        total_hours = sum(log.hours for log in time_logs)
        
        # Group by month
        monthly_hours = {}
        for log in time_logs:
            month_key = f"{log.date.year}-{log.date.month:02d}"
            monthly_hours[month_key] = monthly_hours.get(month_key, 0) + float(log.hours)
        
        return {
            "total_hours": float(total_hours),
            "total_entries": len(time_logs),
            "monthly_breakdown": monthly_hours,
            "year": year or datetime.now().year
        }

class VolunteerStatsCRUD:
    
    def get_volunteer_stats(self, db: Session) -> Dict[str, Any]:
        """Get volunteer statistics."""
        # Total volunteers
        total_volunteers = db.exec(select(func.count(Volunteer.id))).first()
        
        # Active volunteers
        active_volunteers = db.exec(
            select(func.count(Volunteer.id)).where(Volunteer.volunteer_status == "active")
        ).first()
        
        # Total hours
        total_hours_result = db.exec(
            select(func.sum(Volunteer.total_hours_contributed))
        ).first()
        total_hours = float(total_hours_result) if total_hours_result else 0.0
        
        # Volunteers by status
        status_counts = db.exec(
            select(Volunteer.volunteer_status, func.count(Volunteer.id))
            .group_by(Volunteer.volunteer_status)
        ).all()
        
        volunteers_by_status = {status: count for status, count in status_counts}
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        recent_registrations = db.exec(
            select(func.count(Volunteer.id))
            .where(Volunteer.joined_date >= thirty_days_ago)
        ).first()
        
        # Top skills
        skill_counts = db.exec(
            select(VolunteerSkill.name, func.count(VolunteerSkillAssignment.volunteer_id))
            .join(VolunteerSkillAssignment, VolunteerSkill.id == VolunteerSkillAssignment.skill_id)
            .group_by(VolunteerSkill.name)
            .order_by(func.count(VolunteerSkillAssignment.volunteer_id).desc())
            .limit(10)
        ).all()
        
        volunteers_by_skill = {skill: count for skill, count in skill_counts}
        
        return {
            "total_volunteers": total_volunteers,
            "active_volunteers": active_volunteers,
            "total_hours": total_hours,
            "volunteers_by_status": volunteers_by_status,
            "volunteers_by_skill": volunteers_by_skill,
            "recent_registrations": recent_registrations or 0
        }

# Create instances
volunteer_crud = VolunteerCRUD()
volunteer_skill_crud = VolunteerSkillCRUD()
volunteer_time_log_crud = VolunteerTimeLogCRUD()
volunteer_stats_crud = VolunteerStatsCRUD()