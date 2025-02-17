from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import Bracket
from src.schemas import BracketCreate


async def get_all_brackets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bracket))
    return result.scalars().all()


async def get_bracket_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bracket).filter(Bracket.id == id))
    bracket = result.scalars().first()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")
    return bracket


async def create_bracket(bracket: BracketCreate, db: AsyncSession = Depends(get_db)):
    new_bracket = Bracket(**bracket.model_dump())
    db.add(new_bracket)
    await db.commit()
    await db.refresh(new_bracket)
    return new_bracket
