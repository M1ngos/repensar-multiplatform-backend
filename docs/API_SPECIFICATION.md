# Repensar Multiplatform Backend - API Specification

**Version:** 2.0
**Last Updated:** 2025-10-27
**Base URL:** `/api` (or as configured)

## Table of Contents

1. [Authentication](#1-authentication)
2. [Users](#2-users)
3. [Projects](#3-projects)
4. [Tasks](#4-tasks)
5. [Volunteers](#5-volunteers)
6. [Resources](#6-resources)
7. [Analytics](#7-analytics)
8. [Reports & Exports](#8-reports--exports)
9. [Sync (Offline-First)](#9-sync-offline-first)
10. [Common Schemas](#10-common-schemas)
11. [Error Handling](#11-error-handling)

---

## 1. Authentication

All endpoints require JWT authentication unless specified otherwise.

### 1.1 Register User

**Endpoint:** `POST /auth/register`
**Authentication:** None
**Description:** Register a new user account.

**Request Body:**
```json
{
  "name": "string (required)",
  "email": "string (required, valid email)",
  "password": "string (required, min 8 chars)",
  "phone": "string (optional)",
  "user_type": "string (optional, default: 'volunteer')"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1,
  "access_token": "string",
  "refresh_token": "string"
}
```

**Status Codes:**
- `201` - User created successfully
- `400` - Validation error or email already exists
- `500` - Server error

---

### 1.2 Login

**Endpoint:** `POST /auth/login`
**Authentication:** None
**Description:** Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "name": "string",
    "email": "string",
    "user_type": "string"
  }
}
```

**Status Codes:**
- `200` - Login successful
- `401` - Invalid credentials
- `403` - Account locked (after 5 failed attempts)
- `500` - Server error

---

### 1.3 Refresh Token

**Endpoint:** `POST /auth/refresh`
**Authentication:** Refresh Token
**Description:** Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string (required)"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "refresh_token": "string (new token)",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Status Codes:**
- `200` - Token refreshed successfully
- `401` - Invalid or expired refresh token
- `500` - Server error

---

### 1.4 Get Current User

**Endpoint:** `GET /auth/me`
**Authentication:** Bearer Token
**Description:** Get current authenticated user details.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "string",
  "email": "string",
  "phone": "string",
  "user_type": {
    "id": 1,
    "name": "volunteer",
    "permissions": {}
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 1.5 Logout

**Endpoint:** `POST /auth/logout`
**Authentication:** Bearer Token
**Description:** Logout and invalidate current access token.

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 2. Users

### 2.1 List Users

**Endpoint:** `GET /users`
**Authentication:** Bearer Token (admin, staff_member)
**Description:** Get paginated list of users with filtering and search options.

**Query Parameters:**
- `page` (integer, default: 1, min: 1) - Page number (1-indexed)
- `page_size` (integer, default: 20, min: 1, max: 100) - Items per page
- `search` (string, optional) - Search by name, email, department, or employee ID (case-insensitive)
- `user_type_id` (integer, optional) - Filter by user type ID
- `is_active` (boolean, optional) - Filter by active/inactive status
- `department` (string, optional) - Filter by specific department

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "user_type_name": "admin",
      "department": "IT",
      "is_active": true,
      "profile_picture": "https://example.com/avatar.jpg"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "user_type_name": "volunteer",
      "department": null,
      "is_active": true,
      "profile_picture": null
    }
  ],
  "metadata": {
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

**Status Codes:**
- `200` - Success
- `403` - Not authorized (requires admin or staff_member role)
- `500` - Server error

---

### 2.2 Get Current User Profile

**Endpoint:** `GET /users/me`
**Authentication:** Bearer Token
**Description:** Get current authenticated user's detailed profile.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "department": "IT",
  "employee_id": "EMP001",
  "is_active": true,
  "is_email_verified": true,
  "profile_picture": "https://example.com/avatar.jpg",
  "last_login": "2025-10-27T10:30:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-10-27T09:00:00Z",
  "user_type": {
    "id": 1,
    "name": "admin",
    "description": "Administrator with full access"
  },
  "oauth_provider": null
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (invalid or missing token)
- `500` - Server error

---

### 2.3 Get User by ID

**Endpoint:** `GET /users/{user_id}`
**Authentication:** Bearer Token
**Description:** Get detailed user information by ID.

**Path Parameters:**
- `user_id` (integer, required) - User ID

**Permissions:**
- Users can view their own profile
- Admin and staff_member can view any user

**Response:** `200 OK` (same schema as Get Current User Profile)

**Status Codes:**
- `200` - Success
- `403` - Not authorized to view this user
- `404` - User not found
- `500` - Server error

---

### 2.4 Update User

**Endpoint:** `PUT /users/{user_id}`
**Authentication:** Bearer Token
**Description:** Update user information.

**Path Parameters:**
- `user_id` (integer, required) - User ID

**Permissions:**
- Users can update their own profile
- Admin and staff_member can update any user

**Request Body:** (all fields optional)
```json
{
  "name": "string (max 100)",
  "phone": "string (max 20)",
  "department": "string (max 50)",
  "employee_id": "string (max 50)",
  "profile_picture": "string (max 500, URL)"
}
```

**Response:** `200 OK` (returns updated UserDetail)

**Status Codes:**
- `200` - User updated successfully
- `403` - Not authorized to update this user
- `404` - User not found
- `500` - Server error

---

### 2.5 Activate User

**Endpoint:** `POST /users/{user_id}/activate`
**Authentication:** Bearer Token (admin only)
**Description:** Activate a deactivated user account.

**Path Parameters:**
- `user_id` (integer, required) - User ID

**Response:** `200 OK`
```json
{
  "message": "User activated successfully"
}
```

**Status Codes:**
- `200` - User activated
- `403` - Not authorized (requires admin role)
- `404` - User not found
- `500` - Server error

---

### 2.6 Deactivate User

**Endpoint:** `POST /users/{user_id}/deactivate`
**Authentication:** Bearer Token (admin only)
**Description:** Deactivate user account (soft delete).

**Path Parameters:**
- `user_id` (integer, required) - User ID

**Response:** `200 OK`
```json
{
  "message": "User deactivated successfully"
}
```

**Status Codes:**
- `200` - User deactivated
- `400` - Cannot deactivate own account
- `403` - Not authorized (requires admin role)
- `404` - User not found
- `500` - Server error

---

### 2.7 Get User Types

**Endpoint:** `GET /users/types/all`
**Authentication:** Bearer Token
**Description:** Get list of all available user types.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Administrator with full access"
  },
  {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with limited admin access"
  },
  {
    "id": 3,
    "name": "project_manager",
    "description": "Project manager"
  },
  {
    "id": 4,
    "name": "volunteer",
    "description": "Volunteer user"
  }
]
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 2.8 Get Departments

**Endpoint:** `GET /users/departments/all`
**Authentication:** Bearer Token
**Description:** Get list of all unique departments from user records.

**Response:** `200 OK`
```json
[
  "IT",
  "HR",
  "Operations",
  "Finance",
  "Environmental Services"
]
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

## 3. Projects

### 3.1 Create Project

**Endpoint:** `POST /projects`
**Authentication:** Bearer Token (admin, project_manager)
**Description:** Create a new project.

**Request Body:**
```json
{
  "name": "string (required, max 200)",
  "description": "string (optional)",
  "category": "string (required: reforestation|environmental_education|waste_management|conservation|research|community_engagement|climate_action|biodiversity)",
  "status": "string (optional, default: planning)",
  "priority": "string (optional, default: medium)",
  "start_date": "date (optional, YYYY-MM-DD)",
  "end_date": "date (optional, YYYY-MM-DD)",
  "budget": "number (optional)",
  "location": "string (optional)",
  "latitude": "number (optional)",
  "longitude": "number (optional)",
  "requires_volunteers": "boolean (optional, default: false)",
  "min_volunteers": "integer (optional)",
  "max_volunteers": "integer (optional)"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Rainforest Reforestation 2025",
  "category": "reforestation",
  "status": "planning",
  "priority": "high",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "budget": 50000.00,
  "project_manager_id": 2,
  "created_by_id": 2,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Status Codes:**
- `201` - Project created
- `400` - Validation error
- `403` - Not authorized
- `500` - Server error

---

### 3.2 List Projects

**Endpoint:** `GET /projects`
**Authentication:** Bearer Token
**Description:** Get paginated list of projects with filtering.

**Query Parameters:**
- `skip` (integer, default: 0) - Offset for pagination (legacy, prefer page)
- `limit` (integer, default: 100, max: 100) - Items per page (legacy, prefer page_size)
- `status` (string, optional) - Filter by status
- `category` (string, optional) - Filter by category
- `manager_id` (integer, optional) - Filter by project manager
- `requires_volunteers` (boolean, optional) - Filter projects needing volunteers
- `search` (string, optional) - Search in name/description

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Rainforest Reforestation 2025",
    "category": "reforestation",
    "status": "in_progress",
    "priority": "high",
    "start_date": "2025-02-01",
    "end_date": "2025-12-31",
    "project_manager_name": "John Manager",
    "team_size": 5,
    "volunteers_count": 12,
    "progress": 35.5
  }
]
```

---

### 3.3 Get Project Details

**Endpoint:** `GET /projects/{project_id}`
**Authentication:** Bearer Token
**Description:** Get detailed information about a specific project.

**Path Parameters:**
- `project_id` (integer, required) - Project ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Rainforest Reforestation 2025",
  "description": "Large scale reforestation project...",
  "category": "reforestation",
  "status": "in_progress",
  "priority": "high",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "budget": 50000.00,
  "actual_cost": 15000.00,
  "project_manager_id": 2,
  "project_manager_name": "John Manager",
  "created_by_id": 2,
  "created_by_name": "John Manager",
  "team_members": [
    {
      "id": 1,
      "user_id": 3,
      "name": "Alice Smith",
      "email": "alice@example.com",
      "role": "coordinator",
      "joined_date": "2025-02-01"
    }
  ],
  "milestones": [
    {
      "id": 1,
      "name": "Site Preparation",
      "status": "achieved",
      "target_date": "2025-02-15",
      "actual_date": "2025-02-14"
    }
  ],
  "environmental_metrics": [
    {
      "id": 1,
      "metric_name": "Trees Planted",
      "target_value": 1000,
      "current_value": 450,
      "unit": "trees",
      "measurement_date": "2025-03-01"
    }
  ],
  "total_tasks": 25,
  "completed_tasks": 10,
  "progress_percentage": 40.0,
  "volunteer_hours": 320.5
}
```

**Status Codes:**
- `200` - Success
- `404` - Project not found
- `500` - Server error

---

### 3.4 Update Project

**Endpoint:** `PUT /projects/{project_id}`
**Authentication:** Bearer Token (admin, project_manager, project owner)
**Description:** Update project details.

**Path Parameters:**
- `project_id` (integer, required)

**Request Body:** (all fields optional)
```json
{
  "name": "string",
  "description": "string",
  "status": "string",
  "priority": "string",
  "end_date": "date",
  "actual_cost": "number"
}
```

**Response:** `200 OK` (same schema as Get Project)

---

### 3.5 Delete Project

**Endpoint:** `DELETE /projects/{project_id}`
**Authentication:** Bearer Token (admin only)
**Description:** Delete/cancel a project.

**Response:** `200 OK`
```json
{
  "message": "Project deleted successfully"
}
```

---

### 3.6 Get Project Tasks (NEW)

**Endpoint:** `GET /projects/{project_id}/tasks`
**Authentication:** Bearer Token
**Description:** Get all tasks for a specific project with pagination.

**Path Parameters:**
- `project_id` (integer, required)

**Query Parameters:**
- `page` (integer, default: 1) - Page number (1-indexed)
- `page_size` (integer, default: 20, max: 100) - Items per page
- `status` (string, optional) - Filter by task status
- `priority` (string, optional) - Filter by priority
- `suitable_for_volunteers` (boolean, optional) - Filter volunteer-suitable tasks

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "title": "Site Assessment",
      "project_id": 1,
      "project_name": "Rainforest Reforestation 2025",
      "status": "completed",
      "priority": "high",
      "assigned_to_name": "Bob Worker",
      "progress_percentage": 100.0,
      "volunteers_count": 3
    }
  ],
  "metadata": {
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

---

### 3.7 Get Project Volunteers (NEW)

**Endpoint:** `GET /projects/{project_id}/volunteers`
**Authentication:** Bearer Token
**Description:** Get all volunteers assigned to a project.

**Path Parameters:**
- `project_id` (integer, required)

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20, max: 100)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "volunteer_id": "VLT001",
      "name": "Alice Volunteer",
      "email": "alice@example.com",
      "volunteer_status": "active",
      "active_projects_count": 2,
      "total_hours_contributed": 45.5
    }
  ],
  "metadata": {
    "total": 12,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

---

### 3.8 Get Project Resources (NEW)

**Endpoint:** `GET /projects/{project_id}/resources`
**Authentication:** Bearer Token
**Description:** Get all resources allocated to a project.

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response:** `200 OK` (Paginated resource allocations)

---

### 3.9 Get Project Activity (NEW)

**Endpoint:** `GET /projects/{project_id}/activity`
**Authentication:** Bearer Token
**Description:** Get activity log for a project.

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `action_filter` (string, optional) - Filter by action type

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 123,
      "user_name": "John Manager",
      "action": "project_updated",
      "description": "Updated project status to in_progress",
      "created_at": "2025-03-15T14:30:00Z",
      "old_values": {"status": "planning"},
      "new_values": {"status": "in_progress"}
    }
  ],
  "metadata": {
    "total": 58,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 4. Tasks

### 4.1 Create Task

**Endpoint:** `POST /tasks`
**Authentication:** Bearer Token (admin, project_manager)
**Description:** Create a new task within a project.

**Request Body:**
```json
{
  "project_id": "integer (required)",
  "title": "string (required, max 200)",
  "description": "string (optional)",
  "status": "string (optional, default: not_started)",
  "priority": "string (optional, default: medium)",
  "assigned_to_id": "integer (optional)",
  "parent_task_id": "integer (optional)",
  "estimated_hours": "number (optional)",
  "start_date": "date (optional)",
  "due_date": "date (optional)",
  "suitable_for_volunteers": "boolean (optional, default: false)",
  "volunteer_spots": "integer (optional)",
  "required_skills": "object (optional, JSON)"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "project_id": 1,
  "title": "Site Assessment",
  "status": "not_started",
  "priority": "high",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 4.2 List Tasks

**Endpoint:** `GET /tasks`
**Authentication:** Bearer Token
**Description:** Get paginated list of tasks with filtering.

**Query Parameters:**
- `skip` (integer, default: 0)
- `limit` (integer, default: 100)
- `project_id` (integer, optional) - Filter by project
- `status` (string, optional) - Filter by status
- `priority` (string, optional) - Filter by priority
- `assigned_to_id` (integer, optional) - Filter by assignee
- `suitable_for_volunteers` (boolean, optional)
- `search` (string, optional)

**Response:** `200 OK` (List of task summaries)

---

### 4.3 Get Task Details

**Endpoint:** `GET /tasks/{task_id}`
**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "id": 1,
  "project_id": 1,
  "project_name": "Rainforest Reforestation 2025",
  "title": "Site Assessment",
  "description": "Assess the reforestation site...",
  "status": "in_progress",
  "priority": "high",
  "assigned_to_id": 3,
  "assigned_to_name": "Bob Worker",
  "parent_task_id": null,
  "estimated_hours": 8.0,
  "actual_hours": 5.5,
  "progress_percentage": 70.0,
  "start_date": "2025-02-01",
  "due_date": "2025-02-03",
  "suitable_for_volunteers": true,
  "volunteer_spots": 2,
  "volunteers_assigned": [
    {
      "volunteer_id": 1,
      "name": "Alice Volunteer",
      "hours_contributed": 3.0
    }
  ],
  "dependencies": [
    {
      "id": 1,
      "predecessor_task_id": 2,
      "dependency_type": "finish_to_start"
    }
  ]
}
```

---

### 4.4 Update Task

**Endpoint:** `PUT /tasks/{task_id}`
**Authentication:** Bearer Token
**Description:** Update task details.

**Request Body:** (all fields optional)

---

### 4.5 Assign Volunteer to Task

**Endpoint:** `POST /tasks/{task_id}/assign-volunteer`
**Authentication:** Bearer Token (admin, project_manager)

**Request Body:**
```json
{
  "volunteer_id": "integer (required)",
  "role_description": "string (optional)"
}
```

**Response:** `200 OK`

---

## 5. Volunteers

### 5.1 Register Volunteer

**Endpoint:** `POST /volunteers/register`
**Authentication:** None
**Description:** Register a new volunteer (creates user account + volunteer profile).

**Request Body:**
```json
{
  "name": "string (required)",
  "email": "string (required)",
  "password": "string (required, min 8 chars)",
  "phone": "string (optional)",
  "date_of_birth": "date (required, YYYY-MM-DD)",
  "gender": "string (optional)",
  "address": "string (optional)",
  "city": "string (optional)",
  "postal_code": "string (optional)",
  "emergency_contact_name": "string (optional)",
  "emergency_contact_phone": "string (optional)",
  "emergency_contact_relationship": "string (optional)",
  "availability": "string (optional)",
  "motivation": "string (optional)",
  "skill_ids": "array[integer] (optional)"
}
```

**Response:** `201 Created`
```json
{
  "message": "Volunteer registered successfully",
  "volunteer_id": "VLT001",
  "user_id": 5
}
```

---

### 5.2 List Volunteers

**Endpoint:** `GET /volunteers`
**Authentication:** Bearer Token

**Query Parameters:**
- `skip` (integer, default: 0)
- `limit` (integer, default: 100)
- `status` (string, optional) - Filter by volunteer_status
- `search` (string, optional)

**Response:** `200 OK` (List of volunteer summaries)

---

### 5.3 Get Volunteer Profile

**Endpoint:** `GET /volunteers/{volunteer_id}`
**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "id": 1,
  "volunteer_id": "VLT001",
  "user_id": 5,
  "name": "Alice Volunteer",
  "email": "alice@example.com",
  "phone": "+1234567890",
  "date_of_birth": "1995-05-15",
  "gender": "female",
  "address": "123 Main St",
  "city": "Springfield",
  "volunteer_status": "active",
  "background_check_status": "approved",
  "total_hours_contributed": 120.5,
  "joined_date": "2025-01-01",
  "skills": [
    {
      "skill_id": 1,
      "skill_name": "Environmental Education",
      "proficiency_level": "intermediate",
      "years_experience": 2
    }
  ]
}
```

---

### 5.4 Get Volunteer Projects (NEW)

**Endpoint:** `GET /volunteers/{volunteer_id}/projects`
**Authentication:** Bearer Token
**Description:** Get all projects a volunteer is involved in.

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `status` (string, optional) - Filter by project status

**Response:** `200 OK` (Paginated project summaries)

---

### 5.5 Get Volunteer Tasks (NEW)

**Endpoint:** `GET /volunteers/{volunteer_id}/tasks`
**Authentication:** Bearer Token
**Description:** Get all tasks assigned to a volunteer.

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `status` (string, optional) - Filter by task status
- `project_id` (integer, optional) - Filter by project

**Response:** `200 OK` (Paginated task summaries)

---

### 5.6 Get Volunteer Activity (NEW)

**Endpoint:** `GET /volunteers/{volunteer_id}/activity`
**Authentication:** Bearer Token
**Description:** Get activity log for a volunteer.

**Query Parameters:**
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `action_filter` (string, optional)

**Response:** `200 OK` (Paginated activity logs)

---

### 5.7 Log Volunteer Hours

**Endpoint:** `POST /volunteers/{volunteer_id}/time-logs`
**Authentication:** Bearer Token

**Request Body:**
```json
{
  "project_id": "integer (optional)",
  "task_id": "integer (optional)",
  "date": "date (required, YYYY-MM-DD)",
  "hours": "number (required, > 0)",
  "activity": "string (optional)",
  "description": "string (optional)",
  "supervisor_id": "integer (optional)"
}
```

**Response:** `201 Created`

---

### 5.8 Get Volunteer Time Logs

**Endpoint:** `GET /volunteers/{volunteer_id}/time-logs`
**Authentication:** Bearer Token

**Query Parameters:**
- `skip` (integer, default: 0)
- `limit` (integer, default: 100)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `approval_status` (string, optional)

**Response:** `200 OK` (List of time logs)

---

### 5.9 Approve Time Log

**Endpoint:** `POST /volunteers/time-logs/{log_id}/approve`
**Authentication:** Bearer Token (admin, project_manager, supervisor)

**Response:** `200 OK`

---

## 6. Resources

### 6.1 Create Resource

**Endpoint:** `POST /resources`
**Authentication:** Bearer Token (admin, project_manager)

**Request Body:**
```json
{
  "name": "string (required, max 150)",
  "description": "string (optional)",
  "resource_type": "string (required: human|equipment|material|financial)",
  "unit": "string (optional, e.g., 'hours', 'kg', 'units')",
  "unit_cost": "number (optional)",
  "available_quantity": "number (optional)",
  "location": "string (optional)"
}
```

**Response:** `201 Created`

---

### 6.2 List Resources

**Endpoint:** `GET /resources`
**Authentication:** Bearer Token
**Description:** Get paginated list of resources with filtering.

**Query Parameters:**
- `page` (integer, default: 1, min: 1) - Page number (1-indexed)
- `page_size` (integer, default: 20, min: 1, max: 100) - Items per page
- `resource_type` (string, optional) - Filter by resource type
- `search` (string, optional) - Search by name or description
- `location` (string, optional) - Filter by location

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "name": "Safety Equipment Kit",
      "resource_type": "equipment",
      "available_quantity": 15,
      "unit": "kits",
      "unit_cost": 50.00,
      "location": "Main Warehouse",
      "allocated_quantity": 5,
      "is_available": true
    },
    {
      "id": 2,
      "name": "Tree Seedlings",
      "resource_type": "material",
      "available_quantity": 5000,
      "unit": "seedlings",
      "unit_cost": 2.50,
      "location": "Greenhouse A",
      "allocated_quantity": 1200,
      "is_available": true
    }
  ],
  "metadata": {
    "total": 48,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 6.3 Get Resource Details

**Endpoint:** `GET /resources/{resource_id}`
**Authentication:** Bearer Token
**Description:** Get detailed information about a specific resource.

**Path Parameters:**
- `resource_id` (integer, required) - Resource ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Safety Equipment Kit",
  "description": "Complete safety kit including helmets, gloves, and vests",
  "resource_type": "equipment",
  "unit": "kits",
  "unit_cost": 50.00,
  "available_quantity": 15,
  "total_quantity": 20,
  "allocated_quantity": 5,
  "location": "Main Warehouse",
  "supplier": "SafetyPro Ltd.",
  "purchase_date": "2025-01-10",
  "expiry_date": null,
  "maintenance_schedule": "quarterly",
  "last_maintenance_date": "2025-01-15",
  "is_available": true,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-03-15T10:30:00Z",
  "allocations": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "Rainforest Reforestation 2025",
      "quantity_allocated": 3,
      "allocation_date": "2025-02-01",
      "return_date": null,
      "status": "in_use"
    },
    {
      "id": 2,
      "project_id": 2,
      "project_name": "Beach Cleanup Initiative",
      "quantity_allocated": 2,
      "allocation_date": "2025-03-01",
      "return_date": null,
      "status": "in_use"
    }
  ],
  "metadata": {
    "total_cost": 1000.00,
    "utilization_rate": 25.0,
    "notes": "Regular inspection required before each use"
  }
}
```

**Status Codes:**
- `200` - Success
- `404` - Resource not found
- `500` - Server error

---

### 6.4 Update Resource

**Endpoint:** `PUT /resources/{resource_id}`
**Authentication:** Bearer Token (admin, project_manager, staff_member)
**Description:** Update resource information.

**Path Parameters:**
- `resource_id` (integer, required) - Resource ID

**Request Body:** (all fields optional)
```json
{
  "name": "string (max 150)",
  "description": "string",
  "unit": "string (max 20)",
  "unit_cost": "number (min 0)",
  "available_quantity": "number (min 0)",
  "total_quantity": "number (min 0)",
  "location": "string (max 100)",
  "supplier": "string (max 100)",
  "maintenance_schedule": "string",
  "last_maintenance_date": "date (YYYY-MM-DD)",
  "expiry_date": "date (YYYY-MM-DD)",
  "is_available": "boolean",
  "metadata": "object"
}
```

**Response:** `200 OK` (returns updated ResourceDetail schema)

**Status Codes:**
- `200` - Resource updated successfully
- `400` - Validation error (e.g., available_quantity > total_quantity)
- `403` - Not authorized to update resources
- `404` - Resource not found
- `500` - Server error

---

### 6.5 Delete Resource

**Endpoint:** `DELETE /resources/{resource_id}`
**Authentication:** Bearer Token (admin only)
**Description:** Delete a resource. Cannot delete if resource is currently allocated to active projects.

**Path Parameters:**
- `resource_id` (integer, required) - Resource ID

**Response:** `200 OK`
```json
{
  "message": "Resource deleted successfully"
}
```

**Status Codes:**
- `200` - Resource deleted successfully
- `400` - Cannot delete resource (currently allocated to projects)
- `403` - Not authorized (requires admin role)
- `404` - Resource not found
- `500` - Server error

---

### 6.6 Allocate Resource to Project

**Endpoint:** `POST /resources/{resource_id}/allocate`
**Authentication:** Bearer Token (admin, project_manager)

**Request Body:**
```json
{
  "project_id": "integer (required)",
  "quantity_allocated": "number (required)",
  "allocation_date": "date (optional)"
}
```

**Response:** `200 OK`

---

## 7. Analytics

**NEW MODULE** - Provides time-series metrics, trends, and dashboard analytics.

### 7.1 Create Metric Snapshot

**Endpoint:** `POST /analytics/metrics/snapshot`
**Authentication:** Bearer Token (admin, project_manager, staff_member)
**Description:** Manually record a metric snapshot for time-series tracking.

**Request Body:**
```json
{
  "metric_type": "string (required: volunteer_hours|project_progress|task_completion|volunteer_count|resource_utilization|environmental_impact|budget_spent|custom)",
  "metric_name": "string (required)",
  "value": "number (required)",
  "unit": "string (optional)",
  "project_id": "integer (optional)",
  "task_id": "integer (optional)",
  "volunteer_id": "integer (optional)",
  "metadata": "object (optional)",
  "snapshot_date": "datetime (optional, defaults to now)"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Metric snapshot created successfully",
  "snapshot_id": 123
}
```

---

### 7.2 Get Time-Series Metrics

**Endpoint:** `GET /analytics/metrics/time-series`
**Authentication:** Bearer Token
**Description:** Retrieve time-series data for a specific metric type.

**Query Parameters:**
- `metric_type` (string, required) - Type of metric
- `start_date` (date, required, YYYY-MM-DD)
- `end_date` (date, required, YYYY-MM-DD)
- `project_id` (integer, optional) - Filter by project
- `task_id` (integer, optional) - Filter by task
- `volunteer_id` (integer, optional) - Filter by volunteer
- `granularity` (string, optional, default: daily) - hourly|daily|weekly|monthly

**Response:** `200 OK`
```json
{
  "metric_type": "volunteer_hours",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "granularity": "monthly",
  "data_points": 3,
  "data": [
    {
      "period": "2025-01",
      "count": 45,
      "sum": 320.5,
      "avg": 7.12,
      "min": 2.0,
      "max": 12.0
    },
    {
      "period": "2025-02",
      "count": 52,
      "sum": 380.0,
      "avg": 7.31,
      "min": 1.5,
      "max": 15.0
    }
  ]
}
```

---

### 7.3 Get Analytics Dashboard

**Endpoint:** `GET /analytics/dashboard`
**Authentication:** Bearer Token
**Description:** Get aggregated analytics dashboard with KPIs.

**Query Parameters:**
- `project_id` (integer, optional) - Scope to specific project
- `start_date` (date, optional, default: 30 days ago)
- `end_date` (date, optional, default: today)

**Response:** `200 OK`
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-03-31"
  },
  "project_filter": null,
  "summary": {
    "projects": {
      "total_projects": 15,
      "active_projects": 8,
      "completed_projects": 5,
      "planning_projects": 2
    },
    "tasks": {
      "total_tasks": 240,
      "completed_tasks": 120,
      "in_progress_tasks": 85,
      "not_started_tasks": 35,
      "completion_rate": 50.0
    },
    "volunteers": {
      "active_volunteers": 45,
      "total_hours_logged": 3250.5,
      "avg_hours_per_volunteer": 72.23
    },
    "budget": null
  }
}
```

---

### 7.4 Get Volunteer Hours Trends

**Endpoint:** `GET /analytics/trends/volunteer-hours`
**Authentication:** Bearer Token
**Description:** Get volunteer hours trends over time.

**Query Parameters:**
- `start_date` (date, required)
- `end_date` (date, required)
- `project_id` (integer, optional)
- `volunteer_id` (integer, optional)
- `granularity` (string, optional, default: monthly)

**Response:** `200 OK`
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "granularity": "monthly",
  "data_points": 3,
  "trends": [
    {
      "period": "2025-01",
      "total_hours": 320.5,
      "log_count": 45
    },
    {
      "period": "2025-02",
      "total_hours": 380.0,
      "log_count": 52
    }
  ]
}
```

---

### 7.5 Get Project Progress Trends

**Endpoint:** `GET /analytics/trends/project-progress`
**Authentication:** Bearer Token
**Description:** Get project progress trends over time.

**Query Parameters:**
- `project_id` (integer, required)
- `start_date` (date, optional)
- `end_date` (date, optional)

**Response:** `200 OK`
```json
{
  "project_id": 1,
  "project_name": "Rainforest Reforestation 2025",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "data_points": 12,
  "trends": [
    {
      "date": "2025-01-15",
      "progress_percentage": 10.0,
      "metadata": {"source": "snapshot"}
    },
    {
      "date": "2025-02-01",
      "progress_percentage": 25.0,
      "metadata": {"source": "snapshot"}
    }
  ]
}
```

---

### 7.6 Get Environmental Impact Trends

**Endpoint:** `GET /analytics/trends/environmental-impact`
**Authentication:** Bearer Token
**Description:** Get environmental metrics trends over time.

**Query Parameters:**
- `project_id` (integer, optional)
- `metric_name` (string, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)

**Response:** `200 OK`
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "metrics_count": 2,
  "metrics": [
    {
      "metric_name": "Trees Planted",
      "metric_type": "environmental",
      "unit": "trees",
      "data_points": [
        {
          "date": "2025-01-31",
          "target_value": 1000,
          "current_value": 250,
          "progress_percentage": 25.0,
          "project_id": 1
        },
        {
          "date": "2025-02-28",
          "target_value": 1000,
          "current_value": 580,
          "progress_percentage": 58.0,
          "project_id": 1
        }
      ]
    }
  ]
}
```

---

### 7.7 Create Dashboard

**Endpoint:** `POST /analytics/dashboards`
**Authentication:** Bearer Token
**Description:** Create a custom dashboard configuration.

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "widgets": "object (required)",
  "is_default": "boolean (optional, default: false)"
}
```

**Response:** `200 OK`

---

### 7.8 Get User Dashboards

**Endpoint:** `GET /analytics/dashboards`
**Authentication:** Bearer Token
**Description:** Get all dashboards for current user.

**Response:** `200 OK`
```json
{
  "count": 2,
  "dashboards": [
    {
      "id": 1,
      "name": "My Project Overview",
      "description": "Dashboard for tracking my projects",
      "is_default": true,
      "widgets": {...},
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-03-20T14:15:00Z"
    }
  ]
}
```

---

## 8. Reports & Exports

### 8.1 Get Project Reports

**Endpoint:** `GET /reports/projects`
**Authentication:** Bearer Token

**Query Parameters:**
- `project_id` (integer, optional) - Get specific project report

**Response:** `200 OK`

---

### 8.2 Export Projects to CSV

**Endpoint:** `GET /reports/export/projects/csv`
**Authentication:** Bearer Token
**Description:** Export projects to CSV file.

**Query Parameters:**
- `status` (string, optional)
- `category` (string, optional)

**Response:** `200 OK` (CSV file download)
```
Content-Type: text/csv
Content-Disposition: attachment; filename=projects_export_20250327_143000.csv
```

---

### 8.3 Export Volunteers to CSV

**Endpoint:** `GET /reports/export/volunteers/csv`
**Authentication:** Bearer Token (admin, project_manager, staff_member)
**Description:** Export volunteers to CSV file.

**Query Parameters:**
- `volunteer_status` (string, optional)

**Response:** `200 OK` (CSV file download)

---

### 8.4 Export Tasks to CSV

**Endpoint:** `GET /reports/export/tasks/csv`
**Authentication:** Bearer Token

**Query Parameters:**
- `project_id` (integer, optional)
- `status` (string, optional)

**Response:** `200 OK` (CSV file download)

---

### 8.5 Export Time Logs to CSV

**Endpoint:** `GET /reports/export/time-logs/csv`
**Authentication:** Bearer Token (admin, project_manager, staff_member)

**Query Parameters:**
- `project_id` (integer, optional)
- `volunteer_id` (integer, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `approval_status` (string, optional)

**Response:** `200 OK` (CSV file download)

---

### 8.6 Export Projects to JSON

**Endpoint:** `GET /reports/export/projects/json`
**Authentication:** Bearer Token
**Description:** Export detailed project data to JSON.

**Query Parameters:**
- `project_id` (integer, optional) - Export single project with full details
- `status` (string, optional) - Filter projects (when exporting multiple)

**Response:** `200 OK` (JSON file download)
```
Content-Type: application/json
Content-Disposition: attachment; filename=projects_export_20250327_143000.json
```

---

## 9. Sync (Offline-First)

### 9.1 Register Device

**Endpoint:** `POST /sync/device/register`
**Authentication:** Bearer Token

**Request Body:**
```json
{
  "device_id": "string (required, unique)",
  "device_name": "string (required)",
  "device_type": "string (required: Android|iOS|Desktop|Web)",
  "platform": "string (required: Android|iOS|macOS|Windows|Linux|Web)",
  "device_info": "object (optional)",
  "push_token": "string (optional)"
}
```

**Response:** `200 OK`

---

### 9.2 Pull Changes

**Endpoint:** `POST /sync/pull`
**Authentication:** Bearer Token
**Description:** Pull changes from server since last sync.

**Request Body:**
```json
{
  "device_id": "string (required)",
  "entity_types": "array[string] (optional)",
  "last_sync_timestamps": "object (optional, entity_type -> timestamp)"
}
```

**Response:** `200 OK` (Changed entities)

---

### 9.3 Push Changes

**Endpoint:** `POST /sync/push`
**Authentication:** Bearer Token
**Description:** Push local changes to server.

**Request Body:**
```json
{
  "device_id": "string (required)",
  "changes": "array (required)",
  "client_timestamp": "datetime (required)"
}
```

**Response:** `200 OK` (Sync results with conflicts if any)

---

## 10. Common Schemas

### 10.1 PaginatedResponse

Used for all list endpoints with pagination.

```typescript
{
  data: Array<T>,
  metadata: {
    total: number,
    page: number,
    page_size: number,
    total_pages: number,
    has_next: boolean,
    has_previous: boolean
  }
}
```

---

### 10.2 ErrorResponse

```json
{
  "detail": "string (human-readable error message)"
}
```

Or for validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 11. Error Handling

### Standard HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Validation error or invalid input
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Not authorized to perform action
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Authentication Errors

All protected endpoints return `401` if:
- No token provided
- Token expired
- Token invalid

### Rate Limiting

API uses rate limiting (5 requests per IP within sliding window). If exceeded:
- `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

### Account Lockout

After 5 failed login attempts, account is locked for 30 minutes:
- `403 Forbidden`
```json
{
  "detail": "Account locked due to too many failed login attempts"
}
```

---

## Appendix: Enumerations

### Project Category
- `reforestation`
- `environmental_education`
- `waste_management`
- `conservation`
- `research`
- `community_engagement`
- `climate_action`
- `biodiversity`

### Project Status
- `planning`
- `in_progress`
- `suspended`
- `completed`
- `cancelled`

### Task Status
- `not_started`
- `in_progress`
- `completed`
- `cancelled`

### Priority
- `low`
- `medium`
- `high`
- `critical`

### Resource Type
- `human`
- `equipment`
- `material`
- `financial`

### Volunteer Status
- `active`
- `inactive`
- `suspended`

### Metric Type
- `volunteer_hours`
- `project_progress`
- `task_completion`
- `volunteer_count`
- `resource_utilization`
- `environmental_impact`
- `budget_spent`
- `custom`

---

## Notes

1. **Authentication:** All endpoints except `/auth/register`, `/auth/login`, and `/volunteers/register` require a valid JWT Bearer token in the `Authorization` header: `Authorization: Bearer <token>`

2. **Pagination:** New endpoints use page-based pagination (`page`, `page_size`) with metadata. Legacy endpoints may still use skip/limit.

3. **Date Formats:** All dates use ISO 8601 format (YYYY-MM-DD for dates, YYYY-MM-DDTHH:MM:SSZ for datetimes)

4. **Filtering:** Most list endpoints support filtering via query parameters. Combine multiple filters for refined results.

5. **Exports:** Export endpoints return file downloads. Clients should handle `Content-Disposition` headers appropriately.

6. **Time-Series:** For accurate trend analysis, regularly create metric snapshots using `/analytics/metrics/snapshot`

---

**End of API Specification**
