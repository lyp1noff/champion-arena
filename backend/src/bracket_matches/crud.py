from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import BracketMatch
from src.schemas import BracketMatchCreate


async def get_matches_by_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BracketMatch).filter(BracketMatch.bracket_id == bracket_id))
    return result.scalars().all()


async def get_match_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BracketMatch).filter(BracketMatch.id == id))
    match = result.scalars().first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


async def create_bracket_match(match: BracketMatchCreate, db: AsyncSession = Depends(get_db)):
    new_match = BracketMatch(**match.model_dump())
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)
    return new_match
