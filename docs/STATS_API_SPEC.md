# Stats and Analytics API Specification

## Overview

The Stats and Analytics module provides comprehensive data analysis, reporting, and visualization capabilities for the platform. It includes time-series metrics tracking, trend analysis, dashboard management, and data export functionality.

## Permissions

- **View Basic Stats**: All authenticated users
- **View Detailed Analytics**: Staff members, project managers, and admins
- **Create Metric Snapshots**: Staff members, project managers, and admins
- **Export Data**: Staff members, project managers, and admins
- **Manage Dashboards**: All authenticated users (own dashboards only)

## Models

### MetricSnapshot

```json
{
  "id": 1,
  "metric_type": "volunteer_hours",
  "metric_name": "Total Volunteer Hours",
  "value": 125.5,
  "unit": "hours",
  "project_id": 5,
  "task_id": null,
  "volunteer_id": 12,
  "metric_metadata": {
    "category": "community_service",
    "location": "urban"
  },
  "recorded_by_id": 3,
  "snapshot_date": "2025-01-15T14:30:00Z",
  "created_at": "2025-01-15T14:30:00Z"
}
```

### Dashboard

```json
{
  "id": 1,
  "user_id": 5,
  "name": "My Project Dashboard",
  "description": "Custom dashboard for tracking my projects",
  "is_default": true,
  "widgets": {
    "layout": [
      {"id": "widget1", "type": "project_stats", "position": {"x": 0, "y": 0}},
      {"id": "widget2", "type": "volunteer_hours", "position": {"x": 1, "y": 0}}
    ]
  },
  "filters": {
    "date_range": "30_days",
    "project_ids": [1, 2, 3]
  },
  "is_public": false,
  "shared_with_users": null,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### MetricType Enum

- `volunteer_hours`: Volunteer hours logged
- `project_progress`: Project completion percentage
- `task_completion`: Task completion metrics
- `volunteer_count`: Number of volunteers
- `resource_utilization`: Resource usage metrics
- `environmental_impact`: Environmental impact measurements
- `budget_spent`: Budget expenditure
- `custom`: Custom metric type

## Endpoints

### Analytics

#### Create Metric Snapshot

```
POST /api/v1/analytics/metrics/snapshot
```

**Authentication**: Required (Staff member, project manager, or admin)

**Request Body:**
```json
{
  "metric_type": "volunteer_hours",
  "metric_name": "Weekly Volunteer Hours",
  "value": 45.5,
  "unit": "hours",
  "project_id": 3,
  "task_id": null,
  "volunteer_id": 8,
  "metric_metadata": {
    "week": 3,
    "month": "January"
  },
  "snapshot_date": "2025-01-15T12:00:00Z"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Metric snapshot created successfully",
  "snapshot_id": 42
}
```

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to create metric snapshots"
}
```

#### Get Time-Series Metrics

```
GET /api/v1/analytics/metrics/time-series
```

**Query Parameters:**
- `metric_type` (required): Type of metric (from MetricType enum)
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `project_id` (optional): Filter by project ID
- `task_id` (optional): Filter by task ID
- `volunteer_id` (optional): Filter by volunteer ID
- `granularity` (optional): Aggregation level (`hourly`, `daily`, `weekly`, `monthly`). Default: `daily`

**Response: 200 OK**
```json
{
  "metric_type": "volunteer_hours",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "granularity": "weekly",
  "data_points": 5,
  "data": [
    {
      "period": "2025-W01",
      "count": 12,
      "sum": 145.5,
      "avg": 12.125,
      "min": 2.0,
      "max": 35.5
    },
    {
      "period": "2025-W02",
      "count": 15,
      "sum": 178.0,
      "avg": 11.867,
      "min": 1.5,
      "max": 40.0
    }
  ]
}
```

#### Get Analytics Dashboard

```
GET /api/v1/analytics/dashboard
```

**Query Parameters:**
- `project_id` (optional): Filter by project ID
- `start_date` (optional): Start date for metrics (YYYY-MM-DD). Default: 30 days ago
- `end_date` (optional): End date for metrics (YYYY-MM-DD). Default: today

**Response: 200 OK**
```json
{
  "period": {
    "start_date": "2024-12-16",
    "end_date": "2025-01-15"
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
      "total_tasks": 125,
      "completed_tasks": 78,
      "in_progress_tasks": 35,
      "not_started_tasks": 12,
      "completion_rate": 62.4
    },
    "volunteers": {
      "active_volunteers": 45,
      "total_hours_logged": 1250.5,
      "avg_hours_per_volunteer": 27.79
    },
    "budget": null
  }
}
```

**When project_id is specified:**
```json
{
  "period": {
    "start_date": "2024-12-16",
    "end_date": "2025-01-15"
  },
  "project_filter": 3,
  "summary": {
    "projects": {
      "total_projects": 1,
      "active_projects": 1,
      "completed_projects": 0,
      "planning_projects": 0
    },
    "tasks": {
      "total_tasks": 25,
      "completed_tasks": 15,
      "in_progress_tasks": 8,
      "not_started_tasks": 2,
      "completion_rate": 60.0
    },
    "volunteers": {
      "active_volunteers": 12,
      "total_hours_logged": 345.5,
      "avg_hours_per_volunteer": 28.79
    },
    "budget": {
      "total_budget": 50000.0,
      "actual_cost": 32500.0,
      "budget_utilization": 65.0
    }
  }
}
```

#### Get Volunteer Hours Trends

```
GET /api/v1/analytics/trends/volunteer-hours
```

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `project_id` (optional): Filter by project ID
- `volunteer_id` (optional): Filter by volunteer ID
- `granularity` (optional): Aggregation level (`daily`, `weekly`, `monthly`). Default: `monthly`

**Response: 200 OK**
```json
{
  "start_date": "2024-10-01",
  "end_date": "2025-01-15",
  "granularity": "monthly",
  "data_points": 4,
  "trends": [
    {
      "period": "2024-10",
      "total_hours": 456.5,
      "log_count": 78
    },
    {
      "period": "2024-11",
      "total_hours": 523.0,
      "log_count": 92
    },
    {
      "period": "2024-12",
      "total_hours": 498.5,
      "log_count": 85
    },
    {
      "period": "2025-01",
      "total_hours": 234.0,
      "log_count": 42
    }
  ]
}
```

#### Get Project Progress Trends

```
GET /api/v1/analytics/trends/project-progress
```

**Query Parameters:**
- `project_id` (required): Project ID
- `start_date` (optional): Start date (YYYY-MM-DD). Default: project start date or 90 days ago
- `end_date` (optional): End date (YYYY-MM-DD). Default: today

**Response: 200 OK**
```json
{
  "project_id": 3,
  "project_name": "Urban Reforestation Initiative",
  "start_date": "2024-10-15",
  "end_date": "2025-01-15",
  "data_points": 8,
  "trends": [
    {
      "date": "2024-11-01",
      "progress_percentage": 15.5,
      "metadata": {
        "tasks_completed": 5,
        "total_tasks": 32
      }
    },
    {
      "date": "2024-12-01",
      "progress_percentage": 42.3,
      "metadata": {
        "tasks_completed": 14,
        "total_tasks": 33
      }
    },
    {
      "date": "2025-01-01",
      "progress_percentage": 68.7,
      "metadata": {
        "tasks_completed": 23,
        "total_tasks": 33
      }
    }
  ]
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Project not found"
}
```

#### Get Environmental Impact Trends

```
GET /api/v1/analytics/trends/environmental-impact
```

**Query Parameters:**
- `project_id` (optional): Filter by project ID
- `metric_name` (optional): Filter by specific metric name
- `start_date` (optional): Start date (YYYY-MM-DD). Default: 90 days ago
- `end_date` (optional): End date (YYYY-MM-DD). Default: today

**Response: 200 OK**
```json
{
  "start_date": "2024-10-17",
  "end_date": "2025-01-15",
  "metrics_count": 3,
  "metrics": [
    {
      "metric_name": "Trees Planted",
      "metric_type": "biodiversity",
      "unit": "trees",
      "data_points": [
        {
          "date": "2024-11-01",
          "target_value": 5000.0,
          "current_value": 1250.0,
          "progress_percentage": 25.0,
          "project_id": 3
        },
        {
          "date": "2024-12-01",
          "target_value": 5000.0,
          "current_value": 3125.0,
          "progress_percentage": 62.5,
          "project_id": 3
        }
      ]
    },
    {
      "metric_name": "CO2 Offset",
      "metric_type": "carbon_footprint",
      "unit": "kg",
      "data_points": [
        {
          "date": "2024-11-01",
          "target_value": 100000.0,
          "current_value": 22500.0,
          "progress_percentage": 22.5,
          "project_id": 3
        }
      ]
    }
  ]
}
```

### Resource Statistics

#### Get Volunteer Statistics

```
GET /api/v1/volunteers/stats
```

**Authentication**: Not required (public endpoint)

**Description**: Retrieves comprehensive statistics about volunteers in the system, including total counts, activity metrics, skill distribution, and recent registration trends. This endpoint is public and used on landing pages and dashboards.

**Response: 200 OK**
```json
{
  "total_volunteers": 150,
  "active_volunteers": 45,
  "total_hours": 5624.5,
  "volunteers_by_status": {
    "active": 45,
    "inactive": 82,
    "pending": 23
  },
  "volunteers_by_skill": {
    "environmental_conservation": 32,
    "community_outreach": 28,
    "event_planning": 15,
    "data_analysis": 10
  },
  "recent_registrations": 12
}
```

**Response Fields:**
- `total_volunteers`: Total number of volunteers in the system
- `active_volunteers`: Number of currently active volunteers
- `total_hours`: Total volunteer hours logged across all volunteers
- `volunteers_by_status`: Breakdown of volunteers by their status
- `volunteers_by_skill`: Distribution of volunteers across different skill categories
- `recent_registrations`: Number of new volunteer registrations in the last 30 days

#### Get Project Statistics

```
GET /api/v1/projects/stats
```

**Authentication**: Not required (public endpoint)

**Description**: Retrieves comprehensive statistics about projects, including counts by status and category, budget information, and team metrics. This endpoint is public and used on landing pages and dashboards.

**Response: 200 OK**
```json
{
  "total_projects": 15,
  "active_projects": 8,
  "completed_projects": 5,
  "projects_by_status": {
    "planning": 2,
    "active": 8,
    "completed": 5
  },
  "projects_by_category": {
    "environmental": 6,
    "community": 4,
    "education": 3,
    "health": 2
  },
  "total_budget": 500000.0,
  "total_spent": 325000.0,
  "total_volunteer_hours": 5624.5,
  "average_team_size": 8.5
}
```

**Response Fields:**
- `total_projects`: Total number of projects in the system
- `active_projects`: Number of currently active projects
- `completed_projects`: Number of completed projects
- `projects_by_status`: Breakdown of projects by their status
- `projects_by_category`: Distribution of projects across different categories
- `total_budget`: Total budget allocated across all projects
- `total_spent`: Total amount spent across all projects
- `total_volunteer_hours`: Total volunteer hours logged across all projects
- `average_team_size`: Average number of team members per project

#### Get Task Statistics

```
GET /api/v1/tasks/stats
```

**Authentication**: Not required (public endpoint)

**Query Parameters:**
- `project_id` (optional): Filter statistics to a specific project

**Description**: Retrieves comprehensive statistics about tasks, including counts by status and priority, time estimates, and completion metrics. Can be filtered to show statistics for a specific project. This endpoint is public and used on landing pages and dashboards.

**Response: 200 OK**
```json
{
  "total_tasks": 125,
  "not_started": 12,
  "in_progress": 35,
  "completed": 78,
  "cancelled": 0,
  "overdue_tasks": 5,
  "volunteer_suitable_tasks": 42,
  "total_estimated_hours": 1250.5,
  "total_actual_hours": 1104.0,
  "average_completion_time": 12.5,
  "completion_rate": 62.4,
  "tasks_by_priority": {
    "low": 30,
    "medium": 65,
    "high": 25,
    "critical": 5
  },
  "tasks_by_project": {
    "1": 45,
    "2": 38,
    "3": 25,
    "5": 17
  }
}
```

**Response Fields:**
- `total_tasks`: Total number of tasks in the system (or project if filtered)
- `not_started`: Number of tasks that haven't been started
- `in_progress`: Number of tasks currently in progress
- `completed`: Number of completed tasks
- `cancelled`: Number of cancelled tasks
- `overdue_tasks`: Number of tasks that are past their due date
- `volunteer_suitable_tasks`: Number of tasks suitable for volunteer assignment
- `total_estimated_hours`: Sum of estimated hours for all tasks
- `total_actual_hours`: Sum of actual hours logged for all tasks
- `average_completion_time`: Average time to complete a task in days (null if no completed tasks)
- `completion_rate`: Percentage of tasks completed (0-100)
- `tasks_by_priority`: Distribution of tasks by priority level
- `tasks_by_project`: Distribution of tasks across projects (keys are project IDs)

**Response: 200 OK (with project_id filter)**
```json
{
  "total_tasks": 25,
  "not_started": 2,
  "in_progress": 8,
  "completed": 15,
  "cancelled": 0,
  "overdue_tasks": 1,
  "volunteer_suitable_tasks": 10,
  "total_estimated_hours": 250.0,
  "total_actual_hours": 218.5,
  "average_completion_time": 8.3,
  "completion_rate": 60.0,
  "tasks_by_priority": {
    "low": 8,
    "medium": 12,
    "high": 5
  },
  "tasks_by_project": {
    "3": 25
  }
}
```

### Dashboard Management

#### Create Custom Dashboard

```
POST /api/v1/analytics/dashboards
```

**Authentication**: Required

**Request Body:**
```json
{
  "name": "Project Manager View",
  "description": "Dashboard for tracking all active projects",
  "widgets": {
    "layout": [
      {"id": "w1", "type": "project_stats"},
      {"id": "w2", "type": "volunteer_hours"}
    ]
  },
  "is_default": true
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Dashboard created successfully",
  "dashboard_id": 5
}
```

#### Get User Dashboards

```
GET /api/v1/analytics/dashboards
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "count": 2,
  "dashboards": [
    {
      "id": 1,
      "name": "My Main Dashboard",
      "description": "Default dashboard view",
      "is_default": true,
      "widgets": {
        "layout": [...]
      },
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-10T15:30:00Z"
    },
    {
      "id": 2,
      "name": "Volunteer Focus",
      "description": "Dashboard focused on volunteer metrics",
      "is_default": false,
      "widgets": {
        "layout": [...]
      },
      "created_at": "2025-01-05T08:00:00Z",
      "updated_at": "2025-01-05T08:00:00Z"
    }
  ]
}
```

### Reports

#### Get Project Reports

```
GET /api/v1/reports/projects
```

**Query Parameters:**
- `project_id` (optional): Get detailed report for specific project

**Response: 200 OK (without project_id)**
```json
{
  "total_projects": 15,
  "active_projects": 8,
  "completed_projects": 5,
  "total_budget": 500000.0,
  "total_spent": 325000.0
}
```

**Response: 200 OK (with project_id)**
```json
{
  "project": {
    "id": 3,
    "name": "Urban Reforestation",
    "category": "environmental",
    "status": "in_progress",
    "start_date": "2024-10-15",
    "end_date": "2025-06-30",
    "budget": 75000.0,
    "actual_cost": 42500.0
  },
  "team_size": 12,
  "total_tasks": 35,
  "completed_tasks": 23,
  "volunteer_hours": 456.5,
  "milestones": [
    {
      "id": 1,
      "title": "Site Preparation",
      "status": "completed",
      "due_date": "2024-11-30"
    }
  ],
  "environmental_metrics": [
    {
      "metric_name": "Trees Planted",
      "current_value": 3125.0,
      "target_value": 5000.0,
      "unit": "trees"
    }
  ]
}
```

#### Get Volunteer Reports

```
GET /api/v1/reports/volunteers
```

**Response: 200 OK**
```json
{
  "total_volunteers": 150,
  "active_volunteers": 45,
  "total_hours": 5624.5,
  "avg_hours_per_volunteer": 37.5,
  "top_volunteers": [
    {
      "volunteer_id": 12,
      "name": "Jane Smith",
      "total_hours": 156.5
    }
  ]
}
```

#### Get Task Reports

```
GET /api/v1/reports/tasks
```

**Query Parameters:**
- `project_id` (optional): Filter by project ID

**Response: 200 OK**
```json
{
  "total_tasks": 125,
  "completed_tasks": 78,
  "in_progress_tasks": 35,
  "not_started_tasks": 12,
  "completion_rate": 62.4,
  "avg_completion_time_days": 12.5
}
```

#### Get Resource Reports

```
GET /api/v1/reports/resources
```

**Response: 200 OK**
```json
{
  "total_resources": 45,
  "available_resources": 32,
  "in_use_resources": 13,
  "total_value": 125000.0,
  "utilization_rate": 28.9
}
```

#### Get Dashboard Summary

```
GET /api/v1/reports/dashboard
```

**Response: 200 OK**
```json
{
  "projects": {
    "total_projects": 15,
    "active_projects": 8,
    "completed_projects": 5
  },
  "volunteers": {
    "active_volunteers": 45,
    "total_hours": 5624.5
  },
  "tasks": {
    "total_tasks": 125,
    "completed_tasks": 78
  },
  "resources": {
    "total_resources": 45,
    "available_resources": 32
  },
  "summary": {
    "total_projects": 15,
    "active_volunteers": 45,
    "total_tasks": 125,
    "total_volunteer_hours": 5624.5
  }
}
```

### Data Export

#### Export Projects to CSV

```
GET /api/v1/reports/export/projects/csv
```

**Query Parameters:**
- `status` (optional): Filter by project status
- `category` (optional): Filter by project category

**Response: 200 OK**
- Content-Type: `text/csv`
- File: `projects_export_YYYYMMDD_HHMMSS.csv`

**CSV Columns:**
ID, Name, Category, Status, Priority, Start Date, End Date, Budget, Actual Cost, Project Manager ID, Created By ID, Requires Volunteers, Created At

#### Export Volunteers to CSV

```
GET /api/v1/reports/export/volunteers/csv
```

**Authentication**: Required (Staff member, project manager, or admin)

**Query Parameters:**
- `volunteer_status` (optional): Filter by volunteer status

**Response: 200 OK**
- Content-Type: `text/csv`
- File: `volunteers_export_YYYYMMDD_HHMMSS.csv`

**CSV Columns:**
Volunteer ID, User ID, Name, Email, Phone, Date of Birth, Gender, City, Postal Code, Status, Background Check Status, Total Hours, Joined Date, Created At

**Response: 403 Forbidden**
```json
{
  "detail": "Not authorized to export volunteer data"
}
```

#### Export Tasks to CSV

```
GET /api/v1/reports/export/tasks/csv
```

**Query Parameters:**
- `project_id` (optional): Filter by project ID
- `status` (optional): Filter by task status

**Response: 200 OK**
- Content-Type: `text/csv`
- File: `tasks_export_YYYYMMDD_HHMMSS.csv`

**CSV Columns:**
ID, Title, Project ID, Project Name, Status, Priority, Assigned To ID, Estimated Hours, Actual Hours, Progress %, Suitable for Volunteers, Created At

#### Export Time Logs to CSV

```
GET /api/v1/reports/export/time-logs/csv
```

**Authentication**: Required (Staff member, project manager, or admin)

**Query Parameters:**
- `project_id` (optional): Filter by project ID
- `volunteer_id` (optional): Filter by volunteer ID
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `approval_status` (optional): Filter by approval status

**Response: 200 OK**
- Content-Type: `text/csv`
- File: `time_logs_export_YYYYMMDD_HHMMSS.csv`

**CSV Columns:**
ID, Volunteer ID, Volunteer Name, Project ID, Project Name, Task ID, Date, Hours, Activity, Description, Supervisor ID, Approval Status, Created At

#### Export Projects to JSON

```
GET /api/v1/reports/export/projects/json
```

**Query Parameters:**
- `project_id` (optional): Export single project with full details
- `status` (optional): Filter by project status (when exporting multiple)

**Response: 200 OK (single project)**
- Content-Type: `application/json`
- File: `projects_export_YYYYMMDD_HHMMSS.json`

```json
{
  "project": {...},
  "team_members": [
    {
      "team_member": {...},
      "user": {...},
      "user_type": "volunteer"
    }
  ],
  "milestones": [...],
  "environmental_metrics": [
    {
      "metric": {...},
      "recorded_by": "John Doe"
    }
  ],
  "stats": {
    "total_tasks": 35,
    "completed_tasks": 23,
    "volunteer_hours": 456.5
  }
}
```

**Response: 200 OK (multiple projects)**
```json
{
  "projects": [
    {...},
    {...}
  ],
  "total_count": 15,
  "exported_at": "2025-01-15T14:30:00Z"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Project not found"
}
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
- Date parameters use YYYY-MM-DD format
- Metric aggregation supports multiple granularities: hourly, daily, weekly, monthly
- CSV exports are limited to 10,000 records to prevent performance issues
- Default date range for analytics is 30 days when not specified
- Dashboard widgets configuration is stored as JSON and can be customized per user
- Time-series data is aggregated with min, max, avg, sum, and count statistics
- Environmental metrics support multiple measurement types: biodiversity, carbon_footprint, water_quality, waste_reduction
- Export endpoints stream data to support large datasets
- All numeric values (budget, hours, etc.) are returned as floats for consistency
