-- ========================================
-- ENVIRONMENTAL PROJECT MANAGEMENT SYSTEM
-- Complete Database Creation + Insert Scripts
-- PostgreSQL 17
-- ========================================

-- Create database (run separately if needed)
-- CREATE DATABASE environmental_projects;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- UTILITY FUNCTIONS
-- ========================================

-- Function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to automatically create new partitions for activity_logs
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
$$ LANGUAGE plpgsql;

-- Function to cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM auth_sessions WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- TABLE CREATION
-- ========================================

-- User Types Table
CREATE TABLE user_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    dashboard_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_user_types_updated_at BEFORE UPDATE ON user_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type_id INTEGER NOT NULL REFERENCES user_types(id),
    phone VARCHAR(20),
    department VARCHAR(50),
    employee_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE,
    refresh_token_hash VARCHAR(255),
    refresh_token_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_type_id ON users(user_type_id);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_password_reset_token ON users(password_reset_token);
CREATE INDEX idx_users_email_verification_token ON users(email_verification_token);
CREATE INDEX idx_users_refresh_token_hash ON users(refresh_token_hash);

-- Auth Sessions Table (Optional - for session tracking)
CREATE TABLE auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX idx_auth_sessions_session_token ON auth_sessions(session_token);
CREATE INDEX idx_auth_sessions_expires_at ON auth_sessions(expires_at);

-- Volunteer Skills Table
CREATE TABLE volunteer_skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Volunteers Table
CREATE TABLE volunteers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    volunteer_id VARCHAR(20) UNIQUE NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(30),
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    availability JSONB,
    volunteer_status VARCHAR(20) DEFAULT 'active' CHECK (volunteer_status IN ('active', 'inactive', 'suspended')),
    background_check_status VARCHAR(20) DEFAULT 'pending' CHECK (background_check_status IN ('pending', 'approved', 'rejected', 'not_required')),
    orientation_completed BOOLEAN DEFAULT FALSE,
    orientation_date DATE,
    total_hours_contributed DECIMAL(8,2) DEFAULT 0,
    joined_date DATE NOT NULL,
    motivation TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_volunteers_updated_at BEFORE UPDATE ON volunteers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for volunteers
CREATE INDEX idx_volunteers_user_id ON volunteers(user_id);
CREATE INDEX idx_volunteers_volunteer_id ON volunteers(volunteer_id);
CREATE INDEX idx_volunteers_status ON volunteers(volunteer_status);

-- Volunteer Skill Assignments Table
CREATE TABLE volunteer_skill_assignments (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES volunteer_skills(id),
    proficiency_level VARCHAR(20) DEFAULT 'beginner' CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_experience INTEGER DEFAULT 0,
    certified BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(volunteer_id, skill_id)
);

CREATE INDEX idx_volunteer_skill_assignments_volunteer_id ON volunteer_skill_assignments(volunteer_id);
CREATE INDEX idx_volunteer_skill_assignments_skill_id ON volunteer_skill_assignments(skill_id);

-- Projects Table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('reforestation', 'environmental_education', 'waste_management', 'conservation', 'research', 'community_engagement', 'climate_action', 'biodiversity', 'other')),
    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'in_progress', 'suspended', 'completed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    actual_cost DECIMAL(12,2) DEFAULT 0,
    location_name VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    project_manager_id INTEGER REFERENCES users(id),
    created_by_id INTEGER REFERENCES users(id),
    requires_volunteers BOOLEAN DEFAULT FALSE,
    min_volunteers INTEGER DEFAULT 0,
    max_volunteers INTEGER,
    volunteer_requirements TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for projects
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_category ON projects(category);
CREATE INDEX idx_projects_project_manager_id ON projects(project_manager_id);
CREATE INDEX idx_projects_dates ON projects(start_date, end_date);

-- Project Teams Table
CREATE TABLE project_teams (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    role VARCHAR(50),
    is_volunteer BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(project_id, user_id)
);

CREATE INDEX idx_project_teams_project_id ON project_teams(project_id);
CREATE INDEX idx_project_teams_user_id ON project_teams(user_id);
CREATE INDEX idx_project_teams_is_volunteer ON project_teams(is_volunteer);

-- Tasks Table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_task_id INTEGER REFERENCES tasks(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    start_date DATE,
    end_date DATE,
    estimated_hours DECIMAL(6,2),
    actual_hours DECIMAL(6,2) DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    assigned_to_id INTEGER REFERENCES users(id),
    created_by_id INTEGER REFERENCES users(id),
    suitable_for_volunteers BOOLEAN DEFAULT FALSE,
    required_skills JSONB,
    volunteer_spots INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for tasks
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_assigned_to_id ON tasks(assigned_to_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_suitable_for_volunteers ON tasks(suitable_for_volunteers);

-- Task Volunteers Table
CREATE TABLE task_volunteers (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    hours_contributed DECIMAL(6,2) DEFAULT 0,
    performance_rating INTEGER CHECK (performance_rating >= 1 AND performance_rating <= 5),
    notes TEXT,
    UNIQUE(task_id, volunteer_id)
);

CREATE INDEX idx_task_volunteers_task_id ON task_volunteers(task_id);
CREATE INDEX idx_task_volunteers_volunteer_id ON task_volunteers(volunteer_id);

-- Volunteer Time Logs Table
CREATE TABLE volunteer_time_logs (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id),
    task_id INTEGER REFERENCES tasks(id),
    date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    hours DECIMAL(4,2) NOT NULL,
    activity_description TEXT,
    supervisor_id INTEGER REFERENCES users(id),
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_volunteer_time_logs_updated_at BEFORE UPDATE ON volunteer_time_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for volunteer time logs
CREATE INDEX idx_volunteer_time_logs_volunteer_id ON volunteer_time_logs(volunteer_id);
CREATE INDEX idx_volunteer_time_logs_project_id ON volunteer_time_logs(project_id);
CREATE INDEX idx_volunteer_time_logs_date ON volunteer_time_logs(date);
CREATE INDEX idx_volunteer_time_logs_approved ON volunteer_time_logs(approved);

-- Volunteer Training Table
CREATE TABLE volunteer_training (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    duration_hours DECIMAL(4,2),
    valid_for_months INTEGER,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Volunteer Training Records Table
CREATE TABLE volunteer_training_records (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
    training_id INTEGER NOT NULL REFERENCES volunteer_training(id),
    completed_date DATE,
    expires_date DATE,
    score DECIMAL(5,2),
    trainer_id INTEGER REFERENCES users(id),
    certificate_issued BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(volunteer_id, training_id, completed_date)
);

CREATE INDEX idx_volunteer_training_records_volunteer_id ON volunteer_training_records(volunteer_id);
CREATE INDEX idx_volunteer_training_records_expires_date ON volunteer_training_records(expires_date);

-- Task Dependencies Table
CREATE TABLE task_dependencies (
    id SERIAL PRIMARY KEY,
    predecessor_task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    successor_task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'finish_to_start' CHECK (dependency_type IN ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(predecessor_task_id, successor_task_id)
);

-- Resources Table
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('human', 'equipment', 'material', 'financial')),
    description TEXT,
    unit_cost DECIMAL(10,2),
    unit VARCHAR(20),
    available_quantity DECIMAL(10,2),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Project Resources Table
CREATE TABLE project_resources (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL REFERENCES resources(id),
    quantity_allocated DECIMAL(10,2) NOT NULL,
    quantity_used DECIMAL(10,2) DEFAULT 0,
    allocation_date DATE,
    notes TEXT,
    allocated_by_id INTEGER REFERENCES users(id)
);

-- Milestones Table
CREATE TABLE milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    target_date DATE NOT NULL,
    actual_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'achieved', 'missed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Environmental Metrics Table
CREATE TABLE environmental_metrics (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50),
    target_value DECIMAL(12,4),
    current_value DECIMAL(12,4) DEFAULT 0,
    unit VARCHAR(20),
    measurement_date DATE,
    description TEXT,
    recorded_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_environmental_metrics_updated_at BEFORE UPDATE ON environmental_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_environmental_metrics_project_id ON environmental_metrics(project_id);
CREATE INDEX idx_environmental_metrics_measurement_date ON environmental_metrics(measurement_date);

-- Documents Table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    volunteer_id INTEGER REFERENCES volunteers(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    uploaded_by_id INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_volunteer_id ON documents(volunteer_id);
CREATE INDEX idx_documents_is_public ON documents(is_public);

-- Notifications Table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
    related_project_id INTEGER REFERENCES projects(id),
    related_task_id INTEGER REFERENCES tasks(id),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- Activity Logs Table (Partitioned)
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
) PARTITION BY RANGE (created_at);

-- Create partitions for 2025
CREATE TABLE activity_logs_y2025m01 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE activity_logs_y2025m02 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE activity_logs_y2025m03 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE activity_logs_y2025m04 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE activity_logs_y2025m05 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE activity_logs_y2025m06 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE activity_logs_y2025m07 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE activity_logs_y2025m08 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE activity_logs_y2025m09 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE activity_logs_y2025m10 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE activity_logs_y2025m11 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE activity_logs_y2025m12 PARTITION OF activity_logs
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Indexes on partitioned table
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);

-- ========================================
-- VIEWS
-- ========================================

-- View: Active volunteers with their skills
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
GROUP BY v.id, u.name, u.email, u.phone, v.volunteer_status, v.total_hours_contributed, v.joined_date, v.availability;

-- View: Project dashboard
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
GROUP BY p.id, p.name, p.status, p.category, p.start_date, p.end_date, p.budget, p.actual_cost;

-- ========================================
-- INITIAL DATA INSERTS
-- ========================================

-- Insert default user types
INSERT INTO user_types (name, description, permissions, dashboard_config) VALUES 
('admin', 'System Administrator', 
 '{"projects": {"create": true, "read": true, "update": true, "delete": true}, "users": {"create": true, "read": true, "update": true, "delete": true}, "volunteers": {"create": true, "read": true, "update": true, "delete": true}, "reports": {"create": true, "read": true}, "settings": {"read": true, "update": true}}'::jsonb,
 '{"showAllProjects": true, "showFinancials": true, "showUserManagement": true, "showReports": true, "showSettings": true}'::jsonb),
('project_manager', 'Project Manager', 
 '{"projects": {"create": true, "read": true, "update": true, "delete": false}, "tasks": {"create": true, "read": true, "update": true, "delete": true}, "volunteers": {"create": false, "read": true, "update": true, "delete": false}, "reports": {"create": true, "read": true}}'::jsonb,
 '{"showAllProjects": true, "showFinancials": true, "showUserManagement": false, "showReports": true, "showSettings": false}'::jsonb),
('staff_member', 'Staff Member', 
 '{"projects": {"create": false, "read": true, "update": true, "delete": false}, "tasks": {"create": true, "read": true, "update": true, "delete": false}, "volunteers": {"create": false, "read": true, "update": false, "delete": false}}'::jsonb,
 '{"showAllProjects": false, "showFinancials": false, "showUserManagement": false, "showReports": false, "showSettings": false}'::jsonb),
('volunteer', 'Volunteer', 
 '{"projects": {"create": false, "read": true, "update": false, "delete": false}, "tasks": {"create": false, "read": true, "update": true, "delete": false}, "volunteer_profile": {"read": true, "update": true}, "time_tracking": {"create": true, "read": true}}'::jsonb,
 '{"showMyProjects": true, "showMyTasks": true, "showMyHours": true, "showProfile": true, "showTraining": true}'::jsonb),
('viewer', 'Read-only Viewer', 
 '{"projects": {"create": false, "read": true, "update": false, "delete": false}, "reports": {"read": true}}'::jsonb,
 '{"showAllProjects": true, "showFinancials": false, "showUserManagement": false, "showReports": true, "showSettings": false}'::jsonb);

-- Insert volunteer skills
INSERT INTO volunteer_skills (name, category, description) VALUES
('Environmental Education', 'education', 'Teaching and educating others about environmental issues'),
('Tree Planting', 'field_work', 'Physical tree planting and reforestation activities'),
('Data Collection', 'technical', 'Collecting and recording environmental data'),
('Photography', 'technical', 'Documenting projects and activities through photography'),
('Social Media Management', 'administrative', 'Managing social media accounts and content'),
('Grant Writing', 'administrative', 'Writing grant proposals and funding applications'),
('Event Planning', 'administrative', 'Organizing and coordinating events and activities'),
('Translation', 'administrative', 'Translating documents and materials'),
('Web Development', 'technical', 'Website development and maintenance'),
('Graphic Design', 'technical', 'Creating visual materials and designs'),
('Research', 'technical', 'Conducting environmental research and studies'),
('Community Outreach', 'field_work', 'Engaging with local communities');

-- Insert volunteer training modules
INSERT INTO volunteer_training (name, description, is_mandatory, duration_hours, category) VALUES
('General Orientation', 'Basic orientation for all volunteers', TRUE, 2, 'orientation'),
('Safety Procedures', 'Safety guidelines for field work', TRUE, 1, 'safety'),
('Environmental Education Basics', 'Introduction to environmental education principles', FALSE, 4, 'education'),
('Data Collection Methods', 'How to collect and record environmental data', FALSE, 3, 'technical'),
('First Aid', 'Basic first aid training', FALSE, 8, 'safety'),
('Project Management Basics', 'Introduction to project management', FALSE, 6, 'management');

-- Insert test users
INSERT INTO users (
    name, email, password_hash, user_type_id, phone, department, employee_id, is_active, is_email_verified
) VALUES 
('System Administrator', 'admin@repensar.org.mz', '$2b$12$LQv3c1yqBwEHXw17lcHAUO4Q5wrJF.ThjdIe/5bqK1IvZKKQXWOKy', 
 (SELECT id FROM user_types WHERE name = 'admin'), '+258123456789', 'Administration', 'EMP001', true, true),
('João Silva', 'joao.silva@repensar.org.mz', '$2b$12$LQv3c1yqBwEHXw17lcHAUO4Q5wrJF.ThjdIe/5bqK1IvZKKQXWOKy', 
 (SELECT id FROM user_types WHERE name = 'project_manager'), '+258987654321', 'Project Management', 'EMP002', true, true),
('Maria Santos', 'maria.santos@repensar.org.mz', '$2b$12$LQv3c1yqBwEHXw17lcHAUO4Q5wrJF.ThjdIe/5bqK1IvZKKQXWOKy', 
 (SELECT id FROM user_types WHERE name = 'staff_member'), '+258111222333', 'Field Operations', 'EMP003', true, true),
('Carlos Maputo', 'carlos.maputo@gmail.com', '$2b$12$LQv3c1yqBwEHXw17lcHAUO4Q5wrJF.ThjdIe/5bqK1IvZKKQXWOKy', 
 (SELECT id FROM user_types WHERE name = 'volunteer'), '+258444555666', NULL, NULL, true, true),
('Lucia Nhacolo', 'lucia.nhacolo@hotmail.com', '$2b$12$LQv3c1yqBwEHXw17lcHAUO4Q5wrJF.ThjdIe/5bqK1IvZKKQXWOKy', 
 (SELECT id FROM user_types WHERE name = 'volunteer'), '+258222333444', NULL, NULL, true, true);

-- Insert volunteer profiles
INSERT INTO volunteers (
    user_id, volunteer_id, date_of_birth, gender, address, city, postal_code,
    emergency_contact_name, emergency_contact_phone, emergency_contact_relationship,
    availability, volunteer_status, background_check_status, orientation_completed,
    orientation_date, joined_date, motivation
) VALUES 
((SELECT id FROM users WHERE email = 'carlos.maputo@gmail.com'), 'VLT001', '1995-06-15', 'male', 
 'Av. Julius Nyerere, 123', 'Maputo', '1100', 'Ana Maputo', '+258777888999', 'spouse',
 '{"days": ["monday", "wednesday", "saturday"], "hours": "morning", "frequency": "weekly"}'::jsonb,
 'active', 'approved', true, '2025-01-15', '2025-01-10', 
 'Quero contribuir para a preservação do meio ambiente em Moçambique'),
((SELECT id FROM users WHERE email = 'lucia.nhacolo@hotmail.com'), 'VLT002', '1988-03-22', 'female',
 'Bairro da Polana, Rua 45', 'Maputo', '1102', 'Pedro Nhacolo', '+258555666777', 'brother',
 '{"days": ["tuesday", "thursday", "sunday"], "hours": "afternoon", "frequency": "weekly"}'::jsonb,
 'active', 'approved', true, '2025-01-20', '2025-01-18',
 'Como professora, quero educar sobre questões ambientais');

-- Insert volunteer skill assignments
INSERT INTO volunteer_skill_assignments (volunteer_id, skill_id, proficiency_level, years_experience) VALUES 
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Tree Planting'), 'intermediate', 2),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Environmental Education'), 'beginner', 1),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Photography'), 'advanced', 5),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT002'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Environmental Education'), 'expert', 8),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT002'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Event Planning'), 'advanced', 5),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT002'), 
 (SELECT id FROM volunteer_skills WHERE name = 'Community Outreach'), 'advanced', 6);

-- Insert sample projects
INSERT INTO projects (
    name, description, category, status, priority, start_date, end_date, budget,
    location_name, latitude, longitude, project_manager_id, created_by_id,
    requires_volunteers, min_volunteers, max_volunteers, volunteer_requirements
) VALUES 
('Reflorestação da Reserva de Maputo', 
 'Projeto de plantio de árvores nativas na Reserva Especial de Maputo para restaurar áreas degradadas.',
 'reforestation', 'in_progress', 'high', '2025-02-01', '2025-12-31', 50000.00,
 'Reserva Especial de Maputo', -26.0269, 32.5906,
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'),
 (SELECT id FROM users WHERE email = 'admin@repensar.org.mz'),
 true, 5, 15, 'Disponibilidade para trabalho de campo aos fins de semana'),
('Educação Ambiental nas Escolas', 
 'Programa de sensibilização ambiental em escolas primárias da cidade de Maputo.',
 'environmental_education', 'planning', 'medium', '2025-03-01', '2025-11-30', 25000.00,
 'Escolas de Maputo', -25.9692, 32.5731,
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'),
 (SELECT id FROM users WHERE email = 'admin@repensar.org.mz'),
 true, 3, 10, 'Experiência em educação ou comunicação'),
('Gestão de Resíduos Sólidos', 
 'Implementação de sistema de separação e reciclagem de resíduos em comunidades urbanas.',
 'waste_management', 'planning', 'high', '2025-04-01', '2026-03-31', 75000.00,
 'Bairros de Maputo', -25.9553, 32.5892,
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'),
 (SELECT id FROM users WHERE email = 'admin@repensar.org.mz'),
 true, 8, 20, 'Conhecimento básico sobre gestão de resíduos');

-- Insert project teams
INSERT INTO project_teams (project_id, user_id, role, is_volunteer) VALUES 
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'), 'Project Manager', false),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz'), 'Field Coordinator', false),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM users WHERE email = 'carlos.maputo@gmail.com'), 'Volunteer', true),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'), 'Project Manager', false),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 (SELECT id FROM users WHERE email = 'lucia.nhacolo@hotmail.com'), 'Education Volunteer', true);

-- Insert sample tasks
INSERT INTO tasks (
    project_id, title, description, status, priority, start_date, end_date,
    estimated_hours, assigned_to_id, created_by_id, suitable_for_volunteers, volunteer_spots
) VALUES 
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Preparação do solo', 'Limpeza e preparação das áreas para plantio', 'in_progress', 'high',
 '2025-02-01', '2025-02-15', 40.0,
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz'),
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'), true, 3),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Plantio de mudas', 'Plantio das mudas nativas nas áreas preparadas', 'not_started', 'high',
 '2025-02-16', '2025-03-31', 120.0,
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz'),
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'), true, 8),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 'Desenvolvimento de material didático', 'Criação de materiais educativos sobre meio ambiente', 'not_started', 'medium',
 '2025-03-01', '2025-03-15', 30.0,
 (SELECT id FROM users WHERE email = 'lucia.nhacolo@hotmail.com'),
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'), true, 2);

-- Insert task volunteers
INSERT INTO task_volunteers (task_id, volunteer_id, hours_contributed) VALUES 
((SELECT id FROM tasks WHERE title = 'Preparação do solo'),
 (SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'), 8.5);

-- Insert sample volunteer time logs
INSERT INTO volunteer_time_logs (
    volunteer_id, project_id, task_id, date, start_time, end_time, hours,
    activity_description, approved, approved_by_id
) VALUES 
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'),
 (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM tasks WHERE title = 'Preparação do solo'),
 '2025-02-01', '08:00:00', '12:30:00', 4.5,
 'Limpeza de área degradada e remoção de lixo', true,
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz')),
((SELECT id FROM volunteers WHERE volunteer_id = 'VLT001'),
 (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM tasks WHERE title = 'Preparação do solo'),
 '2025-02-03', '08:00:00', '12:00:00', 4.0,
 'Preparação do solo para plantio', true,
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz'));

-- Insert sample milestones
INSERT INTO milestones (project_id, name, description, target_date, status) VALUES 
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Área preparada', 'Conclusão da preparação de 5 hectares', '2025-02-15', 'pending'),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Primeira fase de plantio', 'Plantio de 1000 mudas', '2025-03-31', 'pending'),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 'Material didático pronto', 'Finalização dos materiais educativos', '2025-03-15', 'pending');

-- Insert sample environmental metrics
INSERT INTO environmental_metrics (
    project_id, metric_name, metric_type, target_value, current_value, unit,
    measurement_date, description, recorded_by_id
) VALUES 
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Árvores plantadas', 'quantity', 5000.0, 0.0, 'unidades', '2025-02-01',
 'Número total de árvores plantadas no projeto',
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz')),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'Área reflorestada', 'area', 50.0, 0.0, 'hectares', '2025-02-01',
 'Área total reflorestada em hectares',
 (SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz')),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 'Estudantes alcançados', 'quantity', 2000.0, 0.0, 'estudantes', '2025-03-01',
 'Número de estudantes que participaram nas atividades',
 (SELECT id FROM users WHERE email = 'lucia.nhacolo@hotmail.com'));

-- Insert sample resources
INSERT INTO resources (name, type, description, unit_cost, unit, available_quantity, location) VALUES 
('Mudas de árvores nativas', 'material', 'Mudas de espécies nativas para reflorestação', 5.00, 'unidade', 10000, 'Viveiro Central'),
('Ferramentas de plantio', 'equipment', 'Pás, enxadas e outras ferramentas para plantio', 150.00, 'conjunto', 20, 'Armazém'),
('Veículo 4x4', 'equipment', 'Veículo para transporte em áreas de difícil acesso', 500.00, 'dia', 2, 'Garagem'),
('Material didático', 'material', 'Folhetos, cartazes e outros materiais educativos', 2.00, 'unidade', 5000, 'Escritório');

-- Insert project resource allocations
INSERT INTO project_resources (project_id, resource_id, quantity_allocated, allocation_date, allocated_by_id) VALUES 
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM resources WHERE name = 'Mudas de árvores nativas'), 5000, '2025-02-01',
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz')),
((SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 (SELECT id FROM resources WHERE name = 'Ferramentas de plantio'), 10, '2025-02-01',
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz')),
((SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas'),
 (SELECT id FROM resources WHERE name = 'Material didático'), 2000, '2025-03-01',
 (SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'));

-- Insert sample notifications
INSERT INTO notifications (user_id, title, message, type, related_project_id) VALUES 
((SELECT id FROM users WHERE email = 'carlos.maputo@gmail.com'),
 'Nova atividade disponível', 'Há uma nova atividade de plantio disponível no projeto de Reflorestação da Reserva de Maputo.',
 'info', (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo')),
((SELECT id FROM users WHERE email = 'lucia.nhacolo@hotmail.com'),
 'Reunião de planeamento', 'Reunião de planeamento do projeto de Educação Ambiental agendada para amanhã.',
 'warning', (SELECT id FROM projects WHERE name = 'Educação Ambiental nas Escolas')),
((SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'),
 'Relatório mensal', 'Lembrete: relatório mensal deve ser submetido até ao final da semana.',
 'warning', NULL);

-- Insert sample activity logs
INSERT INTO activity_logs (user_id, project_id, action, description, created_at) VALUES 
((SELECT id FROM users WHERE email = 'admin@repensar.org.mz'),
 (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'project_created', 'Projeto de Reflorestação da Reserva de Maputo foi criado', '2025-01-25 10:00:00+00'),
((SELECT id FROM users WHERE email = 'joao.silva@repensar.org.mz'),
 (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'team_member_added', 'Carlos Maputo foi adicionado como voluntário ao projeto', '2025-01-26 14:30:00+00'),
((SELECT id FROM users WHERE email = 'maria.santos@repensar.org.mz'),
 (SELECT id FROM projects WHERE name = 'Reflorestação da Reserva de Maputo'),
 'task_created', 'Tarefa "Preparação do solo" foi criada', '2025-01-27 09:15:00+00');

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Verify user types
SELECT 'User Types:' as table_name;
SELECT id, name, description FROM user_types ORDER BY id;

-- Verify users
SELECT 'Users:' as table_name;
SELECT u.id, u.name, u.email, ut.name as user_type, u.is_active, u.is_email_verified
FROM users u
JOIN user_types ut ON u.user_type_id = ut.id
ORDER BY u.id;

-- Verify volunteers
SELECT 'Volunteers:' as table_name;
SELECT v.volunteer_id, u.name, v.volunteer_status, v.total_hours_contributed, v.joined_date
FROM volunteers v
JOIN users u ON v.user_id = u.id
ORDER BY v.id;

-- Verify volunteer skills
SELECT 'Volunteer Skills:' as table_name;
SELECT vs.name, vs.category, COUNT(vsa.volunteer_id) as volunteers_with_skill
FROM volunteer_skills vs
LEFT JOIN volunteer_skill_assignments vsa ON vs.id = vsa.skill_id
GROUP BY vs.id, vs.name, vs.category
ORDER BY vs.name;

-- Verify projects
SELECT 'Projects:' as table_name;
SELECT p.id, p.name, p.status, p.category, u.name as project_manager
FROM projects p
LEFT JOIN users u ON p.project_manager_id = u.id
ORDER BY p.id;

-- Verify project teams
SELECT 'Project Teams:' as table_name;
SELECT p.name as project, u.name as member, pt.role, pt.is_volunteer
FROM project_teams pt
JOIN projects p ON pt.project_id = p.id
JOIN users u ON pt.user_id = u.id
WHERE pt.is_active = true
ORDER BY p.name, pt.is_volunteer, u.name;

-- Verify tasks
SELECT 'Tasks:' as table_name;
SELECT p.name as project, t.title, t.status, t.suitable_for_volunteers, t.volunteer_spots
FROM tasks t
JOIN projects p ON t.project_id = p.id
ORDER BY p.name, t.id;

-- Final success message
SELECT '✅ Database setup completed successfully!' as status,
       'All tables created and sample data inserted.' as message,
       'Default password for all users: admin123' as note;
