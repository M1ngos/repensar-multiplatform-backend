# User Roles & Permissions

Reference guide for what each user type can access and perform.

---

## User Types Overview

| Role | Description |
|------|-------------|
| **Admin** | Full system access, user management, all modules |
| **Project Manager** | Manage projects, tasks, team assignments |
| **Staff Member** | Operational tasks, volunteer management, time approval |
| **Volunteer** | Own profile, assigned tasks, time logging |

---

## Permission Matrix

Legend: **C**=Create, **R**=Read, **U**=Update, **D**=Delete, **A**=Approve

### Authentication & Users

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Register/Login | Yes | Yes | Yes | Yes |
| View own profile | Yes | Yes | Yes | Yes |
| Edit own profile | Yes | Yes | Yes | Yes |
| List all users | Yes | No | No | No |
| View any user | Yes | Limited | Limited | No |
| Edit any user | Yes | No | No | No |
| Activate/deactivate users | Yes | No | No | No |

### Projects

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Create project | Yes | Yes | No | No |
| List all projects | Yes | Yes | Yes | Assigned |
| View project details | Yes | Yes | Yes | Assigned |
| Edit project | Yes | Own | No | No |
| Delete project | Yes | No | No | No |
| Manage team members | Yes | Own | No | No |
| Create milestones | Yes | Own | No | No |
| View project stats | Yes | Yes | Yes | No |

### Tasks

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Create task | Yes | Own projects | Assigned projects | No |
| List tasks | Yes | Yes | Yes | Assigned |
| View task details | Yes | Yes | Yes | Assigned |
| Edit task | Yes | Own projects | Assigned projects | No |
| Delete task | Yes | Own projects | No | No |
| Assign volunteers | Yes | Own projects | Assigned projects | No |
| Update task status | Yes | Yes | Yes | Assigned |
| Manage dependencies | Yes | Own projects | No | No |

### Volunteers

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Register as volunteer | Yes | Yes | Yes | Yes |
| View own volunteer profile | Yes | Yes | Yes | Yes |
| Edit own volunteer profile | Yes | Yes | Yes | Yes |
| List all volunteers | Yes | Yes | Yes | No |
| View any volunteer | Yes | Yes | Yes | No |
| Edit any volunteer | Yes | No | Yes | No |
| Manage skills | Yes | No | Yes | No |

### Time Logs

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Create time log | Yes | Yes | Yes | Yes |
| View own time logs | Yes | Yes | Yes | Yes |
| View all time logs | Yes | Own projects | Yes | No |
| Edit time log (before approval) | Yes | Own | Own | Own |
| Approve time logs | Yes | Own projects | Yes | No |
| Delete time logs | Yes | No | Yes | No |

### Blog

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Create post | Yes | No | No | No |
| View published posts | Yes | Yes | Yes | Yes |
| View draft posts | Yes | No | No | No |
| Edit posts | Yes | No | No | No |
| Delete posts | Yes | No | No | No |
| Manage categories | Yes | No | No | No |
| Manage tags | Yes | No | No | No |

### Newsletter & Contact

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Submit contact form | Public | Public | Public | Public |
| View contact submissions | Yes | No | Yes | No |
| Subscribe to newsletter | Public | Public | Public | Public |
| Manage subscribers | Yes | No | No | No |
| Manage tags | Yes | No | No | No |
| Create/manage templates | Yes | No | No | No |
| Create/send campaigns | Yes | No | No | No |

### Gamification

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| View badges | Yes | Yes | Yes | Yes |
| Create badges | Yes | No | No | No |
| Award badges | Yes | No | Yes | No |
| View own achievements | Yes | Yes | Yes | Yes |
| View leaderboards | Yes | Yes | Yes | Yes |
| Award points | Yes | No | Yes | No |
| View own points | Yes | Yes | Yes | Yes |

### Files

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Upload files | Yes | Yes | Yes | Yes |
| View file list | Yes | Yes | Yes | Assigned |
| Download files | Yes | Yes | Yes | Assigned |
| Delete files | Yes | Own | Own | Own |

### Notifications

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| View own notifications | Yes | Yes | Yes | Yes |
| Mark as read | Yes | Yes | Yes | Yes |
| Delete own notifications | Yes | Yes | Yes | Yes |
| SSE stream | Yes | Yes | Yes | Yes |

### Search & Analytics

| Action | Admin | PM | Staff | Volunteer |
|--------|:-----:|:--:|:-----:|:---------:|
| Full-text search | Yes | Yes | Yes | Limited |
| Advanced search | Yes | Yes | Yes | No |
| View analytics | Yes | Yes | Yes | No |
| View dashboards | Yes | Yes | Yes | Limited |

---

## Role Details

### Admin
Full access to all system functionality:
- User management (create, edit, deactivate)
- All CRUD operations on all modules
- System configuration
- Analytics and reporting
- Newsletter campaigns

### Project Manager
Manages projects they create or are assigned to:
- Create and manage own projects
- Assign team members to projects
- Create and assign tasks within projects
- Approve time logs for their projects
- View project analytics

**Cannot:**
- Manage users or other PMs' projects
- Access admin-only modules (blog management, newsletter campaigns)
- Delete projects

### Staff Member
Operational support for volunteer management:
- View and manage volunteers
- Approve time logs
- Manage skills
- Award badges and points
- View contact submissions

**Cannot:**
- Create projects
- Manage users
- Access admin-only modules

### Volunteer
Self-service access to assigned work:
- Manage own profile
- View and update assigned tasks
- Log time on tasks
- View own achievements and points
- Download files from assigned projects

**Cannot:**
- View other volunteers' data
- Create or manage projects/tasks
- Access admin modules

---

## API Enforcement

All permissions are enforced at the API level using dependency injection:

```python
# Admin only
Depends(require_role([UserType.ADMIN]))

# Admin or PM
Depends(require_role([UserType.ADMIN, UserType.PROJECT_MANAGER]))

# Admin, PM, or Staff
Depends(require_role([UserType.ADMIN, UserType.PROJECT_MANAGER, UserType.STAFF_MEMBER]))

# Any authenticated user
Depends(get_current_active_user)
```

Resource ownership is checked within endpoint handlers for actions like "edit own project" or "approve own project's time logs".
