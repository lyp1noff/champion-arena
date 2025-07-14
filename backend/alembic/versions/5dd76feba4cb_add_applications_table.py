"""add applications table

Revision ID: 5dd76feba4cb
Revises: 6b3780a08ed7
Create Date: 2025-06-06 13:59:44.533780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5dd76feba4cb'
down_revision: Union[str, None] = '6b3780a08ed7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('athlete_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['athlete_id'], ['athletes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.UniqueConstraint(
            'athlete_id',
            'category_id',
            'tournament_id',
            name='uix_application_unique'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('applications')
