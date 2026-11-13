"""drop sync inbox and edge state

Tatami now sends full bracket snapshots guarded by the bracket version, so the
per-event inbox (dedup by event_id) and per-edge sequence tracking are unused.

Revision ID: 5d7f9b1c3e46
Revises: 3c5e7a9b1d24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5d7f9b1c3e46"
down_revision: str | None = "3c5e7a9b1d24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("sync_inbox_events")
    op.drop_table("sync_edge_state")


def downgrade() -> None:
    op.create_table(
        "sync_edge_state",
        sa.Column("edge_id", sa.String(length=100), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("last_applied_seq", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("edge_id", "tournament_id"),
    )
    op.create_table(
        "sync_inbox_events",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("edge_id", sa.String(length=100), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_sync_inbox_events_edge_id", "sync_inbox_events", ["edge_id"])
    op.create_index("ix_sync_inbox_events_tournament_id", "sync_inbox_events", ["tournament_id"])
    op.create_index("ix_sync_inbox_events_seq", "sync_inbox_events", ["seq"])
