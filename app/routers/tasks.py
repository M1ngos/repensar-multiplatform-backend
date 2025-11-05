# app/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional, Dict

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.analytics import NotificationType
from app.crud.task import task_crud, task_volunteer_crud, task_dependency_crud
from app.crud.project import project_crud
from app.schemas.task import (
    # Task schemas
    TaskCreate, TaskUpdate, Task, TaskSummary, TaskDetail, TaskProgress, TaskStats,

    # Volunteer assignment schemas
    TaskVolunteerCreate, TaskVolunteerUpdate, TaskVolunteerAssignment,
    VolunteerTaskAssignment, TaskVolunteerMatch,

    # Dependency schemas
    TaskDependencyCreate, TaskDependency
)
from app.services.notification_service import NotificationService
from app.services.analytics_service import AnalyticsService, log_task_assignment
from app.services.event_bus import EventType, get_event_bus

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# ========================================
# TASK ENDPOINTS
# ========================================

@router.post("/", response_model=Task)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task."""
    try:
        # Check if project exists
        project = project_crud.get_project(db, task_data.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check permissions
        if (current_user.user_type.name not in ["admin", "project_manager"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create tasks for this project"
            )
        
        task = task_crud.create_task(db, task_data, current_user.id)
        return Task(**task.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/", response_model=List[TaskSummary])
def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    project_id: Optional[int] = None,
    status: Optional[str] = Query(None, regex="^(not_started|in_progress|completed|cancelled)$"),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    assigned_to_id: Optional[int] = None,
    suitable_for_volunteers: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of tasks with filtering options."""
    try:
        tasks = task_crud.get_tasks(
            db, skip=skip, limit=limit, project_id=project_id,
            status=status, priority=priority, assigned_to_id=assigned_to_id,
            suitable_for_volunteers=suitable_for_volunteers, search=search
        )
        
        # Convert to summary format
        task_summaries = []
        for task in tasks:
            # Get project name
            project = project_crud.get_project(db, task.project_id)
            project_name = project.name if project else "Unknown Project"
            
            # Get assigned user name
            assigned_to_name = None
            if task.assigned_to_id:
                assigned_user = db.get(User, task.assigned_to_id)
                if assigned_user:
                    assigned_to_name = assigned_user.name
            
            # Get volunteers assigned count
            volunteer_assignments = task_volunteer_crud.get_task_volunteers(db, task.id)
            volunteers_assigned = len(volunteer_assignments)
            
            # Calculate days remaining
            days_remaining = None
            is_overdue = False
            if task.end_date:
                from datetime import date
                today = date.today()
                days_remaining = (task.end_date - today).days
                is_overdue = days_remaining < 0 and task.status in ["not_started", "in_progress"]
            
            summary = TaskSummary(
                id=task.id,
                title=task.title,
                status=task.status,
                priority=task.priority,
                start_date=task.start_date,
                end_date=task.end_date,
                estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
                actual_hours=float(task.actual_hours),
                progress_percentage=task.progress_percentage,
                suitable_for_volunteers=task.suitable_for_volunteers,
                volunteer_spots=task.volunteer_spots,
                project_name=project_name,
                assigned_to_name=assigned_to_name,
                volunteers_assigned=volunteers_assigned,
                days_remaining=days_remaining,
                is_overdue=is_overdue
            )
            task_summaries.append(summary)
        
        return task_summaries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}"
        )

@router.get("/stats", response_model=TaskStats)
def get_task_stats(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task statistics."""
    try:
        stats = task_crud.get_task_stats(db, project_id=project_id)
        return TaskStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task stats: {str(e)}"
        )

@router.get("/volunteers/available", response_model=List[TaskVolunteerMatch])
def get_volunteer_available_tasks(
    volunteer_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks available for volunteers."""
    try:
        tasks_data = task_crud.get_volunteer_suitable_tasks(db, volunteer_id, skip, limit)
        
        matches = []
        for data in tasks_data:
            task = data["task"]
            project = data["project"]
            
            match = TaskVolunteerMatch(
                task_id=task.id,
                task_title=task.title,
                project_name=project.name,
                required_skills=task.required_skills,
                volunteer_spots=task.volunteer_spots,
                current_volunteers=data["assigned_volunteers"],
                priority=task.priority,
                start_date=task.start_date,
                end_date=task.end_date,
                match_score=0.0  # TODO: Implement skill matching algorithm
            )
            matches.append(match)
        
        return matches
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer tasks: {str(e)}"
        )

@router.get("/{task_id}", response_model=TaskDetail)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed task information."""
    try:
        task_data = task_crud.get_task_with_details(db, task_id)
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task = task_data["task"]
        project = task_data["project"]
        
        # Build detailed response
        detail = TaskDetail(
            **task.model_dump(),
            project_name=project.name if project else "Unknown",
            project_status=project.status if project else "unknown",
            assigned_to_name=task_data["assigned_user"].name if task_data["assigned_user"] else None,
            created_by_name=task_data["creator"].name if task_data["creator"] else None,
            parent_task_title=task_data["parent_task"].title if task_data["parent_task"] else None,
            subtasks=[],  # Will be populated below
            volunteer_assignments=[],  # Will be populated below
            dependencies=[],  # Will be populated below
            completion_percentage=task.progress_percentage,
            volunteer_hours=task_data["volunteer_hours"]
        )
        
        # Add subtasks
        for subtask in task_data["subtasks"]:
            detail.subtasks.append(TaskSummary(
                id=subtask.id,
                title=subtask.title,
                status=subtask.status,
                priority=subtask.priority,
                start_date=subtask.start_date,
                end_date=subtask.end_date,
                estimated_hours=float(subtask.estimated_hours) if subtask.estimated_hours else None,
                actual_hours=float(subtask.actual_hours),
                progress_percentage=subtask.progress_percentage,
                suitable_for_volunteers=subtask.suitable_for_volunteers,
                volunteer_spots=subtask.volunteer_spots,
                project_name=project.name if project else "Unknown",
                volunteers_assigned=0  # Could be calculated if needed
            ))
        
        # Add volunteer assignments
        for assignment, volunteer, user in task_data["volunteer_assignments"]:
            detail.volunteer_assignments.append(TaskVolunteerAssignment(
                **assignment.model_dump(),
                volunteer_name=user.name,
                volunteer_id_code=volunteer.volunteer_id,
                volunteer_email=user.email
            ))
        
        # Add dependencies
        for dep, pred_task in task_data["predecessor_dependencies"]:
            detail.dependencies.append(TaskDependency(
                **dep.model_dump(),
                predecessor_title=pred_task.title,
                successor_title=task.title
            ))
        
        for dep, succ_task in task_data["successor_dependencies"]:
            detail.dependencies.append(TaskDependency(
                **dep.model_dump(),
                predecessor_title=task.title,
                successor_title=succ_task.title
            ))
        
        # Calculate additional metrics
        if task.end_date:
            from datetime import date
            today = date.today()
            days_remaining = (task.end_date - today).days
            detail.days_remaining = days_remaining
            detail.is_overdue = days_remaining < 0 and task.status in ["not_started", "in_progress"]
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task: {str(e)}"
        )

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task."""
    try:
        # Check if task exists
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Check permissions
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin"] and
            project.project_manager_id != current_user.id and
            task.assigned_to_id != current_user.id and
            task.created_by_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )

        # Track old status for notification
        old_status = task.status
        old_title = task.title

        updated_task = task_crud.update_task(db, task_id, task_data)

        # Send notifications if status changed
        if task_data.status and task_data.status != old_status:
            # Get all volunteers assigned to this task
            volunteer_assignments = task_volunteer_crud.get_task_volunteers(db, task_id)

            # Notify assigned volunteers and task owner
            from app.models.volunteer import Volunteer
            users_to_notify = set()

            # Add task assignee if exists
            if updated_task.assigned_to_id:
                users_to_notify.add(updated_task.assigned_to_id)

            # Add volunteers
            for assignment in volunteer_assignments:
                volunteer = db.get(Volunteer, assignment.volunteer_id)
                if volunteer:
                    users_to_notify.add(volunteer.user_id)

            # Add project manager
            if project.project_manager_id:
                users_to_notify.add(project.project_manager_id)

            # Remove current user from notifications (they made the change)
            users_to_notify.discard(current_user.id)

            # Send notifications
            for user_id in users_to_notify:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    title="Task Status Updated",
                    message=f'Task "{updated_task.title}" status changed from {old_status} to {updated_task.status}',
                    notification_type=NotificationType.info,
                    related_task_id=task_id,
                    related_project_id=updated_task.project_id
                )

            # Publish event
            try:
                event_bus = get_event_bus()
                await event_bus.publish(
                    EventType.TASK_STATUS_CHANGED,
                    {
                        "task_id": task_id,
                        "task_title": updated_task.title,
                        "old_status": old_status,
                        "new_status": updated_task.status,
                        "project_id": updated_task.project_id,
                        "changed_by": current_user.id
                    }
                )

                # Track completion metric
                if updated_task.status == "completed":
                    from app.services.analytics_service import track_task_completion
                    await track_task_completion(db, task_id, updated_task.project_id)
                    await event_bus.publish(EventType.TASK_COMPLETED, {
                        "task_id": task_id,
                        "task_title": updated_task.title,
                        "project_id": updated_task.project_id
                    })
            except Exception as e:
                # Don't fail the request if event publishing fails
                pass

        return Task(**updated_task.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.delete("/{task_id}", response_model=dict)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task (mark as cancelled)."""
    try:
        # Check if task exists
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin"] and 
            project.project_manager_id != current_user.id and
            task.created_by_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this task"
            )
        
        success = task_crud.delete_task(db, task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )

# ========================================
# TASK VOLUNTEER ASSIGNMENT ENDPOINTS
# ========================================

@router.get("/{task_id}/volunteers", response_model=List[TaskVolunteerAssignment])
def get_task_volunteers(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get volunteers assigned to a task."""
    try:
        volunteers_data = task_volunteer_crud.get_task_volunteers(db, task_id)
        
        assignments = []
        for data in volunteers_data:
            assignment = data["assignment"]
            volunteer = data["volunteer"]
            user = data["user"]
            
            assignments.append(TaskVolunteerAssignment(
                **assignment.model_dump(),
                volunteer_name=user.name,
                volunteer_id_code=volunteer.volunteer_id,
                volunteer_email=user.email
            ))
        
        return assignments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task volunteers: {str(e)}"
        )

@router.post("/{task_id}/volunteers", response_model=TaskVolunteerAssignment)
async def assign_volunteer_to_task(
    task_id: int,
    volunteer_data: TaskVolunteerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign volunteer to task."""
    try:
        # Check if task exists and is suitable for volunteers
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        if not task.suitable_for_volunteers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is not suitable for volunteers"
            )

        # Check permissions
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager", "staff_member"] and
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign volunteers to this task"
            )

        assignment = task_volunteer_crud.assign_volunteer(db, task_id, volunteer_data.volunteer_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volunteer already assigned or no available spots"
            )

        # Get volunteer info for response
        from app.models.volunteer import Volunteer
        from app.models.user import User
        volunteer = db.get(Volunteer, assignment.volunteer_id)
        user = db.get(User, volunteer.user_id)

        # Send notification to volunteer about task assignment
        await NotificationService.create_notification(
            db=db,
            user_id=user.id,
            title="New Task Assignment",
            message=f'You have been assigned to task: "{task.title}"',
            notification_type=NotificationType.info,
            related_task_id=task_id,
            related_project_id=task.project_id
        )

        # Log activity
        await log_task_assignment(
            db=db,
            task_id=task_id,
            volunteer_id=volunteer.id,
            assigned_by_id=current_user.id,
            project_id=task.project_id
        )

        # Publish event
        try:
            event_bus = get_event_bus()
            await event_bus.publish(
                EventType.TASK_ASSIGNED,
                {
                    "task_id": task_id,
                    "task_title": task.title,
                    "volunteer_id": volunteer.id,
                    "user_id": user.id,
                    "project_id": task.project_id,
                    "assigned_by": current_user.id
                },
                user_id=user.id
            )
        except Exception as e:
            # Don't fail the request if event publishing fails
            pass

        return TaskVolunteerAssignment(
            **assignment.model_dump(),
            volunteer_name=user.name,
            volunteer_id_code=volunteer.volunteer_id,
            volunteer_email=user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign volunteer: {str(e)}"
        )

@router.put("/{task_id}/volunteers/{volunteer_id}", response_model=TaskVolunteerAssignment)
def update_volunteer_assignment(
    task_id: int,
    volunteer_id: int,
    update_data: TaskVolunteerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update volunteer assignment."""
    try:
        # Check permissions
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager", "staff_member"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update volunteer assignments"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        assignment = task_volunteer_crud.update_volunteer_assignment(
            db, task_id, volunteer_id, 
            hours_contributed=update_dict.get('hours_contributed'),
            performance_rating=update_dict.get('performance_rating'),
            notes=update_dict.get('notes')
        )
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer assignment not found"
            )
        
        # Get volunteer info for response
        from app.models.volunteer import Volunteer
        from app.models.user import User
        volunteer = db.get(Volunteer, assignment.volunteer_id)
        user = db.get(User, volunteer.user_id)
        
        return TaskVolunteerAssignment(
            **assignment.model_dump(),
            volunteer_name=user.name,
            volunteer_id_code=volunteer.volunteer_id,
            volunteer_email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update volunteer assignment: {str(e)}"
        )

@router.delete("/{task_id}/volunteers/{volunteer_id}", response_model=dict)
def remove_volunteer_from_task(
    task_id: int,
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove volunteer from task."""
    try:
        # Check permissions
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove volunteers from this task"
            )
        
        success = task_volunteer_crud.remove_volunteer(db, task_id, volunteer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Volunteer assignment not found"
            )
        
        return {"message": "Volunteer removed from task successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove volunteer: {str(e)}"
        )

# ========================================
# TASK DEPENDENCY ENDPOINTS
# ========================================

@router.get("/{task_id}/dependencies", response_model=Dict[str, List[TaskDependency]])
def get_task_dependencies(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task dependencies."""
    try:
        dependencies = task_dependency_crud.get_task_dependencies(db, task_id)
        
        # Add task titles to dependencies
        result = {"predecessors": [], "successors": []}
        
        for dep in dependencies["predecessors"]:
            pred_task = task_crud.get_task(db, dep.predecessor_task_id)
            succ_task = task_crud.get_task(db, dep.successor_task_id)
            result["predecessors"].append(TaskDependency(
                **dep.model_dump(),
                predecessor_title=pred_task.title if pred_task else "Unknown",
                successor_title=succ_task.title if succ_task else "Unknown"
            ))
        
        for dep in dependencies["successors"]:
            pred_task = task_crud.get_task(db, dep.predecessor_task_id)
            succ_task = task_crud.get_task(db, dep.successor_task_id)
            result["successors"].append(TaskDependency(
                **dep.model_dump(),
                predecessor_title=pred_task.title if pred_task else "Unknown",
                successor_title=succ_task.title if succ_task else "Unknown"
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dependencies: {str(e)}"
        )

@router.post("/{task_id}/dependencies", response_model=TaskDependency)
def create_task_dependency(
    task_id: int,
    dependency_data: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create task dependency."""
    try:
        # Validate that one of the tasks is the current task
        if dependency_data.predecessor_task_id != task_id and dependency_data.successor_task_id != task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dependency must involve the specified task"
            )
        
        # Check permissions
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        project = project_crud.get_project(db, task.project_id)
        if (current_user.user_type.name not in ["admin", "project_manager"] and 
            project.project_manager_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create task dependencies"
            )
        
        dependency = task_dependency_crud.create_dependency(db, dependency_data)
        
        # Get task titles for response
        pred_task = task_crud.get_task(db, dependency.predecessor_task_id)
        succ_task = task_crud.get_task(db, dependency.successor_task_id)
        
        return TaskDependency(
            **dependency.model_dump(),
            predecessor_title=pred_task.title if pred_task else "Unknown",
            successor_title=succ_task.title if succ_task else "Unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dependency: {str(e)}"
        )

@router.delete("/dependencies/{dependency_id}", response_model=dict)
def delete_task_dependency(
    dependency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task dependency."""
    try:
        # Check permissions - this requires finding the task through the dependency
        dependency = task_dependency_crud.get_task_dependencies(db, dependency_id)  # This method needs to be updated
        
        # For now, allow project managers and admins to delete dependencies
        if current_user.user_type.name not in ["admin", "project_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete task dependencies"
            )
        
        success = task_dependency_crud.delete_dependency(db, dependency_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dependency not found"
            )
        
        return {"message": "Task dependency deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dependency: {str(e)}"
        )

# ========================================
# VOLUNTEER TASK ENDPOINTS
# ========================================

@router.get("/volunteers/{volunteer_id}/assignments", response_model=List[VolunteerTaskAssignment])
def get_volunteer_task_assignments(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks assigned to a volunteer."""
    try:
        # Check permissions
        if (current_user.user_type.name not in ["admin", "staff_member", "project_manager"]):
            # Check if it's the volunteer's own tasks
            from app.models.volunteer import Volunteer
            volunteer = db.get(Volunteer, volunteer_id)
            if not volunteer or volunteer.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view these task assignments"
                )
        
        tasks_data = task_volunteer_crud.get_volunteer_tasks(db, volunteer_id)
        
        assignments = []
        for data in tasks_data:
            assignment = data["assignment"]
            task = data["task"]
            project = data["project"]
            
            assignments.append(VolunteerTaskAssignment(
                task_id=task.id,
                task_title=task.title,
                project_name=project.name,
                status=task.status,
                priority=task.priority,
                estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
                start_date=task.start_date,
                end_date=task.end_date,
                required_skills=task.required_skills,
                hours_contributed=float(assignment.hours_contributed),
                assigned_at=assignment.assigned_at
            ))
        
        return assignments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve volunteer assignments: {str(e)}"
        )