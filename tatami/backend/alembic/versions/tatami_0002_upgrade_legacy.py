"""Upgrade legacy and pre-Alembic Tatami databases."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "tatami_0002"
down_revision: str | None = "tatami_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # LEGACY_OUTBOX_SCHEMA: idempotent because nodes may already have run the
    # temporary startup migrator introduced with the Python worker.
    op.execute("ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS failure_kind VARCHAR(50)")
    op.execute("ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ")
    op.execute("ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ")
    op.execute("ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ")
    op.execute("ALTER TABLE outbox_items ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_outbox_items_delivery ON outbox_items (status, next_attempt_at, created_at)")
    op.execute("UPDATE outbox_items SET status = 'retry_wait' WHERE status IN ('failed', 'processing')")
    op.execute("UPDATE outbox_items SET status = 'dead_letter' WHERE status = 'skipped'")
    op.execute("ALTER TABLE outbox_items DROP COLUMN IF EXISTS max_retries")
    op.execute("ALTER TABLE outbox_items DROP COLUMN IF EXISTS endpoint")
    op.execute("ALTER TABLE outbox_items DROP COLUMN IF EXISTS method")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox_worker_state (
            id INTEGER PRIMARY KEY,
            heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            phase VARCHAR(30) NOT NULL DEFAULT 'starting',
            last_success_at TIMESTAMPTZ,
            last_error TEXT,
            circuit_open_until TIMESTAMPTZ
        )
        """
    )
    # LEGACY_WORKER_STATUS_COLUMN: the first Python worker called this status.
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox_worker_state' AND column_name = 'status'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox_worker_state' AND column_name = 'phase'
            ) THEN
                ALTER TABLE outbox_worker_state RENAME COLUMN status TO phase;
            END IF;
        END $$
        """
    )

    # LEGACY_BRACKET_STATE: promote meaningful state values, then remove the
    # duplicate lifecycle column. Old queued JSON is handled separately by DTO.
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'brackets' AND column_name = 'state'
            ) THEN
                UPDATE brackets
                SET status = CASE
                    WHEN status = 'finished' OR state = 'finished' THEN 'finished'
                    WHEN status = 'started' OR state = 'running' THEN 'started'
                    ELSE 'pending'
                END;
                ALTER TABLE brackets DROP COLUMN state;
            END IF;
        END $$
        """
    )
    op.execute("DROP TABLE IF EXISTS match_states")
    op.execute("DROP TABLE IF EXISTS tatami_schema_migrations")

    op.execute("UPDATE tournaments SET status = 'draft' WHERE status NOT IN ('draft', 'upcoming', 'started', 'finished')")
    op.execute("UPDATE brackets SET status = 'pending' WHERE status IS NULL OR status NOT IN ('pending', 'started', 'finished')")
    op.execute("UPDATE matches SET status = 'not_started' WHERE status NOT IN ('not_started', 'started', 'finished')")
    op.execute("UPDATE outbox_items SET status = 'dead_letter' WHERE status NOT IN ('pending', 'processing', 'retry_wait', 'success', 'dead_letter')")
    op.execute("UPDATE outbox_worker_state SET phase = 'starting' WHERE phase NOT IN ('starting', 'idle', 'working', 'offline_wait', 'stopped')")

    constraints = (
        ("tournaments", "ck_tournaments_status", "status IN ('draft', 'upcoming', 'started', 'finished')"),
        ("brackets", "ck_brackets_status", "status IN ('pending', 'started', 'finished')"),
        ("matches", "ck_matches_status", "status IN ('not_started', 'started', 'finished')"),
        (
            "outbox_items",
            "ck_outbox_items_status",
            "status IN ('pending', 'processing', 'retry_wait', 'success', 'dead_letter')",
        ),
        (
            "outbox_worker_state",
            "ck_outbox_worker_phase",
            "phase IN ('starting', 'idle', 'working', 'offline_wait', 'stopped')",
        ),
    )
    for table, name, expression in constraints:
        op.execute(
            f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
                    ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression});
                END IF;
            END $$
            """
        )


def downgrade() -> None:
    for table, name in (
        ("outbox_worker_state", "ck_outbox_worker_phase"),
        ("outbox_items", "ck_outbox_items_status"),
        ("matches", "ck_matches_status"),
        ("brackets", "ck_brackets_status"),
        ("tournaments", "ck_tournaments_status"),
    ):
        op.drop_constraint(name, table, type_="check")
    op.add_column("brackets", sa.Column("state", sa.String(), nullable=True))
    op.execute("UPDATE brackets SET state = CASE WHEN status = 'finished' THEN 'finished' WHEN status = 'started' THEN 'running' ELSE 'draft' END")
    op.alter_column("brackets", "state", nullable=False)
