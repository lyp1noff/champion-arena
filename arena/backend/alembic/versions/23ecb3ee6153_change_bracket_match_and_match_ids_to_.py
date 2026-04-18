"""change_bracket_match_and_match_ids_to_uuid

Revision ID: 23ecb3ee6153
Revises: 1a29e2a0467e
Create Date: 2025-08-01 23:51:55.242688

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23ecb3ee6153"
down_revision: Union[str, None] = "1a29e2a0467e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add new UUID columns to matches table
    op.add_column("matches", sa.Column("id_new", postgresql.UUID(as_uuid=True), nullable=True))

    # Step 2: Generate UUIDs for existing matches
    connection = op.get_bind()
    matches = connection.execute(sa.text("SELECT id FROM matches")).fetchall()

    for match_row in matches:
        old_id = match_row[0]
        new_uuid = str(uuid.uuid4())
        connection.execute(
            sa.text("UPDATE matches SET id_new = :new_uuid WHERE id = :old_id"),
            {"new_uuid": new_uuid, "old_id": old_id},
        )

    # Step 3: Add new UUID column to bracket_matches table
    op.add_column("bracket_matches", sa.Column("id_new", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("bracket_matches", sa.Column("match_id_new", postgresql.UUID(as_uuid=True), nullable=True))

    # Step 4: Generate UUIDs for existing bracket_matches and update match_id references
    bracket_matches = connection.execute(sa.text("SELECT id, match_id FROM bracket_matches")).fetchall()

    # Create a mapping of old match IDs to new UUIDs
    match_id_mapping = {}
    matches_with_new_ids = connection.execute(sa.text("SELECT id, id_new FROM matches")).fetchall()
    for match_row in matches_with_new_ids:
        old_id = match_row[0]
        new_uuid = match_row[1]
        match_id_mapping[old_id] = new_uuid

    for bracket_match_row in bracket_matches:
        old_id = bracket_match_row[0]
        old_match_id = bracket_match_row[1]
        new_uuid = str(uuid.uuid4())
        new_match_uuid = match_id_mapping.get(old_match_id)

        connection.execute(
            sa.text("UPDATE bracket_matches SET id_new = :new_uuid, match_id_new = :new_match_uuid WHERE id = :old_id"),
            {"new_uuid": new_uuid, "new_match_uuid": new_match_uuid, "old_id": old_id},
        )

    # Step 5: Drop foreign key constraints
    op.drop_constraint("bracket_matches_match_id_fkey", "bracket_matches", type_="foreignkey")

    # Step 6: Drop old columns and rename new ones
    # For matches table
    op.drop_column("matches", "id")
    op.alter_column("matches", "id_new", new_column_name="id")
    op.create_primary_key("matches_pkey", "matches", ["id"])
    op.create_index("ix_matches_id", "matches", ["id"])

    # For bracket_matches table
    op.drop_column("bracket_matches", "id")
    op.drop_column("bracket_matches", "match_id")
    op.alter_column("bracket_matches", "id_new", new_column_name="id")
    op.alter_column("bracket_matches", "match_id_new", new_column_name="match_id")
    op.create_primary_key("bracket_matches_pkey", "bracket_matches", ["id"])
    op.create_index("ix_bracket_matches_id", "bracket_matches", ["id"])
    op.create_index("ix_bracket_matches_match_id", "bracket_matches", ["match_id"])

    # Step 7: Recreate foreign key constraint
    op.create_foreign_key(
        "bracket_matches_match_id_fkey", "bracket_matches", "matches", ["match_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # This downgrade is complex and would require recreating integer IDs
    # For safety, we'll raise an error indicating manual intervention is needed
    raise Exception(
        "Downgrade from UUID to integer IDs requires manual intervention. "
        "Please restore from backup or implement custom downgrade logic."
    )
