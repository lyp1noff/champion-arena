from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Tournament
from src.schemas import (
    TournamentResponse,
    TournamentCreate,
    PaginatedTournamentResponse,
)
from src.database import get_db

router = APIRouter(prefix="/tournaments")


@router.get("", response_model=PaginatedTournamentResponse)
async def get_tournaments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_by: str = Query("id"),
    order: str = Query("asc"),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    valid_order_fields = {"id", "name", "location", "start_date", "end_date"}
    order_by = order_by if order_by in valid_order_fields else "id"

    order_column = (
        desc(getattr(Tournament, order_by))
        if order.lower() == "desc"
        else asc(getattr(Tournament, order_by))
    )
    offset = (page - 1) * limit

    filters = [Tournament.name.ilike(f"%{search}%")] if search else []

    total = await db.scalar(select(func.count(Tournament.id)).where(*filters))

    result = await db.execute(
        select(Tournament)
        .where(*filters)
        .order_by(order_column)
        .offset(offset)
        .limit(limit)
    )

    return {
        "data": result.scalars().all(),
        "total": total or 0,
        "page": page,
        "limit": limit,
    }


@router.get("{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tournament)
        .options(joinedload(Tournament.coach))
        .filter(Tournament.id == id)
    )
    tournament = result.scalars().first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return tournament


@router.post("", response_model=TournamentResponse)
async def create_tournament(
    tournament: TournamentCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_tournament = Tournament(**tournament.model_dump())
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
