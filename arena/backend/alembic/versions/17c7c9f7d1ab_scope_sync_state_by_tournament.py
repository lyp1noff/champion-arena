"""scope sync state by tournament

Revision ID: 17c7c9f7d1ab
Revises: e2f4b6c8d0a1
Create Date: 2026-04-18 16:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17c7c9f7d1ab"
down_revision: str | None = "e2f4b6c8d0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Old sync rows are operational metadata only and are not safe to map across tournaments.
    op.drop_table("sync_edge_state")
    op.drop_index(op.f("ix_sync_inbox_events_seq"), table_name="sync_inbox_events")
    op.drop_index(op.f("ix_sync_inbox_events_edge_id"), table_name="sync_inbox_events")
    op.drop_table("sync_inbox_events")

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
        sa.UniqueConstraint("edge_id", "tournament_id", "seq", name="uix_sync_inbox_edge_tournament_seq"),
    )
    op.create_index(op.f("ix_sync_inbox_events_edge_id"), "sync_inbox_events", ["edge_id"], unique=False)
    op.create_index(op.f("ix_sync_inbox_events_tournament_id"), "sync_inbox_events", ["tournament_id"], unique=False)
    op.create_index(op.f("ix_sync_inbox_events_seq"), "sync_inbox_events", ["seq"], unique=False)

    op.create_table(
        "sync_edge_state",
        sa.Column("edge_id", sa.String(length=100), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("last_applied_seq", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("edge_id", "tournament_id"),
    )


def downgrade() -> None:
    op.drop_table("sync_edge_state")
    op.drop_index(op.f("ix_sync_inbox_events_seq"), table_name="sync_inbox_events")
    op.drop_index(op.f("ix_sync_inbox_events_tournament_id"), table_name="sync_inbox_events")
    op.drop_index(op.f("ix_sync_inbox_events_edge_id"), table_name="sync_inbox_events")
    op.drop_table("sync_inbox_events")

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
