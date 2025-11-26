# Dashboard Specification

Frontend implementation guide for role-based dashboards.

---

## Overview

Each user role has a customized dashboard with relevant widgets, data, and actions. All dashboards share common navigation but show role-specific content.

**Color Palette:**
Current in app
```

---

## Admin Dashboard

**Route:** `/admin` or `/dashboard/admin`

### Sidebar Navigation

```
Dashboard (home)
├── Users
│   ├── All Users
│   └── User Types
├── Projects
│   ├── All Projects
│   └── Project Stats
├── Tasks
├── Volunteers
│   ├── All Volunteers
│   └── Skills
├── Time Logs
├── Blog
│   ├── Posts
│   ├── Categories
│   └── Tags
├── Newsletter
│   ├── Contacts
│   ├── Subscribers
│   ├── Tags
│   ├── Templates
│   └── Campaigns
├── Gamification
│   ├── Badges
│   ├── Achievements
│   └── Leaderboards
├── Files
├── Analytics
└── Settings
```

### Dashboard Widgets

#### Row 1: Quick Stats (4 cards)
| Widget | Data Source | Display |
|--------|-------------|---------|
| Total Users | `GET /users?limit=1` → total_count | Number + trend |
| Active Projects | `GET /projects/stats` | Number |
| Pending Time Logs | `GET /volunteers/time-logs?status=pending&limit=1` → total | Number (warning if >10) |
| New Contacts | `GET /contact/submissions?unread_only=true&limit=1` → total | Number (badge if >0) |

#### Row 2: Activity Overview
| Widget | Data Source | Display |
|--------|-------------|---------|
| Recent Activity | `GET /notifications?limit=10` | Activity feed list |
| System Health | `GET /health` | Status indicator |

#### Row 3: Charts
| Widget | Data Source | Display |
|--------|-------------|---------|
| Projects by Status | `GET /projects/stats` | Pie chart |
| Volunteer Hours (30 days) | `GET /analytics/time-series?metric=volunteer_hours&period=day&days=30` | Line chart |
| New Signups (30 days) | `GET /analytics/time-series?metric=new_users&period=day&days=30` | Bar chart |

#### Row 4: Tables
| Widget | Data Source | Display |
|--------|-------------|---------|
| Recent Users | `GET /users?limit=5&sort=-created_at` | Table: name, email, type, joined |
| Pending Approvals | `GET /volunteers/time-logs?status=pending&limit=5` | Table: volunteer, task, hours, date |

### Quick Actions
- Create User
- Create Project
- Send Newsletter Campaign
- View All Notifications

---

## Project Manager Dashboard

**Route:** `/dashboard/pm`

### Sidebar Navigation

```
Dashboard (home)
├── My Projects
├── Tasks
│   ├── All Tasks
│   └── Task Board
├── Team
├── Time Logs
│   ├── Pending Approval
│   └── Approved
├── Reports
└── Profile
```

### Dashboard Widgets

#### Row 1: Quick Stats (4 cards)
| Widget | Data Source | Display |
|--------|-------------|---------|
| My Projects | `GET /projects?manager_id={user_id}&limit=1` → total | Number |
| Active Tasks | `GET /tasks?status=in_progress&limit=1` → total | Number |
| Team Members | Count from projects team endpoints | Number |
| Hours This Month | `GET /analytics/dashboards/pm` | Number |

#### Row 2: Project Overview
| Widget | Data Source | Display |
|--------|-------------|---------|
| My Projects List | `GET /projects?manager_id={user_id}&limit=5` | Cards: name, progress, team count, status |

#### Row 3: Task Board (Kanban)
| Widget | Data Source | Display |
|--------|-------------|---------|
| Task Board | `GET /tasks?project_id={selected}` | Kanban: To Do, In Progress, Done |

**Columns:** Draggable cards with: title, assignee avatar, priority badge, due date

#### Row 4: Tables
| Widget | Data Source | Display |
|--------|-------------|---------|
| Pending Time Approvals | `GET /volunteers/time-logs?project_id={any_owned}&status=pending` | Table: volunteer, task, hours, actions (approve/reject) |
| Upcoming Milestones | `GET /projects/{id}/milestones?upcoming=true` | Table: milestone, project, due date |

### Quick Actions
- Create Project
- Create Task
- Invite Team Member
- Approve Time Logs

---

## Staff Member Dashboard

**Route:** `/dashboard/staff`

### Sidebar Navigation

```
Dashboard (home)
├── Volunteers
│   ├── All Volunteers
│   └── Skills
├── Time Logs
│   ├── Pending
│   └── All Logs
├── Tasks
├── Contacts
├── Gamification
│   ├── Award Badge
│   └── Award Points
└── Profile
```

### Dashboard Widgets

#### Row 1: Quick Stats (4 cards)
| Widget | Data Source | Display |
|--------|-------------|---------|
| Active Volunteers | `GET /volunteers?status=active&limit=1` → total | Number |
| Pending Time Logs | `GET /volunteers/time-logs?status=pending&limit=1` → total | Number (warning color) |
| Unread Contacts | `GET /contact/submissions?unread_only=true&limit=1` → total | Number (badge) |
| Badges Awarded Today | Custom query or analytics | Number |

#### Row 2: Action Queues
| Widget | Data Source | Display |
|--------|-------------|---------|
| Time Logs to Approve | `GET /volunteers/time-logs?status=pending&limit=10` | Table with approve/reject buttons |
| Recent Contact Submissions | `GET /contact/submissions?limit=5` | List: name, preview, timestamp, read status |

#### Row 3: Volunteer Activity
| Widget | Data Source | Display |
|--------|-------------|---------|
| Top Volunteers (This Month) | `GET /gamification/leaderboards/points?period=month&limit=5` | Leaderboard: rank, name, points, hours |
| Recent Volunteer Signups | `GET /volunteers?limit=5&sort=-created_at` | List: name, skills, joined |

### Quick Actions
- Approve All Time Logs
- Add Volunteer
- Award Badge
- Award Points

---

## Volunteer Dashboard

**Route:** `/dashboard/volunteer`

### Sidebar Navigation

```
Dashboard (home)
├── My Tasks
├── My Hours
├── Available Tasks
├── My Achievements
│   ├── Badges
│   └── Points
├── Leaderboards
└── Profile
```

### Dashboard Widgets

#### Row 1: Personal Stats (4 cards)
| Widget | Data Source | Display |
|--------|-------------|---------|
| My Points | `GET /gamification/points/summary` | Number + rank |
| Hours This Month | `GET /volunteers/time-logs?volunteer_id={id}&month=current` → sum | Number |
| Badges Earned | `GET /gamification/volunteers/{id}/badges` → count | Number |
| Tasks Assigned | `GET /tasks?volunteer_id={id}&status=in_progress&limit=1` → total | Number |

#### Row 2: My Tasks
| Widget | Data Source | Display |
|--------|-------------|---------|
| Current Tasks | `GET /tasks?volunteer_id={id}&status=in_progress` | Cards: title, project, due date, status button |

#### Row 3: Progress & Achievements
| Widget | Data Source | Display |
|--------|-------------|---------|
| Recent Badges | `GET /gamification/volunteers/{id}/badges?limit=4` | Badge icons with names |
| Hours Chart (6 months) | `GET /analytics/time-series?metric=my_hours&period=month&months=6` | Bar chart |

#### Row 4: Opportunities
| Widget | Data Source | Display |
|--------|-------------|---------|
| Available Tasks | `GET /tasks/volunteers/available?limit=5` | List: title, project, skills needed, apply button |
| Upcoming Achievements | `GET /gamification/achievements?in_progress=true` | Progress bars: achievement name, current/target |

### Quick Actions
- Log Hours
- View All Tasks
- Browse Opportunities
- View Leaderboard

---

## Common Components

### Header
- Logo
- Search bar (full-text search)
- Notifications bell (with count badge)
- User avatar dropdown (Profile, Settings, Logout)

### Notification Panel
**Data Source:** `GET /notifications?limit=20`
- Real-time updates via `GET /notifications/stream` (SSE)
- Mark as read: `PUT /notifications/{id}/read`
- Click to navigate to related item

### User Profile Dropdown
- View Profile
- Settings
- Logout (`POST /auth/logout`)

---

## Data Refresh Strategy

| Type | Refresh Method |
|------|----------------|
| Stats Cards | Refresh every 60 seconds or on action |
| Tables | Refresh on action, paginate on demand |
| Charts | Refresh every 5 minutes |
| Notifications | Real-time via SSE |
| Task Board | Refresh on drag-drop action |

---

## Mobile Responsive Notes

- Sidebar collapses to hamburger menu
- Stats cards stack 2x2 on tablet, 1 column on mobile
- Tables become cards on mobile
- Kanban scrolls horizontally on mobile
- Keep quick actions in floating action button (FAB)

---

## API Endpoints Summary

### Stats & Dashboards
```
GET /projects/stats
GET /projects/dashboard
GET /analytics/dashboards/{role}
GET /analytics/time-series?metric=X&period=Y
```

### Lists (all support pagination)
```
GET /users?skip=0&limit=20
GET /projects?skip=0&limit=20
GET /tasks?skip=0&limit=20
GET /volunteers?skip=0&limit=20
GET /volunteers/time-logs?skip=0&limit=20
GET /notifications?skip=0&limit=20
```

### Actions
```
POST /volunteers/time-logs/{id}/approve
POST /volunteers/time-logs/{id}/reject
PUT /notifications/{id}/read
POST /tasks/{id}/volunteers
POST /gamification/points/award
POST /gamification/badges/{id}/award
```

---

## Implementation Notes

1. Use role from JWT token (`user_type` claim) to determine dashboard view
2. Redirect unauthorized users to their correct dashboard
3. Cache stats locally, refresh in background
4. Show loading skeletons during data fetch
5. Handle empty states gracefully with helpful messages
6. Use optimistic updates for better UX (approve buttons, mark as read)
