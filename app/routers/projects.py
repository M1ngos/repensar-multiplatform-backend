# app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.project import (
    project_crud, project_team_crud, milestone_crud, environmental_metric_crud
)
from app.schemas.project import (
    # Project schemas
    ProjectCreate, ProjectUpdate, Project, ProjectSummary, ProjectDetail, 
    ProjectDashboard, ProjectStats,
    
    # Team schemas
    ProjectTeamCreate, ProjectTeamUpdate, ProjectTeamMember,
    
    # Milestone schemas
    MilestoneCreate, MilestoneUpdate, Milestone,
    
    # Environmental metrics schemas
    EnvironmentalMetricCreate, EnvironmentalMetricUpdate, EnvironmentalMetric
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# ========================================
# PROJECT ENDPOINTS
# ========================================

@router.post("/", response_model=Project)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project."""
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "project_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create projects"
            )
        
        project = project_crud.create_project(db, project_data, current_user.id)
        return Project(**project.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/", response_model=List[ProjectSummary])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(planning|in_progress|suspended|completed|cancelled)$"),
    category: Optional[str] = None,
    manager_id: Optional[int] = None,
    requires_volunteers: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of projects with filtering options."""
    try:
        projects = project_crud.get_projects(
            db, skip=skip, limit=limit, status=status, category=category,
            manager_id=manager_id, requires_volunteers=requires_volunteers, search=search
        )
        
        # Convert to summary format
        project_summaries = []
        for project in projects:
            # Get project manager name
            manager_name = None
            if project.project_manager_id:
                from app.models.user import User
                manager = db.get(User, project.project_manager_id)
                if manager:
                    manager_name = manager.name
            
            # Get team size and volunteers count
            team_data = project_team_crud.get_team_members(db, project.id)
            team_size = len(team_data)
            volunteers_count = len([tm for tm in team_data if tm["team_member"].is_volunteer])
            
            # Calculate progress if has tasks
            progress = 0.0
            details = project_crud.get_project_with_details(db, project.id)
            if details and details["total_tasks"] > 0:
                progress = (details["completed_tasks"] / details["total_tasks"]) * 100
            
            summary = ProjectSummary(
                id=project.id,
                name=project.name,
                category=project.category,
                status=project.status,
                priority=project.priority,
                start_date=project.start_date,
                end_date=project.end_date,
                budget=float(project.budget) if project.budget else None,
                actual_cost=float(project.actual_cost),
                location_name=project.location_name,
                requires_volunteers=project.requires_volunteers,
                project_manager_name=manager_name,
                team_size=team_size,
                volunteers_count=volunteers_count,
                progress_percentage=progress
            )
            project_summaries.append(summary)
        
        return project_summaries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

@router.get("/dashboard", response_model=List[ProjectDashboard])
def get_projects_dashboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project dashboard data."""
    try:
        dashboard_data = project_crud.get_project_dashboard_data(db, skip=skip, limit=limit)
        
        dashboards = []
        for data in dashboard_data:
            # Calculate additional metrics
            progress = 0.0
            if data["total_tasks"] > 0:
                progress = (data["completed_tasks"] / data["total_tasks"]) * 100
            
            days_remaining = None
            if data["end_date"]:
                from datetime import date
                today = date.today()
                if data["end_date"] > today:
                    days_remaining = (data["end_date"] - today).days
            
            budget_utilization = None
            if data["budget"] and data["budget"] > 0:
                budget_utilization = (data["actual_cost"] / data["budget"]) * 100
            
            dashboard = ProjectDashboard(
                **data,
                progress_percentage=progress,
                days_remaining=days_remaining,
                budget_utilization=budget_utilization
            )
            dashboards.append(dashboard)
        
        return dashboards
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@router.get("/stats", response_model=ProjectStats)
def get_project_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project statistics."""
    try:
        stats = project_crud.get_project_stats(db)
        return ProjectStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project stats: {str(e)}"
        )

@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed project information."""
    try:
        project_data = project_crud.get_project_with_details(db, project_id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = project_data["project"]
        
        # Build detailed response
        detail = ProjectDetail(
            **project.model_dump(),
            project_manager_name=project_data["manager"].name if project_data["manager"] else None,
            created_by_name=project_data["creator"].name if project_data["creator"] else None,
            team_members=[],  # Will be populated from team data
            milestones=[Milestone(**m.model_dump()) for m in project_data["milestones"]],
            environmental_metrics=[],  # Will be populated from metrics data
            total_tasks=project_data["total_tasks"],
            completed_tasks=project_data["completed_tasks"],
            progress_percentage=(project_data["completed_tasks"] / max(project_data["total_tasks"], 1)) * 100,
            volunteer_hours=project_data["volunteer_hours"]
        )
        
        # Add team members
        for team_member, user, user_type in project_data["team_members"]:
            detail.team_members.append(ProjectTeamMember(
                **team_member.model_dump(),
                name=user.name,
                email=user.email,
                user_type=user_type
            ))
        
        # Add environmental metrics
        for metric, recorder in project_data["environmental_metrics"]:
            detail.environmental_metrics.append(EnvironmentalMetric(
                **metric.model_dump(),
                recorded_by_name=recorder.name if recorder else None
            ))
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )

@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project."""
    try:
        # Check if project exists
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id and
            project.created_by_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
        
        updated_project = project_crud.update_project(db, project_id, project_data)
        return Project(**updated_project.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}", response_model=dict)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project (mark as cancelled)."""
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete projects"
            )
        
        success = project_crud.delete_project(db, project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

# ========================================
# PROJECT TEAM ENDPOINTS
# ========================================

@router.get("/{project_id}/team", response_model=List[ProjectTeamMember])
def get_project_team(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project team members."""
    try:
        team_data = project_team_crud.get_team_members(db, project_id)
        
        team_members = []
        for data in team_data:
            team_member = data["team_member"]
            user = data["user"]
            user_type = data["user_type"]
            
            team_members.append(ProjectTeamMember(
                **team_member.model_dump(),
                name=user.name,
                email=user.email,
                user_type=user_type
            ))
        
        return team_members
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team members: {str(e)}"
        )

@router.post("/{project_id}/team", response_model=ProjectTeamMember)
def add_team_member(
    project_id: int,
    team_data: ProjectTeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add team member to project."""
    try:
        # Check if project exists
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage project team"
            )
        
        team_member = project_team_crud.add_team_member(db, project_id, team_data)
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a team member"
            )
        
        # Get user info for response
        from app.models.user import User, UserType
        user = db.get(User, team_member.user_id)
        user_type = db.get(UserType, user.user_type_id)
        
        return ProjectTeamMember(
            **team_member.model_dump(),
            name=user.name,
            email=user.email,
            user_type=user_type.name if user_type else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )

@router.put("/{project_id}/team/{user_id}", response_model=ProjectTeamMember)
def update_team_member(
    project_id: int,
    user_id: int,
    update_data: ProjectTeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update team member."""
    try:
        # Check permissions
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage project team"
            )
        
        team_member = project_team_crud.update_team_member(db, project_id, user_id, update_data)
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        # Get user info for response
        from app.models.user import User, UserType
        user = db.get(User, team_member.user_id)
        user_type = db.get(UserType, user.user_type_id)
        
        return ProjectTeamMember(
            **team_member.model_dump(),
            name=user.name,
            email=user.email,
            user_type=user_type.name if user_type else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team member: {str(e)}"
        )

@router.delete("/{project_id}/team/{user_id}", response_model=dict)
def remove_team_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove team member from project."""
    try:
        # Check permissions
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to manage project team"
            )
        
        success = project_team_crud.remove_team_member(db, project_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        return {"message": "Team member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}"
        )

# ========================================
# MILESTONE ENDPOINTS
# ========================================

@router.get("/{project_id}/milestones", response_model=List[Milestone])
def get_project_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project milestones."""
    try:
        milestones = milestone_crud.get_project_milestones(db, project_id)
        return [Milestone(**m.model_dump()) for m in milestones]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve milestones: {str(e)}"
        )

@router.post("/{project_id}/milestones", response_model=Milestone)
def create_milestone(
    project_id: int,
    milestone_data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create project milestone."""
    try:
        # Check permissions
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if (current_user.user_type.name not in ["admin", "project_manager"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create milestones"
            )
        
        milestone_data.project_id = project_id
        milestone = milestone_crud.create_milestone(db, milestone_data)
        return Milestone(**milestone.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create milestone: {str(e)}"
        )

@router.put("/milestones/{milestone_id}", response_model=Milestone)
def update_milestone(
    milestone_id: int,
    milestone_data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update milestone."""
    try:
        milestone = milestone_crud.get_milestone(db, milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check permissions
        project = project_crud.get_project(db, milestone.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update milestones"
            )
        
        updated_milestone = milestone_crud.update_milestone(db, milestone_id, milestone_data)
        return Milestone(**updated_milestone.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update milestone: {str(e)}"
        )

@router.delete("/milestones/{milestone_id}", response_model=dict)
def delete_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete milestone."""
    try:
        milestone = milestone_crud.get_milestone(db, milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        # Check permissions
        project = project_crud.get_project(db, milestone.project_id)
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete milestones"
            )
        
        success = milestone_crud.delete_milestone(db, milestone_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )
        
        return {"message": "Milestone deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete milestone: {str(e)}"
        )

# ========================================
# ENVIRONMENTAL METRICS ENDPOINTS
# ========================================

@router.get("/{project_id}/metrics", response_model=List[EnvironmentalMetric])
def get_project_metrics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project environmental metrics."""
    try:
        metrics = environmental_metric_crud.get_project_metrics(db, project_id)
        return [EnvironmentalMetric(**m.model_dump()) for m in metrics]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )

@router.post("/{project_id}/metrics", response_model=EnvironmentalMetric)
def create_environmental_metric(
    project_id: int,
    metric_data: EnvironmentalMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create environmental metric."""
    try:
        # Check permissions
        project = project_crud.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if (current_user.user_type.name not in ["admin", "project_manager", "staff_member"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create metrics"
            )
        
        metric_data.project_id = project_id
        metric_data.recorded_by_id = current_user.id
        
        metric = environmental_metric_crud.create_metric(db, metric_data)
        return EnvironmentalMetric(**metric.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create metric: {str(e)}"
        )

@router.put("/metrics/{metric_id}", response_model=EnvironmentalMetric)
def update_environmental_metric(
    metric_id: int,
    metric_data: EnvironmentalMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update environmental metric."""
    try:
        metric = environmental_metric_crud.get_metric(db, metric_id)
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        # Check permissions
        project = project_crud.get_project(db, metric.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager", "staff_member"] and 
            project.project_manager_id != current_user.id and
            metric.recorded_by_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this metric"
            )
        
        updated_metric = environmental_metric_crud.update_metric(db, metric_id, metric_data)
        return EnvironmentalMetric(**updated_metric.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update metric: {str(e)}"
        )

@router.delete("/metrics/{metric_id}", response_model=dict)
def delete_environmental_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete environmental metric."""
    try:
        metric = environmental_metric_crud.get_metric(db, metric_id)
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        # Check permissions
        project = project_crud.get_project(db, metric.project_id)
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id and
            metric.recorded_by_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this metric"
            )
        
        success = environmental_metric_crud.delete_metric(db, metric_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        return {"message": "Environmental metric deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metric: {str(e)}"
        )