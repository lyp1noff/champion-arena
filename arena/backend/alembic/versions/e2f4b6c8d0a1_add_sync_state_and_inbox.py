"""add sync state and inbox

Revision ID: e2f4b6c8d0a1
Revises: c1a2b3c4d5e6
Create Date: 2026-02-03 15:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f4b6c8d0a1"
down_revision: str | None = "c1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("brackets", sa.Column("state", sa.String(length=20), nullable=True))
    op.add_column("brackets", sa.Column("version", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE brackets
        SET state = CASE
            WHEN status = 'finished' THEN 'finished'
            WHEN status = 'started' THEN 'running'
            ELSE 'draft'
        END
        """
    )
    op.execute("UPDATE brackets SET version = 1 WHERE version IS NULL")

    op.alter_column("brackets", "state", nullable=False, server_default="draft")
    op.alter_column("brackets", "version", nullable=False, server_default="1")
    op.create_index(op.f("ix_brackets_state"), "brackets", ["state"], unique=False)

    op.create_table(
        "sync_inbox_events",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("edge_id", sa.String(length=100), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint("edge_id", "seq", name="uix_sync_inbox_edge_seq"),
    )
    op.create_index(op.f("ix_sync_inbox_events_edge_id"), "sync_inbox_events", ["edge_id"], unique=False)
    op.create_index(op.f("ix_sync_inbox_events_seq"), "sync_inbox_events", ["seq"], unique=False)

    op.create_table(
        "sync_edge_state",
        sa.Column("edge_id", sa.String(length=100), nullable=False),
        sa.Column("last_applied_seq", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("edge_id"),
    )


def downgrade() -> None:
    op.drop_table("sync_edge_state")
    op.drop_index(op.f("ix_sync_inbox_events_seq"), table_name="sync_inbox_events")
    op.drop_index(op.f("ix_sync_inbox_events_edge_id"), table_name="sync_inbox_events")
    op.drop_table("sync_inbox_events")

    op.drop_index(op.f("ix_brackets_state"), table_name="brackets")
    op.drop_column("brackets", "version")
    op.drop_column("brackets", "state")
