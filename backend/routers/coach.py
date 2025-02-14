from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import CoachResponse, CoachCreate
from database import get_db
from crud import get_coach, create_coach, get_coaches

router = APIRouter()

@router.get("/coaches", response_model=list[CoachResponse])
async def get_all_coachs(db: AsyncSession = Depends(get_db)):
    return await get_coaches(db=db)


@router.get("/coach/{id}", response_model=CoachResponse)
async def get_coach_by_id(id: int, db: AsyncSession = Depends(get_db)):
    return await get_coach(db=db, id=id)

@router.post("/coach", response_model=CoachResponse)
async def create_new_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    return await create_coach(db=db, coach = coach)