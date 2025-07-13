"""athlete coach m2m migration

Revision ID: c753b78a5a9a
Revises: 5dd76feba4cb
Create Date: 2025-07-10 23:35:21.535097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c753b78a5a9a'
down_revision: Union[str, None] = '5dd76feba4cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. создать таблицу athlete_coach_links
    op.create_table(
        'athlete_coach_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('athlete_id', sa.Integer(), nullable=False),
        sa.Column('coach_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('athlete_id', 'coach_id', name='uix_athlete_coach'),
        sa.ForeignKeyConstraint(['athlete_id'], ['athletes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ondelete='CASCADE')
    )

    # 2. скопировать данные из старого столбца coach_id
    op.execute("""
               INSERT INTO athlete_coach_links (athlete_id, coach_id)
               SELECT id, coach_id
               FROM athletes
               WHERE coach_id IS NOT NULL
               """)

    # 3. удалить столбец coach_id из таблицы athletes
    op.drop_column('athletes', 'coach_id')


def downgrade():
    # 1. добавить обратно coach_id
    op.add_column('athletes', sa.Column(
        'coach_id',
        sa.Integer(),
        sa.ForeignKey('coaches.id', ondelete='SET NULL'),
        nullable=True
    ))

    # 2. вернуть данные из связей обратно в coach_id
    op.execute("""
               UPDATE athletes
               SET coach_id = sub.coach_id FROM (
            SELECT athlete_id, coach_id
            FROM athlete_coach_links
            GROUP BY athlete_id, coach_id
        ) AS sub
               WHERE athletes.id = sub.athlete_id
               """)

    # 3. удалить таблицу связей
    op.drop_table('athlete_coach_links')
