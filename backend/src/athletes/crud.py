from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import Athlete
from src.schemas import AthleteCreate


async def get_all_athletes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete))
    return result.scalars().all()


async def get_athlete_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


async def create_athlete(athlete: AthleteCreate, db: AsyncSession):
    try:
        new_athlete = Athlete(**athlete.model_dump())
        db.add(new_athlete)
        await db.commit()
        await db.refresh(new_athlete)
        return new_athlete

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid coach_id: coach does not exist")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
