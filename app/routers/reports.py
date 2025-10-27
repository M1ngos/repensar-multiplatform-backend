# app/routers/reports.py
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import date, datetime
import csv
import io
import json

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.volunteer import Volunteer, VolunteerTimeLog
from app.crud.project import project_crud
from app.crud.task import task_crud
from app.crud.volunteer import volunteer_stats_crud, volunteer_crud
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

# ========================================
# EXPORT ENDPOINTS
# ========================================

@router.get("/export/projects/csv")
def export_projects_csv(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export projects to CSV format.
    """
    try:
        # Get projects
        projects = project_crud.get_projects(
            db, skip=0, limit=10000,
            status=status, category=category
        )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Name", "Category", "Status", "Priority",
            "Start Date", "End Date", "Budget", "Actual Cost",
            "Project Manager ID", "Created By ID",
            "Requires Volunteers", "Created At"
        ])

        # Write data rows
        for project in projects:
            writer.writerow([
                project.id,
                project.name,
                project.category,
                project.status,
                project.priority,
                project.start_date.isoformat() if project.start_date else "",
                project.end_date.isoformat() if project.end_date else "",
                float(project.budget) if project.budget else 0.0,
                float(project.actual_cost) if project.actual_cost else 0.0,
                project.project_manager_id,
                project.created_by_id,
                project.requires_volunteers,
                project.created_at.isoformat()
            ])

        # Prepare response
        output.seek(0)
        filename = f"projects_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export projects: {str(e)}"
        )

@router.get("/export/volunteers/csv")
def export_volunteers_csv(
    volunteer_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export volunteers to CSV format.
    """
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "project_manager", "staff_member"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to export volunteer data"
            )

        # Get volunteers
        volunteers = volunteer_crud.get_volunteers(db, skip=0, limit=10000)

        if volunteer_status:
            volunteers = [v for v in volunteers if v.volunteer_status == volunteer_status]

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Volunteer ID", "User ID", "Name", "Email", "Phone",
            "Date of Birth", "Gender", "City", "Postal Code",
            "Status", "Background Check Status", "Total Hours",
            "Joined Date", "Created At"
        ])

        # Write data rows
        for volunteer in volunteers:
            user = db.get(User, volunteer.user_id)
            writer.writerow([
                volunteer.volunteer_id,
                volunteer.user_id,
                user.name if user else "",
                user.email if user else "",
                user.phone if user else "",
                volunteer.date_of_birth.isoformat() if volunteer.date_of_birth else "",
                volunteer.gender or "",
                volunteer.city or "",
                volunteer.postal_code or "",
                volunteer.volunteer_status,
                volunteer.background_check_status or "",
                float(volunteer.total_hours_contributed) if volunteer.total_hours_contributed else 0.0,
                volunteer.joined_date.isoformat() if volunteer.joined_date else "",
                volunteer.created_at.isoformat()
            ])

        # Prepare response
        output.seek(0)
        filename = f"volunteers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export volunteers: {str(e)}"
        )

@router.get("/export/tasks/csv")
def export_tasks_csv(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export tasks to CSV format.
    """
    try:
        # Get tasks
        tasks = task_crud.get_tasks(
            db, skip=0, limit=10000,
            project_id=project_id, status=status
        )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Title", "Project ID", "Project Name",
            "Status", "Priority", "Assigned To ID",
            "Estimated Hours", "Actual Hours", "Progress %",
            "Suitable for Volunteers", "Created At"
        ])

        # Write data rows
        for task in tasks:
            project = db.get(Project, task.project_id)
            writer.writerow([
                task.id,
                task.title,
                task.project_id,
                project.name if project else "",
                task.status,
                task.priority,
                task.assigned_to_id or "",
                float(task.estimated_hours) if task.estimated_hours else 0.0,
                float(task.actual_hours) if task.actual_hours else 0.0,
                float(task.progress_percentage) if task.progress_percentage else 0.0,
                task.suitable_for_volunteers,
                task.created_at.isoformat()
            ])

        # Prepare response
        output.seek(0)
        filename = f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export tasks: {str(e)}"
        )

@router.get("/export/time-logs/csv")
def export_time_logs_csv(
    project_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    approval_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export volunteer time logs to CSV format.
    """
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "project_manager", "staff_member"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to export time log data"
            )

        # Build query
        query = select(VolunteerTimeLog)

        filters = []
        if project_id:
            filters.append(VolunteerTimeLog.project_id == project_id)
        if volunteer_id:
            filters.append(VolunteerTimeLog.volunteer_id == volunteer_id)
        if start_date:
            filters.append(VolunteerTimeLog.date >= start_date)
        if end_date:
            filters.append(VolunteerTimeLog.date <= end_date)
        if approval_status:
            filters.append(VolunteerTimeLog.approval_status == approval_status)

        if filters:
            from sqlmodel import and_
            query = query.where(and_(*filters))

        time_logs = db.exec(query.limit(10000)).all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Volunteer ID", "Volunteer Name",
            "Project ID", "Project Name", "Task ID",
            "Date", "Hours", "Activity", "Description",
            "Supervisor ID", "Approval Status",
            "Created At"
        ])

        # Write data rows
        for log in time_logs:
            volunteer = db.get(Volunteer, log.volunteer_id)
            user = db.get(User, volunteer.user_id) if volunteer else None
            project = db.get(Project, log.project_id) if log.project_id else None

            writer.writerow([
                log.id,
                log.volunteer_id,
                user.name if user else "",
                log.project_id or "",
                project.name if project else "",
                log.task_id or "",
                log.date.isoformat(),
                float(log.hours),
                log.activity or "",
                log.description or "",
                log.supervisor_id or "",
                log.approval_status,
                log.created_at.isoformat()
            ])

        # Prepare response
        output.seek(0)
        filename = f"time_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export time logs: {str(e)}"
        )

@router.get("/export/projects/json")
def export_projects_json(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export detailed project report to JSON format.
    """
    try:
        if project_id:
            # Export single project with full details
            project_data = project_crud.get_project_with_details(db, project_id)
            if not project_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            export_data = {
                "project": project_data["project"].model_dump(mode='json'),
                "team_members": [
                    {
                        "team_member": tm.model_dump(mode='json'),
                        "user": u.model_dump(mode='json'),
                        "user_type": ut
                    }
                    for tm, u, ut in project_data["team_members"]
                ],
                "milestones": [m.model_dump(mode='json') for m in project_data["milestones"]],
                "environmental_metrics": [
                    {
                        "metric": m.model_dump(mode='json'),
                        "recorded_by": r.name if r else None
                    }
                    for m, r in project_data["environmental_metrics"]
                ],
                "stats": {
                    "total_tasks": project_data["total_tasks"],
                    "completed_tasks": project_data["completed_tasks"],
                    "volunteer_hours": project_data["volunteer_hours"]
                }
            }
        else:
            # Export all projects summary
            projects = project_crud.get_projects(db, skip=0, limit=10000, status=status)
            export_data = {
                "projects": [p.model_dump(mode='json') for p in projects],
                "total_count": len(projects),
                "exported_at": datetime.now().isoformat()
            }

        # Convert to JSON
        json_str = json.dumps(export_data, indent=2, default=str)
        filename = f"projects_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export projects to JSON: {str(e)}"
        )