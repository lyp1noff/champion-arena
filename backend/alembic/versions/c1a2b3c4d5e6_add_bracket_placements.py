"""add bracket placements

Revision ID: c1a2b3c4d5e6
Revises: b9d2e3f4a1c7
Create Date: 2026-02-02 15:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2b3c4d5e6"
down_revision: str | None = "b9d2e3f4a1c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("brackets", sa.Column("place_1_id", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("place_2_id", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("place_3_a_id", sa.Integer(), nullable=True))
    op.add_column("brackets", sa.Column("place_3_b_id", sa.Integer(), nullable=True))

    op.create_index(op.f("ix_brackets_place_1_id"), "brackets", ["place_1_id"], unique=False)
    op.create_index(op.f("ix_brackets_place_2_id"), "brackets", ["place_2_id"], unique=False)
    op.create_index(op.f("ix_brackets_place_3_a_id"), "brackets", ["place_3_a_id"], unique=False)
    op.create_index(op.f("ix_brackets_place_3_b_id"), "brackets", ["place_3_b_id"], unique=False)

    op.create_foreign_key(
        "fk_brackets_place_1_id_athletes",
        "brackets",
        "athletes",
        ["place_1_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_brackets_place_2_id_athletes",
        "brackets",
        "athletes",
        ["place_2_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_brackets_place_3_a_id_athletes",
        "brackets",
        "athletes",
        ["place_3_a_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_brackets_place_3_b_id_athletes",
        "brackets",
        "athletes",
        ["place_3_b_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_brackets_place_3_b_id_athletes", "brackets", type_="foreignkey")
    op.drop_constraint("fk_brackets_place_3_a_id_athletes", "brackets", type_="foreignkey")
    op.drop_constraint("fk_brackets_place_2_id_athletes", "brackets", type_="foreignkey")
    op.drop_constraint("fk_brackets_place_1_id_athletes", "brackets", type_="foreignkey")

    op.drop_index(op.f("ix_brackets_place_3_b_id"), table_name="brackets")
    op.drop_index(op.f("ix_brackets_place_3_a_id"), table_name="brackets")
    op.drop_index(op.f("ix_brackets_place_2_id"), table_name="brackets")
    op.drop_index(op.f("ix_brackets_place_1_id"), table_name="brackets")

    op.drop_column("brackets", "place_3_b_id")
    op.drop_column("brackets", "place_3_a_id")
    op.drop_column("brackets", "place_2_id")
    op.drop_column("brackets", "place_1_id")
