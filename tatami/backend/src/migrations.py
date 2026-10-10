from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

OUTBOX_MIGRATION_VERSION = 1
OUTBOX_MIGRATION_LOCK_ID = 2_026_101_001


async def migrate_outbox_schema(connection: AsyncConnection) -> None:
    """Apply Tatami-local migrations once while prepare_database holds the schema lock."""
    migration_table_sql = """
        CREATE TABLE IF NOT EXISTS tatami_schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """
    await connection.execute(text(migration_table_sql))
    applied = await connection.scalar(
        text("SELECT 1 FROM tatami_schema_migrations WHERE version = :version"),
        {"version": OUTBOX_MIGRATION_VERSION},
    )
    if applied:
        return

    statements = (
        "ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS failure_kind VARCHAR(50)",
        "ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ",
        "ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ",
        "ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ",
        "ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ",
        "CREATE INDEX IF NOT EXISTS ix_outbox_items_delivery ON outbox_items (status, next_attempt_at, created_at)",
        "UPDATE outbox_items SET status = 'retry_wait' WHERE status = 'failed'",
        "UPDATE outbox_items SET status = 'dead_letter' WHERE status = 'skipped'",
        """
        UPDATE outbox_items
        SET status = 'retry_wait', next_attempt_at = NOW()
        WHERE status = 'processing' AND lease_until IS NULL
        """,
        "ALTER TABLE outbox_items DROP COLUMN IF EXISTS max_retries",
        "ALTER TABLE outbox_items DROP COLUMN IF EXISTS endpoint",
        "ALTER TABLE outbox_items DROP COLUMN IF EXISTS method",
    )
    for statement in statements:
        await connection.execute(text(statement))
    await connection.execute(
        text("INSERT INTO tatami_schema_migrations (version) VALUES (:version)"),
        {"version": OUTBOX_MIGRATION_VERSION},
    )
