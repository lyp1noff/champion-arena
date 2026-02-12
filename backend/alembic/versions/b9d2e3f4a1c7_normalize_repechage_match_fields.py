"""normalize repechage match fields

Revision ID: b9d2e3f4a1c7
Revises: a7c9d21ef4b8
Create Date: 2026-02-02 00:00:01.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b9d2e3f4a1c7"
down_revision = "a7c9d21ef4b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE matches SET stage = 'main' WHERE stage IS NULL")

    op.execute(
        """
        UPDATE matches
        SET
            stage = 'repechage',
            repechage_side = UPPER(split_part(lower(round_type), '_', 2)),
            repechage_step = CASE
                WHEN split_part(lower(round_type), '_', 3) ~ '^[0-9]+$'
                THEN split_part(lower(round_type), '_', 3)::integer
                ELSE NULL
            END
        WHERE lower(round_type) LIKE 'repechage_%'
        """
    )

    op.execute(
        """
        UPDATE matches
        SET
            repechage_side = NULL,
            repechage_step = NULL
        WHERE stage <> 'repechage'
        """
    )


def downgrade() -> None:
    # Data normalization only; no safe automatic downgrade needed.
    pass
