from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.models import Athlete, Coach
from src.schemas import (
    AthleteResponse,
    AthleteCreate,
    AthleteUpdate,
    PaginatedAthletesResponse,
)
from src.database import get_db

router = APIRouter(
    prefix="/athletes", tags=["Athletes"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=PaginatedAthletesResponse)
async def get_athletes(
        page: int = Query(1, alias="page", ge=1),
        limit: int = Query(10, alias="limit", ge=1, le=100),
        order_by: str = Query("id", alias="order_by"),
        order: str = Query("asc", alias="order"),
        search: str = Query(None, alias="search"),
        coach_search: str = Query(None, alias="coach_search"),
        db: AsyncSession = Depends(get_db),
):
    valid_order_fields = {
        "id",
        "last_name",
        "first_name",
        "gender",
        "birth_date",
        "coach_last_name",
        "age",
    }

    if order_by not in valid_order_fields:
        order_by = "id"

    if order_by == "age":
        order_column = func.date_part("year", func.age(Athlete.birth_date))
    elif order_by == "coach_last_name":
        order_column = Coach.last_name
    else:
        order_column = getattr(Athlete, order_by)

    order_column = desc(order_column) if order.lower() == "desc" else asc(order_column)

    offset = (page - 1) * limit

    filters = []
    if search:
        filters.append(
            or_(
                Athlete.first_name.ilike(f"%{search}%"),
                Athlete.last_name.ilike(f"%{search}%"),
            )
        )
    if coach_search:
        filters.append(Coach.last_name.ilike(f"%{coach_search}%"))

    total_query = await db.execute(
        select(func.count(Athlete.id))
        .outerjoin(Coach, Athlete.coach_id == Coach.id)
        .where(*filters)
    )
    total = total_query.scalar_one_or_none() or 0

    result = await db.execute(
        select(
            Athlete,
            Coach.last_name.label("coach_last_name"),
            func.date_part("year", func.age(Athlete.birth_date)).label("age"),
        )
        .outerjoin(Coach, Athlete.coach_id == Coach.id)
        .where(*filters)
        .order_by(order_column)
        .offset(offset)
        .limit(limit)
    )

    athletes = [
        AthleteResponse.model_validate(
            {**vars(athlete), "coach_last_name": coach_last_name, "age": age}
        )
        for athlete, coach_last_name, age in result.all()
    ]

    return {
        "data": athletes,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/all", response_model=List[AthleteResponse])
async def get_all_athletes(
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Athlete,
            Coach.last_name.label("coach_last_name"),
            func.date_part("year", func.age(Athlete.birth_date)).label("age"),
        ).outerjoin(Coach, Athlete.coach_id == Coach.id)
    )

    athletes = [
        AthleteResponse.model_validate(
            {**vars(athlete), "coach_last_name": coach_last_name, "age": age}
        )
        for athlete, coach_last_name, age in result.all()
    ]
    return athletes


@router.get("/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Athlete,
            Coach.last_name.label("coach_last_name"),
            func.date_part("year", func.age(Athlete.birth_date)).label("age"),
        )
        .outerjoin(Coach, Athlete.coach_id == Coach.id)
        .filter(Athlete.id == id)
    )
    athlete = result.first()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    athlete_data = AthleteResponse.model_validate(
        {**vars(athlete[0]), "coach_last_name": athlete[1], "age": athlete[2]}
    )

    return athlete_data


@router.post("", response_model=AthleteResponse)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_athlete = Athlete(**athlete.model_dump())
        db.add(new_athlete)
        await db.commit()
        await db.refresh(new_athlete)
        return new_athlete

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Invalid coach_id: coach does not exist"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=AthleteResponse)
async def update_athlete(
        id: int, athlete_update: AthleteUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    for key, value in athlete_update.model_dump(exclude_unset=True).items():
        setattr(athlete, key, value)

    await db.commit()
    await db.refresh(athlete)

    return athlete


@router.delete("/{id}", status_code=204)
async def delete_athlete(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()

    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    await db.delete(athlete)
    await db.commit()
