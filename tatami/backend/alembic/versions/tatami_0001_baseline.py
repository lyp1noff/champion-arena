"""Frozen schema baseline for new Tatami databases."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "tatami_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'upcoming', 'started', 'finished')", name="ck_tournaments_status"),
    )
    op.create_index("ix_tournaments_id", "tournaments", ["id"])

    op.create_table(
        "athletes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("coaches_last_name", sa.String(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_athletes_id", "athletes", ["id"])

    op.create_table(
        "global_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("value", sa.String(), nullable=True),
    )
    op.create_index("ix_global_settings_id", "global_settings", ["id"])

    op.create_table(
        "brackets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("tournament_id", sa.Integer(), sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("display_name", sa.String(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IS NULL OR status IN ('pending', 'started', 'finished')", name="ck_brackets_status"),
    )
    op.create_index("ix_brackets_id", "brackets", ["id"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(), nullable=False, unique=True),
        sa.Column("athlete1_id", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("athlete2_id", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("winner_id", sa.Integer(), nullable=True),
        sa.Column("score_athlete1", sa.Integer(), nullable=True),
        sa.Column("score_athlete2", sa.Integer(), nullable=True),
        sa.Column("round_type", sa.String(), nullable=True),
        sa.Column("stage", sa.String(), nullable=False, server_default="main"),
        sa.Column("repechage_side", sa.String(), nullable=True),
        sa.Column("repechage_step", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="not_started"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('not_started', 'started', 'finished')", name="ck_matches_status"),
    )
    op.create_index("ix_matches_id", "matches", ["id"])

    op.create_table(
        "timetable_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tournament_id", sa.Integer(), sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bracket_id", sa.Integer(), sa.ForeignKey("brackets.id", ondelete="CASCADE"), nullable=True),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("tatami", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("bracket_id", name="uix_timetable_bracket_id"),
    )
    op.create_index("ix_timetable_entries_id", "timetable_entries", ["id"])
    op.create_index("ix_timetable_entries_tournament_id", "timetable_entries", ["tournament_id"])
    op.create_index("ix_timetable_entries_bracket_id", "timetable_entries", ["bracket_id"])

    op.create_table(
        "bracket_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(), nullable=False, unique=True),
        sa.Column("bracket_id", sa.Integer(), sa.ForeignKey("brackets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("next_slot", sa.Integer(), nullable=True),
    )
    op.create_index("ix_bracket_matches_id", "bracket_matches", ["id"])

    op.create_table(
        "bracket_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bracket_id", sa.Integer(), sa.ForeignKey("brackets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("athlete_id", sa.Integer(), sa.ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=False),
    )
    op.create_index("ix_bracket_participants_id", "bracket_participants", ["id"])
    op.create_index("ix_bracket_participants_bracket_id", "bracket_participants", ["bracket_id"])
    op.create_index("ix_bracket_participants_athlete_id", "bracket_participants", ["athlete_id"])

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
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'retry_wait', 'success', 'dead_letter')",
            name="ck_outbox_items_status",
        ),
    )
    op.create_index("ix_outbox_items_id", "outbox_items", ["id"])
    op.create_index("ix_outbox_items_delivery", "outbox_items", ["status", "next_attempt_at", "created_at"])

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


def downgrade() -> None:
    for table in (
        "outbox_worker_state",
        "outbox_items",
        "bracket_participants",
        "bracket_matches",
        "timetable_entries",
        "matches",
        "brackets",
        "global_settings",
        "athletes",
        "tournaments",
    ):
        op.drop_table(table)
