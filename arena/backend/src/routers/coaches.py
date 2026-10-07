from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import AthleteCoachLink, Coach
from src.schemas import CoachCreate, CoachResponse, CoachUpdate

router = APIRouter(prefix="/coaches", tags=["Coaches"], dependencies=[Depends(get_current_user)])


def _coach_response(coach: Coach, athlete_count: int = 0) -> CoachResponse:
    return CoachResponse(
        id=coach.id,
        first_name=coach.first_name,
        last_name=coach.last_name,
        athlete_count=athlete_count,
    )


@router.get("", response_model=list[CoachResponse])
async def get_coaches(db: AsyncSession = Depends(get_db)) -> list[CoachResponse]:
    result = await db.execute(
        select(Coach, func.count(AthleteCoachLink.id))
        .outerjoin(AthleteCoachLink, AthleteCoachLink.coach_id == Coach.id)
        .group_by(Coach.id)
        .order_by(Coach.last_name, Coach.first_name, Coach.id)
    )
    return [_coach_response(coach, int(athlete_count)) for coach, athlete_count in result.all()]


@router.get("/{id}", response_model=CoachResponse)
async def get_coach(id: int, db: AsyncSession = Depends(get_db)) -> CoachResponse:
    result = await db.execute(
        select(Coach, func.count(AthleteCoachLink.id))
        .outerjoin(AthleteCoachLink, AthleteCoachLink.coach_id == Coach.id)
        .where(Coach.id == id)
        .group_by(Coach.id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    coach, athlete_count = row
    return _coach_response(coach, int(athlete_count))


@router.post("", response_model=CoachResponse)
async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)) -> CoachResponse:
    new_coach = Coach(first_name=coach.first_name, last_name=coach.last_name)
    db.add(new_coach)
    await db.commit()
    await db.refresh(new_coach)
    return _coach_response(new_coach)


@router.put("/{id}", response_model=CoachResponse)
async def update_coach(id: int, coach_data: CoachUpdate, db: AsyncSession = Depends(get_db)) -> CoachResponse:
    coach = await db.get(Coach, id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")

    coach.first_name = coach_data.first_name
    coach.last_name = coach_data.last_name
    athlete_count = await db.scalar(
        select(func.count()).select_from(AthleteCoachLink).where(AthleteCoachLink.coach_id == id)
    )
    await db.commit()
    await db.refresh(coach)
    return _coach_response(coach, int(athlete_count or 0))


@router.delete("/{id}", status_code=204)
async def delete_coach(id: int, db: AsyncSession = Depends(get_db)) -> None:
    coach = await db.get(Coach, id, with_for_update=True)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")

    athlete_count = await db.scalar(
        select(func.count()).select_from(AthleteCoachLink).where(AthleteCoachLink.coach_id == id)
    )
    if athlete_count:
        raise HTTPException(status_code=409, detail="Coach cannot be deleted while athletes are assigned")

    await db.delete(coach)
    await db.commit()
