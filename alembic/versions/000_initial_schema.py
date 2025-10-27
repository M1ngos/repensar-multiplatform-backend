"""Initial database schema from db.sql

Revision ID: 000
Revises:
Create Date: 2025-10-15 10:00:00.000000

This migration creates the complete base schema equivalent to db.sql
For existing databases created with db.sql, run: alembic stamp 000
For new installations, run: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create complete initial database schema"""

    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # Create utility functions
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
        RETURNS void AS $$
        DECLARE
            partition_name text;
            end_date date;
        BEGIN
            partition_name := table_name || '_y' || EXTRACT(year FROM start_date) || 'm' || LPAD(EXTRACT(month FROM start_date)::text, 2, '0');
            end_date := start_date + INTERVAL '1 month';

            EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                           partition_name, table_name, start_date, end_date);
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
        RETURNS void AS $$
        BEGIN
            DELETE FROM auth_sessions WHERE expires_at < CURRENT_TIMESTAMP;
        END;
        $$ LANGUAGE plpgsql
    """)

    # User Types Table
    op.create_table(
        'user_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dashboard_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.execute("CREATE TRIGGER update_user_types_updated_at BEFORE UPDATE ON user_types FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Users Table (base - before OAuth additions)
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('user_type_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_attempts', sa.Integer(), server_default='0', nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=True),
        sa.Column('refresh_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.ForeignKeyConstraint(['user_type_id'], ['user_types.id'])
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_user_type_id', 'users', ['user_type_id'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_password_reset_token', 'users', ['password_reset_token'])
    op.create_index('idx_users_email_verification_token', 'users', ['email_verification_token'])
    op.create_index('idx_users_refresh_token_hash', 'users', ['refresh_token_hash'])
    op.execute("CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Auth Sessions Table
    op.create_table(
        'auth_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_index('idx_auth_sessions_session_token', 'auth_sessions', ['session_token'])
    op.create_index('idx_auth_sessions_expires_at', 'auth_sessions', ['expires_at'])

    # Volunteer Skills
    op.create_table(
        'volunteer_skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Volunteers
    op.create_table(
        'volunteers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.String(length=20), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=30), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(length=50), nullable=True),
        sa.Column('availability', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('volunteer_status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('background_check_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('orientation_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('orientation_date', sa.Date(), nullable=True),
        sa.Column('total_hours_contributed', sa.Numeric(precision=8, scale=2), server_default='0', nullable=False),
        sa.Column('joined_date', sa.Date(), nullable=False),
        sa.Column('motivation', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('volunteer_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("volunteer_status IN ('active', 'inactive', 'suspended')"),
        sa.CheckConstraint("background_check_status IN ('pending', 'approved', 'rejected', 'not_required')")
    )
    op.create_index('idx_volunteers_user_id', 'volunteers', ['user_id'])
    op.create_index('idx_volunteers_volunteer_id', 'volunteers', ['volunteer_id'])
    op.create_index('idx_volunteers_status', 'volunteers', ['volunteer_status'])
    op.execute("CREATE TRIGGER update_volunteers_updated_at BEFORE UPDATE ON volunteers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Volunteer Skill Assignments
    op.create_table(
        'volunteer_skill_assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('proficiency_level', sa.String(length=20), server_default='beginner', nullable=False),
        sa.Column('years_experience', sa.Integer(), server_default='0', nullable=False),
        sa.Column('certified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['volunteer_skills.id']),
        sa.UniqueConstraint('volunteer_id', 'skill_id'),
        sa.CheckConstraint("proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')")
    )
    op.create_index('idx_volunteer_skill_assignments_volunteer_id', 'volunteer_skill_assignments', ['volunteer_id'])
    op.create_index('idx_volunteer_skill_assignments_skill_id', 'volunteer_skill_assignments', ['skill_id'])

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='planning', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='medium', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('budget', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('actual_cost', sa.Numeric(precision=12, scale=2), server_default='0', nullable=False),
        sa.Column('location_name', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('project_manager_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('requires_volunteers', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('min_volunteers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_volunteers', sa.Integer(), nullable=True),
        sa.Column('volunteer_requirements', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_manager_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.CheckConstraint("category IN ('reforestation', 'environmental_education', 'waste_management', 'conservation', 'research', 'community_engagement', 'climate_action', 'biodiversity', 'other')"),
        sa.CheckConstraint("status IN ('planning', 'in_progress', 'suspended', 'completed', 'cancelled')"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')")
    )
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_category', 'projects', ['category'])
    op.create_index('idx_projects_project_manager_id', 'projects', ['project_manager_id'])
    op.create_index('idx_projects_dates', 'projects', ['start_date', 'end_date'])
    op.execute("CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Project Teams
    op.create_table(
        'project_teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('is_volunteer', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('project_id', 'user_id')
    )
    op.create_index('idx_project_teams_project_id', 'project_teams', ['project_id'])
    op.create_index('idx_project_teams_user_id', 'project_teams', ['user_id'])
    op.create_index('idx_project_teams_is_volunteer', 'project_teams', ['is_volunteer'])

    # Tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='not_started', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='medium', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('estimated_hours', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(precision=6, scale=2), server_default='0', nullable=False),
        sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('suitable_for_volunteers', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('volunteer_spots', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'cancelled')"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')"),
        sa.CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100")
    )
    op.create_index('idx_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('idx_tasks_assigned_to_id', 'tasks', ['assigned_to_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_suitable_for_volunteers', 'tasks', ['suitable_for_volunteers'])
    op.execute("CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Task Volunteers
    op.create_table(
        'task_volunteers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('hours_contributed', sa.Numeric(precision=6, scale=2), server_default='0', nullable=False),
        sa.Column('performance_rating', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id']),
        sa.UniqueConstraint('task_id', 'volunteer_id'),
        sa.CheckConstraint("performance_rating >= 1 AND performance_rating <= 5")
    )
    op.create_index('idx_task_volunteers_task_id', 'task_volunteers', ['task_id'])
    op.create_index('idx_task_volunteers_volunteer_id', 'task_volunteers', ['volunteer_id'])

    # Volunteer Time Logs
    op.create_table(
        'volunteer_time_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('hours', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=True),
        sa.Column('approved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'])
    )
    op.create_index('idx_volunteer_time_logs_volunteer_id', 'volunteer_time_logs', ['volunteer_id'])
    op.create_index('idx_volunteer_time_logs_project_id', 'volunteer_time_logs', ['project_id'])
    op.create_index('idx_volunteer_time_logs_date', 'volunteer_time_logs', ['date'])
    op.create_index('idx_volunteer_time_logs_approved', 'volunteer_time_logs', ['approved'])
    op.execute("CREATE TRIGGER update_volunteer_time_logs_updated_at BEFORE UPDATE ON volunteer_time_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Volunteer Training
    op.create_table(
        'volunteer_training',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('duration_hours', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('valid_for_months', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Volunteer Training Records
    op.create_table(
        'volunteer_training_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('training_id', sa.Integer(), nullable=False),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('expires_date', sa.Date(), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('trainer_id', sa.Integer(), nullable=True),
        sa.Column('certificate_issued', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['training_id'], ['volunteer_training.id']),
        sa.ForeignKeyConstraint(['trainer_id'], ['users.id']),
        sa.UniqueConstraint('volunteer_id', 'training_id', 'completed_date')
    )
    op.create_index('idx_volunteer_training_records_volunteer_id', 'volunteer_training_records', ['volunteer_id'])
    op.create_index('idx_volunteer_training_records_expires_date', 'volunteer_training_records', ['expires_date'])

    # Task Dependencies
    op.create_table(
        'task_dependencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('predecessor_task_id', sa.Integer(), nullable=False),
        sa.Column('successor_task_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', sa.String(length=20), server_default='finish_to_start', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['predecessor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('predecessor_task_id', 'successor_task_id'),
        sa.CheckConstraint("dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')")
    )

    # Resources
    op.create_table(
        'resources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('available_quantity', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('human', 'equipment', 'material', 'financial')")
    )
    op.execute("CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Project Resources
    op.create_table(
        'project_resources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('quantity_allocated', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity_used', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
        sa.Column('allocation_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('allocated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id']),
        sa.ForeignKeyConstraint(['allocated_by_id'], ['users.id'])
    )

    # Milestones
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('pending', 'achieved', 'missed', 'cancelled')")
    )
    op.execute("CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON milestones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Environmental Metrics
    op.create_table(
        'environmental_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=True),
        sa.Column('target_value', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('current_value', sa.Numeric(precision=12, scale=4), server_default='0', nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('measurement_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recorded_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id'])
    )
    op.create_index('idx_environmental_metrics_project_id', 'environmental_metrics', ['project_id'])
    op.create_index('idx_environmental_metrics_measurement_date', 'environmental_metrics', ['measurement_date'])
    op.execute("CREATE TRIGGER update_environmental_metrics_updated_at BEFORE UPDATE ON environmental_metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('volunteer_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['volunteers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'])
    )
    op.create_index('idx_documents_project_id', 'documents', ['project_id'])
    op.create_index('idx_documents_volunteer_id', 'documents', ['volunteer_id'])
    op.create_index('idx_documents_is_public', 'documents', ['is_public'])

    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=20), server_default='info', nullable=False),
        sa.Column('related_project_id', sa.Integer(), nullable=True),
        sa.Column('related_task_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['related_project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.id']),
        sa.CheckConstraint("type IN ('info', 'warning', 'error', 'success')")
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])

    # Activity Logs (Partitioned Table)
    op.execute("""
        CREATE TABLE activity_logs (
            id BIGSERIAL,
            user_id INTEGER REFERENCES users(id),
            project_id INTEGER REFERENCES projects(id),
            task_id INTEGER REFERENCES tasks(id),
            volunteer_id INTEGER REFERENCES volunteers(id),
            action VARCHAR(100) NOT NULL,
            description TEXT,
            old_values JSONB,
            new_values JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)

    # Create partitions for 2025
    for month in range(1, 13):
        month_str = str(month).zfill(2)
        next_month = month + 1 if month < 12 else 1
        next_month_str = str(next_month).zfill(2)
        year = 2025
        next_year = 2025 if month < 12 else 2026

        op.execute(f"""
            CREATE TABLE activity_logs_y2025m{month_str} PARTITION OF activity_logs
                FOR VALUES FROM ('{year}-{month_str}-01') TO ('{next_year}-{next_month_str}-01')
        """)

    # Indexes on partitioned table
    op.execute("CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id)")
    op.execute("CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at)")
    op.execute("CREATE INDEX idx_activity_logs_action ON activity_logs(action)")

    # Create Views
    op.execute("""
        CREATE VIEW volunteer_profiles AS
        SELECT
            v.id,
            v.volunteer_id,
            u.name,
            u.email,
            u.phone,
            v.volunteer_status,
            v.total_hours_contributed,
            v.joined_date,
            array_agg(vs.name) as skills,
            v.availability
        FROM volunteers v
        JOIN users u ON v.user_id = u.id
        LEFT JOIN volunteer_skill_assignments vsa ON v.id = vsa.volunteer_id
        LEFT JOIN volunteer_skills vs ON vsa.skill_id = vs.id
        WHERE v.volunteer_status = 'active' AND u.is_active = true
        GROUP BY v.id, u.name, u.email, u.phone, v.volunteer_status, v.total_hours_contributed, v.joined_date, v.availability
    """)

    op.execute("""
        CREATE VIEW project_dashboard AS
        SELECT
            p.id,
            p.name,
            p.status,
            p.category,
            p.start_date,
            p.end_date,
            p.budget,
            p.actual_cost,
            COUNT(DISTINCT pt.user_id) as team_size,
            COUNT(DISTINCT CASE WHEN pt.is_volunteer THEN pt.user_id END) as volunteers_count,
            COUNT(DISTINCT t.id) as total_tasks,
            COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
            COALESCE(SUM(vtl.hours), 0) as volunteer_hours
        FROM projects p
        LEFT JOIN project_teams pt ON p.id = pt.project_id AND pt.is_active = true
        LEFT JOIN tasks t ON p.id = t.project_id
        LEFT JOIN volunteer_time_logs vtl ON p.id = vtl.project_id AND vtl.approved = true
        GROUP BY p.id, p.name, p.status, p.category, p.start_date, p.end_date, p.budget, p.actual_cost
    """)


def downgrade():
    """Drop all tables and objects"""

    # Drop views
    op.execute("DROP VIEW IF EXISTS project_dashboard")
    op.execute("DROP VIEW IF EXISTS volunteer_profiles")

    # Drop partitioned table and partitions
    op.execute("DROP TABLE IF EXISTS activity_logs CASCADE")

    # Drop tables in reverse order
    op.drop_table('notifications')
    op.drop_table('documents')
    op.drop_table('environmental_metrics')
    op.drop_table('milestones')
    op.drop_table('project_resources')
    op.drop_table('resources')
    op.drop_table('task_dependencies')
    op.drop_table('volunteer_training_records')
    op.drop_table('volunteer_training')
    op.drop_table('volunteer_time_logs')
    op.drop_table('task_volunteers')
    op.drop_table('tasks')
    op.drop_table('project_teams')
    op.drop_table('projects')
    op.drop_table('volunteer_skill_assignments')
    op.drop_table('volunteers')
    op.drop_table('volunteer_skills')
    op.drop_table('auth_sessions')
    op.drop_table('users')
    op.drop_table('user_types')

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS cleanup_expired_sessions()")
    op.execute("DROP FUNCTION IF EXISTS create_monthly_partition(text, date)")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"")
