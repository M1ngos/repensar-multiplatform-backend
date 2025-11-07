"""
DEPRECATED: This seed script is deprecated.

Database seeding is now handled by Alembic migrations.
See: alembic/versions/cd04f478e6b0_seed_initial_user_types.py

To seed the database, run: alembic upgrade head

This file is kept for reference only.
"""

from sqlmodel import Session
from app.database.engine import engine
from app.models.user import UserType

import warnings

def seed_user_types():
    """
    DEPRECATED: Seed initial user types

    This function is deprecated. Use Alembic migrations instead:
        alembic upgrade head
    """
    warnings.warn(
        "seed_user_types() is deprecated. Use 'alembic upgrade head' instead.",
        DeprecationWarning,
        stacklevel=2
    )

    with Session(engine) as session:
        # Check if user types already exist
        existing_types = session.query(UserType).count()
        if existing_types > 0:
            print("User types already seeded")
            return
        
        # Create default user types
        user_types = [
            UserType(name="volunteer", description="Volunteer user"),
            UserType(name="organization", description="Organization user"),
            UserType(name="admin", description="Administrator user"),
        ]
        
        for user_type in user_types:
            session.add(user_type)
        
        session.commit()
        print("User types seeded successfully")

if __name__ == "__main__":
    seed_user_types()