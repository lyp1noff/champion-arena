from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import *
from models import *
from database import get_db


async def get_coaches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach))
    return result.scalars().all()


async def get_coach(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Coach).filter(Coach.id == id))
    coach = result.scalars().first()
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach


async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    new_coach = Coach(**coach.model_dump())
    db.add(new_coach)
    await db.commit()
    await db.refresh(new_coach)
    return new_coach


async def get_athletes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete))
    return result.scalars().all()


async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    new_athlete = Athlete(**athlete.model_dump())
    db.add(new_athlete)
    await db.commit()
    await db.refresh(new_athlete)
    return new_athlete


async def get_tournaments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament))
    return result.scalars().all()


async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    new_tournament = Tournament(**tournament.model_dump())
    db.add(new_tournament)
    await db.commit()
    await db.refresh(new_tournament)
    return new_tournament


async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()