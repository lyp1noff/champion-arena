from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import Coach
from src.schemas import CoachCreate, CoachResponse

router = APIRouter(prefix="/coaches", tags=["Coaches"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[CoachResponse])
async def get_coaches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach))
    return result.scalars().all()


@router.get("/{id}", response_model=CoachResponse)
async def get_coach(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach).filter(Coach.id == id))
    coach = result.scalars().first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach


@router.post("", response_model=CoachResponse)
async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    new_coach = Coach(**coach.model_dump())
    db.add(new_coach)
    await db.commit()
    await db.refresh(new_coach)
    return new_coach
