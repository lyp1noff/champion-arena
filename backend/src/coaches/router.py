from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import CoachResponse, CoachCreate
from src.database import get_db
from src.coaches.crud import (
    create_coach as crud_create_coach,
    get_all_coaches as crud_get_all_coaches,
    get_coach_by_id as crud_get_coach_by_id,
)

router = APIRouter()

@router.get("/coaches", response_model=list[CoachResponse])
async def get_coaches(db: AsyncSession = Depends(get_db)):
    return await crud_get_all_coaches(db=db)


@router.get("/coaches/{id}", response_model=CoachResponse)
async def get_coach(id: int, db: AsyncSession = Depends(get_db)):
    return await crud_get_coach_by_id(db=db, id=id)

@router.post("/coaches", response_model=CoachResponse)
async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_coach(db=db, coach = coach)