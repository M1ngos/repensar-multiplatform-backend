-- Clear all seeded data from Repensar database
-- Run with: psql -h localhost -U dev -d repensar -f scripts/clear_data.sql

BEGIN;

-- Disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- Clear tables in order (most dependent first)
TRUNCATE TABLE messages CASCADE;
TRUNCATE TABLE conversations CASCADE;
TRUNCATE TABLE notification CASCADE;

TRUNCATE TABLE blog_post_tags CASCADE;
TRUNCATE TABLE blog_post_categories CASCADE;
TRUNCATE TABLE blog_posts CASCADE;
TRUNCATE TABLE blog_tags CASCADE;
TRUNCATE TABLE blog_categories CASCADE;

TRUNCATE TABLE taskdependency CASCADE;
TRUNCATE TABLE taskvolunteer CASCADE;
TRUNCATE TABLE task CASCADE;

TRUNCATE TABLE volunteertimelog CASCADE;
TRUNCATE TABLE volunteerskillassignment CASCADE;
TRUNCATE TABLE volunteer CASCADE;

TRUNCATE TABLE projectresource CASCADE;
TRUNCATE TABLE environmentalmetric CASCADE;
TRUNCATE TABLE milestone CASCADE;
TRUNCATE TABLE projectteam CASCADE;
TRUNCATE TABLE project CASCADE;

TRUNCATE TABLE resource CASCADE;

-- Preserve admin users (optional - comment out to delete all users)
DELETE FROM users WHERE email NOT IN ('admin@repensar.org', 'manager@repensar.org', 'staff@repensar.org');

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

COMMIT;

-- Show summary
SELECT
    'Users' as table_name, COUNT(*) as remaining_rows FROM users
UNION ALL
SELECT 'Volunteers', COUNT(*) FROM volunteer
UNION ALL
SELECT 'Projects', COUNT(*) FROM project
UNION ALL
SELECT 'Tasks', COUNT(*) FROM task
UNION ALL
SELECT 'Resources', COUNT(*) FROM resource;

\echo 'Database cleared successfully!'
