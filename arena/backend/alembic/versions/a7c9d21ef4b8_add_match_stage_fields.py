"""add match stage fields

Revision ID: a7c9d21ef4b8
Revises: f1b2c3d4e5f6
Create Date: 2026-02-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c9d21ef4b8"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("stage", sa.String(length=20), nullable=True))
    op.add_column("matches", sa.Column("repechage_side", sa.String(length=1), nullable=True))
    op.add_column("matches", sa.Column("repechage_step", sa.Integer(), nullable=True))

    op.execute("UPDATE matches SET stage = 'main' WHERE stage IS NULL")
    op.execute(
        """
        UPDATE matches
        SET
            stage = 'repechage',
            repechage_side = UPPER(split_part(round_type, '_', 2)),
            repechage_step = NULLIF(split_part(round_type, '_', 3), '')::integer
        WHERE round_type LIKE 'repechage_%'
        """
    )

    op.alter_column("matches", "stage", nullable=False)
    op.create_index(op.f("ix_matches_stage"), "matches", ["stage"], unique=False)
    op.create_index(op.f("ix_matches_repechage_side"), "matches", ["repechage_side"], unique=False)
    op.create_index(op.f("ix_matches_repechage_step"), "matches", ["repechage_step"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_matches_repechage_step"), table_name="matches")
    op.drop_index(op.f("ix_matches_repechage_side"), table_name="matches")
    op.drop_index(op.f("ix_matches_stage"), table_name="matches")
    op.drop_column("matches", "repechage_step")
    op.drop_column("matches", "repechage_side")
    op.drop_column("matches", "stage")
