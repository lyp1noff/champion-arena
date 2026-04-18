"""add timetable entries

Revision ID: f1b2c3d4e5f6
Revises: ee60f1efb4bd
Create Date: 2026-02-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, None] = "ee60f1efb4bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "timetable_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tournament_id", sa.Integer(), sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bracket_id", sa.Integer(), sa.ForeignKey("brackets.id", ondelete="CASCADE"), nullable=True),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("tatami", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("end_time >= start_time", name="check_timetable_end_time"),
        sa.UniqueConstraint("bracket_id", name="uix_timetable_bracket_id"),
    )
    op.create_index("ix_timetable_entries_tournament_id", "timetable_entries", ["tournament_id"], unique=False)
    op.create_index(
        "ix_timetable_entries_tournament_day_tatami_time",
        "timetable_entries",
        ["tournament_id", "day", "tatami", "start_time"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO timetable_entries
            (tournament_id, bracket_id, entry_type, title, notes, day, tatami, start_time, end_time, order_index)
        SELECT
            b.tournament_id,
            b.id,
            'bracket',
            NULL,
            NULL,
            b.day,
            b.tatami,
            b.start_time,
            b.start_time,
            ROW_NUMBER() OVER (
                PARTITION BY b.tournament_id, b.day, b.tatami
                ORDER BY b.start_time, b.id
            )
        FROM brackets b
        """
    )

    op.drop_column("brackets", "start_time")
    op.drop_column("brackets", "day")
    op.drop_column("brackets", "tatami")


def downgrade() -> None:
    op.add_column("brackets", sa.Column("tatami", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("day", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("start_time", sa.Time(), nullable=True))

    op.execute(
        """
        UPDATE brackets b
        SET
            tatami = t.tatami,
            day = t.day,
            start_time = t.start_time
        FROM timetable_entries t
        WHERE t.bracket_id = b.id
        """
    )

    op.execute("UPDATE brackets SET day = 1 WHERE day IS NULL")

    op.alter_column("brackets", "day", nullable=False)
    op.alter_column("brackets", "tatami", nullable=False)

    op.drop_index("ix_timetable_entries_tournament_day_tatami_time", table_name="timetable_entries")
    op.drop_index("ix_timetable_entries_tournament_id", table_name="timetable_entries")
    op.drop_table("timetable_entries")
