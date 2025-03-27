from sqlalchemy import delete
from sqlalchemy.future import select
from src.models import BracketParticipant, BracketMatch
from sqlalchemy.ext.asyncio import AsyncSession


async def regenerate_bracket_matches(session: AsyncSession, bracket_id: int):
    await session.execute(
        delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id)
    )

    result = await session.execute(
        select(BracketParticipant)
        .filter_by(bracket_id=bracket_id)
        .order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()
    athlete_ids = [p.athlete_id for p in participants if p.athlete_id is not None]

    if len(athlete_ids) % 2 != 0:
        athlete_ids.append(None)

    for i in range(0, len(athlete_ids), 2):
        match = BracketMatch(
            bracket_id=bracket_id,
            round_number=1,
            position=(i // 2) + 1,
            athlete1_id=athlete_ids[i],
            athlete2_id=athlete_ids[i + 1] if i + 1 < len(athlete_ids) else None,
        )
        session.add(match)

    await session.commit()
