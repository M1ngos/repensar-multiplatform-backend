# Database Setup Guide

## Overview

**✨ NEW: Alembic-first approach!**

This project now uses Alembic for ALL database schema management:
- **Alembic migrations**: Creates complete schema from scratch
- **db.sql**: Legacy file for reference (optional for seed data)

## Migration Chain

```
None → 000 → 001 → 002 → 003 → 004 (head)
```

| Migration | Description |
|-----------|-------------|
| **000** | Initial schema (all base tables, functions, views from db.sql) |
| **001** | Add token_family to users |
| **002** | Add OAuth fields (oauth_provider, oauth_provider_id, profile_picture) |
| **003** | Add sync optimization indexes |
| **004** | Create sync tables (devices, device_sync_states, sync_conflicts) |

---

## Setup Instructions

### For Fresh Installations (New Database)

**✨ Recommended approach for all new setups:**

```bash
# 1. Create database
createdb repensar

# 2. Run all migrations (creates complete schema)
alembic upgrade head

# 3. Done! Your database is ready
```

That's it! Alembic will create:
- ✅ All tables with proper constraints
- ✅ All indexes
- ✅ All triggers and functions
- ✅ Activity log partitions for 2025
- ✅ Views (volunteer_profiles, project_dashboard)
- ✅ Sync tables for offline support

**Optional: Add seed data**

Migration 000 creates the schema but NOT the seed data. To add initial data:

```bash
# Option 1: Run seed data from db.sql (lines 554-797)
psql -d repensar -c "$(sed -n '554,797p' db.sql)"

# Option 2: Create your own seed script
python scripts/seed_development.py
```

---

### For Existing Database (Created with db.sql)

If you already created your database with `db.sql` before this change:

```bash
# 1. Check current status
alembic current
# Output: 004 (head)  - if you already stamped it

# If it shows "No version found", do this:

# 2. Tell Alembic the base schema (000) already exists
alembic stamp 000

# 3. Upgrade to add the new features (001-004)
alembic upgrade head

# 4. Verify
alembic current
# Output: 004 (head)
```

**What this does:**
- `stamp 000`: Marks migration 000 as applied (doesn't run it)
- `upgrade head`: Runs migrations 001→002→003→004
  - Adds token_family column
  - Adds OAuth fields
  - Adds sync indexes
  - Creates sync tables

---

## Migration History

Our current migration chain:

```
None → 001 → 002 → 003 → 004 (head)
```

| Migration | Description | Equivalent in db.sql? |
|-----------|-------------|----------------------|
| **000** *(implicit)* | Base schema | ✅ Lines 54-502 (all CREATE TABLE) |
| **001** | Add token_family to users | ❌ Not in db.sql |
| **002** | Add OAuth fields (oauth_provider, oauth_provider_id, profile_picture) | ❌ Not in db.sql |
| **003** | Add sync optimization indexes | ❌ Not in db.sql |
| **004** | Create sync tables (devices, device_sync_states, sync_conflicts) | ❌ Not in db.sql |

---

## Keeping db.sql and Alembic in Sync

### When to Update db.sql

Update `db.sql` when:
1. You create a new Alembic migration
2. The change should be in the base schema for new installations

**Example workflow:**

```bash
# 1. Create a new migration
alembic revision -m "Add new field"

# 2. Edit the migration file
# ... add your changes ...

# 3. Test the migration
alembic upgrade head

# 4. Update db.sql to include the change
# Edit db.sql manually to add the new field to the base CREATE TABLE

# 5. Commit both files
git add alembic/versions/005_*.py db.sql
git commit -m "Add new field to schema"
```

### Recommended: Create a Consolidated Script

Create a script that generates `db.sql` from your current database:

```bash
#!/bin/bash
# scripts/export_schema.sh

# Export schema only (no data)
pg_dump -d repensar --schema-only --no-owner --no-acl -f db_schema_only.sql

# Export seed data only
pg_dump -d repensar --data-only --no-owner --no-acl \
  -t user_types \
  -t volunteer_skills \
  -t volunteer_training \
  -f db_seed_data.sql

# Combine
cat db_schema_only.sql db_seed_data.sql > db.sql
```

---

## Best Practices

### For Development

```bash
# Fresh start
dropdb repensar && createdb repensar
psql -d repensar -f db.sql
alembic stamp head
```

### For Production/Staging

```bash
# Use migrations only
alembic upgrade head
```

### For CI/CD

```yaml
# .github/workflows/test.yml
- name: Setup Database
  run: |
    createdb repensar_test
    alembic upgrade head
    python scripts/seed_test_data.py
```

---

## Migration Cheat Sheet

```bash
# Create new migration
alembic revision -m "Description"

# Auto-generate migration (compares models to DB)
alembic revision --autogenerate -m "Description"

# Show current version
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 002

# Mark as applied without running (for existing DB)
alembic stamp head

# Mark specific version
alembic stamp 003
```

---

## Troubleshooting

### "Alembic says no version found but I have the database"

You ran `db.sql` directly. Solution:

```bash
alembic stamp head
```

### "Migration fails with 'table already exists'"

The database already has the schema. Solution:

```bash
# Skip to the version after the failing one
alembic stamp 002  # if 001 fails because tables exist
alembic upgrade head
```

### "I need to sync db.sql with current migrations"

Generate a fresh schema dump:

```bash
# Backup current db.sql
cp db.sql db.sql.backup

# Export current schema
pg_dump -d repensar --schema-only --no-owner --no-acl > db_new.sql

# Manually merge seed data from db.sql.backup
```

---

## Recommendations

### Short Term (Now)

1. **Keep both db.sql and Alembic**: db.sql for quick dev setup, Alembic for production
2. **Document which to use**: Add this to your README
3. **Always use Alembic in production**: More reliable and trackable

### Long Term (Future)

Consider one of these approaches:

#### Option 1: Alembic-First
- Create migration `000_initial_schema.py` that creates everything db.sql does
- Deprecate db.sql
- Use Alembic for all environments

#### Option 2: db.sql + Stamp
- Keep db.sql as the canonical source
- Always stamp after running db.sql
- Use Alembic only for incremental changes

#### Option 3: Hybrid (Current Approach - Good!)
- Use db.sql for local dev (fast, includes data)
- Use Alembic for staging/production (trackable, reliable)
- Keep both in sync manually

---

## Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `db.sql` | Complete DB with seed data | Local development, quick setup |
| `alembic/versions/001_*.py` | Add token_family | Applied after db.sql or standalone |
| `alembic/versions/002_*.py` | Add OAuth fields | Applied after 001 |
| `alembic/versions/003_*.py` | Add sync indexes | Applied after 002 |
| `alembic/versions/004_*.py` | Create sync tables | Applied after 003 |

---

## Quick Reference

### New Developer Setup

```bash
# 1. Clone repo
git clone <repo>
cd repensar-multiplatform-backend

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Create database
createdb repensar

# 4. Run migrations
alembic upgrade head

# 5. (Optional) Add seed data
psql -d repensar -c "$(sed -n '554,797p' db.sql)"

# 6. Start server
python -m uvicorn app.main:app --reload
```

### Production Deployment

```bash
# First time deployment
createdb repensar_prod
alembic upgrade head
python scripts/seed_production.py

# Updates
git pull
alembic upgrade head
systemctl restart repensar-api
```

### For Your Existing Database (YOU - Right Now!)

Since you already ran `db.sql`:

```bash
# Tell Alembic that migration 000 already exists
alembic stamp 000

# Apply the additional migrations (001-004)
alembic upgrade head

# Verify
alembic current
# Should show: 004 (head)
```

### After Creating a New Migration

```bash
# 1. Create migration
alembic revision -m "Add new feature"

# 2. Edit the migration file
# (add your changes)

# 3. Test it
alembic upgrade head

# 4. Commit
git add alembic/versions/*.py
git commit -m "Add migration: description"
```
