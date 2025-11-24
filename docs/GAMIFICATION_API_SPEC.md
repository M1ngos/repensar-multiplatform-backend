# Gamification Module - Frontend API Specification

## Overview

The Gamification Module provides a comprehensive system for recognizing and rewarding volunteer contributions through badges, achievements, points, and leaderboards. This document describes all available API endpoints for frontend integration.

**Base URL**: `/gamification`
**Authentication**: All endpoints require JWT authentication via Bearer token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Badges](#badges)
3. [Achievements](#achievements)
4. [Points](#points)
5. [Leaderboards](#leaderboards)
6. [Statistics](#statistics)
7. [Events](#events)
8. [Error Handling](#error-handling)
9. [Frontend Integration Guide](#frontend-integration-guide)

---

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Permission Levels

- **Public** (authenticated users): View own data, public leaderboards
- **Volunteer**: View own badges, achievements, points, progress
- **Admin**: Full CRUD access, manual awards, view all data

---

## Badges

### 1. List All Badges

```http
GET /gamification/badges
```

Get a list of all available badges.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip. Default: 0
- `limit` (integer, optional): Max records to return (1-100). Default: 100
- `category` (string, optional): Filter by category (time, skills, projects, training, leadership, special)
- `rarity` (string, optional): Filter by rarity (common, rare, epic, legendary)
- `is_active` (boolean, optional): Filter by active status

**Response: 200 OK**

```json
[
  {
    "id": 1,
    "name": "First Step",
    "category": "time",
    "rarity": "common",
    "color": "#4CAF50",
    "icon_url": "/badges/first-step.png",
    "points_value": 10,
    "is_secret": false
  },
  {
    "id": 3,
    "name": "Century Club",
    "category": "time",
    "rarity": "epic",
    "color": "#9C27B0",
    "icon_url": "/badges/century-club.png",
    "points_value": 100,
    "is_secret": false
  }
]
```

---

### 2. Get Badge Details

```http
GET /gamification/badges/{badge_id}
```

Get detailed information about a specific badge.

**Response: 200 OK**

```json
{
  "id": 1,
  "name": "First Step",
  "description": "Completed your first hour of volunteer work",
  "category": "time",
  "icon_url": "/badges/first-step.png",
  "color": "#4CAF50",
  "rarity": "common",
  "points_value": 10,
  "is_active": true,
  "is_secret": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Response: 404 Not Found**

```json
{
  "detail": "Badge not found"
}
```

---

### 3. Get Badge Categories

```http
GET /gamification/badges/categories
```

Get list of available badge categories.

**Response: 200 OK**

```json
{
  "categories": ["time", "skills", "projects", "training", "leadership", "special"]
}
```

---

### 4. Get Volunteer's Badges

```http
GET /gamification/volunteers/{volunteer_id}/badges
```

Get all badges earned by a volunteer.

**Permissions**: Volunteers can only view their own badges. Admins can view all.

**Response: 200 OK**

```json
{
  "total_badges": 5,
  "showcased_badges": ["Century Club", "Quick Learner"],
  "badges": [
    {
      "id": 15,
      "volunteer_id": 123,
      "badge_id": 1,
      "earned_at": "2024-01-15T10:30:00Z",
      "earned_reason": "Logged first volunteer hour",
      "awarded_by_id": null,
      "is_showcased": false,
      "badge": {
        "id": 1,
        "name": "First Step",
        "category": "time",
        "rarity": "common",
        "color": "#4CAF50",
        "icon_url": "/badges/first-step.png",
        "points_value": 10,
        "is_secret": false
      }
    },
    {
      "id": 28,
      "volunteer_id": 123,
      "badge_id": 3,
      "earned_at": "2024-10-20T14:22:00Z",
      "earned_reason": "Reached 100 hours milestone",
      "awarded_by_id": null,
      "is_showcased": true,
      "badge": {
        "id": 3,
        "name": "Century Club",
        "category": "time",
        "rarity": "epic",
        "color": "#9C27B0",
        "icon_url": "/badges/century-club.png",
        "points_value": 100,
        "is_secret": false
      }
    }
  ]
}
```

---

### 5. Toggle Badge Showcase

```http
PUT /gamification/volunteers/{volunteer_id}/badges/{badge_id}/showcase
```

Toggle whether a badge is displayed on the volunteer's profile.

**Permissions**: Volunteers can only showcase their own badges.

**Request Body:**

```json
{
  "is_showcased": true
}
```

**Response: 200 OK**

```json
{
  "message": "Badge showcase updated",
  "is_showcased": true
}
```

---

### 6. Create Badge (Admin Only)

```http
POST /gamification/badges
```

Create a new badge.

**Permissions**: Admin only

**Request Body:**

```json
{
  "name": "Superstar Volunteer",
  "description": "Reached 1000 hours of volunteer service",
  "category": "time",
  "icon_url": "/badges/superstar.png",
  "color": "#FFD700",
  "rarity": "legendary",
  "points_value": 500,
  "is_active": true,
  "is_secret": false
}
```

**Response: 201 Created**

Returns the created badge object.

---

### 7. Update Badge (Admin Only)

```http
PUT /gamification/badges/{badge_id}
```

Update an existing badge.

**Permissions**: Admin only

**Request Body** (all fields optional):

```json
{
  "name": "Updated Badge Name",
  "is_active": false
}
```

**Response: 200 OK**

Returns the updated badge object.

---

### 8. Delete Badge (Admin Only)

```http
DELETE /gamification/badges/{badge_id}
```

Soft delete a badge (sets `is_active` to false).

**Permissions**: Admin only

**Response: 204 No Content**

---

### 9. Manually Award Badge (Admin Only)

```http
POST /gamification/volunteers/{volunteer_id}/badges/award
```

Manually award a badge to a volunteer.

**Permissions**: Admin only

**Request Body:**

```json
{
  "badge_id": 5,
  "earned_reason": "Outstanding leadership during community event"
}
```

**Response: 200 OK**

```json
{
  "status": "awarded",
  "badge_id": 5,
  "badge_name": "Leadership Excellence",
  "points_awarded": 75
}
```

**Response: 200 OK** (if already earned)

```json
{
  "status": "already_earned",
  "badge_id": 5
}
```

---

## Achievements

### 1. List All Achievements

```http
GET /gamification/achievements
```

Get a list of all available achievements.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip. Default: 0
- `limit` (integer, optional): Max records to return (1-100). Default: 100
- `achievement_type` (string, optional): Filter by type
- `is_active` (boolean, optional): Filter by active status

**Achievement Types:**
- `hours_logged`
- `projects_completed`
- `tasks_completed`
- `skills_acquired`
- `trainings_completed`
- `consecutive_days`
- `volunteer_referred`
- `custom`

**Response: 200 OK**

```json
[
  {
    "id": 1,
    "name": "First Hour",
    "achievement_type": "hours_logged",
    "points_reward": 10,
    "is_repeatable": false,
    "is_secret": false
  }
]
```

---

### 2. Get Achievement Details

```http
GET /gamification/achievements/{achievement_id}
```

Get detailed information about a specific achievement.

**Response: 200 OK**

```json
{
  "id": 4,
  "name": "100 Hour Milestone",
  "description": "Reach 100 hours of volunteer service",
  "achievement_type": "hours_logged",
  "criteria": {
    "hours_required": 100
  },
  "points_reward": 100,
  "badge_id": 3,
  "is_repeatable": false,
  "tracks_progress": true,
  "is_active": true,
  "is_secret": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### 3. Get Achievement Types

```http
GET /gamification/achievements/types
```

Get list of available achievement types.

**Response: 200 OK**

```json
{
  "types": [
    "hours_logged",
    "projects_completed",
    "tasks_completed",
    "skills_acquired",
    "trainings_completed",
    "consecutive_days",
    "volunteer_referred",
    "custom"
  ]
}
```

---

### 4. Get Volunteer's Achievement Progress

```http
GET /gamification/volunteers/{volunteer_id}/achievements
```

Get all achievement progress for a volunteer.

**Permissions**: Volunteers can only view their own progress. Admins can view all.

**Response: 200 OK**

```json
{
  "total_achievements": 16,
  "completed": 5,
  "in_progress": 11,
  "achievements": [
    {
      "id": 1,
      "name": "First Hour",
      "description": "Log your first hour of volunteer work",
      "achievement_type": "hours_logged",
      "points_reward": 10,
      "is_completed": true,
      "completed_at": "2024-01-15T10:30:00Z",
      "current_progress": 1,
      "target_progress": 1,
      "progress_percentage": 100.0,
      "times_completed": 1,
      "badge": {
        "id": 1,
        "name": "First Step",
        "category": "time",
        "rarity": "common",
        "color": "#4CAF50",
        "icon_url": "/badges/first-step.png",
        "points_value": 10,
        "is_secret": false
      }
    },
    {
      "id": 4,
      "name": "100 Hour Milestone",
      "description": "Reach 100 hours of volunteer service",
      "achievement_type": "hours_logged",
      "points_reward": 100,
      "is_completed": false,
      "completed_at": null,
      "current_progress": 76.5,
      "target_progress": 100,
      "progress_percentage": 76.5,
      "times_completed": 0,
      "badge": {
        "id": 3,
        "name": "Century Club",
        "category": "time",
        "rarity": "epic",
        "color": "#9C27B0",
        "icon_url": "/badges/century-club.png",
        "points_value": 100,
        "is_secret": false
      }
    }
  ]
}
```

---

### 5. Get Specific Achievement Progress

```http
GET /gamification/volunteers/{volunteer_id}/achievements/{achievement_id}/progress
```

Get progress for a specific achievement.

**Response: 200 OK**

Returns a single achievement progress object (same structure as in the array above).

---

### 6. Create Achievement (Admin Only)

```http
POST /gamification/achievements
```

Create a new achievement.

**Permissions**: Admin only

**Request Body:**

```json
{
  "name": "Task Master",
  "description": "Complete 100 volunteer tasks",
  "achievement_type": "tasks_completed",
  "criteria": {
    "tasks_required": 100
  },
  "points_reward": 150,
  "badge_id": 8,
  "is_repeatable": false,
  "tracks_progress": true,
  "is_active": true,
  "is_secret": false
}
```

**Response: 201 Created**

Returns the created achievement object.

---

### 7. Update Achievement (Admin Only)

```http
PUT /gamification/achievements/{achievement_id}
```

Update an existing achievement.

**Permissions**: Admin only

**Request Body** (all fields optional):

```json
{
  "points_reward": 200,
  "is_active": true
}
```

**Response: 200 OK**

Returns the updated achievement object.

---

### 8. Delete Achievement (Admin Only)

```http
DELETE /gamification/achievements/{achievement_id}
```

Soft delete an achievement.

**Permissions**: Admin only

**Response: 204 No Content**

---

## Points

### 1. Get Volunteer's Points Summary

```http
GET /gamification/volunteers/{volunteer_id}/points
```

Get points summary and recent history for a volunteer.

**Permissions**: Volunteers can only view their own points. Admins can view all.

**Response: 200 OK**

```json
{
  "id": 45,
  "volunteer_id": 123,
  "total_points": 1250,
  "current_points": 1250,
  "rank": 15,
  "rank_percentile": 85.5,
  "current_streak_days": 12,
  "longest_streak_days": 25,
  "last_activity_date": "2025-11-24T15:30:00Z",
  "updated_at": "2025-11-24T15:30:00Z",
  "recent_history": [
    {
      "id": 450,
      "points_change": 50,
      "event_type": "task_completed",
      "description": "Completed task: Update volunteer database",
      "reference_id": 789,
      "reference_type": "task",
      "balance_after": 1250,
      "awarded_by_id": null,
      "created_at": "2025-11-24T15:30:00Z"
    },
    {
      "id": 449,
      "points_change": 10,
      "event_type": "hours_logged",
      "description": "Logged 2 hours of volunteer work",
      "reference_id": 456,
      "reference_type": "timelog",
      "balance_after": 1200,
      "awarded_by_id": null,
      "created_at": "2025-11-24T14:00:00Z"
    }
  ]
}
```

---

### 2. Get Full Points History

```http
GET /gamification/volunteers/{volunteer_id}/points/history
```

Get complete points history for a volunteer.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip. Default: 0
- `limit` (integer, optional): Max records to return (1-100). Default: 50

**Permissions**: Volunteers can only view their own history. Admins can view all.

**Response: 200 OK**

Returns an array of points history entries (same structure as in `recent_history` above).

---

### 3. Get Volunteer's Streak

```http
GET /gamification/volunteers/{volunteer_id}/streak
```

Get activity streak information for a volunteer.

**Permissions**: Volunteers can only view their own streak. Admins can view all.

**Response: 200 OK**

```json
{
  "volunteer_id": 123,
  "current_streak_days": 12,
  "longest_streak_days": 25,
  "last_activity_date": "2025-11-24T15:30:00Z",
  "is_active_today": true
}
```

---

### 4. Get Global Rankings

```http
GET /gamification/points/rankings
```

Get global volunteer rankings by points.

**Query Parameters:**
- `limit` (integer, optional): Max rankings to return (1-100). Default: 100

**Response: 200 OK**

```json
[
  {
    "rank": 1,
    "volunteer_id": 45,
    "volunteer_name": "Sarah Johnson",
    "volunteer_avatar": "/avatars/45.jpg",
    "total_points": 2500,
    "badges_count": 12,
    "achievements_count": 15
  },
  {
    "rank": 2,
    "volunteer_id": 123,
    "volunteer_name": "John Doe",
    "volunteer_avatar": "/avatars/123.jpg",
    "total_points": 2150,
    "badges_count": 10,
    "achievements_count": 12
  }
]
```

---

### 5. Manually Award Points (Admin Only)

```http
POST /gamification/volunteers/{volunteer_id}/points/award
```

Manually award points to a volunteer.

**Permissions**: Admin only

**Request Body:**

```json
{
  "points": 100,
  "event_type": "manual_adjustment",
  "description": "Bonus for outstanding leadership during event",
  "reference_id": null,
  "reference_type": null
}
```

**Note**: `points` can be negative for deductions.

**Response: 200 OK**

```json
{
  "volunteer_id": 123,
  "points_change": 100,
  "new_balance": 1350,
  "event_type": "manual_adjustment",
  "description": "Bonus for outstanding leadership during event",
  "created_at": "2025-11-24T16:15:00Z"
}
```

---

## Leaderboards

### 1. Get Leaderboard

```http
GET /gamification/leaderboards/{leaderboard_type}
```

Get a leaderboard by type and timeframe.

**Path Parameters:**
- `leaderboard_type`: Type of leaderboard (points, hours, projects)

**Query Parameters:**
- `timeframe` (string, optional): Timeframe (all_time, weekly, monthly). Default: all_time

**Response: 200 OK**

```json
{
  "id": 42,
  "leaderboard_type": "points",
  "timeframe": "monthly",
  "period_start": "2025-11-01T00:00:00Z",
  "period_end": "2025-11-30T23:59:59Z",
  "generated_at": "2025-11-24T16:00:00Z",
  "is_current": true,
  "total_participants": 150,
  "average_value": 285.5,
  "median_value": 220.0,
  "rankings": [
    {
      "volunteer_id": 45,
      "rank": 1,
      "value": 2500,
      "volunteer_name": "Sarah Johnson",
      "volunteer_avatar": "/avatars/45.jpg"
    },
    {
      "volunteer_id": 123,
      "rank": 2,
      "value": 2150,
      "volunteer_name": "John Doe",
      "volunteer_avatar": "/avatars/123.jpg"
    },
    {
      "volunteer_id": 78,
      "rank": 3,
      "value": 1890,
      "volunteer_name": "Maria Garcia",
      "volunteer_avatar": "/avatars/78.jpg"
    }
  ]
}
```

---

### 2. Get Volunteer's Leaderboard Positions

```http
GET /gamification/leaderboards/volunteer/{volunteer_id}/position
```

Get a volunteer's position across all leaderboards.

**Permissions**: Volunteers can only view their own positions. Admins can view all.

**Response: 200 OK**

```json
[
  {
    "volunteer_id": 123,
    "leaderboard_type": "points",
    "timeframe": "all_time",
    "rank": 15,
    "value": 1250,
    "total_participants": 200,
    "percentile": 92.5
  },
  {
    "volunteer_id": 123,
    "leaderboard_type": "points",
    "timeframe": "monthly",
    "rank": 8,
    "value": 450,
    "total_participants": 150,
    "percentile": 94.67
  },
  {
    "volunteer_id": 123,
    "leaderboard_type": "hours",
    "timeframe": "all_time",
    "rank": 22,
    "value": 76.5,
    "total_participants": 200,
    "percentile": 89.0
  }
]
```

---

### 3. Generate Leaderboards (Admin Only)

```http
POST /gamification/leaderboards/generate
```

Manually trigger leaderboard regeneration for all types and timeframes.

**Permissions**: Admin only

**Response: 200 OK**

```json
{
  "message": "Successfully generated 9 leaderboards"
}
```

---

## Statistics

### 1. Get Overall Gamification Stats (Admin Only)

```http
GET /gamification/stats
```

Get overall gamification statistics.

**Permissions**: Admin only

**Response: 200 OK**

```json
{
  "total_badges": 13,
  "total_achievements": 16,
  "total_points_awarded": 125000,
  "total_badges_earned": 450,
  "total_achievements_completed": 280,
  "active_volunteers": 200,
  "avg_points_per_volunteer": 625.0,
  "most_earned_badge": {
    "id": 1,
    "name": "First Step",
    "category": "time",
    "rarity": "common",
    "color": "#4CAF50",
    "icon_url": "/badges/first-step.png",
    "points_value": 10,
    "is_secret": false
  },
  "most_completed_achievement": {
    "id": 1,
    "name": "First Hour",
    "achievement_type": "hours_logged",
    "points_reward": 10,
    "is_repeatable": false,
    "is_secret": false
  }
}
```

---

### 2. Get Volunteer Gamification Summary

```http
GET /gamification/stats/volunteer/{volunteer_id}
```

Get complete gamification summary for a volunteer.

**Permissions**: Volunteers can only view their own summary. Admins can view all.

**Response: 200 OK**

```json
{
  "volunteer_id": 123,
  "points": {
    "id": 45,
    "volunteer_id": 123,
    "total_points": 1250,
    "current_points": 1250,
    "rank": 15,
    "rank_percentile": 85.5,
    "current_streak_days": 12,
    "longest_streak_days": 25,
    "last_activity_date": "2025-11-24T15:30:00Z",
    "updated_at": "2025-11-24T15:30:00Z"
  },
  "badges_earned": 5,
  "achievements_completed": 8,
  "recent_badges": [
    {
      "id": 28,
      "volunteer_id": 123,
      "badge_id": 3,
      "earned_at": "2024-10-20T14:22:00Z",
      "earned_reason": "Reached 100 hours milestone",
      "awarded_by_id": null,
      "is_showcased": true,
      "badge": {
        "id": 3,
        "name": "Century Club",
        "category": "time",
        "rarity": "epic",
        "color": "#9C27B0",
        "icon_url": "/badges/century-club.png",
        "points_value": 100,
        "is_secret": false
      }
    }
  ],
  "achievement_progress": [
    {
      "id": 4,
      "name": "100 Hour Milestone",
      "description": "Reach 100 hours of volunteer service",
      "achievement_type": "hours_logged",
      "points_reward": 100,
      "is_completed": false,
      "completed_at": null,
      "current_progress": 76.5,
      "target_progress": 100,
      "progress_percentage": 76.5,
      "times_completed": 0,
      "badge": {
        "id": 3,
        "name": "Century Club",
        "category": "time",
        "rarity": "epic",
        "color": "#9C27B0",
        "icon_url": "/badges/century-club.png",
        "points_value": 100,
        "is_secret": false
      }
    }
  ],
  "leaderboard_positions": [
    {
      "volunteer_id": 123,
      "leaderboard_type": "points",
      "timeframe": "all_time",
      "rank": 15,
      "value": 1250,
      "total_participants": 200,
      "percentile": 92.5
    }
  ]
}
```

---

## Events

The gamification system publishes events that can be subscribed to for real-time notifications:

### Published Events

1. **`badge.earned`** - When a volunteer earns a badge
   ```json
   {
     "volunteer_id": 123,
     "badge_id": 3,
     "badge_name": "Century Club",
     "points_awarded": 100
   }
   ```

2. **`achievement.completed`** - When a volunteer completes an achievement
   ```json
   {
     "volunteer_id": 123,
     "achievement_id": 4,
     "achievement_name": "100 Hour Milestone",
     "points_awarded": 100
   }
   ```

3. **`points.awarded`** - When points are awarded (automatic or manual)
4. **`rank.changed`** - When a volunteer's rank changes significantly

### Consumed Events

The gamification system automatically responds to these events:

- **`task.completed`** - Awards points and checks achievements
- **`timelog.approved`** - Awards points based on hours logged
- **`training.completed`** - Awards points for training completion
- **`skill.added`** - Awards points for certified skills

---

## Error Handling

### Standard Error Responses

**400 Bad Request** - Invalid input data
```json
{
  "detail": "Badge with name 'First Step' already exists"
}
```

**401 Unauthorized** - Missing or invalid authentication
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden** - Insufficient permissions
```json
{
  "detail": "Only administrators can create badges"
}
```

**404 Not Found** - Resource not found
```json
{
  "detail": "Badge not found"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to award badge"
}
```

---

## Frontend Integration Guide

### Automatic Points and Achievements

The gamification system automatically awards points and checks achievements when volunteers:
- Log hours (approved timelogs)
- Complete tasks
- Complete projects
- Complete training
- Get skills certified

**No frontend action required** for these automatic awards.

### Displaying Progress

#### Badge Progress Bar Component

```typescript
interface BadgeProgressProps {
  currentCount: number;
  targetCount: number;
  badgeName: string;
}

function BadgeProgress({ currentCount, targetCount, badgeName }: BadgeProgressProps) {
  const percentage = (currentCount / targetCount) * 100;

  return (
    <div className="badge-progress">
      <h4>{badgeName}</h4>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
      <p>{currentCount} / {targetCount}</p>
    </div>
  );
}
```

#### Achievement Progress

```typescript
async function fetchAchievementProgress(volunteerId: number) {
  const response = await fetch(
    `/gamification/volunteers/${volunteerId}/achievements`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const data = await response.json();
  return data.achievements;
}
```

### Real-time Updates

Subscribe to Server-Sent Events (SSE) for real-time gamification updates:

```typescript
const eventSource = new EventSource('/notifications/stream', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

eventSource.addEventListener('badge_earned', (event) => {
  const data = JSON.parse(event.data);
  showBadgeNotification(data.badge_name, data.points_awarded);
});

eventSource.addEventListener('achievement_completed', (event) => {
  const data = JSON.parse(event.data);
  showAchievementNotification(data.achievement_name, data.points_awarded);
});
```

### Leaderboard Updates

Leaderboards are cached and updated hourly. Fetch the current leaderboard:

```typescript
async function fetchLeaderboard(type: 'points' | 'hours' | 'projects', timeframe: string) {
  const response = await fetch(
    `/gamification/leaderboards/${type}?timeframe=${timeframe}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  return await response.json();
}
```

### Showcasing Badges

Allow volunteers to select badges to showcase on their profile:

```typescript
async function toggleBadgeShowcase(volunteerId: number, badgeId: number, showcase: boolean) {
  const response = await fetch(
    `/gamification/volunteers/${volunteerId}/badges/${badgeId}/showcase`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_showcased: showcase })
    }
  );

  return await response.json();
}
```

### Dashboard Components

#### Points Widget

```typescript
interface PointsWidgetProps {
  volunteerId: number;
}

function PointsWidget({ volunteerId }: PointsWidgetProps) {
  const [points, setPoints] = useState(null);

  useEffect(() => {
    fetch(`/gamification/volunteers/${volunteerId}/points`)
      .then(res => res.json())
      .then(setPoints);
  }, [volunteerId]);

  if (!points) return <div>Loading...</div>;

  return (
    <div className="points-widget">
      <h3>Your Points</h3>
      <div className="total-points">{points.total_points}</div>
      <div className="rank">Rank: #{points.rank}</div>
      <div className="percentile">Top {100 - points.rank_percentile}%</div>
      <div className="streak">
        🔥 {points.current_streak_days} day streak
      </div>
    </div>
  );
}
```

#### Badge Gallery

```typescript
interface BadgeGalleryProps {
  volunteerId: number;
}

function BadgeGallery({ volunteerId }: BadgeGalleryProps) {
  const [badges, setBadges] = useState(null);

  useEffect(() => {
    fetch(`/gamification/volunteers/${volunteerId}/badges`)
      .then(res => res.json())
      .then(setBadges);
  }, [volunteerId]);

  if (!badges) return <div>Loading...</div>;

  return (
    <div className="badge-gallery">
      <h3>Badges ({badges.total_badges})</h3>
      <div className="badge-grid">
        {badges.badges.map(vb => (
          <div key={vb.id} className={`badge ${vb.badge.rarity}`}>
            <img src={vb.badge.icon_url} alt={vb.badge.name} />
            <h4>{vb.badge.name}</h4>
            <p className="rarity">{vb.badge.rarity}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Best Practices

1. **Cache Leaderboards**: Leaderboards update hourly, so cache them on the frontend for better performance
2. **Show Progress**: Display progress bars for in-progress achievements to motivate volunteers
3. **Celebrate Milestones**: Show prominent notifications when badges/achievements are earned
4. **Use SSE**: Subscribe to real-time events for instant gamification updates
5. **Showcase Badges**: Allow volunteers to select their favorite badges to display
6. **Responsive Design**: Badge icons should work at multiple sizes (16px, 32px, 64px)
7. **Color Coding**: Use badge rarity colors consistently:
   - Common: Green (#4CAF50)
   - Rare: Blue (#2196F3)
   - Epic: Purple (#9C27B0)
   - Legendary: Gold (#FFD700)

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse:
- Standard users: 60 requests per minute
- Admins: 120 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1698765432
```

---

## Support

For questions or issues with the gamification API:
- Backend Issues: Contact the backend team
- Frontend Integration: See examples in this document
- Feature Requests: Submit via the project management system
