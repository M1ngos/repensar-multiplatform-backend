# Repensar Multiplatform Backend - API Specification

## Base Information

**Base URL**: `http://localhost:8000` (Development)
**Framework**: FastAPI
**Authentication**: JWT Bearer Token
**Documentation**: `/docs` (Swagger UI) or `/redoc`
**OpenAPI Spec**: `/openapi.json`

## Authentication

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

### Token Lifecycle
- **Access Token**: 30 minutes expiry
- **Refresh Token**: 30 days expiry
- Token rotation enabled for security

## User Roles

- `admin` - Full system access
- `project_manager` - Manage projects, tasks, volunteers
- `staff_member` - Staff operations
- `volunteer` - Limited volunteer access

---

## 1. Authentication Module

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login with email/password | No |
| POST | `/auth/refresh` | Refresh access token | No (refresh token) |
| POST | `/auth/logout` | Logout current device | Yes |
| POST | `/auth/logout-all-devices` | Logout all devices | Yes |
| GET | `/auth/me` | Get current user profile | Yes |
| POST | `/auth/change-password` | Change password | Yes |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password with token | No |
| POST | `/auth/verify-email` | Verify email with token | No |
| POST | `/auth/resend-verification` | Resend verification email | No |
| GET | `/auth/permissions` | Get user permissions | Yes |
| GET | `/auth/validate-token` | Validate JWT token | Yes |
| GET | `/auth/audit-log` | Get user audit log | Yes |
| GET | `/auth/google/login` | Get Google OAuth URL | No |
| POST | `/auth/google/callback` | Handle Google OAuth callback | No |

### Key Request/Response Examples

**Register**:
```json
POST /auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone": "+1234567890",
  "department": "Operations"
}
```

**Login**:
```json
POST /auth/login
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

---

## 2. User Management

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users/` | List all users (paginated) | Yes |
| GET | `/users/me` | Get current user | Yes |
| GET | `/users/{user_id}` | Get user by ID | Yes |
| PUT | `/users/{user_id}` | Update user | Yes |
| POST | `/users/{user_id}/activate` | Activate user | Yes (admin) |
| POST | `/users/{user_id}/deactivate` | Deactivate user | Yes (admin) |
| GET | `/users/types/all` | Get all user types | Yes |
| GET | `/users/departments/all` | Get departments | Yes |

### Query Parameters (GET /users/)

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)
- `search` - Search by name, email, department, employee_id
- `user_type_id` - Filter by user type
- `is_active` - Filter by active status (true/false)
- `department` - Filter by department

---

## 3. Volunteers Module

### Endpoints

#### Profile Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/volunteers/register` | Register new volunteer with user account |
| GET | `/volunteers/` | List volunteers (with filters) |
| GET | `/volunteers/stats` | Get volunteer statistics dashboard |
| GET | `/volunteers/{volunteer_id}` | Get volunteer profile |
| PUT | `/volunteers/{volunteer_id}` | Update volunteer profile |
| DELETE | `/volunteers/{volunteer_id}` | Deactivate volunteer |

#### Skills Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/volunteers/skills/available` | List available skills |
| GET | `/volunteers/{volunteer_id}/skills` | Get volunteer's skills |
| POST | `/volunteers/{volunteer_id}/skills` | Assign skill to volunteer |
| PUT | `/volunteers/{volunteer_id}/skills/{skill_id}` | Update skill assignment |
| DELETE | `/volunteers/{volunteer_id}/skills/{skill_id}` | Remove skill |

#### Time Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/volunteers/{volunteer_id}/hours` | Get volunteer time logs |
| POST | `/volunteers/{volunteer_id}/hours` | Log volunteer hours |
| PUT | `/volunteers/hours/{time_log_id}` | Update time log |
| POST | `/volunteers/hours/{time_log_id}/approve` | Approve/reject time log |
| DELETE | `/volunteers/hours/{time_log_id}` | Delete time log |
| GET | `/volunteers/{volunteer_id}/hours/summary` | Get hours summary |

#### Relations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/volunteers/{volunteer_id}/projects` | Get volunteer's projects |
| GET | `/volunteers/{volunteer_id}/tasks` | Get volunteer's tasks |
| GET | `/volunteers/{volunteer_id}/activity` | Get volunteer activity log |

### Key Examples

**Register Volunteer**:
```json
POST /volunteers/register
{
  "user": {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "phone": "+1234567890"
  },
  "volunteer": {
    "date_of_birth": "1990-01-15",
    "gender": "female",
    "address": "123 Main St",
    "city": "Springfield",
    "emergency_contact_name": "John Smith",
    "emergency_contact_phone": "+1234567891"
  }
}
```

**Log Hours**:
```json
POST /volunteers/{volunteer_id}/hours
{
  "task_id": 123,
  "hours_worked": 4.5,
  "date": "2025-01-15",
  "description": "Planted trees in community park"
}
```

---

## 4. Projects Module

### Endpoints

#### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/` | Create new project |
| GET | `/projects/` | List projects (with filters) |
| GET | `/projects/dashboard` | Get projects dashboard data |
| GET | `/projects/stats` | Get project statistics |
| GET | `/projects/{project_id}` | Get detailed project info |
| PUT | `/projects/{project_id}` | Update project |
| DELETE | `/projects/{project_id}` | Delete project (mark as cancelled) |

#### Team Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{project_id}/team` | Get project team members |
| POST | `/projects/{project_id}/team` | Add team member |
| PUT | `/projects/{project_id}/team/{user_id}` | Update team member role |
| DELETE | `/projects/{project_id}/team/{user_id}` | Remove team member |

#### Milestones

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{project_id}/milestones` | Get milestones |
| POST | `/projects/{project_id}/milestones` | Create milestone |
| PUT | `/projects/milestones/{milestone_id}` | Update milestone |
| DELETE | `/projects/milestones/{milestone_id}` | Delete milestone |

#### Environmental Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{project_id}/metrics` | Get environmental metrics |
| POST | `/projects/{project_id}/metrics` | Create metric |
| PUT | `/projects/metrics/{metric_id}` | Update metric |
| DELETE | `/projects/metrics/{metric_id}` | Delete metric |

#### Relations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{project_id}/tasks` | Get project tasks |
| GET | `/projects/{project_id}/volunteers` | Get project volunteers |
| GET | `/projects/{project_id}/resources` | Get project resources |
| GET | `/projects/{project_id}/activity` | Get project activity log |

### Query Parameters (GET /projects/)

- `status` - Filter by status: `planning`, `in_progress`, `suspended`, `completed`, `cancelled`
- `category` - Filter by category
- `manager_id` - Filter by project manager
- `requires_volunteers` - Filter projects needing volunteers (true/false)
- `search` - Full-text search

### Key Examples

**Create Project**:
```json
POST /projects/
{
  "name": "Community Reforestation Initiative",
  "description": "Plant 1000 trees in urban areas",
  "category": "environmental",
  "status": "planning",
  "priority": "high",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "budget": 50000.00,
  "manager_id": 5,
  "location_name": "Central Park",
  "latitude": 40.785091,
  "longitude": -73.968285
}
```

---

## 5. Tasks Module

### Endpoints

#### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks/` | Create new task |
| GET | `/tasks/` | List tasks (with filters) |
| GET | `/tasks/stats` | Get task statistics |
| GET | `/tasks/volunteers/available` | Get tasks available for volunteers |
| GET | `/tasks/{task_id}` | Get detailed task information |
| PUT | `/tasks/{task_id}` | Update task |
| DELETE | `/tasks/{task_id}` | Delete task (mark as cancelled) |

#### Volunteer Assignments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{task_id}/volunteers` | Get volunteers assigned to task |
| POST | `/tasks/{task_id}/volunteers` | Assign volunteer to task |
| PUT | `/tasks/{task_id}/volunteers/{volunteer_id}` | Update volunteer assignment |
| DELETE | `/tasks/{task_id}/volunteers/{volunteer_id}` | Remove volunteer from task |
| GET | `/tasks/volunteers/{volunteer_id}/assignments` | Get volunteer's task assignments |

#### Dependencies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{task_id}/dependencies` | Get task dependencies |
| POST | `/tasks/{task_id}/dependencies` | Create task dependency |
| DELETE | `/tasks/dependencies/{dependency_id}` | Delete dependency |

### Query Parameters (GET /tasks/)

- `project_id` - Filter by project
- `status` - Filter by status: `not_started`, `in_progress`, `completed`, `cancelled`
- `priority` - Filter by priority: `low`, `medium`, `high`, `critical`
- `assigned_to_id` - Filter by assignee
- `suitable_for_volunteers` - Filter volunteer-suitable tasks (true/false)
- `search` - Full-text search

### Key Examples

**Create Task**:
```json
POST /tasks/
{
  "title": "Plant saplings in sector A",
  "description": "Plant 50 tree saplings in designated area",
  "project_id": 10,
  "status": "not_started",
  "priority": "high",
  "assigned_to_id": 15,
  "suitable_for_volunteers": true,
  "volunteer_spots": 10,
  "estimated_hours": 8.0,
  "start_date": "2025-02-15",
  "due_date": "2025-02-15"
}
```

---

## 6. Resources Module

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resources/` | Create new resource |
| GET | `/resources/` | List resources |
| GET | `/resources/stats` | Get resource statistics |
| GET | `/resources/{resource_id}` | Get resource by ID |
| GET | `/resources/projects/{project_id}/resources` | Get project resources |
| POST | `/resources/projects/{project_id}/resources` | Allocate resource to project |

### Query Parameters

- `resource_type` - Filter by resource type

---

## 7. Notifications Module

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/stream` | SSE endpoint for real-time notifications |
| GET | `/notifications` | List notifications (paginated) |
| GET | `/notifications/unread-count` | Get unread count |
| GET | `/notifications/{notification_id}` | Get specific notification |
| PATCH | `/notifications/{notification_id}/read` | Mark as read |
| POST | `/notifications/mark-all-read` | Mark all as read |
| DELETE | `/notifications/{notification_id}` | Delete notification |
| POST | `/notifications/create` | Create notification (admin/system) |

### Real-time with Server-Sent Events (SSE)

**Connection**:
```javascript
const eventSource = new EventSource('/notifications/stream', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

eventSource.addEventListener('notification', (event) => {
  const notification = JSON.parse(event.data);
  // Handle notification
});

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to notification stream');
});
```

### Notification Types

- `info` - Informational
- `success` - Success message
- `warning` - Warning
- `error` - Error message

---

## 8. Files Module

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/files/upload` | Upload file (image or document) |
| GET | `/files` | List uploaded files |
| GET | `/files/{file_id}` | Get file by ID |
| DELETE | `/files/{file_id}` | Delete file |

### Query Parameters (GET /files)

- `category` - Filter by category: `profile`, `project`, `task`, `resource`, `document`, `other`
- `project_id` - Filter by project
- `task_id` - Filter by task

### Supported File Types

- **Images**: JPEG, PNG, GIF, WEBP
- **Documents**: PDF, DOC, DOCX
- **Max Size**: 10MB

### Key Examples

**Upload File**:
```javascript
POST /files/upload
Content-Type: multipart/form-data

{
  file: <binary>,
  category: "project",
  project_id: 10,
  description: "Project blueprint"
}

Response:
{
  "id": 123,
  "filename": "blueprint.pdf",
  "file_path": "/uploads/files/...",
  "thumbnail_path": null,
  "category": "project",
  "project_id": 10,
  "uploaded_by_id": 5,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

## 9. Sync Module (Offline-First)

### Endpoints

#### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/device/register` | Register/update device |
| GET | `/sync/device/list` | List user's devices |
| POST | `/sync/device/{device_id}/revoke` | Revoke device |

#### Sync Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/pull` | Pull changes from server (incremental) |
| POST | `/sync/push` | Push local changes to server |
| GET | `/sync/status` | Get sync status for device |

#### Conflict Resolution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sync/conflicts` | Get sync conflicts |
| POST | `/sync/conflicts/{conflict_id}/resolve` | Resolve conflict |

### Supported Entities for Sync

- Volunteers, Projects, Tasks, Resources
- Volunteer skills, time logs, training records
- Project teams, milestones, environmental metrics
- Task dependencies

### Key Examples

**Register Device**:
```json
POST /sync/device/register
{
  "device_id": "unique-device-uuid",
  "platform": "android",
  "os_version": "14.0",
  "app_version": "1.2.0"
}
```

**Pull Changes** (Incremental Sync):
```json
POST /sync/pull
{
  "device_id": "unique-device-uuid",
  "entity_types": ["projects", "tasks", "volunteers"],
  "last_sync_timestamp": "2025-01-14T12:00:00Z"
}

Response:
{
  "changes": {
    "projects": {
      "created": [...],
      "updated": [...],
      "deleted": [...]
    },
    "tasks": { ... },
    "volunteers": { ... }
  },
  "server_timestamp": "2025-01-15T12:00:00Z"
}
```

**Push Changes**:
```json
POST /sync/push
{
  "device_id": "unique-device-uuid",
  "changes": {
    "projects": {
      "created": [...],
      "updated": [...],
      "deleted": [...]
    }
  },
  "client_timestamp": "2025-01-15T11:30:00Z"
}

Response:
{
  "conflicts": [
    {
      "entity_type": "projects",
      "entity_id": 10,
      "conflict_id": "uuid",
      "client_version": 5,
      "server_version": 6,
      "client_data": { ... },
      "server_data": { ... }
    }
  ],
  "successful_updates": [...],
  "failed_updates": [...]
}
```

---

## 10. Analytics Module

### Endpoints

#### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analytics/metrics/snapshot` | Create metric snapshot |
| GET | `/analytics/metrics/time-series` | Get time-series metrics |

#### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/dashboard` | Get analytics dashboard |
| POST | `/analytics/dashboards` | Create custom dashboard |
| GET | `/analytics/dashboards` | Get user dashboards |

#### Trends

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/trends/volunteer-hours` | Volunteer hours trends |
| GET | `/analytics/trends/project-progress` | Project progress trends |
| GET | `/analytics/trends/environmental-impact` | Environmental impact trends |

### Query Parameters

- `start_date` - Start date for date range
- `end_date` - End date for date range
- `project_id` - Filter by project
- `volunteer_id` - Filter by volunteer
- `granularity` - Time granularity: `hourly`, `daily`, `weekly`, `monthly`

---

## 11. Search Module

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search` | Search across all entities |
| GET | `/search/projects` | Search projects only |
| GET | `/search/tasks` | Search tasks only |
| GET | `/search/volunteers` | Search volunteers only |

### Query Parameters

- `q` - Search query (minimum 2 characters)
- `limit` - Results limit (default 20, max 100)

### Example

```
GET /search?q=reforestation&limit=10

Response:
{
  "projects": [...],
  "tasks": [...],
  "volunteers": [...]
}
```

---

## 12. Reports Module

### Endpoints

#### Report Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/projects` | Get project reports |
| GET | `/reports/volunteers` | Get volunteer reports |
| GET | `/reports/tasks` | Get task reports |
| GET | `/reports/resources` | Get resource reports |
| GET | `/reports/dashboard` | Get dashboard summary |

#### Data Export (CSV)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/export/projects/csv` | Export projects to CSV |
| GET | `/reports/export/volunteers/csv` | Export volunteers to CSV |
| GET | `/reports/export/tasks/csv` | Export tasks to CSV |
| GET | `/reports/export/time-logs/csv` | Export time logs to CSV |

#### Data Export (JSON)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/export/projects/json` | Export projects to JSON |

---

## Common Response Patterns

### Paginated Response

```json
{
  "data": [...],
  "metadata": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests (Rate Limit)
- `500` - Internal Server Error

### Success Response

```json
{
  "message": "Operation successful",
  "id": 123
}
```

---

## Key Data Models

### User

```typescript
interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  department?: string;
  employee_id?: string;
  profile_picture?: string;
  user_type_id: number;
  user_type?: UserType;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### UserType

```typescript
interface UserType {
  id: number;
  name: "admin" | "project_manager" | "staff_member" | "volunteer";
  description?: string;
  permissions: Record<string, any>;
  dashboard_config?: Record<string, any>;
}
```

### Volunteer

```typescript
interface Volunteer {
  id: number;
  volunteer_id: string;
  user_id: number;
  user?: User;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  city?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  volunteer_status: "active" | "inactive" | "on_leave";
  background_check_status?: "pending" | "cleared" | "failed";
  total_hours_contributed: number;
  rating?: number;
  created_at: string;
  updated_at: string;
}
```

### Project

```typescript
interface Project {
  id: number;
  name: string;
  description?: string;
  category?: string;
  status: "planning" | "in_progress" | "suspended" | "completed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  start_date?: string;
  end_date?: string;
  budget?: number;
  actual_cost?: number;
  manager_id: number;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
  updated_at: string;
}
```

### Task

```typescript
interface Task {
  id: number;
  title: string;
  description?: string;
  project_id: number;
  status: "not_started" | "in_progress" | "completed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  assigned_to_id?: number;
  suitable_for_volunteers: boolean;
  volunteer_spots?: number;
  progress_percentage: number;
  estimated_hours?: number;
  actual_hours?: number;
  start_date?: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
}
```

### Notification

```typescript
interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  is_read: boolean;
  read_at?: string;
  project_id?: number;
  task_id?: number;
  created_at: string;
}
```

---

## Frontend Implementation Checklist

### Core Features

- [ ] Authentication flow (register, login, logout, refresh)
- [ ] Protected routes with JWT token management
- [ ] User profile management
- [ ] Role-based access control (RBAC)

### Volunteers Management

- [ ] Volunteer registration and profile
- [ ] Skills management
- [ ] Time tracking and approval
- [ ] Volunteer dashboard with stats

### Projects & Tasks

- [ ] Project listing, creation, and management
- [ ] Task management with dependencies
- [ ] Team management
- [ ] Milestone tracking
- [ ] Environmental metrics

### Real-time Features

- [ ] SSE connection for notifications
- [ ] Real-time notification display
- [ ] Notification badge with unread count

### Offline Capabilities

- [ ] Device registration
- [ ] Incremental sync (pull/push)
- [ ] Conflict resolution UI
- [ ] Offline data storage

### Files & Media

- [ ] File upload with drag-and-drop
- [ ] Image preview and thumbnails
- [ ] Document viewer
- [ ] File categorization

### Analytics & Reports

- [ ] Dashboard with metrics
- [ ] Charts and trends
- [ ] Report generation
- [ ] CSV/JSON export

### Search

- [ ] Global search across entities
- [ ] Entity-specific search
- [ ] Search filters

---

## Configuration

### Environment Variables for Frontend

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_SSE=true
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

### CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React/Next.js default)
- Configure additional origins in backend's `FRONTEND_URL` environment variable

---

## Additional Resources

- **OpenAPI Specification**: Available at `/openapi.json`
- **Interactive API Docs**: `/docs` (Swagger UI)
- **Alternative Docs**: `/redoc` (ReDoc)

---

## Support & Development

For backend implementation details, refer to:
- `/app/routers/` - API route implementations
- `/app/models/` - Database models
- `/app/schemas/` - Request/Response schemas
- `/app/core/` - Core configuration and utilities
