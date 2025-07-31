"""add_tournament_bracket_match_status

Revision ID: 3ec4fbe1c99b
Revises: c94337081108
Create Date: 2025-07-30 16:24:06.121126

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3ec4fbe1c99b"
down_revision: Union[str, None] = "c94337081108"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("brackets", sa.Column("status", sa.String(length=20), nullable=True))
    op.execute("UPDATE brackets SET status = 'pending'")
    op.alter_column("brackets", "status", nullable=False)
    op.add_column("matches", sa.Column("status", sa.String(length=20), nullable=True))
    op.execute("UPDATE matches SET status = 'not_started'")
    op.alter_column("matches", "status", nullable=False)
    op.add_column(
        "matches", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "matches", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.drop_column("matches", "is_finished")
    op.add_column(
        "tournaments", sa.Column("status", sa.String(length=20), nullable=True)
    )
    op.execute("UPDATE tournaments SET status = 'draft'")
    op.alter_column("tournaments", "status", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tournaments", "status")
    op.add_column("matches", sa.Column("is_finished", sa.BOOLEAN(), nullable=True))
    op.drop_column("matches", "ended_at")
    op.drop_column("matches", "started_at")
    op.drop_column("matches", "status")
    op.drop_column("brackets", "status")
