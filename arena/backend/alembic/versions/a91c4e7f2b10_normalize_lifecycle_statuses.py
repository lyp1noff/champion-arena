"""normalize lifecycle statuses

Revision ID: a91c4e7f2b10
Revises: 8f2e4a1b6c9d
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a91c4e7f2b10"
down_revision: str | None = "8f2e4a1b6c9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # LEGACY_BRACKET_STATE: reconcile the only meaningful legacy values before
    # dropping the duplicate state machine. Remove this SQL after all DBs pass it.
    op.execute(
        """
        UPDATE brackets
        SET status = CASE
            WHEN status = 'finished' OR state = 'finished' THEN 'finished'
            WHEN status = 'started' OR state = 'running' THEN 'started'
            ELSE 'pending'
        END
        """
    )
    op.drop_index(op.f("ix_brackets_state"), table_name="brackets")
    op.drop_column("brackets", "state")

    # LEGACY_STATUS_VALUES: repair out-of-vocabulary values before enforcing
    # the canonical enums. Remove this compatibility once all databases pass.
    op.execute("UPDATE tournaments SET status = 'draft' WHERE status IS NULL OR status NOT IN ('draft', 'upcoming', 'started', 'finished')")
    op.execute("UPDATE applications SET status = 'pending' WHERE status IS NULL OR status NOT IN ('pending', 'approved', 'rejected')")
    op.execute("UPDATE brackets SET status = 'pending' WHERE status IS NULL OR status NOT IN ('pending', 'started', 'finished')")
    op.execute("UPDATE matches SET status = 'not_started' WHERE status IS NULL OR status NOT IN ('not_started', 'started', 'finished')")

    op.create_check_constraint(
        "ck_tournaments_status",
        "tournaments",
        "status IN ('draft', 'upcoming', 'started', 'finished')",
    )
    op.create_check_constraint(
        "ck_applications_status",
        "applications",
        "status IN ('pending', 'approved', 'rejected')",
    )
    op.create_check_constraint(
        "ck_brackets_status",
        "brackets",
        "status IN ('pending', 'started', 'finished')",
    )
    op.create_check_constraint(
        "ck_matches_status",
        "matches",
        "status IN ('not_started', 'started', 'finished')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_matches_status", "matches", type_="check")
    op.drop_constraint("ck_brackets_status", "brackets", type_="check")
    op.drop_constraint("ck_applications_status", "applications", type_="check")
    op.drop_constraint("ck_tournaments_status", "tournaments", type_="check")

    op.add_column("brackets", sa.Column("state", sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE brackets
        SET state = CASE
            WHEN status = 'finished' THEN 'finished'
            WHEN status = 'started' THEN 'running'
            ELSE 'draft'
        END
        """
    )
    op.alter_column("brackets", "state", nullable=False, server_default="draft")
    op.create_index(op.f("ix_brackets_state"), "brackets", ["state"], unique=False)
