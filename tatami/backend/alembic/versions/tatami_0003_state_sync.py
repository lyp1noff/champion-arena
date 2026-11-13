"""Replace the outbox queue with per-bracket sync state.

A bracket is "dirty" while version > synced_version; the sync worker sends the
current snapshot of dirty brackets. Brackets of tournaments that still had
undelivered outbox items are marked dirty so their latest state is re-sent once
after the upgrade. Dead letters are not: Arena already rejected them and the old
worker never retried them, so re-sending could overwrite a past tournament.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "tatami_0003"
down_revision: str | None = "tatami_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("brackets", sa.Column("synced_version", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("brackets", sa.Column("sync_error", sa.Text(), nullable=True))
    op.add_column("brackets", sa.Column("sync_blocked_version", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("sync_remote_version", sa.Integer(), nullable=True))

    op.execute("UPDATE brackets SET synced_version = version")
    op.execute("""
        UPDATE brackets SET synced_version = NULL
        WHERE tournament_id IN (
            SELECT DISTINCT tournament_id FROM outbox_items
            WHERE status IN ('pending', 'processing', 'retry_wait') AND tournament_id IS NOT NULL
        )
        """)

    op.drop_table("outbox_items")
    op.drop_table("outbox_worker_state")
    op.create_table(
        "sync_worker_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False, server_default="starting"),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "phase IN ('starting', 'idle', 'sending', 'offline', 'stopped')",
            name="ck_sync_worker_phase",
        ),
    )


def downgrade() -> None:
    op.drop_table("sync_worker_state")
    op.create_table(
        "outbox_worker_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False, server_default="starting"),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("circuit_open_until", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "phase IN ('starting', 'idle', 'working', 'offline_wait', 'stopped')",
            name="ck_outbox_worker_phase",
        ),
    )
    op.create_table(
        "outbox_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tournament_id", sa.Integer(), sa.ForeignKey("tournaments.id"), nullable=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("failure_kind", sa.String(50), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'retry_wait', 'success', 'dead_letter')",
            name="ck_outbox_items_status",
        ),
    )
    op.create_index("ix_outbox_items_id", "outbox_items", ["id"])
    op.create_index("ix_outbox_items_delivery", "outbox_items", ["status", "next_attempt_at", "created_at"])
    for column in ("sync_remote_version", "sync_blocked_version", "sync_error", "synced_at", "synced_version"):
        op.drop_column("brackets", column)
