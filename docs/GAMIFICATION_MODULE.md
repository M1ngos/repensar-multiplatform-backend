# Gamification Module - Technical Specification

## Status
✅ **Database Models**: Complete
✅ **Migrations**: Complete (migration 009)
✅ **Seed Data**: Complete (migration 010)
⏳ **API Endpoints**: Not yet implemented
⏳ **Services**: Not yet implemented

## Overview

The Gamification Module provides a comprehensive system for recognizing and rewarding volunteer contributions through badges, achievements, points, and leaderboards. It's designed to motivate volunteers, track their progress, and create a sense of accomplishment and community.

## Database Schema

### Models

#### 1. Badge
Defines available badges in the system.

**Table**: `badges`

**Fields**:
- `id` (int, PK): Unique identifier
- `name` (str, unique): Badge name
- `description` (text): Badge description
- `category` (str): Badge category - "time", "skills", "projects", "training", "leadership", "special"
- `icon_url` (str, optional): URL to badge icon/image
- `color` (str, optional): Hex color code (e.g., "#4CAF50")
- `rarity` (str): Rarity level - "common", "rare", "epic", "legendary"
- `points_value` (int): Points awarded when earned
- `is_active` (bool): Whether badge is currently available
- `is_secret` (bool): Hidden until earned
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `volunteer_badges`: List of VolunteerBadge objects (who has earned this badge)

**Indexes**:
- `name` (unique), `category`, `is_active`

---

#### 2. Achievement
Defines achievements with criteria for earning them.

**Table**: `achievements`

**Fields**:
- `id` (int, PK): Unique identifier
- `name` (str, unique): Achievement name
- `description` (text): Achievement description
- `achievement_type` (str): Type - "hours_logged", "projects_completed", "tasks_completed", "skills_acquired", "trainings_completed", "consecutive_days", "volunteer_referred", "custom"
- `criteria` (JSON): Achievement criteria (e.g., `{"hours_required": 100}`)
- `points_reward` (int): Points awarded when achieved
- `badge_id` (int, FK, optional): Badge awarded upon completion
- `is_repeatable` (bool): Can be earned multiple times
- `tracks_progress` (bool): Whether to show progress (e.g., 50/100)
- `is_active` (bool): Whether achievement is currently available
- `is_secret` (bool): Hidden until earned
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `volunteer_achievements`: List of VolunteerAchievement objects (progress tracking)

**Indexes**:
- `name` (unique), `achievement_type`, `is_active`

**Criteria Examples**:
```json
{"hours_required": 100}
{"projects_required": 5}
{"tasks_required": 50}
{"skills_required": 5, "certified": true}
{"trainings_required": 10}
{"days_required": 7}
{"volunteers_required": 1}
```

---

#### 3. VolunteerBadge
Tracks badges earned by volunteers.

**Table**: `volunteer_badges`

**Fields**:
- `id` (int, PK): Unique identifier
- `volunteer_id` (int, FK): Reference to volunteer
- `badge_id` (int, FK): Reference to badge
- `earned_at` (datetime): When badge was earned
- `earned_reason` (text, optional): Context about how it was earned
- `awarded_by_id` (int, FK, optional): For manual awards
- `is_showcased` (bool): Whether displayed on volunteer's profile

**Relationships**:
- `badge`: Parent Badge object

**Indexes**:
- `volunteer_id`, `badge_id`, `earned_at`

---

#### 4. VolunteerAchievement
Tracks achievement progress and completion.

**Table**: `volunteer_achievements`

**Fields**:
- `id` (int, PK): Unique identifier
- `volunteer_id` (int, FK): Reference to volunteer
- `achievement_id` (int, FK): Reference to achievement
- `current_progress` (Decimal): Current progress value
- `target_progress` (Decimal): Target value (from achievement criteria)
- `is_completed` (bool): Whether achievement is completed
- `completed_at` (datetime, optional): Completion timestamp
- `times_completed` (int): Count for repeatable achievements
- `started_at` (datetime): When tracking started
- `last_progress_at` (datetime, optional): Last progress update

**Relationships**:
- `achievement`: Parent Achievement object

**Indexes**:
- `volunteer_id`, `achievement_id`, `is_completed`, `completed_at`

---

#### 5. VolunteerPoints
Current points balance for each volunteer.

**Table**: `volunteer_points`

**Fields**:
- `id` (int, PK): Unique identifier
- `volunteer_id` (int, FK, unique): Reference to volunteer
- `total_points` (int): All-time total points
- `current_points` (int): Current balance (if points can be spent)
- `rank` (int, optional): Current rank position
- `rank_percentile` (Decimal, optional): Percentile ranking (0-100)
- `current_streak_days` (int): Current consecutive active days
- `longest_streak_days` (int): Best streak ever
- `last_activity_date` (datetime, optional): Last activity date
- `updated_at` (datetime): Last update timestamp

**Relationships**:
- `points_history`: List of PointsHistory objects

**Indexes**:
- `volunteer_id` (unique), `total_points`, `rank`

---

#### 6. PointsHistory
Audit trail for all points changes.

**Table**: `points_history`

**Fields**:
- `id` (int, PK): Unique identifier
- `volunteer_points_id` (int, FK): Reference to volunteer points record
- `volunteer_id` (int, FK): Reference to volunteer
- `points_change` (int): Points added/removed (can be negative)
- `event_type` (str): Event type - "hours_logged", "task_completed", "project_completed", "training_completed", "skill_certified", "achievement_earned", "badge_earned", "volunteer_referred", "manual_adjustment"
- `description` (str): Human-readable description
- `reference_id` (int, optional): ID of related entity (task, project, etc.)
- `reference_type` (str, optional): Type of entity (e.g., "task", "project")
- `balance_after` (int): Points balance after this change
- `awarded_by_id` (int, FK, optional): For manual adjustments
- `created_at` (datetime): When points were awarded

**Relationships**:
- `volunteer_points`: Parent VolunteerPoints object

**Indexes**:
- `volunteer_points_id`, `volunteer_id`, `event_type`, `created_at`

**Cascade**: DELETE on volunteer_points deletion

---

#### 7. Leaderboard
Cached leaderboard snapshots for performance.

**Table**: `leaderboards`

**Fields**:
- `id` (int, PK): Unique identifier
- `leaderboard_type` (str): Type - "points", "hours", "projects"
- `timeframe` (str): Timeframe - "all_time", "monthly", "weekly"
- `period_start` (datetime, optional): Period start date
- `period_end` (datetime, optional): Period end date
- `rankings` (JSON): Array of rankings (e.g., `[{"volunteer_id": 1, "rank": 1, "value": 1500, "volunteer_name": "John"}]`)
- `generated_at` (datetime): When leaderboard was generated
- `is_current` (bool): Whether this is the active leaderboard
- `total_participants` (int): Number of participants
- `average_value` (Decimal, optional): Average value
- `median_value` (Decimal, optional): Median value

**Indexes**:
- `leaderboard_type`, `timeframe`, `period_start`, `generated_at`, `is_current`

---

## Enums

### BadgeCategory
```python
TIME = "time"              # Time-based achievements
SKILLS = "skills"          # Skill-related achievements
PROJECTS = "projects"      # Project completion achievements
TRAINING = "training"      # Training completion achievements
LEADERSHIP = "leadership"  # Leadership and mentoring
SPECIAL = "special"        # Special event badges
```

### AchievementType
```python
HOURS_LOGGED = "hours_logged"
PROJECTS_COMPLETED = "projects_completed"
TASKS_COMPLETED = "tasks_completed"
SKILLS_ACQUIRED = "skills_acquired"
TRAININGS_COMPLETED = "trainings_completed"
CONSECUTIVE_DAYS = "consecutive_days"
VOLUNTEER_REFERRED = "volunteer_referred"
CUSTOM = "custom"
```

### PointsEventType
```python
HOURS_LOGGED = "hours_logged"
TASK_COMPLETED = "task_completed"
PROJECT_COMPLETED = "project_completed"
TRAINING_COMPLETED = "training_completed"
SKILL_CERTIFIED = "skill_certified"
ACHIEVEMENT_EARNED = "achievement_earned"
BADGE_EARNED = "badge_earned"
VOLUNTEER_REFERRED = "volunteer_referred"
MANUAL_ADJUSTMENT = "manual_adjustment"
```

---

## Seeded Data (Migration 010)

### Badges (13 total)

**Time Badges**:
1. First Step (common) - 1 hour
2. Dedicated Volunteer (rare) - 50 hours
3. Century Club (epic) - 100 hours
4. Hero of the Community (legendary) - 500 hours

**Project Badges**:
5. Project Pioneer (common) - 1 project
6. Multi-Tasker (rare) - 5 projects

**Skill Badges**:
7. Quick Learner (common) - 1 skill
8. Jack of All Trades (epic) - 5 skills

**Training Badges**:
9. Trained and Ready (common) - 1 training
10. Lifelong Learner (rare) - 10 trainings

**Leadership Badge**:
11. Mentor (rare) - Refer a volunteer

**Streak Badges**:
12. Consistent Contributor (rare) - 7 days streak
13. Month of Service (epic) - 30 days streak

### Achievements (16 total)

**Hours-based** (5): 1, 10, 50, 100, 500 hours
**Projects** (2): 1, 5 projects
**Tasks** (2): 10, 50 tasks
**Skills** (2): 1, 5 certified skills
**Training** (2): 1, 10 trainings
**Streaks** (2): 7, 30 consecutive days
**Referral** (1): 1 volunteer (repeatable)

---

## Use Cases

### 1. Automatic Points Award
When a volunteer logs hours, completes a task, or finishes training:
- Points are automatically awarded
- Progress is updated toward relevant achievements
- Achievements are auto-completed when criteria met
- Associated badges are awarded

### 2. Achievement Tracking
- System tracks progress toward all active achievements
- Volunteers can see their progress (e.g., "75/100 hours")
- Notifications when achievements are completed
- Repeatable achievements can be earned multiple times

### 3. Badge Collection
- Badges are earned through achievements or manual awards
- Volunteers can showcase favorite badges on their profile
- Secret badges provide surprises
- Rarity levels indicate prestige

### 4. Leaderboards
- Cached snapshots for performance
- Multiple types: points, hours, projects
- Multiple timeframes: all-time, monthly, weekly
- Statistics: total participants, averages, medians

### 5. Streaks
- Track consecutive days of volunteer activity
- Current streak vs. longest streak
- Streak achievements motivate daily participation

---

## Suggested API Endpoints

### Badges

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/badges/` | List all badges | Yes |
| GET | `/badges/{id}` | Get badge details | Yes |
| POST | `/badges/` | Create badge | Yes (admin) |
| PUT | `/badges/{id}` | Update badge | Yes (admin) |
| DELETE | `/badges/{id}` | Delete badge | Yes (admin) |
| GET | `/badges/categories` | List badge categories | Yes |
| GET | `/volunteers/{id}/badges` | Get volunteer's badges | Yes |
| POST | `/volunteers/{id}/badges/{badge_id}/award` | Manually award badge | Yes (admin) |
| PUT | `/volunteers/{id}/badges/{badge_id}/showcase` | Toggle badge showcase | Yes |

### Achievements

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/achievements/` | List all achievements | Yes |
| GET | `/achievements/{id}` | Get achievement details | Yes |
| POST | `/achievements/` | Create achievement | Yes (admin) |
| PUT | `/achievements/{id}` | Update achievement | Yes (admin) |
| DELETE | `/achievements/{id}` | Delete achievement | Yes (admin) |
| GET | `/achievements/types` | List achievement types | Yes |
| GET | `/volunteers/{id}/achievements` | Get volunteer's achievement progress | Yes |
| GET | `/volunteers/{id}/achievements/{id}/progress` | Get specific achievement progress | Yes |

### Points

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/volunteers/{id}/points` | Get volunteer's points | Yes |
| GET | `/volunteers/{id}/points/history` | Get points history | Yes |
| POST | `/volunteers/{id}/points/award` | Manually award points | Yes (admin) |
| GET | `/volunteers/{id}/streak` | Get streak information | Yes |
| GET | `/points/rankings` | Get global rankings | Yes |

### Leaderboards

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/leaderboards/{type}` | Get leaderboard (type: points, hours, projects) | Yes |
| GET | `/leaderboards/{type}/{timeframe}` | Get leaderboard for timeframe | Yes |
| POST | `/leaderboards/generate` | Generate new leaderboard snapshot | Yes (admin) |
| GET | `/leaderboards/volunteer/{id}/position` | Get volunteer's leaderboard position | Yes |

### Statistics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/gamification/stats` | Get overall gamification stats | Yes (admin) |
| GET | `/gamification/stats/volunteer/{id}` | Get volunteer gamification summary | Yes |

---

## Request/Response Examples

### Get Volunteer's Badges
```json
GET /volunteers/123/badges

Response:
{
  "total_badges": 5,
  "showcased_badges": ["Century Club", "Quick Learner"],
  "badges": [
    {
      "id": 1,
      "name": "First Step",
      "description": "Completed your first hour of volunteer work",
      "category": "time",
      "rarity": "common",
      "color": "#4CAF50",
      "icon_url": "/badges/first-step.png",
      "earned_at": "2024-01-15T10:30:00Z",
      "is_showcased": false
    },
    {
      "id": 3,
      "name": "Century Club",
      "description": "Reached 100 hours of volunteer service",
      "category": "time",
      "rarity": "epic",
      "color": "#9C27B0",
      "icon_url": "/badges/century-club.png",
      "earned_at": "2024-10-20T14:22:00Z",
      "is_showcased": true
    }
  ]
}
```

### Get Achievements Progress
```json
GET /volunteers/123/achievements

Response:
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
      "badge": {
        "id": 1,
        "name": "First Step"
      }
    },
    {
      "id": 4,
      "name": "100 Hour Milestone",
      "description": "Reach 100 hours of volunteer service",
      "achievement_type": "hours_logged",
      "points_reward": 100,
      "is_completed": false,
      "current_progress": 76.5,
      "target_progress": 100,
      "progress_percentage": 76.5,
      "badge": {
        "id": 3,
        "name": "Century Club"
      }
    }
  ]
}
```

### Get Points Summary
```json
GET /volunteers/123/points

Response:
{
  "volunteer_id": 123,
  "total_points": 1250,
  "current_points": 1250,
  "rank": 15,
  "rank_percentile": 85.5,
  "current_streak_days": 12,
  "longest_streak_days": 25,
  "last_activity_date": "2025-11-07",
  "recent_history": [
    {
      "id": 450,
      "points_change": 50,
      "event_type": "task_completed",
      "description": "Completed task: Update volunteer database",
      "reference_id": 789,
      "reference_type": "task",
      "balance_after": 1250,
      "created_at": "2025-11-07T15:30:00Z"
    },
    {
      "id": 449,
      "points_change": 10,
      "event_type": "hours_logged",
      "description": "Logged 2 hours of volunteer work",
      "reference_id": 456,
      "reference_type": "time_log",
      "balance_after": 1200,
      "created_at": "2025-11-07T14:00:00Z"
    }
  ]
}
```

### Get Leaderboard
```json
GET /leaderboards/points/monthly

Response:
{
  "id": 42,
  "leaderboard_type": "points",
  "timeframe": "monthly",
  "period_start": "2025-11-01T00:00:00Z",
  "period_end": "2025-11-30T23:59:59Z",
  "generated_at": "2025-11-07T16:00:00Z",
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

### Award Manual Points
```json
POST /volunteers/123/points/award
{
  "points": 100,
  "event_type": "manual_adjustment",
  "description": "Bonus for outstanding leadership during event",
  "reason": "Led team during community cleanup event"
}

Response:
{
  "volunteer_id": 123,
  "points_change": 100,
  "new_balance": 1350,
  "event_type": "manual_adjustment",
  "description": "Bonus for outstanding leadership during event",
  "created_at": "2025-11-07T16:15:00Z"
}
```

---

## Business Logic

### Points Award Calculation
Suggested point values for common events:
- **Hour logged**: 5 points per hour
- **Task completed**: 10-50 points (based on complexity)
- **Project completed**: 100 points
- **Training completed**: 25 points
- **Skill certified**: 50 points
- **Volunteer referred**: 50 points

### Achievement Completion Flow
1. Event occurs (e.g., volunteer logs hours)
2. System checks all active achievements of relevant type
3. Updates `current_progress` for each achievement
4. If `current_progress >= target_progress`:
   - Set `is_completed = true`
   - Set `completed_at = now()`
   - Increment `times_completed` (if repeatable)
   - Award points from `points_reward`
   - If `badge_id` exists, award badge
   - Send notification to volunteer

### Streak Calculation
- Streak continues if volunteer has activity on consecutive calendar days
- Breaks if a day is skipped
- Track in `VolunteerPoints.current_streak_days`
- Update `longest_streak_days` if current exceeds it

### Leaderboard Generation
- Run periodically (e.g., daily via cron job)
- Mark old leaderboards as `is_current = false`
- Generate new snapshot with current rankings
- Cache in JSON for fast retrieval
- Include statistics (average, median)

---

## Integration Points

### With Time Tracking Module
- Award points when hours are logged
- Update hours-based achievement progress
- Track activity dates for streak calculation

### With Task Module
- Award points on task completion
- Update task-based achievement progress

### With Project Module
- Award points on project completion
- Update project-based achievement progress

### With Skills Module
- Award points when skills are certified
- Update skills-based achievement progress

### With Training Module
- Award points on training completion
- Update training-based achievement progress

---

## Performance Considerations

1. **Leaderboard Caching**: Use cached snapshots instead of real-time queries
2. **Async Processing**: Award points and check achievements asynchronously
3. **Batch Updates**: Update rankings periodically, not on every point change
4. **Indexes**: Ensure proper indexing on frequently queried fields
5. **Pagination**: Always paginate large result sets (leaderboards, history)

---

## Notification Strategy

Notify volunteers when:
- Achievement completed
- Badge earned
- Rank changes significantly (e.g., enters top 10)
- Streak milestone reached (e.g., 7, 14, 30 days)
- New achievements or badges available

---

## Security Considerations

1. **Authorization**: Only admins can create/edit badges and achievements
2. **Audit Trail**: All points changes are logged in `points_history`
3. **Manual Awards**: Require admin permission and log who awarded
4. **Data Integrity**: Validate achievement criteria before saving
5. **Rate Limiting**: Prevent gaming the system through rapid actions

---

## File Locations

- **Models**: `app/models/gamification.py`
- **Migration (Schema)**: `alembic/versions/009_create_gamification_tables.py`
- **Migration (Seed)**: `alembic/versions/010_seed_gamification_data.py`
- **Migration IDs**: `009` (schema), `010` (seed)
- **Depends on**: Migration `008` (Communication module)

---

## Next Steps

To complete this module:

1. ✅ Create database models
2. ✅ Create and run migrations
3. ✅ Seed initial badges and achievements
4. ⏳ Implement API routes in `app/routers/gamification.py`
5. ⏳ Create service layer in `app/services/gamification.py`
6. ⏳ Add schemas in `app/schemas/gamification.py`
7. ⏳ Implement achievement checking logic
8. ⏳ Create background job for leaderboard generation
9. ⏳ Integrate with other modules (tasks, projects, time tracking)
10. ⏳ Write tests
11. ⏳ Add notification integration
12. ⏳ Create admin interface for managing badges/achievements
