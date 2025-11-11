# Scripts

This directory contains utility scripts for the Repensar Multiplatform Backend.

## seed_data.py

A comprehensive data seeding script that populates the database with realistic mock data through HTTP API requests.

### Features

- Creates 100+ entities for each type (users, volunteers, projects, tasks, etc.)
- Validates all relationships between entities
- Provides detailed progress tracking and colored console output
- Comprehensive error reporting and assertion testing
- Supports dry-run mode for testing without creating data

### Usage

Make sure the backend server is running first:

```bash
# Start the backend server
uv run uvicorn app.main:app --reload
```

Then run the seeding script in a new terminal:

```bash
# Basic usage (uses http://localhost:8000 by default)
uv run python scripts/seed_data.py

# Specify custom API URL
uv run python scripts/seed_data.py --api-url http://localhost:8000

# Dry run (test without creating data)
uv run python scripts/seed_data.py --dry-run

# Verbose mode (show all errors instead of just first 3 per type)
uv run python scripts/seed_data.py --verbose

# Combined flags
uv run python scripts/seed_data.py --api-url http://localhost:8000 --verbose
```

### What Gets Created

The script creates the following entities in dependency order:

1. **Users** (100+): Admin, project managers, staff, and regular users
2. **Volunteers** (80+): Linked to user accounts with demographic info
3. **Volunteer Skills** (25+): Various skill categories
4. **Skill Assignments**: 2-5 skills per volunteer
5. **Projects** (30+): Various categories, statuses, and priorities
6. **Project Teams**: 3-8 members per project
7. **Milestones**: 2-4 per project
8. **Environmental Metrics**: 2-4 per project
9. **Tasks** (150+): Linked to projects, some suitable for volunteers
10. **Task-Volunteer Assignments**: Volunteers assigned to suitable tasks
11. **Task Dependencies**: Task chains and relationships
12. **Resources** (50+): Equipment, materials, financial, human resources
13. **Project Resources**: 3-8 resources allocated per project
14. **Volunteer Time Logs** (500+): Historical time tracking
15. **Notifications** (100+): Various notification types

### Validation

The script performs comprehensive relationship validation:

- Volunteer ↔ User relationship
- Volunteer ↔ Skills relationship
- Project ↔ Tasks relationship
- Project ↔ Team relationship
- Task ↔ Volunteers relationship
- Volunteer ↔ Time Logs relationship
- Project ↔ Resources relationship
- Project ↔ Milestones relationship

### Output

The script provides:

- Real-time progress bars for each entity type
- Color-coded success/failure messages
- Comprehensive summary at completion
- Assertion test results
- Detailed error reporting

### Exit Codes

- `0`: Success (all entities created, all assertions passed)
- `1`: Failure (some entities failed or assertions failed)

### Environment Variables

You can set the default API URL via environment variable:

```bash
export API_URL=http://localhost:8000
uv run python scripts/seed_data.py
```

### Dependencies

The script requires:

- `httpx`: HTTP client for API requests
- `faker`: Realistic mock data generation

These are automatically installed when you run `uv sync` after adding faker to `pyproject.toml`.

# If nothing else works
DISABLE_RATE_LIMITING=true uv run python scripts/seed_data.py