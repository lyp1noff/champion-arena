"""drop seq uniqueness from sync inbox

Revision ID: 8f2e4a1b6c9d
Revises: 17c7c9f7d1ab
Create Date: 2026-04-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f2e4a1b6c9d"
down_revision: Union[str, None] = "17c7c9f7d1ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uix_sync_inbox_edge_tournament_seq", "sync_inbox_events", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uix_sync_inbox_edge_tournament_seq",
        "sync_inbox_events",
        ["edge_id", "tournament_id", "seq"],
    )
