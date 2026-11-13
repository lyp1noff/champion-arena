"""drop tournaments.export_last_updated_at

The PDF export is rendered on every request and streamed to the client, so the
old "regenerate only if changed" timestamp is no longer read anywhere.

Revision ID: 3c5e7a9b1d24
Revises: a91c4e7f2b10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3c5e7a9b1d24"
down_revision: str | None = "a91c4e7f2b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("tournaments", "export_last_updated_at")


def downgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("export_last_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
