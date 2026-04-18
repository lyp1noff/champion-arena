"""default_sql_create_update_values

Revision ID: ba485a35aa38
Revises: 23ecb3ee6153
Create Date: 2025-08-09 18:41:13.408653

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba485a35aa38"
down_revision: Union[str, None] = "23ecb3ee6153"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES_WITH_TIMESTAMPS = [
    "users",
    "athletes",
    "coaches",
    "categories",
    "tournaments",
    "applications",
    "brackets",
    "matches",
    "athlete_coach_links",
]


def upgrade() -> None:
    op.alter_column(
        "bracket_matches",
        "match_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    for t in TABLES_WITH_TIMESTAMPS:
        op.alter_column(
            t,
            "created_at",
            server_default=sa.text("now()"),
            existing_type=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )
        op.alter_column(
            t,
            "updated_at",
            server_default=sa.text("now()"),
            existing_type=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          NEW.updated_at := now();
          RETURN NEW;
        END;
        $$;
        """
    )

    for t in TABLES_WITH_TIMESTAMPS:
        op.execute(
            f"""
            DROP TRIGGER IF EXISTS trg_{t}_updated_at ON {t};
            CREATE TRIGGER trg_{t}_updated_at
            BEFORE UPDATE ON {t}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
            """
        )


def downgrade() -> None:
    op.alter_column(
        "bracket_matches",
        "match_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    for t in TABLES_WITH_TIMESTAMPS:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{t}_updated_at ON {t};")

    for t in TABLES_WITH_TIMESTAMPS:
        op.alter_column(
            t,
            "created_at",
            server_default=None,
            existing_type=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )
        op.alter_column(
            t,
            "updated_at",
            server_default=None,
            existing_type=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )

    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
