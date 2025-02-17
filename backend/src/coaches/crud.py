from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import Coach
from src.schemas import CoachCreate


async def get_all_coaches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach))
    return result.scalars().all()


async def get_coach_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach).filter(Coach.id == id))
    coach = result.scalars().first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach


async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    new_coach = Coach(**coach.model_dump())
    db.add(new_coach)
    await db.commit()
    await db.refresh(new_coach)
    return new_coach
