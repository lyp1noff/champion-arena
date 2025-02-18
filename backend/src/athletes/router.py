from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Athlete
from src.schemas import AthleteResponse, AthleteCreate, PaginatedAthletesResponse
from src.database import get_db
from src.athletes.crud import (
    create_athlete as crud_create_athlete,
    get_all_athletes as crud_get_all_athletes,
    get_athlete_by_id as crud_get_athlete_by_id,
)

router = APIRouter()

@router.get("/athletes", response_model=PaginatedAthletesResponse)
async def get_athletes(
    page: int = Query(1, alias="page", ge=1),
    limit: int = Query(10, alias="limit", ge=1, le=100),
    order_by: str = Query("id", alias="order_by"),
    order: str = Query("asc", alias="order"),
    db: AsyncSession = Depends(get_db),
):
    valid_order_fields = {"id", "last_name", "first_name", "gender", "birth_date", "coach_id"}
    
    if order_by not in valid_order_fields:
        order_by = "id"
    
    order_column = getattr(Athlete, order_by)
    if order.lower() == "desc":
        order_column = desc(order_column)
    else:
        order_column = asc(order_column)

    offset = (page - 1) * limit

    async with db as session:
        total_query = await session.execute(select(Athlete))
        total = len(total_query.scalars().all())

        result = await session.execute(
            select(Athlete).order_by(order_column).offset(offset).limit(limit)
        )
        athletes = result.scalars().all()

    return {
        "data": athletes,
        "total": total,
        "page": page,
        "limit": limit,
    }

# @router.get("/athletes", response_model=list[AthleteResponse])
# async def get_athletes(db: AsyncSession = Depends(get_db)):
#     return await crud_get_all_athletes(db=db)


@router.get("/athletes/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):
    return await crud_get_athlete_by_id(db=db, id=id)

@router.post("/athletes", response_model=AthleteResponse)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_athlete(db=db, athlete = athlete)
