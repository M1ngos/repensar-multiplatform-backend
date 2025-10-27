# app/routers/analytics.py
"""
Analytics router for time-series metrics, trends, and dashboard data.
Provides endpoints for historical data analysis and KPI tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.analytics import MetricSnapshot, MetricType, Dashboard
from app.models.project import Project
from app.models.task import Task
from app.models.volunteer import Volunteer, VolunteerTimeLog
from app.schemas.common import PaginatedResponse, create_pagination_metadata

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# ========================================
# TIME-SERIES METRICS ENDPOINTS
# ========================================

@router.post("/metrics/snapshot")
def create_metric_snapshot(
    metric_type: MetricType,
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    metric_metadata: Optional[Dict[str, Any]] = None,
    snapshot_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new metric snapshot for time-series tracking.
    Requires admin or project_manager role.
    """
    try:
        # Check permissions
        if current_user.user_type.name not in ["admin", "project_manager", "staff_member"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create metric snapshots"
            )

        # Create snapshot
        snapshot = MetricSnapshot(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            project_id=project_id,
            task_id=task_id,
            volunteer_id=volunteer_id,
            metric_metadata=metric_metadata,
            recorded_by_id=current_user.id,
            snapshot_date=snapshot_date or datetime.utcnow()
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "success": True,
            "message": "Metric snapshot created successfully",
            "snapshot_id": snapshot.id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create metric snapshot: {str(e)}"
        )

@router.get("/metrics/time-series")
def get_time_series_metrics(
    metric_type: MetricType,
    start_date: date,
    end_date: date,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    granularity: str = Query("daily", regex="^(hourly|daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get time-series metrics for a specific type and date range.
    Returns aggregated data based on granularity.
    """
    try:
        # Build query
        query = select(MetricSnapshot).where(
            and_(
                MetricSnapshot.metric_type == metric_type,
                MetricSnapshot.snapshot_date >= datetime.combine(start_date, datetime.min.time()),
                MetricSnapshot.snapshot_date <= datetime.combine(end_date, datetime.max.time())
            )
        )

        if project_id:
            query = query.where(MetricSnapshot.project_id == project_id)
        if task_id:
            query = query.where(MetricSnapshot.task_id == task_id)
        if volunteer_id:
            query = query.where(MetricSnapshot.volunteer_id == volunteer_id)

        query = query.order_by(MetricSnapshot.snapshot_date)

        snapshots = db.exec(query).all()

        # Aggregate data based on granularity
        aggregated_data = _aggregate_metrics(snapshots, granularity)

        return {
            "metric_type": metric_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "granularity": granularity,
            "data_points": len(aggregated_data),
            "data": aggregated_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve time-series metrics: {str(e)}"
        )

def _aggregate_metrics(snapshots: List[MetricSnapshot], granularity: str) -> List[Dict[str, Any]]:
    """Helper function to aggregate metrics based on granularity."""
    if not snapshots:
        return []

    aggregated = {}

    for snapshot in snapshots:
        # Determine the key based on granularity
        if granularity == "hourly":
            key = snapshot.snapshot_date.strftime("%Y-%m-%d %H:00")
        elif granularity == "daily":
            key = snapshot.snapshot_date.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            key = snapshot.snapshot_date.strftime("%Y-W%W")
        elif granularity == "monthly":
            key = snapshot.snapshot_date.strftime("%Y-%m")
        else:
            key = snapshot.snapshot_date.strftime("%Y-%m-%d")

        if key not in aggregated:
            aggregated[key] = {
                "period": key,
                "values": [],
                "count": 0,
                "sum": 0.0,
                "avg": 0.0,
                "min": float('inf'),
                "max": float('-inf')
            }

        aggregated[key]["values"].append(snapshot.value)
        aggregated[key]["count"] += 1
        aggregated[key]["sum"] += snapshot.value
        aggregated[key]["min"] = min(aggregated[key]["min"], snapshot.value)
        aggregated[key]["max"] = max(aggregated[key]["max"], snapshot.value)

    # Calculate averages
    result = []
    for key in sorted(aggregated.keys()):
        data = aggregated[key]
        data["avg"] = data["sum"] / data["count"] if data["count"] > 0 else 0.0
        del data["values"]  # Remove raw values to reduce response size
        result.append(data)

    return result

# ========================================
# DASHBOARD ENDPOINTS
# ========================================

@router.get("/dashboard")
def get_analytics_dashboard(
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated analytics dashboard with key metrics and KPIs.
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Build base filters
        date_filter = and_(
            VolunteerTimeLog.date >= start_date,
            VolunteerTimeLog.date <= end_date
        )

        # Get project statistics
        project_query = select(Project)
        if project_id:
            project_query = project_query.where(Project.id == project_id)

        projects = db.exec(project_query).all()

        project_stats = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.status == "in_progress"]),
            "completed_projects": len([p for p in projects if p.status == "completed"]),
            "planning_projects": len([p for p in projects if p.status == "planning"])
        }

        # Get task statistics
        task_query = select(Task)
        if project_id:
            task_query = task_query.where(Task.project_id == project_id)

        tasks = db.exec(task_query).all()

        task_stats = {
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.status == "completed"]),
            "in_progress_tasks": len([t for t in tasks if t.status == "in_progress"]),
            "not_started_tasks": len([t for t in tasks if t.status == "not_started"]),
            "completion_rate": (len([t for t in tasks if t.status == "completed"]) / len(tasks) * 100) if tasks else 0
        }

        # Get volunteer statistics
        volunteer_count_query = select(func.count(Volunteer.id)).where(Volunteer.volunteer_status == "active")
        active_volunteers = db.exec(volunteer_count_query).one()

        # Get volunteer hours
        hours_query = select(func.sum(VolunteerTimeLog.hours)).where(
            and_(
                VolunteerTimeLog.approval_status == "approved",
                date_filter
            )
        )
        if project_id:
            hours_query = hours_query.where(VolunteerTimeLog.project_id == project_id)

        total_hours = db.exec(hours_query).one() or 0.0

        volunteer_stats = {
            "active_volunteers": active_volunteers,
            "total_hours_logged": float(total_hours),
            "avg_hours_per_volunteer": float(total_hours / active_volunteers) if active_volunteers > 0 else 0.0
        }

        # Get budget statistics (if project specified)
        budget_stats = {}
        if project_id:
            project = db.get(Project, project_id)
            if project:
                budget_stats = {
                    "total_budget": float(project.budget) if project.budget else 0.0,
                    "actual_cost": float(project.actual_cost) if project.actual_cost else 0.0,
                    "budget_utilization": (float(project.actual_cost) / float(project.budget) * 100) if project.budget and project.budget > 0 else 0.0
                }

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "project_filter": project_id,
            "summary": {
                "projects": project_stats,
                "tasks": task_stats,
                "volunteers": volunteer_stats,
                "budget": budget_stats if budget_stats else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@router.get("/trends/volunteer-hours")
def get_volunteer_hours_trends(
    start_date: date,
    end_date: date,
    project_id: Optional[int] = None,
    volunteer_id: Optional[int] = None,
    granularity: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get volunteer hours trends over time.
    """
    try:
        # Build query
        query = select(VolunteerTimeLog).where(
            and_(
                VolunteerTimeLog.date >= start_date,
                VolunteerTimeLog.date <= end_date,
                VolunteerTimeLog.approval_status == "approved"
            )
        )

        if project_id:
            query = query.where(VolunteerTimeLog.project_id == project_id)
        if volunteer_id:
            query = query.where(VolunteerTimeLog.volunteer_id == volunteer_id)

        time_logs = db.exec(query).all()

        # Aggregate by time period
        aggregated = {}
        for log in time_logs:
            if granularity == "daily":
                key = log.date.strftime("%Y-%m-%d")
            elif granularity == "weekly":
                key = log.date.strftime("%Y-W%W")
            elif granularity == "monthly":
                key = log.date.strftime("%Y-%m")
            else:
                key = log.date.strftime("%Y-%m")

            if key not in aggregated:
                aggregated[key] = {"period": key, "total_hours": 0.0, "log_count": 0}

            aggregated[key]["total_hours"] += float(log.hours)
            aggregated[key]["log_count"] += 1

        result = [aggregated[key] for key in sorted(aggregated.keys())]

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "granularity": granularity,
            "data_points": len(result),
            "trends": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer hours trends: {str(e)}"
        )

@router.get("/trends/project-progress")
def get_project_progress_trends(
    project_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project progress trends over time based on MetricSnapshot data.
    """
    try:
        # Check if project exists
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Set default dates
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = project.start_date or (end_date - timedelta(days=90))

        # Get progress snapshots
        query = select(MetricSnapshot).where(
            and_(
                MetricSnapshot.metric_type == MetricType.project_progress,
                MetricSnapshot.project_id == project_id,
                MetricSnapshot.snapshot_date >= datetime.combine(start_date, datetime.min.time()),
                MetricSnapshot.snapshot_date <= datetime.combine(end_date, datetime.max.time())
            )
        ).order_by(MetricSnapshot.snapshot_date)

        snapshots = db.exec(query).all()

        # Format results
        trends = [
            {
                "date": snapshot.snapshot_date.date().isoformat(),
                "progress_percentage": snapshot.value,
                "metadata": snapshot.metric_metadata
            }
            for snapshot in snapshots
        ]

        # If no snapshots, calculate current progress
        if not trends:
            from app.crud.project import project_crud
            project_data = project_crud.get_project_with_details(db, project_id)
            current_progress = (project_data["completed_tasks"] / max(project_data["total_tasks"], 1)) * 100 if project_data else 0.0

            trends = [{
                "date": date.today().isoformat(),
                "progress_percentage": current_progress,
                "metadata": {"source": "calculated"}
            }]

        return {
            "project_id": project_id,
            "project_name": project.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data_points": len(trends),
            "trends": trends
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project progress trends: {str(e)}"
        )

@router.get("/trends/environmental-impact")
def get_environmental_impact_trends(
    project_id: Optional[int] = None,
    metric_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get environmental impact metrics trends over time.
    """
    try:
        from app.models.project import EnvironmentalMetric

        # Set default dates
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Build query
        query = select(EnvironmentalMetric).where(
            and_(
                EnvironmentalMetric.measurement_date >= start_date,
                EnvironmentalMetric.measurement_date <= end_date
            )
        )

        if project_id:
            query = query.where(EnvironmentalMetric.project_id == project_id)
        if metric_name:
            query = query.where(EnvironmentalMetric.metric_name == metric_name)

        query = query.order_by(EnvironmentalMetric.measurement_date)

        metrics = db.exec(query).all()

        # Group by metric name and aggregate
        grouped = {}
        for metric in metrics:
            name = metric.metric_name
            if name not in grouped:
                grouped[name] = {
                    "metric_name": name,
                    "metric_type": metric.metric_type,
                    "unit": metric.unit,
                    "data_points": []
                }

            grouped[name]["data_points"].append({
                "date": metric.measurement_date.isoformat() if metric.measurement_date else None,
                "target_value": float(metric.target_value) if metric.target_value else None,
                "current_value": float(metric.current_value),
                "progress_percentage": (float(metric.current_value) / float(metric.target_value) * 100) if metric.target_value and metric.target_value > 0 else None,
                "project_id": metric.project_id
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics_count": len(grouped),
            "metrics": list(grouped.values())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve environmental impact trends: {str(e)}"
        )

# ========================================
# USER DASHBOARD MANAGEMENT
# ========================================

@router.post("/dashboards")
def create_dashboard(
    name: str,
    description: Optional[str] = None,
    widgets: Dict[str, Any] = {},
    is_default: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new custom dashboard."""
    try:
        # If setting as default, unset other defaults
        if is_default:
            existing_default = db.exec(
                select(Dashboard).where(
                    and_(Dashboard.user_id == current_user.id, Dashboard.is_default == True)
                )
            ).first()
            if existing_default:
                existing_default.is_default = False
                db.add(existing_default)

        dashboard = Dashboard(
            user_id=current_user.id,
            name=name,
            description=description,
            widgets=widgets,
            is_default=is_default
        )

        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)

        return {
            "success": True,
            "message": "Dashboard created successfully",
            "dashboard_id": dashboard.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}"
        )

@router.get("/dashboards")
def get_user_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all dashboards for the current user."""
    try:
        dashboards = db.exec(
            select(Dashboard).where(Dashboard.user_id == current_user.id)
        ).all()

        return {
            "count": len(dashboards),
            "dashboards": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "is_default": d.is_default,
                    "widgets": d.widgets,
                    "created_at": d.created_at.isoformat(),
                    "updated_at": d.updated_at.isoformat()
                }
                for d in dashboards
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboards: {str(e)}"
        )
