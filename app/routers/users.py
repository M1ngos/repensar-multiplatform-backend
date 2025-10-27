# app/routers/users.py
"""User management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import Optional

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.user import user_crud
from app.schemas.user import UserSummary, UserDetail, UserUpdate, UserTypeResponse
from app.schemas.common import PaginatedResponse, create_pagination_metadata

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


# ========================================
# USER ENDPOINTS
# ========================================

@router.get("/", response_model=PaginatedResponse[UserSummary])
def get_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, department, or employee ID"),
    user_type_id: Optional[int] = Query(None, description="Filter by user type ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users with filtering and search options.

    - **search**: Search by name, email, department, or employee ID (case-insensitive)
    - **user_type_id**: Filter by user type (admin, staff_member, volunteer, etc.)
    - **is_active**: Filter by active/inactive status
    - **department**: Filter by specific department
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    """
    try:
        # Check permissions - only admin and staff can list all users
        if current_user.user_type.name not in ["admin", "staff_member"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to list users"
            )

        # Calculate skip offset
        skip = (page - 1) * page_size

        # Get users with filters
        users, total = user_crud.get_users(
            db,
            skip=skip,
            limit=page_size,
            search=search,
            user_type_id=user_type_id,
            is_active=is_active,
            department=department
        )

        # Convert to summary format
        user_summaries = [
            UserSummary(
                id=user.id,
                name=user.name,
                email=user.email,
                user_type_name=user.user_type.name,
                department=user.department,
                is_active=user.is_active,
                profile_picture=user.profile_picture
            )
            for user in users
        ]

        # Create pagination metadata
        metadata = create_pagination_metadata(total, page, page_size)

        return PaginatedResponse[UserSummary](
            data=user_summaries,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/me", response_model=UserDetail)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user's profile."""
    try:
        return UserDetail(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            phone=current_user.phone,
            department=current_user.department,
            employee_id=current_user.employee_id,
            is_active=current_user.is_active,
            is_email_verified=current_user.is_email_verified,
            profile_picture=current_user.profile_picture,
            last_login=current_user.last_login,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            user_type=UserTypeResponse(
                id=current_user.user_type.id,
                name=current_user.user_type.name,
                description=current_user.user_type.description
            ),
            oauth_provider=current_user.oauth_provider
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserDetail)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID."""
    try:
        # Check permissions - users can view their own profile, admins/staff can view all
        if (current_user.user_type.name not in ["admin", "staff_member"] and
            current_user.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )

        user = user_crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserDetail(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            department=user.department,
            employee_id=user.employee_id,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            profile_picture=user.profile_picture,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            user_type=UserTypeResponse(
                id=user.user_type.id,
                name=user.user_type.name,
                description=user.user_type.description
            ),
            oauth_provider=user.oauth_provider
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserDetail)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information."""
    try:
        # Check permissions - users can update their own profile, admins/staff can update all
        if (current_user.user_type.name not in ["admin", "staff_member"] and
            current_user.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )

        # Check if user exists
        user = user_crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update user
        updated_user = user_crud.update_user(db, user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update user"
            )

        return UserDetail(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            phone=updated_user.phone,
            department=updated_user.department,
            employee_id=updated_user.employee_id,
            is_active=updated_user.is_active,
            is_email_verified=updated_user.is_email_verified,
            profile_picture=updated_user.profile_picture,
            last_login=updated_user.last_login,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            user_type=UserTypeResponse(
                id=updated_user.user_type.id,
                name=updated_user.user_type.name,
                description=updated_user.user_type.description
            ),
            oauth_provider=updated_user.oauth_provider
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.post("/{user_id}/deactivate", response_model=dict)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate user (soft delete)."""
    try:
        # Check permissions - only admins can deactivate users
        if current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to deactivate users"
            )

        # Prevent self-deactivation
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        success = user_crud.deactivate_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": "User deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )


@router.post("/{user_id}/activate", response_model=dict)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate user."""
    try:
        # Check permissions - only admins can activate users
        if current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to activate users"
            )

        success = user_crud.activate_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": "User activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


# ========================================
# UTILITY ENDPOINTS
# ========================================

@router.get("/types/all", response_model=list[UserTypeResponse])
def get_user_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user types."""
    try:
        user_types = user_crud.get_user_types(db)
        return [
            UserTypeResponse(
                id=ut.id,
                name=ut.name,
                description=ut.description
            )
            for ut in user_types
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user types: {str(e)}"
        )


@router.get("/departments/all", response_model=list[str])
def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all departments."""
    try:
        departments = user_crud.get_departments(db)
        return departments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve departments: {str(e)}"
        )
