# app/services/search_service.py
"""
Full-text search service using PostgreSQL.
"""
from sqlmodel import Session, select, text, col, or_, and_
from typing import List, Dict, Any
from app.models.project import Project
from app.models.task import Task
from app.models.volunteer import Volunteer
from app.models.user import User


class SearchService:
    """Service for full-text search across entities."""

    @staticmethod
    def search_projects(db: Session, query: str, limit: int = 20) -> List[Project]:
        """
        Search projects by name, description, and location.

        Args:
            db: Database session
            query: Search query
            limit: Maximum results

        Returns:
            List of matching projects
        """
        # PostgreSQL full-text search
        search_query = select(Project).where(
            or_(
                col(Project.name).contains(query),
                col(Project.description).contains(query),
                col(Project.location).contains(query)
            )
        ).limit(limit)

        return list(db.exec(search_query).all())

    @staticmethod
    def search_tasks(db: Session, query: str, limit: int = 20) -> List[Task]:
        """
        Search tasks by title and description.

        Args:
            db: Database session
            query: Search query
            limit: Maximum results

        Returns:
            List of matching tasks
        """
        search_query = select(Task).where(
            or_(
                col(Task.title).contains(query),
                col(Task.description).contains(query)
            )
        ).limit(limit)

        return list(db.exec(search_query).all())

    @staticmethod
    def search_volunteers(db: Session, query: str, limit: int = 20) -> List[Dict]:
        """
        Search volunteers by name, skills, and bio.

        Args:
            db: Database session
            query: Search query
            limit: Maximum results

        Returns:
            List of matching volunteers with user info
        """
        # Join with users to search names
        results = db.exec(
            select(Volunteer, User)
            .join(User, Volunteer.user_id == User.id)
            .where(
                or_(
                    col(User.name).contains(query),
                    col(User.email).contains(query),
                    col(Volunteer.bio).contains(query)
                )
            )
            .limit(limit)
        ).all()

        return [
            {
                "volunteer": volunteer,
                "user": user
            }
            for volunteer, user in results
        ]

    @staticmethod
    def global_search(db: Session, query: str) -> Dict[str, List]:
        """
        Search across all entities.

        Args:
            db: Database session
            query: Search query

        Returns:
            Dict with projects, tasks, and volunteers results
        """
        return {
            "projects": SearchService.search_projects(db, query, limit=10),
            "tasks": SearchService.search_tasks(db, query, limit=10),
            "volunteers": SearchService.search_volunteers(db, query, limit=10)
        }
