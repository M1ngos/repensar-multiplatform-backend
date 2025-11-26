#!/usr/bin/env python3
"""
Database clearing script for Repensar Multiplatform Backend.

This script removes all seeded data from the database while preserving
the schema and essential system data (user types, etc.).

IMPORTANT: This will delete ALL data! Use with caution.

Usage:
    python scripts/clear_data.py [--confirm] [--preserve-admin]

    --confirm: Skip confirmation prompt
    --preserve-admin: Keep admin, manager, and staff test users
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Add project root to path
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select, delete
from app.database.engine import engine
from app.models.user import User
from app.models.volunteer import (
    Volunteer, VolunteerSkillAssignment, VolunteerTimeLog, TaskVolunteer
)
from app.models.project import (
    Project, ProjectTeam, Milestone, EnvironmentalMetric
)
from app.models.task import Task, TaskDependency
from app.models.resource import Resource, ProjectResource
from app.models.analytics import Notification, ActivityLog
from app.models.communication import Conversation, Message
from app.models.blog import BlogPost, BlogPostTag, BlogPostCategory, Tag, Category
from app.models.gamification import (
    VolunteerBadge, VolunteerAchievement, VolunteerPoints, PointsHistory,
    Leaderboard, Badge, Achievement
)

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def clear_table(session: Session, model, name: str, preserve_condition=None) -> int:
    """
    Clear a table with optional preservation condition.

    Args:
        session: Database session
        model: SQLModel class
        name: Display name for the table
        preserve_condition: Optional WHERE condition to preserve certain rows

    Returns:
        Number of deleted rows
    """
    try:
        if preserve_condition is not None:
            # Delete with condition (e.g., preserve admin users)
            stmt = delete(model).where(preserve_condition)
        else:
            # Delete all rows
            stmt = delete(model)

        result = session.exec(stmt)
        count = result.rowcount if hasattr(result, 'rowcount') else 0
        session.commit()

        print(f"{Colors.GREEN}✓{Colors.RESET} Cleared {name}: {count} rows deleted")
        return count
    except Exception as e:
        session.rollback()
        print(f"{Colors.RED}✗{Colors.RESET} Failed to clear {name}: {str(e)}")
        return 0


def clear_all_data(preserve_admin: bool = False):
    """Clear all data from the database."""
    print_header("Clearing Database")

    total_deleted = 0

    with Session(engine) as session:
        # Order matters! Delete child tables before parent tables to avoid FK violations

        print(f"{Colors.BOLD}Phase 1: Communication & Notifications{Colors.RESET}")
        total_deleted += clear_table(session, Message, "Messages")
        total_deleted += clear_table(session, Conversation, "Conversations")
        total_deleted += clear_table(session, Notification, "Notifications")

        print(f"\n{Colors.BOLD}Phase 2: Blog{Colors.RESET}")
        total_deleted += clear_table(session, BlogPostTag, "Blog Post Tags")
        total_deleted += clear_table(session, BlogPostCategory, "Blog Post Categories")
        total_deleted += clear_table(session, BlogPost, "Blog Posts")
        total_deleted += clear_table(session, Tag, "Blog Tags")
        total_deleted += clear_table(session, Category, "Blog Categories")

        print(f"\n{Colors.BOLD}Phase 3: Activity Logs{Colors.RESET}")
        total_deleted += clear_table(session, ActivityLog, "Activity Logs")

        print(f"\n{Colors.BOLD}Phase 4: Gamification{Colors.RESET}")
        total_deleted += clear_table(session, PointsHistory, "Points History")
        total_deleted += clear_table(session, VolunteerBadge, "Volunteer Badges")
        total_deleted += clear_table(session, VolunteerAchievement, "Volunteer Achievements")
        total_deleted += clear_table(session, VolunteerPoints, "Volunteer Points")
        total_deleted += clear_table(session, Leaderboard, "Leaderboards")
        total_deleted += clear_table(session, Achievement, "Achievements")
        total_deleted += clear_table(session, Badge, "Badges")

        print(f"\n{Colors.BOLD}Phase 5: Task Dependencies{Colors.RESET}")
        total_deleted += clear_table(session, TaskDependency, "Task Dependencies")
        total_deleted += clear_table(session, TaskVolunteer, "Task Volunteers")

        print(f"\n{Colors.BOLD}Phase 6: Tasks{Colors.RESET}")
        total_deleted += clear_table(session, Task, "Tasks")

        print(f"\n{Colors.BOLD}Phase 7: Volunteer Data{Colors.RESET}")
        total_deleted += clear_table(session, VolunteerTimeLog, "Volunteer Time Logs")
        total_deleted += clear_table(session, VolunteerSkillAssignment, "Volunteer Skills")
        total_deleted += clear_table(session, Volunteer, "Volunteers")

        print(f"\n{Colors.BOLD}Phase 8: Project Data{Colors.RESET}")
        total_deleted += clear_table(session, ProjectResource, "Project Resources")
        total_deleted += clear_table(session, EnvironmentalMetric, "Environmental Metrics")
        total_deleted += clear_table(session, Milestone, "Project Milestones")
        total_deleted += clear_table(session, ProjectTeam, "Project Team Members")
        total_deleted += clear_table(session, Project, "Projects")

        print(f"\n{Colors.BOLD}Phase 9: Resources{Colors.RESET}")
        total_deleted += clear_table(session, Resource, "Resources")

        print(f"\n{Colors.BOLD}Phase 10: Users{Colors.RESET}")
        if preserve_admin:
            # Preserve admin, manager, and staff test users
            test_emails = ['admin@repensar.org', 'manager@repensar.org', 'staff@repensar.org']
            condition = ~User.email.in_(test_emails)
            total_deleted += clear_table(session, User, "Users (preserving admin accounts)", condition)
            print(f"{Colors.YELLOW}ℹ{Colors.RESET} Preserved admin accounts: {', '.join(test_emails)}")
        else:
            total_deleted += clear_table(session, User, "Users")

    print_header(f"Database Cleared Successfully - {total_deleted} total rows deleted")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clear all data from the Repensar database"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--preserve-admin",
        action="store_true",
        help="Keep admin, manager, and staff test users"
    )

    args = parser.parse_args()

    # Print warning
    print(f"\n{Colors.BOLD}{Colors.RED}{'!'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.RED}WARNING: This will DELETE ALL DATA from the database!{Colors.RESET}")
    print(f"{Colors.RED}{'!'*80}{Colors.RESET}\n")

    if args.preserve_admin:
        print(f"{Colors.YELLOW}Admin accounts will be preserved:{Colors.RESET}")
        print(f"  - admin@repensar.org")
        print(f"  - manager@repensar.org")
        print(f"  - staff@repensar.org\n")

    # Confirmation
    if not args.confirm:
        response = input(f"{Colors.YELLOW}Are you sure you want to continue? (yes/no): {Colors.RESET}")
        if response.lower() not in ['yes', 'y']:
            print(f"\n{Colors.CYAN}Operation cancelled.{Colors.RESET}")
            sys.exit(0)

    try:
        clear_all_data(preserve_admin=args.preserve_admin)
        print(f"\n{Colors.GREEN}✓ Database cleared successfully!{Colors.RESET}")
        print(f"{Colors.CYAN}You can now run the seed script to populate with fresh data.{Colors.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error clearing database:{Colors.RESET}")
        print(f"{Colors.RED}{str(e)}{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
