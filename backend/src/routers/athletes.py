from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import Athlete, AthleteCoachLink, Coach
from src.schemas import (
    AthleteCreate,
    AthleteResponse,
    AthleteUpdate,
    PaginatedAthletesResponse,
)

router = APIRouter(prefix="/athletes", tags=["Athletes"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedAthletesResponse)
async def get_athletes(
    page: int = Query(1, alias="page", ge=1),
    limit: int = Query(10, alias="limit", ge=1, le=100),
    order_by: str = Query("id", alias="order_by"),
    order: str = Query("asc", alias="order"),
    search: str = Query(None, alias="search"),
    coach_search: str = Query(None, alias="coach_search"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedAthletesResponse:
    offset = (page - 1) * limit

    stmt = select(Athlete).options(selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach))

    if search:
        stmt = stmt.where(
            or_(
                Athlete.first_name.ilike(f"%{search}%"),
                Athlete.last_name.ilike(f"%{search}%"),
            )
        )

    if coach_search:
        stmt = stmt.join(AthleteCoachLink, Athlete.id == AthleteCoachLink.athlete_id)
        stmt = stmt.join(Coach, AthleteCoachLink.coach_id == Coach.id)
        stmt = stmt.where(Coach.last_name.ilike(f"%{coach_search}%"))

    valid_order_fields = {
        "id",
        "last_name",
        "first_name",
        "gender",
        "birth_date",
        "age",
        "coaches_last_name",
    }

    if order_by not in valid_order_fields:
        order_by = "id"

    if order_by == "coaches_last_name":
        # Only add joins if they don't already exist (from coach_search)
        if not coach_search:
            stmt = stmt.outerjoin(AthleteCoachLink, Athlete.id == AthleteCoachLink.athlete_id)
            stmt = stmt.outerjoin(Coach, AthleteCoachLink.coach_id == Coach.id)
        # Group by athlete to avoid duplicates and sort by the first coach's last name
        stmt = stmt.group_by(Athlete.id)
        order_column = func.min(Coach.last_name)
        stmt = stmt.order_by(desc(order_column) if order.lower() == "desc" else asc(order_column))
    elif order_by == "age":
        if order.lower() == "asc":
            stmt = stmt.order_by(desc(Athlete.birth_date))
        else:
            stmt = stmt.order_by(asc(Athlete.birth_date))
    else:
        order_column = getattr(Athlete, order_by)
        stmt = stmt.order_by(desc(order_column) if order.lower() == "desc" else asc(order_column))

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    athletes = result.scalars().all()

    athlete_responses = []
    for athlete in athletes:
        coaches_id = [link.coach.id for link in athlete.coach_links if link.coach is not None]
        coaches_last_name = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]

        age = None if athlete.birth_date is None else int((datetime.now(UTC).date() - athlete.birth_date).days // 365)

        athlete_responses.append(
            AthleteResponse(
                id=athlete.id,
                first_name=athlete.first_name,
                last_name=athlete.last_name,
                gender=athlete.gender,
                birth_date=athlete.birth_date,
                coaches_last_name=coaches_last_name,
                coaches_id=coaches_id,
                age=age,
            )
        )

    total_stmt = select(func.count(Athlete.id))
    if search or coach_search:
        total_stmt = total_stmt.select_from(Athlete)
        if coach_search:
            total_stmt = total_stmt.join(AthleteCoachLink, Athlete.id == AthleteCoachLink.athlete_id)
            total_stmt = total_stmt.join(Coach, AthleteCoachLink.coach_id == Coach.id)
        if search:
            total_stmt = total_stmt.where(
                or_(
                    Athlete.first_name.ilike(f"%{search}%"),
                    Athlete.last_name.ilike(f"%{search}%"),
                )
            )
        if coach_search:
            total_stmt = total_stmt.where(Coach.last_name.ilike(f"%{coach_search}%"))

    total_result = await db.execute(total_stmt)
    total = total_result.scalar_one() or 0

    return PaginatedAthletesResponse(
        data=athlete_responses,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/all", response_model=list[AthleteResponse])
async def get_all_athletes(
    db: AsyncSession = Depends(get_db),
) -> list[AthleteResponse]:
    stmt = select(Athlete).options(selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach))
    result = await db.execute(stmt)
    athletes_db = result.scalars().all()

    athletes = []
    for athlete in athletes_db:
        coaches_id = [link.coach.id for link in athlete.coach_links if link.coach is not None]
        coaches_last_name = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]

        age = None if athlete.birth_date is None else int((datetime.now(UTC).date() - athlete.birth_date).days // 365)

        athletes.append(
            AthleteResponse(
                id=athlete.id,
                first_name=athlete.first_name,
                last_name=athlete.last_name,
                gender=athlete.gender,
                birth_date=athlete.birth_date,
                coaches_last_name=coaches_last_name,
                coaches_id=coaches_id,
                age=age,
            )
        )

    return athletes


@router.get("/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)) -> AthleteResponse:
    stmt = (
        select(Athlete)
        .where(Athlete.id == id)
        .options(selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach))
    )
    result = await db.execute(stmt)
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    coaches_id = [link.coach.id for link in athlete.coach_links if link.coach is not None]

    coaches_last_name = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]

    age = None if athlete.birth_date is None else int((datetime.now(UTC).date() - athlete.birth_date).days // 365)

    return AthleteResponse(
        id=athlete.id,
        first_name=athlete.first_name,
        last_name=athlete.last_name,
        gender=athlete.gender,
        birth_date=athlete.birth_date,
        coaches_last_name=coaches_last_name,
        coaches_id=coaches_id,
        age=age,
    )


@router.post("", response_model=AthleteResponse)
async def create_athlete(athlete_data: AthleteCreate, db: AsyncSession = Depends(get_db)) -> AthleteResponse:
    new_athlete = Athlete(
        first_name=athlete_data.first_name,
        last_name=athlete_data.last_name,
        gender=athlete_data.gender,
        birth_date=athlete_data.birth_date,
    )
    db.add(new_athlete)
    await db.flush()

    if athlete_data.coaches_id:
        links = [AthleteCoachLink(athlete_id=new_athlete.id, coach_id=coach_id) for coach_id in athlete_data.coaches_id]
        db.add_all(links)

    await db.commit()
    await db.refresh(new_athlete)

    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == new_athlete.id)
        .options(selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach))
    )
    athlete = result.scalar_one()

    coaches_last_name = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]
    coaches_id = [link.coach.id for link in athlete.coach_links if link.coach is not None]

    return AthleteResponse(
        id=athlete.id,
        first_name=athlete.first_name,
        last_name=athlete.last_name,
        gender=athlete.gender,
        birth_date=athlete.birth_date,
        coaches_last_name=coaches_last_name,
        coaches_id=coaches_id,
    )


@router.put("/{id}", response_model=AthleteResponse)
async def update_athlete(id: int, athlete_update: AthleteUpdate, db: AsyncSession = Depends(get_db)) -> AthleteResponse:
    result = await db.execute(select(Athlete).where(Athlete.id == id))
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    for key, value in athlete_update.model_dump(exclude_unset=True).items():
        if key != "coaches_id":
            setattr(athlete, key, value)

    if athlete_update.coaches_id is not None:
        await db.execute(delete(AthleteCoachLink).where(AthleteCoachLink.athlete_id == id))
        links = [AthleteCoachLink(athlete_id=id, coach_id=coach_id) for coach_id in athlete_update.coaches_id]
        db.add_all(links)

    await db.commit()

    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == id)
        .options(selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach))
    )
    athlete = result.scalar_one()

    coaches_last_name = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]

    coaches_id = [link.coach.id for link in athlete.coach_links if link.coach is not None]

    return AthleteResponse(
        id=athlete.id,
        first_name=athlete.first_name,
        last_name=athlete.last_name,
        gender=athlete.gender,
        birth_date=athlete.birth_date,
        coaches_last_name=coaches_last_name,
        coaches_id=coaches_id,
    )


@router.delete("/{id}", status_code=204)
async def delete_athlete(id: int, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    await db.delete(athlete)
    await db.commit()
    # No response body for 204 No Content
