from datetime import datetime, UTC
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.models import Bracket, BracketMatch, BracketParticipant, Match, Tournament, Athlete
from src.schemas import (
    BracketMatchesFull,
    BracketResponse,
    TournamentResponse,
    TournamentCreate,
    PaginatedTournamentResponse,
    TournamentUpdate,
)
from src.database import get_db
from src.services.brackets import regenerate_tournament_brackets
from src.services.export_file import generate_pdf
from src.services.import_competitors import import_competitors_from_cbr
from src.services.serialize import serialize_bracket, \
    serialize_bracket_matches_full
from src.utils import sanitize_filename

router = APIRouter(
    prefix="/tournaments",
    tags=["Tournaments"],
)


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


@router.get("/{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return tournament


@router.post(
    "", response_model=TournamentResponse, dependencies=[Depends(get_current_user)]
)
async def create_tournament(
        tournament: TournamentCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_tournament = Tournament(**tournament.model_dump())
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament
    except IntegrityError:
        raise HTTPException(
            status_code=400, detail="Tournament with these details already exists"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{id}", response_model=TournamentResponse, dependencies=[Depends(get_current_user)]
)
async def update_tournament(
        id: int, tournament_update: TournamentUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    for key, value in tournament_update.model_dump(exclude_unset=True).items():
        setattr(tournament, key, value)

    await db.commit()
    await db.refresh(tournament)

    return tournament


@router.delete("/{id}", dependencies=[Depends(get_current_user)], status_code=204)
async def delete_tournament(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    await db.delete(tournament)
    await db.commit()


@router.get("/{tournament_id}/brackets", response_model=List[BracketResponse])
async def get_all_brackets(tournament_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bracket)
        .filter_by(tournament_id=tournament_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach)
        )
        .order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )
    brackets = result.scalars().all()
    return [serialize_bracket(b) for b in brackets]


@router.get("/{tournament_id}/matches_full", response_model=List[BracketMatchesFull],
            dependencies=[Depends(get_current_user)])
async def get_matches_for_tournament_full(
        tournament_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Bracket)
        .filter(Bracket.tournament_id == tournament_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.athlete1)
            .joinedload(Athlete.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.athlete2)
            .joinedload(Athlete.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.winner)
            .joinedload(Athlete.coach),
        )
        .order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )

    brackets = result.scalars().all()
    return [serialize_bracket_matches_full(bracket) for bracket in brackets]


@router.post("/{tournament_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_tournament(
        tournament_id: int, session: AsyncSession = Depends(get_db)
):
    try:
        await regenerate_tournament_brackets(session, tournament_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tournament_id}/export_file", dependencies=[Depends(get_current_user)])
async def generate_brackets_export_file(
        tournament_id: int, session: AsyncSession = Depends(get_db)
):
    tournament = await get_tournament(tournament_id, session)
    tournament_title = (
        f"{tournament.name} - {tournament.start_date.strftime('%d.%m.%Y')}"
    )
    final_filename = f"{sanitize_filename(tournament_title)}.pdf"
    final_path = Path("pdf_storage") / final_filename

    if final_path.exists():
        file_mtime = datetime.fromtimestamp(final_path.stat().st_mtime, UTC)

        if tournament.export_last_updated_at and file_mtime > tournament.export_last_updated_at:
            pass
        else:
            data = await get_matches_for_tournament_full(tournament_id, session)
            await run_in_threadpool(generate_pdf, data, tournament_title)
    else:
        data = await get_matches_for_tournament_full(tournament_id, session)
        await run_in_threadpool(generate_pdf, data, tournament_title)

    return {"filename": final_path}


@router.post("/{tournament_id}/import", dependencies=[Depends(get_current_user)])
async def import_competitors(
        tournament_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    return await import_competitors_from_cbr(db, tournament_id, content)
