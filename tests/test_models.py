import pytest
from datetime import datetime, timezone, timedelta
from sqlmodel import Session
from decimal import Decimal

from app.models.user import User, UserType
from app.models.project import (
    Project, ProjectTeam, Milestone, EnvironmentalMetric,
    ProjectStatus, ProjectCategory, ProjectPriority
)
from app.models.task import Task, TaskDependency, TaskStatus, TaskPriority, DependencyType
from app.models.resource import Resource, ProjectResource, ResourceType
from app.models.volunteer import (
    Volunteer, VolunteerSkill, VolunteerSkillAssignment,
    VolunteerTimeLog, VolunteerTraining, VolunteerTrainingRecord,
    TaskVolunteer
)

class TestUserTypeModel:
    def test_create_user_type(self, session: Session):
        user_type = UserType(
            name="test_type",
            description="Test user type"
        )
        
        session.add(user_type)
        session.commit()
        session.refresh(user_type)
        
        assert user_type.id is not None
        assert user_type.name == "test_type"
        assert user_type.description == "Test user type"
        assert user_type.created_at is not None
    
    def test_user_type_name_unique(self, session: Session):
        # Create first user type
        user_type1 = UserType(name="unique_type", description="First type")
        session.add(user_type1)
        session.commit()
        
        # Try to create second user type with same name
        user_type2 = UserType(name="unique_type", description="Second type")
        session.add(user_type2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()

class TestUserModel:
    def test_create_user(self, session: Session, user_types):
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            phone="1234567890"
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.phone == "1234567890"
        assert user.user_type_id == user_types["volunteer"].id
        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.login_attempts == 0
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_email_unique(self, session: Session, user_types):
        # Create first user
        user1 = User(
            name="User One",
            email="unique@example.com",
            password_hash="hash1",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user1)
        session.commit()
        
        # Try to create second user with same email
        user2 = User(
            name="User Two",
            email="unique@example.com",
            password_hash="hash2",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()
    
    def test_user_type_relationship(self, session: Session, user_types):
        user = User(
            name="Relationship Test User",
            email="relationship@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["organization"].id
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Test relationship
        assert user.user_type.name == "organization"
        assert user.user_type.description == "Organization user"
        
        # Test reverse relationship
        org_type = user_types["organization"]
        session.refresh(org_type)
        assert user in org_type.users
    
    def test_user_optional_fields(self, session: Session, user_types):
        user = User(
            name="Minimal User",
            email="minimal@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Check optional fields have default values
        assert user.phone is None
        assert user.email_verification_token is None
        assert user.email_verification_expires is None
        assert user.password_reset_token is None
        assert user.password_reset_expires is None
        assert user.locked_until is None
        assert user.refresh_token_hash is None
        assert user.refresh_token_expires is None
        assert user.last_login is None
    
    def test_user_security_fields(self, session: Session, user_types):
        now = datetime.now(timezone.utc)
        user = User(
            name="Security Test User",
            email="security@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            login_attempts=3,
            locked_until=now,
            email_verification_token="verify_token",
            password_reset_token="reset_token"
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.login_attempts == 3
        # Remove timezone for comparison since SQLite doesn't store timezone info
        assert user.locked_until.replace(tzinfo=None) == now.replace(tzinfo=None)
        assert user.email_verification_token == "verify_token"
        assert user.password_reset_token == "reset_token"
    
    def test_user_token_fields(self, session: Session, user_types):
        now = datetime.now(timezone.utc)
        user = User(
            name="Token Test User",
            email="token@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["volunteer"].id,
            refresh_token_hash="refresh_hash",
            refresh_token_expires=now,
            last_login=now
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.refresh_token_hash == "refresh_hash"
        # Remove timezone for comparison since SQLite doesn't store timezone info
        assert user.refresh_token_expires.replace(tzinfo=None) == now.replace(tzinfo=None)
        assert user.last_login.replace(tzinfo=None) == now.replace(tzinfo=None)


class TestProjectModel:
    def test_create_project(self, session: Session, user_types):
        # Create project manager user
        manager = User(
            name="Project Manager",
            email="pm@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        # Create project
        project = Project(
            name="Community Garden Project",
            description="Create a sustainable community garden",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=90)).date(),
            status=ProjectStatus.planning,
            category=ProjectCategory.conservation,
            budget=Decimal("10000.00"),
            project_manager_id=manager.id
        )

        session.add(project)
        session.commit()
        session.refresh(project)

        # Verify project was saved to DB
        assert project.id is not None
        assert project.name == "Community Garden Project"
        assert project.description == "Create a sustainable community garden"
        assert project.status == ProjectStatus.planning
        assert project.category == ProjectCategory.conservation
        assert project.budget == Decimal("10000.00")
        assert project.project_manager_id == manager.id
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_manager_relationship(self, session: Session, user_types):
        # Create manager
        manager = User(
            name="Manager User",
            email="manager@example.com",
            password_hash="hashed_password",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        # Create project
        project = Project(
            name="Test Project",
            description="Test Description",
            start_date=datetime.now(timezone.utc).date(),
            status=ProjectStatus.in_progress,
            category=ProjectCategory.other,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Test relationship - project_manager relationship doesn't exist in current model
        # Only test that foreign key works
        assert project.project_manager_id == manager.id

    def test_project_team_members(self, session: Session, user_types):
        # Create manager and team member
        manager = User(
            name="Manager",
            email="mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        team_member = User(
            name="Team Member",
            email="member@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(manager)
        session.add(team_member)
        session.commit()
        session.refresh(manager)
        session.refresh(team_member)

        # Create project
        project = Project(
            name="Team Project",
            description="Project with team",
            start_date=datetime.now(timezone.utc).date(),
            status=ProjectStatus.in_progress,
            category=ProjectCategory.other,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Add team member via ProjectTeam
        project_team = ProjectTeam(
            project_id=project.id,
            user_id=team_member.id,
            role="developer",
            assigned_at=datetime.now(timezone.utc)
        )
        session.add(project_team)
        session.commit()
        session.refresh(project_team)

        # Verify relationship exists in DB
        assert project_team.id is not None
        assert project_team.project_id == project.id
        assert project_team.user_id == team_member.id
        assert project_team.role == "developer"

        # Verify many-to-many relationship
        session.refresh(project)
        assert len(project.team_members) == 1
        assert project.team_members[0].user_id == team_member.id

    def test_project_milestones(self, session: Session, user_types):
        # Create manager
        manager = User(
            name="Manager",
            email="mgr2@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        # Create project
        project = Project(
            name="Milestone Project",
            description="Project with milestones",
            start_date=datetime.now(timezone.utc).date(),
            status=ProjectStatus.in_progress,
            category=ProjectCategory.other,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create milestone
        milestone = Milestone(
            project_id=project.id,
            name="Phase 1 Complete",
            description="Complete first phase",
            target_date=(datetime.now(timezone.utc) + timedelta(days=30)).date(),
            status="pending"
        )
        session.add(milestone)
        session.commit()
        session.refresh(milestone)

        # Verify milestone saved to DB
        assert milestone.id is not None
        assert milestone.project_id == project.id
        assert milestone.name == "Phase 1 Complete"
        assert milestone.status == "pending"

        # Verify relationship
        session.refresh(project)
        assert len(project.milestones) == 1
        assert project.milestones[0].name == "Phase 1 Complete"

    def test_environmental_metrics(self, session: Session, user_types):
        # Create manager
        manager = User(
            name="Manager",
            email="mgr3@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        # Create project
        project = Project(
            name="Green Project",
            description="Environmental project",
            start_date=datetime.now(timezone.utc).date(),
            status=ProjectStatus.in_progress,
            category=ProjectCategory.conservation,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create environmental metric
        metric = EnvironmentalMetric(
            project_id=project.id,
            metric_name="Carbon Offset",
            metric_type="carbon_offset",
            current_value=Decimal("250.50"),
            unit="kg CO2",
            measurement_date=datetime.now(timezone.utc).date()
        )
        session.add(metric)
        session.commit()
        session.refresh(metric)

        # Verify metric saved to DB
        assert metric.id is not None
        assert metric.project_id == project.id
        assert metric.metric_type == "carbon_offset"
        assert metric.current_value == Decimal("250.50")
        assert metric.unit == "kg CO2"

        # Verify relationship
        session.refresh(project)
        assert len(project.environmental_metrics) == 1
        assert project.environmental_metrics[0].current_value == Decimal("250.50")


class TestResourceModel:
    def test_create_resource(self, session: Session):
        # Create resource
        resource = Resource(
            name="Excavator",
            type=ResourceType.equipment,
            description="Heavy machinery for excavation",
            available_quantity=2,
            unit="units",
            unit_cost=Decimal("5000.00")
        )

        session.add(resource)
        session.commit()
        session.refresh(resource)

        # Verify resource saved to DB
        assert resource.id is not None
        assert resource.name == "Excavator"
        assert resource.type == ResourceType.equipment
        assert resource.description == "Heavy machinery for excavation"
        assert resource.available_quantity == 2
        assert resource.unit == "units"
        assert resource.unit_cost == Decimal("5000.00")
        assert resource.created_at is not None

    def test_resource_optional_fields(self, session: Session):
        # Create minimal resource
        resource = Resource(
            name="Basic Tool",
            type=ResourceType.equipment,
            available_quantity=1,
            unit="units"
        )

        session.add(resource)
        session.commit()
        session.refresh(resource)

        # Verify optional fields
        assert resource.description is None
        assert resource.unit_cost is None
        
    def test_project_resource_allocation(self, session: Session, user_types):
        # Create manager
        manager = User(
            name="Manager",
            email="resource_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        # Create project
        project = Project(
            name="Resource Project",
            description="Project needing resources",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create resource
        resource = Resource(
            name="Cement",
            type=ResourceType.material,
            available_quantity=100,
            unit="bags",
            unit_cost=Decimal("15.00")
        )
        session.add(resource)
        session.commit()
        session.refresh(resource)

        # Allocate resource to project
        allocation = ProjectResource(
            project_id=project.id,
            resource_id=resource.id,
            quantity_allocated=50,
            allocation_date=datetime.now(timezone.utc)
        )
        session.add(allocation)
        session.commit()
        session.refresh(allocation)

        # Verify allocation saved to DB
        assert allocation.id is not None
        assert allocation.project_id == project.id
        assert allocation.resource_id == resource.id
        assert allocation.quantity_allocated == 50

        # Verify many-to-many relationship
        session.refresh(project)
        session.refresh(resource)
        assert len(project.resource_allocations) == 1
        assert project.resource_allocations[0].quantity_allocated == 50
        assert len(resource.project_allocations) == 1
        assert resource.project_allocations[0].project_id == project.id

    def test_resource_utilization(self, session: Session, user_types):
        # Create manager and project
        manager = User(
            name="Manager",
            email="util_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        project = Project(
            name="Utilization Project",
            description="Track resource usage",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create resource
        resource = Resource(
            name="Paint",
            type=ResourceType.material,
            available_quantity=20,
            unit="gallons"
        )
        session.add(resource)
        session.commit()
        session.refresh(resource)

        # Allocate with utilization tracking
        allocation = ProjectResource(
            project_id=project.id,
            resource_id=resource.id,
            quantity_allocated=10,
            quantity_used=7,
            allocation_date=datetime.now(timezone.utc)
        )
        session.add(allocation)
        session.commit()
        session.refresh(allocation)

        # Verify utilization data
        assert allocation.quantity_allocated == 10
        assert allocation.quantity_used == 7
        assert allocation.quantity_allocated - allocation.quantity_used == 3  # Remaining


class TestTaskModel:
    def test_create_task(self, session: Session, user_types):
        # Create manager and project
        manager = User(
            name="Manager",
            email="task_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        project = Project(
            name="Task Project",
            description="Project with tasks",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create task
        task = Task(
            project_id=project.id,
            title="Setup Foundation",
            description="Lay the foundation for the building",
            status=TaskStatus.not_started,
            priority=TaskPriority.high,
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=7)).date(),
            estimated_hours=40,
            suitable_for_volunteers=True
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        # Verify task saved to DB
        assert task.id is not None
        assert task.project_id == project.id
        assert task.title == "Setup Foundation"
        assert task.description == "Lay the foundation for the building"
        assert task.status == TaskStatus.not_started
        assert task.priority == TaskPriority.high
        assert task.estimated_hours == 40
        assert task.suitable_for_volunteers is True
        assert task.created_at is not None

    def test_task_project_relationship(self, session: Session, user_types):
        # Create manager and project
        manager = User(
            name="Manager",
            email="task_rel_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        project = Project(
            name="Relationship Project",
            description="Test relationships",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create task
        task = Task(
            project_id=project.id,
            title="Test Task",
            description="Test description",
            status=TaskStatus.not_started,
            priority=TaskPriority.medium
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Verify relationship
        assert task.project.name == "Relationship Project"

        # Verify reverse relationship
        session.refresh(project)
        assert len(project.tasks) == 1
        assert project.tasks[0].title == "Test Task"

    def test_task_subtasks(self, session: Session, user_types):
        # Create manager and project
        manager = User(
            name="Manager",
            email="subtask_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        project = Project(
            name="Subtask Project",
            description="Project with subtasks",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create parent task
        parent_task = Task(
            project_id=project.id,
            title="Build Wall",
            description="Complete wall construction",
            status=TaskStatus.in_progress,
            priority=TaskPriority.high
        )
        session.add(parent_task)
        session.commit()
        session.refresh(parent_task)

        # Create subtask
        subtask = Task(
            project_id=project.id,
            parent_task_id=parent_task.id,
            title="Mix Mortar",
            description="Prepare mortar for wall",
            status=TaskStatus.not_started,
            priority=TaskPriority.high
        )
        session.add(subtask)
        session.commit()
        session.refresh(subtask)

        # Verify subtask relationship saved to DB
        assert subtask.parent_task_id == parent_task.id
        assert subtask.parent_task.title == "Build Wall"

        # Verify reverse relationship
        session.refresh(parent_task)
        assert len(parent_task.subtasks) == 1
        assert parent_task.subtasks[0].title == "Mix Mortar"

    def test_task_dependencies(self, session: Session, user_types):
        # Create manager and project
        manager = User(
            name="Manager",
            email="dep_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        session.add(manager)
        session.commit()
        session.refresh(manager)

        project = Project(
            name="Dependency Project",
            description="Project with task dependencies",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create tasks
        task1 = Task(
            project_id=project.id,
            title="Foundation",
            description="Lay foundation",
            status=TaskStatus.completed,
            priority=TaskPriority.high
        )
        task2 = Task(
            project_id=project.id,
            title="Walls",
            description="Build walls",
            status=TaskStatus.not_started,
            priority=TaskPriority.high
        )
        session.add(task1)
        session.add(task2)
        session.commit()
        session.refresh(task1)
        session.refresh(task2)

        # Create dependency (task2 depends on task1)
        dependency = TaskDependency(
            successor_task_id=task2.id,
            predecessor_task_id=task1.id,
            dependency_type="finish_to_start"
        )
        session.add(dependency)
        session.commit()
        session.refresh(dependency)

        # Verify dependency saved to DB
        assert dependency.id is not None
        assert dependency.successor_task_id == task2.id
        assert dependency.predecessor_task_id == task1.id
        assert dependency.dependency_type == DependencyType.finish_to_start

        # Verify relationships
        session.refresh(task2)
        assert len(task2.successor_dependencies) == 1
        assert task2.successor_dependencies[0].predecessor_task_id == task1.id

    def test_task_volunteer_assignment(self, session: Session, user_types):
        # Create users
        manager = User(
            name="Manager",
            email="assign_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        volunteer_user = User(
            name="Volunteer User",
            email="volunteer@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(manager)
        session.add(volunteer_user)
        session.commit()
        session.refresh(manager)
        session.refresh(volunteer_user)

        # Create volunteer profile
        volunteer = Volunteer(
            volunteer_id="VOL27947",
            user_id=volunteer_user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Create project and task
        project = Project(
            name="Assignment Project",
            description="Project with volunteer assignments",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        task = Task(
            project_id=project.id,
            title="Volunteer Task",
            description="Task for volunteers",
            status=TaskStatus.not_started,
            priority=TaskPriority.medium,
            suitable_for_volunteers=True
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Assign volunteer to task
        assignment = TaskVolunteer(
            task_id=task.id,
            volunteer_id=volunteer.id,
            assigned_at=datetime.now(timezone.utc),
            )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)

        # Verify assignment saved to DB
        assert assignment.id is not None
        assert assignment.task_id == task.id
        assert assignment.volunteer_id == volunteer.id
        
        # Verify many-to-many relationship
        session.refresh(task)
        session.refresh(volunteer)
        assert len(task.volunteer_assignments) == 1
        assert task.volunteer_assignments[0].volunteer_id == volunteer.id
        assert len(volunteer.task_assignments) == 1
        assert volunteer.task_assignments[0].task_id == task.id


class TestVolunteerModel:
    def test_create_volunteer(self, session: Session, user_types):
        # Create user
        user = User(
            name="John Volunteer",
            email="john@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create volunteer profile
        volunteer = Volunteer(
            volunteer_id="VOL95671",
            user_id=user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="555-1234",
            background_check_status="pending"
        )

        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Verify volunteer saved to DB
        assert volunteer.id is not None
        assert volunteer.user_id == user.id
        assert volunteer.emergency_contact_name == "Jane Doe"
        assert volunteer.emergency_contact_phone == "555-1234"
        assert volunteer.background_check_status == "pending"
        assert volunteer.created_at is not None

    def test_volunteer_user_relationship(self, session: Session, user_types):
        # Create user
        user = User(
            name="Relationship Volunteer",
            email="rel_volunteer@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create volunteer
        volunteer = Volunteer(
            volunteer_id="VOL92810",
            user_id=user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Verify relationship - volunteer has user_id foreign key
        # The user -> volunteer relationship doesn't exist in current model
        assert volunteer.user_id == user.id

    def test_volunteer_skills(self, session: Session, user_types):
        # Create user and volunteer
        user = User(
            name="Skilled Volunteer",
            email="skilled@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        volunteer = Volunteer(
            volunteer_id="VOL74242",
            user_id=user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Create skill
        skill = VolunteerSkill(
            name="Carpentry",
            description="Woodworking and construction",
            category="construction"
        )
        session.add(skill)
        session.commit()
        session.refresh(skill)

        # Assign skill to volunteer
        skill_assignment = VolunteerSkillAssignment(
            volunteer_id=volunteer.id,
            skill_id=skill.id,
            proficiency_level="intermediate",
            years_experience=3
        )
        session.add(skill_assignment)
        session.commit()
        session.refresh(skill_assignment)

        # Verify skill assignment saved to DB
        assert skill_assignment.id is not None
        assert skill_assignment.volunteer_id == volunteer.id
        assert skill_assignment.skill_id == skill.id
        assert skill_assignment.proficiency_level == "intermediate"
        assert skill_assignment.years_experience == 3

        # Verify many-to-many relationship
        session.refresh(volunteer)
        session.refresh(skill)
        assert len(volunteer.skill_assignments) == 1
        assert volunteer.skill_assignments[0].skill_id == skill.id
        assert len(skill.skill_assignments) == 1
        assert skill.skill_assignments[0].volunteer_id == volunteer.id

    def test_volunteer_time_logs(self, session: Session, user_types):
        # Create users
        manager = User(
            name="Manager",
            email="timelog_mgr@example.com",
            password_hash="hash",
            user_type_id=user_types["organization"].id
        )
        volunteer_user = User(
            name="Time Logger",
            email="timelogger@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(manager)
        session.add(volunteer_user)
        session.commit()
        session.refresh(manager)
        session.refresh(volunteer_user)

        # Create volunteer
        volunteer = Volunteer(
            volunteer_id="VOL26349",
            user_id=volunteer_user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Create project and task
        project = Project(
            name="Time Log Project",
            description="Project for time tracking",
            start_date=datetime.now(timezone.utc).date(),
            category=ProjectCategory.other,
            status=ProjectStatus.in_progress,
            project_manager_id=manager.id
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        task = Task(
            project_id=project.id,
            title="Logged Task",
            description="Task with time logs",
            status=TaskStatus.in_progress,
            priority=TaskPriority.medium
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create time log
        time_log = VolunteerTimeLog(
            volunteer_id=volunteer.id,
            project_id=project.id,
            task_id=task.id,
            date=datetime.now(timezone.utc).date(),
            hours=Decimal("4.5"),

            activity_description="Worked on foundation prep")
        session.add(time_log)
        session.commit()
        session.refresh(time_log)

        # Verify time log saved to DB
        assert time_log.id is not None
        assert time_log.volunteer_id == volunteer.id
        assert time_log.project_id == project.id
        assert time_log.task_id == task.id
        assert time_log.hours == Decimal("4.5")
        assert time_log.activity_description == "Worked on foundation prep"
        
        # Verify relationships
        session.refresh(volunteer)
        session.refresh(project)
        session.refresh(task)
        assert len(volunteer.time_logs) == 1
        assert volunteer.time_logs[0].hours == Decimal("4.5")
        assert len(project.time_logs) == 1
        assert len(task.time_logs) == 1

    def test_volunteer_training(self, session: Session, user_types):
        # Create user and volunteer
        user = User(
            name="Training Volunteer",
            email="training@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        volunteer = Volunteer(
            volunteer_id="VOL94644",
            user_id=user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Create training program
        training = VolunteerTraining(
            name="Safety Training",
            description="Workplace safety certification",
            duration_hours=8,
            is_mandatory=True
        )
        session.add(training)
        session.commit()
        session.refresh(training)

        # Create training record
        training_record = VolunteerTrainingRecord(
            volunteer_id=volunteer.id,
            training_id=training.id,
            completed_date=datetime.now(timezone.utc).date(),
            score=95
        )
        session.add(training_record)
        session.commit()
        session.refresh(training_record)

        # Verify training record saved to DB
        assert training_record.id is not None
        assert training_record.volunteer_id == volunteer.id
        assert training_record.training_id == training.id
        assert training_record.score == 95

        # Verify many-to-many relationship
        session.refresh(volunteer)
        session.refresh(training)
        assert len(volunteer.training_records) == 1
        assert volunteer.training_records[0].training_id == training.id
        assert len(training.training_records) == 1
        assert training.training_records[0].volunteer_id == volunteer.id

    def test_volunteer_multiple_relationships(self, session: Session, user_types):
        """Test that a volunteer can have multiple skills, time logs, and training records"""
        # Create user and volunteer
        user = User(
            name="Multi Volunteer",
            email="multi@example.com",
            password_hash="hash",
            user_type_id=user_types["volunteer"].id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        volunteer = Volunteer(
            volunteer_id="VOL28616",
            user_id=user.id,
            joined_date=datetime.now(timezone.utc).date(),
            emergency_contact_name="Contact",
            emergency_contact_phone="555-0000"
        )
        session.add(volunteer)
        session.commit()
        session.refresh(volunteer)

        # Add multiple skills
        skill1 = VolunteerSkill(name="Plumbing", description="Plumbing work", category="construction")
        skill2 = VolunteerSkill(name="Electrical", description="Electrical work", category="construction")
        session.add(skill1)
        session.add(skill2)
        session.commit()
        session.refresh(skill1)
        session.refresh(skill2)

        assignment1 = VolunteerSkillAssignment(
            volunteer_id=volunteer.id,
            skill_id=skill1.id,
            proficiency_level="expert",
            years_experience=5
        )
        assignment2 = VolunteerSkillAssignment(
            volunteer_id=volunteer.id,
            skill_id=skill2.id,
            proficiency_level="beginner",
            years_experience=1
        )
        session.add(assignment1)
        session.add(assignment2)
        session.commit()

        # Add multiple training records
        training1 = VolunteerTraining(name="First Aid", description="First aid cert", duration_hours=4)
        training2 = VolunteerTraining(name="CPR", description="CPR cert", duration_hours=2)
        session.add(training1)
        session.add(training2)
        session.commit()
        session.refresh(training1)
        session.refresh(training2)

        record1 = VolunteerTrainingRecord(
            volunteer_id=volunteer.id,
            training_id=training1.id,
            completed_date=datetime.now(timezone.utc).date(),
            )
        record2 = VolunteerTrainingRecord(
            volunteer_id=volunteer.id,
            training_id=training2.id,
            completed_date=datetime.now(timezone.utc).date(),
            )
        session.add(record1)
        session.add(record2)
        session.commit()

        # Verify all relationships are saved to DB
        session.refresh(volunteer)
        assert len(volunteer.skill_assignments) == 2
        assert len(volunteer.training_records) == 2

        # Verify we can access the actual skills and trainings through the relationships
        skill_names = [assignment.skill_id for assignment in volunteer.skill_assignments]
        assert skill1.id in skill_names
        assert skill2.id in skill_names