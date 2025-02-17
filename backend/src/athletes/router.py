from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import AthleteResponse, AthleteCreate
from src.database import get_db
from src.athletes.crud import (
    create_athlete as crud_create_athlete,
    get_all_athletes as crud_get_all_athletes,
    get_athlete_by_id as crud_get_athlete_by_id,
)

router = APIRouter()

@router.get("/athletes", response_model=list[AthleteResponse])
async def get_athletes(db: AsyncSession = Depends(get_db)):
    return await crud_get_all_athletes(db=db)


@router.get("/athletes/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):
    return await crud_get_athlete_by_id(db=db, id=id)

@router.post("/athletes", response_model=AthleteResponse)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_athlete(db=db, athlete = athlete)
