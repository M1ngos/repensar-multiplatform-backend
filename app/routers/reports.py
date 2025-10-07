# app/routers/reports.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional, Dict, Any

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.project import project_crud
from app.crud.task import task_crud
from app.crud.volunteer import volunteer_stats_crud
from app.crud.resource import resource_crud

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)

@router.get("/projects")
def get_project_reports(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get project reports."""
    if project_id:
        project_data = project_crud.get_project_with_details(db, project_id)
        if not project_data:
            return {"error": "Project not found"}
        
        return {
            "project": project_data["project"].model_dump(),
            "team_size": len(project_data["team_members"]),
            "total_tasks": project_data["total_tasks"],
            "completed_tasks": project_data["completed_tasks"],
            "volunteer_hours": project_data["volunteer_hours"],
            "milestones": [m.model_dump() for m in project_data["milestones"]],
            "environmental_metrics": [m.model_dump() for m, _ in project_data["environmental_metrics"]]
        }
    else:
        return project_crud.get_project_stats(db)

@router.get("/volunteers")
def get_volunteer_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get volunteer reports."""
    return volunteer_stats_crud.get_volunteer_stats(db)

@router.get("/tasks")
def get_task_reports(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get task reports."""
    return task_crud.get_task_stats(db, project_id=project_id)

@router.get("/resources")
def get_resource_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get resource reports."""
    return resource_crud.get_resource_stats(db)

@router.get("/dashboard")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard summary with key metrics."""
    project_stats = project_crud.get_project_stats(db)
    volunteer_stats = volunteer_stats_crud.get_volunteer_stats(db)
    task_stats = task_crud.get_task_stats(db)
    resource_stats = resource_crud.get_resource_stats(db)
    
    return {
        "projects": project_stats,
        "volunteers": volunteer_stats,
        "tasks": task_stats,
        "resources": resource_stats,
        "summary": {
            "total_projects": project_stats.get("total_projects", 0),
            "active_volunteers": volunteer_stats.get("active_volunteers", 0),
            "total_tasks": task_stats.get("total_tasks", 0),
            "total_volunteer_hours": volunteer_stats.get("total_hours", 0)
        }
    }