"""Create activity_log partitions for 2026 and 2027, plus DEFAULT partition.

Revision ID: 013
Revises: 012
Create Date: 2026-03-10 00:00:00.000000

The initial schema only created monthly partitions for 2025.  Any INSERT
with created_at >= 2026-01-01 raises a PostgreSQL CheckViolation because
no matching partition exists.  This migration:

1. Creates monthly partitions for all of 2026 and 2027 (24 partitions).
2. Adds a DEFAULT partition that catches rows that fall outside every range
   partition — so the application never crashes on a missing partition again;
   rows simply land in the default bucket and remain queryable.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _monthly_partitions(year: int) -> list[tuple[str, str, str]]:
    """Return (partition_name, from_date, to_date) tuples for every month of *year*."""
    partitions = []
    for month in range(1, 13):
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year = year + 1
        name = f"activity_logs_y{year}m{month:02d}"
        from_date = f"{year}-{month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"
        partitions.append((name, from_date, to_date))
    return partitions


def _create_partition(name: str, from_date: str, to_date: str) -> None:
    """Create a single range partition if it does not already exist."""
    # Use to_regclass so the statement is idempotent — safe to re-run.
    op.execute(f"""
        DO $$
        BEGIN
            IF to_regclass('{name}') IS NULL THEN
                EXECUTE 'CREATE TABLE {name}
                    PARTITION OF activity_logs
                    FOR VALUES FROM (''{from_date}'') TO (''{to_date}'')';
            END IF;
        END
        $$;
    """)


def _drop_partition(name: str) -> None:
    """Detach and drop a partition if it exists (used in downgrade)."""
    op.execute(f"""
        DO $$
        BEGIN
            IF to_regclass('{name}') IS NOT NULL THEN
                EXECUTE 'ALTER TABLE activity_logs DETACH PARTITION {name}';
                EXECUTE 'DROP TABLE IF EXISTS {name}';
            END IF;
        END
        $$;
    """)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade():
    """Create 2026 + 2027 monthly partitions and a DEFAULT catch-all partition."""

    # 1. Monthly partitions for 2026 and 2027
    for year in (2026, 2027):
        for name, from_date, to_date in _monthly_partitions(year):
            _create_partition(name, from_date, to_date)

    # 2. DEFAULT partition — catches any row that doesn't match a range partition.
    #    This prevents hard failures if we ever run out of range partitions again.
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('activity_logs_default') IS NULL THEN
                CREATE TABLE activity_logs_default
                    PARTITION OF activity_logs DEFAULT;
            END IF;
        END
        $$;
    """)


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade():
    """Remove the DEFAULT partition and 2026/2027 range partitions.

    NOTE: downgrade will fail if any of these partitions contain rows.
    Detach the partition and migrate data before downgrading.
    """

    # Remove DEFAULT first (it may hold overflow rows — warn in logs)
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('activity_logs_default') IS NOT NULL THEN
                ALTER TABLE activity_logs DETACH PARTITION activity_logs_default;
                DROP TABLE IF EXISTS activity_logs_default;
            END IF;
        END
        $$;
    """)

    # Remove 2027 then 2026 monthly partitions (reverse order, safe)
    for year in (2027, 2026):
        for name, _, _ in reversed(_monthly_partitions(year)):
            _drop_partition(name)
