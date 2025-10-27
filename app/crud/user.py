# app/crud/user.py
"""User CRUD operations."""
from sqlmodel import Session, select, func, or_
from typing import List, Optional
from datetime import datetime

from app.models.user import User, UserType
from app.schemas.user import UserUpdate


class UserCRUD:
    """CRUD operations for User model."""

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.get(User, user_id)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.exec(select(User).where(User.email == email)).first()

    def get_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        user_type_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        department: Optional[str] = None
    ) -> tuple[List[User], int]:
        """
        Get users with optional filtering and search.

        Returns:
            Tuple of (users list, total count)
        """
        # Build base query
        query = select(User).join(UserType, User.user_type_id == UserType.id)
        count_query = select(func.count(User.id)).join(UserType, User.user_type_id == UserType.id)

        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            search_filter = or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.department.ilike(search_pattern),
                User.employee_id.ilike(search_pattern)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if user_type_id:
            query = query.where(User.user_type_id == user_type_id)
            count_query = count_query.where(User.user_type_id == user_type_id)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        if department:
            query = query.where(User.department == department)
            count_query = count_query.where(User.department == department)

        # Get total count
        total = db.exec(count_query).one()

        # Apply pagination and fetch results
        query = query.offset(skip).limit(limit).order_by(User.name)
        users = db.exec(query).all()

        return list(users), total

    def update_user(
        self, db: Session, user_id: int, user_data: UserUpdate
    ) -> Optional[User]:
        """Update user information."""
        user = self.get_user(db, user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            for key, value in update_data.items():
                setattr(user, key, value)

            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate user (soft delete)."""
        user = self.get_user(db, user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        return True

    def activate_user(self, db: Session, user_id: int) -> bool:
        """Activate user."""
        user = self.get_user(db, user_id)
        if not user:
            return False

        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        return True

    def get_user_types(self, db: Session) -> List[UserType]:
        """Get all user types."""
        return db.exec(select(UserType)).all()

    def get_departments(self, db: Session) -> List[str]:
        """Get list of unique departments."""
        query = select(User.department).where(User.department.isnot(None)).distinct()
        departments = db.exec(query).all()
        return [dept for dept in departments if dept]


# Create a singleton instance
user_crud = UserCRUD()
