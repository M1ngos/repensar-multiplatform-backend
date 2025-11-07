# Migration to Alembic-Only Database Management

This document describes the migration from mixed database initialization (SQLModel + manual seeding) to Alembic-exclusive database management.

## What Changed

### 1. Application Startup (`app/main.py`)
- **Removed**: `create_db_and_tables()` call from application startup
- **Reason**: Database schema management should be explicit and version-controlled via Alembic migrations
- **Impact**: The application no longer automatically creates tables on startup

### 2. New Alembic Migration (`alembic/versions/cd04f478e6b0_seed_initial_user_types.py`)
- **Created**: New migration to seed initial user types
- **Includes**: Four user types with complete permissions and dashboard configurations:
  - **admin**: Full system access
  - **project_manager**: Project and volunteer management
  - **staff_member**: Operational and volunteer management
  - **volunteer**: Limited access to own tasks and profile

### 3. Seed Script (`app/database/seed.py`)
- **Status**: Deprecated with warning messages
- **Reason**: Data seeding should be part of migrations for consistency
- **Action**: Kept for reference but should not be used

### 4. Documentation (`README.md`)
- **Updated**: Comprehensive Alembic workflow instructions
- **Added**: Migration creation, rollback, and status check commands

## Migration Steps for Existing Installations

### If You Have an Existing Database

1. **Stamp your current database** to mark it as having the base schema:
   ```bash
   alembic stamp 000
   ```

2. **Apply remaining migrations** including the new user types seeding:
   ```bash
   alembic upgrade head
   ```

### For New Installations

Simply run:
```bash
alembic upgrade head
```

This will:
- Create all tables with constraints and indexes
- Set up PostgreSQL functions and triggers
- Create database views
- Seed initial user types

## User Types and Permissions

The migration creates four user types with the following permissions:

### Admin
- **Full CRUD** on all entities (users, projects, tasks, volunteers, resources, reports)
- **System configuration** and user management
- **Dashboard**: Overview, projects, tasks, volunteers, reports, analytics

### Project Manager
- **Create and manage** projects, tasks, and resources
- **Update** volunteer information
- **Approve** volunteer time logs
- **Dashboard**: My projects, tasks, volunteers, reports

### Staff Member
- **Create and manage** volunteers
- **Update** tasks and resources
- **Approve** volunteer time logs
- **Dashboard**: Tasks, volunteers, time logs

### Volunteer
- **Read-only** access to projects and tasks
- **Full access** to own profile and time logs
- **Create** time log entries
- **Dashboard**: My tasks, my hours, available tasks

## Development Workflow

### Making Schema Changes

1. **Modify your SQLModel models** in `app/models/`

2. **Generate a migration**:
   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```

3. **Review the generated migration** in `alembic/versions/`
   - Alembic may not detect all changes (e.g., column renames)
   - Always review and test migrations before applying

4. **Apply the migration**:
   ```bash
   alembic upgrade head
   ```

### Adding Seed Data

For new seed data (like default settings, initial categories, etc.):

1. **Create a data migration**:
   ```bash
   alembic revision -m "seed_category_defaults"
   ```

2. **Use `op.bulk_insert()` or `op.execute()`** to insert data

3. **Implement downgrade** to remove the data

See `alembic/versions/cd04f478e6b0_seed_initial_user_types.py` for an example.

## Verification

### Check Current Migration Status
```bash
alembic current
```

Expected output:
```
cd04f478e6b0 (head)
```

### Verify User Types Created
```sql
SELECT name, description FROM user_types;
```

Expected result:
```
name             | description
-----------------+----------------------------------------------------------
admin            | Administrator with full system access
project_manager  | Project manager with project and volunteer management...
staff_member     | Staff member with operational and volunteer management...
volunteer        | Volunteer with limited access to assigned tasks...
```

## Rollback Plan

If you need to rollback these changes:

1. **Rollback the seed migration**:
   ```bash
   alembic downgrade -1
   ```
   This removes the seeded user types.

2. **To restore old behavior** (not recommended):
   - Uncomment `create_db_and_tables()` in `app/main.py`
   - Restore the import in line 6-7

## Benefits of Alembic-Only Approach

1. **Version Control**: All schema changes are tracked in version control
2. **Reproducibility**: Same schema can be recreated consistently across environments
3. **Rollback Capability**: Easy to revert problematic changes
4. **Collaboration**: Team members can see and review schema changes
5. **Production Safety**: Explicit migration application prevents accidental schema changes
6. **Data Migrations**: Can include data transformations alongside schema changes

## Common Issues

### Issue: "relation already exists"
**Solution**: Your database already has tables. Run `alembic stamp 000` first.

### Issue: User types already exist
**Solution**: Check if manual seeding was done. You can safely skip the seed migration or clear existing user types first.

### Issue: Migration conflicts
**Solution**: Check migration dependencies in revision files. Ensure linear migration path.

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [FastAPI + Alembic Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/#alembic-note)

## Questions or Issues?

If you encounter any issues during migration, check:
1. Database connection string in `.env` or `alembic.ini`
2. Migration status with `alembic current`
3. Database logs for constraint violations or errors
4. Alembic history with `alembic history`
