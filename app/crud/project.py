# app/crud/project.py
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.project import Project, ProjectTeam, Milestone, EnvironmentalMetric
from app.models.user import User, UserType
from app.models.volunteer import Volunteer, VolunteerTimeLog
from app.models.task import Task
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectTeamCreate, ProjectTeamUpdate,
    MilestoneCreate, MilestoneUpdate, EnvironmentalMetricCreate, EnvironmentalMetricUpdate
)

class ProjectCRUD:
    def create_project(self, db: Session, project_data: ProjectCreate, current_user_id: int) -> Project:
        """Create a new project."""
        project = Project(
            **project_data.model_dump(exclude={'created_by_id'}),
            created_by_id=current_user_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    def get_project(self, db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.get(Project, project_id)
    
    def get_projects(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        category: Optional[str] = None,
        manager_id: Optional[int] = None,
        requires_volunteers: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Project]:
        """Get projects with filtering options."""
        query = select(Project)
        
        if status:
            query = query.where(Project.status == status)
        if category:
            query = query.where(Project.category == category)
        if manager_id:
            query = query.where(Project.project_manager_id == manager_id)
        if requires_volunteers is not None:
            query = query.where(Project.requires_volunteers == requires_volunteers)
        if search:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%")
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
        return db.exec(query).all()
    
    def update_project(self, db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """Update project."""
        project = db.get(Project, project_id)
        if not project:
            return None
        
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return project
    
    def delete_project(self, db: Session, project_id: int) -> bool:
        """Delete project (soft delete by changing status)."""
        project = db.get(Project, project_id)
        if not project:
            return False
        
        project.status = "cancelled"
        project.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    def get_project_with_details(self, db: Session, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project with all related details."""
        project = db.get(Project, project_id)
        if not project:
            return None
        
        # Get project manager info
        manager = None
        if project.project_manager_id:
            manager = db.get(User, project.project_manager_id)
        
        # Get created by info
        creator = None
        if project.created_by_id:
            creator = db.get(User, project.created_by_id)
        
        # Get team members with user info
        team_query = (
            select(ProjectTeam, User, UserType)
            .join(User, ProjectTeam.user_id == User.id)
            .join(UserType, User.user_type_id == UserType.id)
            .where(and_(ProjectTeam.project_id == project_id, ProjectTeam.is_active == True))
        )
        team_data = db.exec(team_query).all()
        
        # Get milestones
        milestones_query = select(Milestone).where(Milestone.project_id == project_id)
        milestones = db.exec(milestones_query).all()
        
        # Get environmental metrics with recorder info
        metrics_query = (
            select(EnvironmentalMetric, User)
            .outerjoin(User, EnvironmentalMetric.recorded_by_id == User.id)
            .where(EnvironmentalMetric.project_id == project_id)
        )
        metrics_data = db.exec(metrics_query).all()
        
        # Get tasks count
        total_tasks = db.exec(
            select(func.count(Task.id)).where(Task.project_id == project_id)
        ).first()
        
        completed_tasks = db.exec(
            select(func.count(Task.id))
            .where(and_(Task.project_id == project_id, Task.status == 'completed'))
        ).first()
        
        # Get volunteer hours
        volunteer_hours = db.exec(
            select(func.coalesce(func.sum(VolunteerTimeLog.hours), 0))
            .where(and_(VolunteerTimeLog.project_id == project_id, VolunteerTimeLog.approved == True))
        ).first()
        
        return {
            "project": project,
            "manager": manager,
            "creator": creator,
            "team_members": team_data,
            "milestones": milestones,
            "environmental_metrics": metrics_data,
            "total_tasks": total_tasks or 0,
            "completed_tasks": completed_tasks or 0,
            "volunteer_hours": float(volunteer_hours or 0)
        }
    
    def get_project_dashboard_data(self, db: Session, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get dashboard data for projects."""
        query = """
        SELECT 
            p.id, p.name, p.status, p.category, p.start_date, p.end_date, 
            p.budget, p.actual_cost,
            COUNT(DISTINCT pt.user_id) as team_size,
            COUNT(DISTINCT CASE WHEN pt.is_volunteer THEN pt.user_id END) as volunteers_count,
            COUNT(DISTINCT t.id) as total_tasks,
            COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
            COALESCE(SUM(vtl.hours), 0) as volunteer_hours
        FROM projects p
        LEFT JOIN project_teams pt ON p.id = pt.project_id AND pt.is_active = true
        LEFT JOIN tasks t ON p.id = t.project_id
        LEFT JOIN volunteer_time_logs vtl ON p.id = vtl.project_id AND vtl.approved = true
        GROUP BY p.id, p.name, p.status, p.category, p.start_date, p.end_date, p.budget, p.actual_cost
        ORDER BY p.created_at DESC
        OFFSET :skip LIMIT :limit
        """
        
        result = db.exec(query, {"skip": skip, "limit": limit})
        return [dict(row) for row in result]
    
    def get_project_stats(self, db: Session) -> Dict[str, Any]:
        """Get project statistics."""
        total_projects = db.exec(select(func.count(Project.id))).first()
        active_projects = db.exec(
            select(func.count(Project.id))
            .where(Project.status.in_(["planning", "in_progress"]))
        ).first()
        completed_projects = db.exec(
            select(func.count(Project.id))
            .where(Project.status == "completed")
        ).first()
        
        # Projects by status
        status_query = select(Project.status, func.count(Project.id)).group_by(Project.status)
        status_data = db.exec(status_query).all()
        projects_by_status = {status: count for status, count in status_data}
        
        # Projects by category
        category_query = select(Project.category, func.count(Project.id)).group_by(Project.category)
        category_data = db.exec(category_query).all()
        projects_by_category = {category: count for category, count in category_data}
        
        # Financial stats
        total_budget = db.exec(
            select(func.coalesce(func.sum(Project.budget), 0))
        ).first()
        total_spent = db.exec(
            select(func.coalesce(func.sum(Project.actual_cost), 0))
        ).first()
        
        # Volunteer hours
        total_volunteer_hours = db.exec(
            select(func.coalesce(func.sum(VolunteerTimeLog.hours), 0))
            .where(VolunteerTimeLog.approved == True)
        ).first()
        
        # Average team size
        avg_team_size = db.exec(
            select(func.avg(func.count(ProjectTeam.id)))
            .join(Project, ProjectTeam.project_id == Project.id)
            .where(ProjectTeam.is_active == True)
            .group_by(Project.id)
        ).first()
        
        return {
            "total_projects": total_projects or 0,
            "active_projects": active_projects or 0,
            "completed_projects": completed_projects or 0,
            "projects_by_status": projects_by_status,
            "projects_by_category": projects_by_category,
            "total_budget": float(total_budget or 0),
            "total_spent": float(total_spent or 0),
            "total_volunteer_hours": float(total_volunteer_hours or 0),
            "average_team_size": float(avg_team_size or 0)
        }

class ProjectTeamCRUD:
    def add_team_member(self, db: Session, project_id: int, team_data: ProjectTeamCreate) -> Optional[ProjectTeam]:
        """Add team member to project."""
        # Check if already exists and active
        existing = db.exec(
            select(ProjectTeam)
            .where(and_(
                ProjectTeam.project_id == project_id,
                ProjectTeam.user_id == team_data.user_id,
                ProjectTeam.is_active == True
            ))
        ).first()
        
        if existing:
            return None  # Already a team member
        
        team_member = ProjectTeam(
            project_id=project_id,
            **team_data.model_dump()
        )
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        return team_member
    
    def get_team_members(self, db: Session, project_id: int) -> List[Dict[str, Any]]:
        """Get team members with user info."""
        query = (
            select(ProjectTeam, User, UserType)
            .join(User, ProjectTeam.user_id == User.id)
            .join(UserType, User.user_type_id == UserType.id)
            .where(and_(ProjectTeam.project_id == project_id, ProjectTeam.is_active == True))
        )
        results = db.exec(query).all()
        
        team_members = []
        for team_member, user, user_type in results:
            team_members.append({
                "team_member": team_member,
                "user": user,
                "user_type": user_type.name
            })
        
        return team_members
    
    def update_team_member(
        self, 
        db: Session, 
        project_id: int, 
        user_id: int, 
        update_data: ProjectTeamUpdate
    ) -> Optional[ProjectTeam]:
        """Update team member."""
        team_member = db.exec(
            select(ProjectTeam)
            .where(and_(
                ProjectTeam.project_id == project_id,
                ProjectTeam.user_id == user_id
            ))
        ).first()
        
        if not team_member:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(team_member, field, value)
        
        if not update_dict.get('is_active', True):
            team_member.removed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(team_member)
        return team_member
    
    def remove_team_member(self, db: Session, project_id: int, user_id: int) -> bool:
        """Remove team member from project."""
        team_member = db.exec(
            select(ProjectTeam)
            .where(and_(
                ProjectTeam.project_id == project_id,
                ProjectTeam.user_id == user_id,
                ProjectTeam.is_active == True
            ))
        ).first()
        
        if not team_member:
            return False
        
        team_member.is_active = False
        team_member.removed_at = datetime.utcnow()
        db.commit()
        return True

class MilestoneCRUD:
    def create_milestone(self, db: Session, milestone_data: MilestoneCreate) -> Milestone:
        """Create milestone."""
        milestone = Milestone(**milestone_data.model_dump())
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone
    
    def get_milestone(self, db: Session, milestone_id: int) -> Optional[Milestone]:
        """Get milestone by ID."""
        return db.get(Milestone, milestone_id)
    
    def get_project_milestones(self, db: Session, project_id: int) -> List[Milestone]:
        """Get milestones for a project."""
        query = select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.target_date)
        return db.exec(query).all()
    
    def update_milestone(self, db: Session, milestone_id: int, milestone_data: MilestoneUpdate) -> Optional[Milestone]:
        """Update milestone."""
        milestone = db.get(Milestone, milestone_id)
        if not milestone:
            return None
        
        update_data = milestone_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(milestone, field, value)
        
        milestone.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(milestone)
        return milestone
    
    def delete_milestone(self, db: Session, milestone_id: int) -> bool:
        """Delete milestone."""
        milestone = db.get(Milestone, milestone_id)
        if not milestone:
            return False
        
        db.delete(milestone)
        db.commit()
        return True

class EnvironmentalMetricCRUD:
    def create_metric(self, db: Session, metric_data: EnvironmentalMetricCreate) -> EnvironmentalMetric:
        """Create environmental metric."""
        metric = EnvironmentalMetric(**metric_data.model_dump())
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric
    
    def get_metric(self, db: Session, metric_id: int) -> Optional[EnvironmentalMetric]:
        """Get metric by ID."""
        return db.get(EnvironmentalMetric, metric_id)
    
    def get_project_metrics(self, db: Session, project_id: int) -> List[EnvironmentalMetric]:
        """Get metrics for a project."""
        query = (
            select(EnvironmentalMetric)
            .where(EnvironmentalMetric.project_id == project_id)
            .order_by(EnvironmentalMetric.measurement_date.desc())
        )
        return db.exec(query).all()
    
    def update_metric(self, db: Session, metric_id: int, metric_data: EnvironmentalMetricUpdate) -> Optional[EnvironmentalMetric]:
        """Update environmental metric."""
        metric = db.get(EnvironmentalMetric, metric_id)
        if not metric:
            return None
        
        update_data = metric_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(metric, field, value)
        
        metric.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(metric)
        return metric
    
    def delete_metric(self, db: Session, metric_id: int) -> bool:
        """Delete environmental metric."""
        metric = db.get(EnvironmentalMetric, metric_id)
        if not metric:
            return False
        
        db.delete(metric)
        db.commit()
        return True

# Create instances
project_crud = ProjectCRUD()
project_team_crud = ProjectTeamCRUD()
milestone_crud = MilestoneCRUD()
environmental_metric_crud = EnvironmentalMetricCRUD()