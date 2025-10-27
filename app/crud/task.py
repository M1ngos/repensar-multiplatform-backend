# app/crud/task.py
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.models.task import Task, TaskDependency
from app.models.project import Project
from app.models.user import User
from app.models.volunteer import TaskVolunteer, Volunteer, VolunteerTimeLog
from app.schemas.task import TaskCreate, TaskUpdate, TaskDependencyCreate

class TaskCRUD:
    def create_task(self, db: Session, task_data: TaskCreate, current_user_id: int) -> Task:
        """Create a new task."""
        task = Task(
            **task_data.model_dump(exclude={'created_by_id'}),
            created_by_id=current_user_id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    def get_task(self, db: Session, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return db.get(Task, task_id)
    
    def get_tasks(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        suitable_for_volunteers: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Task]:
        """Get tasks with filtering options."""
        query = select(Task)
        
        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assigned_to_id:
            query = query.where(Task.assigned_to_id == assigned_to_id)
        if suitable_for_volunteers is not None:
            query = query.where(Task.suitable_for_volunteers == suitable_for_volunteers)
        if search:
            query = query.where(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%")
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        return db.exec(query).all()

    def count_tasks(
        self,
        db: Session,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        suitable_for_volunteers: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count tasks with filtering options (for pagination)."""
        query = select(func.count(Task.id))

        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assigned_to_id:
            query = query.where(Task.assigned_to_id == assigned_to_id)
        if suitable_for_volunteers is not None:
            query = query.where(Task.suitable_for_volunteers == suitable_for_volunteers)
        if search:
            query = query.where(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%")
                )
            )

        return db.exec(query).one()

    def update_task(self, db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update task."""
        task = db.get(Task, task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task
    
    def delete_task(self, db: Session, task_id: int) -> bool:
        """Delete task (mark as cancelled)."""
        task = db.get(Task, task_id)
        if not task:
            return False
        
        task.status = "cancelled"
        task.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    def get_task_with_details(self, db: Session, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task with all related details."""
        task = db.get(Task, task_id)
        if not task:
            return None
        
        # Get project info
        project = db.get(Project, task.project_id)
        
        # Get assigned user info
        assigned_user = None
        if task.assigned_to_id:
            assigned_user = db.get(User, task.assigned_to_id)
        
        # Get creator info
        creator = None
        if task.created_by_id:
            creator = db.get(User, task.created_by_id)
        
        # Get parent task
        parent_task = None
        if task.parent_task_id:
            parent_task = db.get(Task, task.parent_task_id)
        
        # Get subtasks
        subtasks = db.exec(
            select(Task).where(Task.parent_task_id == task_id)
        ).all()
        
        # Get volunteer assignments with volunteer info
        volunteer_assignments_query = (
            select(TaskVolunteer, Volunteer, User)
            .join(Volunteer, TaskVolunteer.volunteer_id == Volunteer.id)
            .join(User, Volunteer.user_id == User.id)
            .where(and_(TaskVolunteer.task_id == task_id, TaskVolunteer.is_active == True))
        )
        volunteer_data = db.exec(volunteer_assignments_query).all()
        
        # Get dependencies
        predecessor_deps = db.exec(
            select(TaskDependency, Task)
            .join(Task, TaskDependency.predecessor_task_id == Task.id)
            .where(TaskDependency.successor_task_id == task_id)
        ).all()
        
        successor_deps = db.exec(
            select(TaskDependency, Task)
            .join(Task, TaskDependency.successor_task_id == Task.id)
            .where(TaskDependency.predecessor_task_id == task_id)
        ).all()
        
        # Get volunteer hours for this task
        volunteer_hours = db.exec(
            select(func.coalesce(func.sum(VolunteerTimeLog.hours), 0))
            .where(and_(VolunteerTimeLog.task_id == task_id, VolunteerTimeLog.approved == True))
        ).first()
        
        return {
            "task": task,
            "project": project,
            "assigned_user": assigned_user,
            "creator": creator,
            "parent_task": parent_task,
            "subtasks": subtasks,
            "volunteer_assignments": volunteer_data,
            "predecessor_dependencies": predecessor_deps,
            "successor_dependencies": successor_deps,
            "volunteer_hours": float(volunteer_hours or 0)
        }
    
    def get_project_tasks(self, db: Session, project_id: int) -> List[Task]:
        """Get all tasks for a project."""
        query = select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
        return db.exec(query).all()
    
    def get_user_tasks(self, db: Session, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get tasks assigned to a user."""
        query = select(Task).where(Task.assigned_to_id == user_id)
        
        if status:
            query = query.where(Task.status == status)
        
        query = query.order_by(Task.priority.desc(), Task.end_date.asc())
        return db.exec(query).all()
    
    def get_volunteer_suitable_tasks(
        self, 
        db: Session, 
        volunteer_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get tasks suitable for volunteers, optionally filtered by volunteer skills."""
        query = (
            select(Task, Project)
            .join(Project, Task.project_id == Project.id)
            .where(and_(
                Task.suitable_for_volunteers == True,
                Task.status.in_(["not_started", "in_progress"]),
                Task.volunteer_spots > 0
            ))
        )
        
        # Get current volunteer assignments count
        subquery = (
            select(TaskVolunteer.task_id, func.count(TaskVolunteer.id).label("assigned_count"))
            .where(TaskVolunteer.is_active == True)
            .group_by(TaskVolunteer.task_id)
            .subquery()
        )
        
        # Filter tasks that still have available spots
        query = (
            select(Task, Project, func.coalesce(subquery.c.assigned_count, 0).label("assigned_count"))
            .join(Project, Task.project_id == Project.id)
            .outerjoin(subquery, Task.id == subquery.c.task_id)
            .where(and_(
                Task.suitable_for_volunteers == True,
                Task.status.in_(["not_started", "in_progress"]),
                Task.volunteer_spots > func.coalesce(subquery.c.assigned_count, 0)
            ))
            .offset(skip)
            .limit(limit)
        )
        
        results = db.exec(query).all()
        
        tasks_data = []
        for task, project, assigned_count in results:
            tasks_data.append({
                "task": task,
                "project": project,
                "assigned_volunteers": assigned_count or 0,
                "available_spots": task.volunteer_spots - (assigned_count or 0)
            })
        
        return tasks_data
    
    def get_task_stats(self, db: Session, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get task statistics."""
        base_query = select(Task)
        if project_id:
            base_query = base_query.where(Task.project_id == project_id)
        
        # Total counts
        total_tasks = db.exec(select(func.count(Task.id))).first()
        
        # Status counts
        status_counts = {}
        for status in ["not_started", "in_progress", "completed", "cancelled"]:
            count = db.exec(
                select(func.count(Task.id))
                .where(Task.status == status)
            ).first()
            status_counts[status] = count or 0
        
        # Priority counts
        priority_query = select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        if project_id:
            priority_query = priority_query.where(Task.project_id == project_id)
        priority_data = db.exec(priority_query).all()
        tasks_by_priority = {priority: count for priority, count in priority_data}
        
        # Project counts (if not filtering by project)
        tasks_by_project = {}
        if not project_id:
            project_query = (
                select(Project.name, func.count(Task.id))
                .join(Project, Task.project_id == Project.id)
                .group_by(Project.name)
            )
            project_data = db.exec(project_query).all()
            tasks_by_project = {project: count for project, count in project_data}
        
        # Overdue tasks
        today = date.today()
        overdue_count = db.exec(
            select(func.count(Task.id))
            .where(and_(
                Task.end_date < today,
                Task.status.in_(["not_started", "in_progress"])
            ))
        ).first()
        
        # Volunteer suitable tasks
        volunteer_suitable_count = db.exec(
            select(func.count(Task.id))
            .where(Task.suitable_for_volunteers == True)
        ).first()
        
        # Hours statistics
        estimated_hours = db.exec(
            select(func.coalesce(func.sum(Task.estimated_hours), 0))
        ).first()
        
        actual_hours = db.exec(
            select(func.coalesce(func.sum(Task.actual_hours), 0))
        ).first()
        
        # Completion rate
        completed_tasks = status_counts.get("completed", 0)
        completion_rate = (completed_tasks / max(total_tasks or 1, 1)) * 100
        
        return {
            "total_tasks": total_tasks or 0,
            "not_started": status_counts.get("not_started", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "completed": status_counts.get("completed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "overdue_tasks": overdue_count or 0,
            "volunteer_suitable_tasks": volunteer_suitable_count or 0,
            "total_estimated_hours": float(estimated_hours or 0),
            "total_actual_hours": float(actual_hours or 0),
            "completion_rate": completion_rate,
            "tasks_by_priority": tasks_by_priority,
            "tasks_by_project": tasks_by_project
        }

class TaskVolunteerCRUD:
    def assign_volunteer(self, db: Session, task_id: int, volunteer_id: int) -> Optional[TaskVolunteer]:
        """Assign volunteer to task."""
        # Check if already assigned and active
        existing = db.exec(
            select(TaskVolunteer)
            .where(and_(
                TaskVolunteer.task_id == task_id,
                TaskVolunteer.volunteer_id == volunteer_id,
                TaskVolunteer.is_active == True
            ))
        ).first()
        
        if existing:
            return None  # Already assigned
        
        # Check if task has available spots
        task = db.get(Task, task_id)
        if not task or not task.suitable_for_volunteers:
            return None
        
        current_assignments = db.exec(
            select(func.count(TaskVolunteer.id))
            .where(and_(TaskVolunteer.task_id == task_id, TaskVolunteer.is_active == True))
        ).first()
        
        if current_assignments >= task.volunteer_spots:
            return None  # No available spots
        
        assignment = TaskVolunteer(
            task_id=task_id,
            volunteer_id=volunteer_id
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def get_task_volunteers(self, db: Session, task_id: int) -> List[Dict[str, Any]]:
        """Get volunteers assigned to a task."""
        query = (
            select(TaskVolunteer, Volunteer, User)
            .join(Volunteer, TaskVolunteer.volunteer_id == Volunteer.id)
            .join(User, Volunteer.user_id == User.id)
            .where(and_(TaskVolunteer.task_id == task_id, TaskVolunteer.is_active == True))
        )
        results = db.exec(query).all()
        
        volunteers = []
        for assignment, volunteer, user in results:
            volunteers.append({
                "assignment": assignment,
                "volunteer": volunteer,
                "user": user
            })
        
        return volunteers
    
    def get_volunteer_tasks(self, db: Session, volunteer_id: int) -> List[Dict[str, Any]]:
        """Get tasks assigned to a volunteer."""
        query = (
            select(TaskVolunteer, Task, Project)
            .join(Task, TaskVolunteer.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(and_(TaskVolunteer.volunteer_id == volunteer_id, TaskVolunteer.is_active == True))
            .order_by(Task.priority.desc(), Task.end_date.asc())
        )
        results = db.exec(query).all()
        
        tasks = []
        for assignment, task, project in results:
            tasks.append({
                "assignment": assignment,
                "task": task,
                "project": project
            })
        
        return tasks
    
    def update_volunteer_assignment(
        self, 
        db: Session, 
        task_id: int, 
        volunteer_id: int, 
        hours_contributed: Optional[float] = None,
        performance_rating: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[TaskVolunteer]:
        """Update volunteer assignment."""
        assignment = db.exec(
            select(TaskVolunteer)
            .where(and_(
                TaskVolunteer.task_id == task_id,
                TaskVolunteer.volunteer_id == volunteer_id
            ))
        ).first()
        
        if not assignment:
            return None
        
        if hours_contributed is not None:
            assignment.hours_contributed = hours_contributed
        if performance_rating is not None:
            assignment.performance_rating = performance_rating
        if notes is not None:
            assignment.notes = notes
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def remove_volunteer(self, db: Session, task_id: int, volunteer_id: int) -> bool:
        """Remove volunteer from task."""
        assignment = db.exec(
            select(TaskVolunteer)
            .where(and_(
                TaskVolunteer.task_id == task_id,
                TaskVolunteer.volunteer_id == volunteer_id,
                TaskVolunteer.is_active == True
            ))
        ).first()
        
        if not assignment:
            return False
        
        assignment.is_active = False
        assignment.removed_at = datetime.utcnow()
        db.commit()
        return True

class TaskDependencyCRUD:
    def create_dependency(self, db: Session, dependency_data: TaskDependencyCreate) -> TaskDependency:
        """Create task dependency."""
        dependency = TaskDependency(**dependency_data.model_dump())
        db.add(dependency)
        db.commit()
        db.refresh(dependency)
        return dependency
    
    def get_task_dependencies(self, db: Session, task_id: int) -> Dict[str, List[TaskDependency]]:
        """Get all dependencies for a task."""
        # Predecessors (tasks this task depends on)
        predecessors = db.exec(
            select(TaskDependency)
            .where(TaskDependency.successor_task_id == task_id)
        ).all()
        
        # Successors (tasks that depend on this task)
        successors = db.exec(
            select(TaskDependency)
            .where(TaskDependency.predecessor_task_id == task_id)
        ).all()
        
        return {
            "predecessors": predecessors,
            "successors": successors
        }
    
    def delete_dependency(self, db: Session, dependency_id: int) -> bool:
        """Delete task dependency."""
        dependency = db.get(TaskDependency, dependency_id)
        if not dependency:
            return False
        
        db.delete(dependency)
        db.commit()
        return True

# Create instances
task_crud = TaskCRUD()
task_volunteer_crud = TaskVolunteerCRUD()
task_dependency_crud = TaskDependencyCRUD()