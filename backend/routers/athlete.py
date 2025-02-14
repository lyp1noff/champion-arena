from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import AthleteResponse, AthleteCreate
from database import get_db
from crud import get_athlete, create_athlete, get_athletes

router = APIRouter()

@router.get("/athletes", response_model=list[AthleteResponse])
async def get_all_athletes(db: AsyncSession = Depends(get_db)):
    return await get_athletes(db=db)


@router.get("/athlete/{id}", response_model=AthleteResponse)
async def get_athlete_by_id(id: int, db: AsyncSession = Depends(get_db)):
    return await get_athlete(db=db, id=id)

@router.post("/athlete", response_model=AthleteResponse)
async def create_new_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    return await create_athlete(db=db, athlete = athlete)
