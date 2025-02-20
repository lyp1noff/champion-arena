from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import AthleteResponse, AthleteCreate, PaginatedAthletesResponse
from src.database import get_db
from src.athletes.crud import (
    create_athlete as crud_create_athlete,
    get_paginated_athletes as crud_get_paginated_athletes,
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
    return await crud_get_paginated_athletes(page, limit, order_by, order, db)


# @router.get("/athletes", response_model=list[AthleteResponse])
# async def get_athletes(db: AsyncSession = Depends(get_db)):
#     return await crud_get_all_athletes(db=db)


@router.get("/athletes/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):
    return await crud_get_athlete_by_id(db=db, id=id)

@router.post("/athletes", response_model=AthleteResponse)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_athlete(db=db, athlete = athlete)
