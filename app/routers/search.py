# app/routers/search.py
"""
Search API for full-text search across projects, tasks, and volunteers.
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List, Dict, Any

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.search_service import SearchService
from pydantic import BaseModel

router = APIRouter(prefix="/search", tags=["search"])


class SearchResults(BaseModel):
    """Search results across all entities."""
    projects: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    volunteers: List[Dict[str, Any]]
    total: int


@router.get("", response_model=SearchResults)
async def global_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search across projects, tasks, and volunteers.

    Returns up to 10 results per category.
    """
    results = SearchService.global_search(db, q)

    # Convert to dicts
    projects = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "type": "project"
        }
        for p in results["projects"]
    ]

    tasks = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "project_id": t.project_id,
            "type": "task"
        }
        for t in results["tasks"]
    ]

    volunteers = [
        {
            "id": v["volunteer"].id,
            "name": v["user"].name,
            "email": v["user"].email,
            "bio": v["volunteer"].bio,
            "type": "volunteer"
        }
        for v in results["volunteers"]
    ]

    return SearchResults(
        projects=projects,
        tasks=tasks,
        volunteers=volunteers,
        total=len(projects) + len(tasks) + len(volunteers)
    )


@router.get("/projects")
async def search_projects(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search projects only."""
    projects = SearchService.search_projects(db, q, limit)
    return [{"id": p.id, "name": p.name, "description": p.description} for p in projects]


@router.get("/tasks")
async def search_tasks(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search tasks only."""
    tasks = SearchService.search_tasks(db, q, limit)
    return [{"id": t.id, "title": t.title, "description": t.description, "project_id": t.project_id} for t in tasks]


@router.get("/volunteers")
async def search_volunteers(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search volunteers only."""
    volunteers = SearchService.search_volunteers(db, q, limit)
    return [
        {
            "id": v["volunteer"].id,
            "name": v["user"].name,
            "email": v["user"].email,
            "bio": v["volunteer"].bio
        }
        for v in volunteers
    ]
