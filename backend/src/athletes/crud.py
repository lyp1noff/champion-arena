from sqlalchemy import select, asc, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import Athlete
from src.schemas import AthleteCreate


async def get_paginated_athletes(page: int, limit: int, order_by: str, order: str, db: AsyncSession):
    valid_order_fields = {"id", "last_name", "first_name", "gender", "birth_date", "coach_id"}
    
    if order_by not in valid_order_fields:
        order_by = "id"
    
    order_column = getattr(Athlete, order_by)
    if order.lower() == "desc":
        order_column = desc(order_column)
    else:
        order_column = asc(order_column)

    offset = (page - 1) * limit

    total_query = await db.execute(select(Athlete))
    total = len(total_query.scalars().all())

    result = await db.execute(
        select(Athlete)
        .options(joinedload(Athlete.coach))
        .order_by(order_column)
        .offset(offset)
        .limit(limit)
    )
    athletes = result.scalars().all()

    for athlete in athletes:
        athlete.coach_last_name = athlete.coach.last_name if athlete.coach else None

    return {
        "data": athletes,
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_all_athletes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).options(joinedload(Athlete.coach)))
    athletes = result.scalars().all()

    for athlete in athletes:
        athlete.coach_last_name = athlete.coach.last_name if athlete.coach else None

    return athletes


async def get_athlete_by_id(id: int, db: AsyncSession):
    result = await db.execute(
        select(Athlete)
        .options(joinedload(Athlete.coach))
        .filter(Athlete.id == id)
    )
    athlete = result.scalars().first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    athlete.coach_last_name = athlete.coach.last_name if athlete.coach else None

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
