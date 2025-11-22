# Users API Specification

## Overview

The Users module provides functionality for user management including user profiles, user types, departments, and user activation/deactivation. It supports filtering, searching, and pagination for user listings.

## Permissions

- **List Users**: Admin and staff_member roles only
- **View Own Profile**: All authenticated users (via `/me` endpoint)
- **View Other User Profiles**: Admin, staff_member, or the user themselves
- **Update Users**: Admin, staff_member, or the user themselves
- **Activate/Deactivate Users**: Admin only
- **View User Types**: All authenticated users
- **View Departments**: All authenticated users

## Models

### UserSummary

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "user_type_name": "staff_member",
  "department": "Conservation",
  "is_active": true,
  "profile_picture": "https://example.com/profiles/john.jpg"
}
```

### UserDetail

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "department": "Conservation",
  "employee_id": "EMP001",
  "is_active": true,
  "is_email_verified": true,
  "profile_picture": "https://example.com/profiles/john.jpg",
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": "2025-01-15T09:45:00Z",
  "user_type": {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with extended permissions"
  },
  "oauth_provider": null
}
```

### UserUpdate

```json
{
  "name": "John Smith",
  "phone": "+1234567890",
  "department": "Wildlife Protection",
  "profile_picture": "https://example.com/profiles/new-photo.jpg"
}
```

### UserTypeResponse

```json
{
  "id": 1,
  "name": "admin",
  "description": "Administrator with full system access"
}
```

## Endpoints

### User Management

#### List Users

```
GET /api/v1/users/
```

**Authentication**: Required (Admin or staff_member only)

**Query Parameters:**
- `page` (optional): Page number (1-indexed). Default: 1
- `page_size` (optional): Items per page (1-100). Default: 20
- `search` (optional): Search by name, email, department, or employee ID (case-insensitive)
- `user_type_id` (optional): Filter by user type ID
- `is_active` (optional): Filter by active status (true/false)
- `department` (optional): Filter by department name

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "user_type_name": "staff_member",
      "department": "Conservation",
      "is_active": true,
      "profile_picture": "https://example.com/profiles/john.jpg"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "user_type_name": "volunteer",
      "department": null,
      "is_active": true,
      "profile_picture": null
    }
  ],
  "metadata": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to list users"
}
```

#### Get Current User Profile

```
GET /api/v1/users/me
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "department": "Conservation",
  "employee_id": "EMP001",
  "is_active": true,
  "is_email_verified": true,
  "profile_picture": "https://example.com/profiles/john.jpg",
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": "2025-01-15T09:45:00Z",
  "user_type": {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with extended permissions"
  },
  "oauth_provider": null
}
```

#### Get User by ID

```
GET /api/v1/users/{user_id}
```

**Authentication**: Required (Admin, staff_member, or the user themselves)

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "department": "Conservation",
  "employee_id": "EMP001",
  "is_active": true,
  "is_email_verified": true,
  "profile_picture": "https://example.com/profiles/john.jpg",
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": "2025-01-15T09:45:00Z",
  "user_type": {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with extended permissions"
  },
  "oauth_provider": null
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to view this user"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "User not found"
}
```

#### Update User

```
PUT /api/v1/users/{user_id}
```

**Authentication**: Required (Admin, staff_member, or the user themselves)

**Request Body:**
```json
{
  "name": "John Smith",
  "phone": "+1234567890",
  "department": "Wildlife Protection",
  "profile_picture": "https://example.com/profiles/new-photo.jpg"
}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "department": "Wildlife Protection",
  "employee_id": "EMP001",
  "is_active": true,
  "is_email_verified": true,
  "profile_picture": "https://example.com/profiles/new-photo.jpg",
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "user_type": {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with extended permissions"
  },
  "oauth_provider": null
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to update this user"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "User not found"
}
```

#### Deactivate User

```
POST /api/v1/users/{user_id}/deactivate
```

**Authentication**: Required (Admin only)

**Response: 200 OK**
```json
{
  "message": "User deactivated successfully"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "Cannot deactivate your own account"
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to deactivate users"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "User not found"
}
```

#### Activate User

```
POST /api/v1/users/{user_id}/activate
```

**Authentication**: Required (Admin only)

**Response: 200 OK**
```json
{
  "message": "User activated successfully"
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to activate users"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "User not found"
}
```

### Utility Endpoints

#### Get All User Types

```
GET /api/v1/users/types/all
```

**Authentication**: Required

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Administrator with full system access"
  },
  {
    "id": 2,
    "name": "staff_member",
    "description": "Staff member with extended permissions"
  },
  {
    "id": 3,
    "name": "volunteer",
    "description": "Volunteer user"
  },
  {
    "id": 4,
    "name": "project_manager",
    "description": "Project manager"
  }
]
```

#### Get All Departments

```
GET /api/v1/users/departments/all
```

**Authentication**: Required

**Response: 200 OK**
```json
[
  "Conservation",
  "Wildlife Protection",
  "Education",
  "Research",
  "Administration"
]
```

## Error Responses

All endpoints may return the following error responses:

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**
```json
{
  "detail": "Insufficient permissions"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## Notes

- All timestamps are in UTC ISO 8601 format
- Search is case-insensitive and matches against name, email, department, or employee ID
- Users cannot deactivate their own accounts (safety measure)
- OAuth users may not have a password_hash field
- Profile pictures should be absolute URLs (can be from external services or internal storage)
- Pagination uses 1-indexed page numbers
- Maximum page size is 100 items
