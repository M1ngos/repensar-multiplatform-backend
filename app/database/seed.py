from sqlmodel import Session
from app.database.engine import engine
from app.models.user import UserType

def seed_user_types():
    """Seed initial user types"""
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