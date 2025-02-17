from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import BracketParticipant
from src.schemas import BracketParticipantCreate


async def get_participants_by_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BracketParticipant).filter(BracketParticipant.bracket_id == bracket_id))
    return result.scalars().all()


async def create_bracket_participant(participant: BracketParticipantCreate, db: AsyncSession = Depends(get_db)):
    new_participant = BracketParticipant(**participant.model_dump())
    db.add(new_participant)
    await db.commit()
    await db.refresh(new_participant)
    return new_participant
