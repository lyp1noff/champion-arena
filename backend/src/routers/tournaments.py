from datetime import datetime, UTC
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import asc, desc, select, func, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies.auth import get_current_user
from src.models import (
    Bracket,
    BracketMatch,
    BracketParticipant,
    Match,
    Tournament,
    Athlete,
    Coach,
    Application,
    AthleteCoachLink,
)
from src.schemas import (
    BracketMatchesFull,
    BracketResponse,
    TournamentResponse,
    TournamentCreate,
    PaginatedTournamentResponse,
    TournamentUpdate,
    ApplicationCreate,
    ApplicationResponse,
)
from src.database import get_db
from src.services.brackets import regenerate_tournament_brackets
from src.services.export_file import generate_pdf
from src.services.import_competitors import import_competitors_from_cbr
from src.services.serialize import serialize_bracket, serialize_bracket_matches_full
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
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .order_by(
            Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast()
        )
    )
    brackets = result.scalars().all()
    return [serialize_bracket(b) for b in brackets]


# CLI ONLY
@router.get("/{tournament_id}/coaches/participants")
async def get_participant_count_per_coach(
    tournament_id: int, db: AsyncSession = Depends(get_db)
):
    subquery = (
        select(
            distinct(Athlete.id).label("athlete_id"),
            AthleteCoachLink.coach_id.label("coach_id"),
        )
        .join(BracketParticipant, BracketParticipant.athlete_id == Athlete.id)
        .join(AthleteCoachLink, AthleteCoachLink.athlete_id == Athlete.id)
        .join(Bracket, Bracket.id == BracketParticipant.bracket_id)
        .filter(Bracket.tournament_id == tournament_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Coach.id,
            Coach.last_name,
            Coach.first_name,
            func.count(subquery.c.athlete_id).label("participant_count"),
        )
        .join(subquery, subquery.c.coach_id == Coach.id)
        .group_by(Coach.id, Coach.last_name, Coach.first_name)
        .order_by(func.count(subquery.c.athlete_id).desc())
    )

    coaches_data = result.all()

    return [
        {
            "coach_id": coach_id,
            "coach_last_name": last_name,
            "coach_first_name": first_name,
            "participant_count": participant_count,
        }
        for coach_id, last_name, first_name, participant_count in coaches_data
    ]


@router.get(
    "/{tournament_id}/matches_full",
    response_model=List[BracketMatchesFull],
    dependencies=[Depends(get_current_user)],
)
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
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.athlete2)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.winner)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .order_by(
            Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast()
        )
    )

    brackets = result.scalars().all()
    return [serialize_bracket_matches_full(bracket) for bracket in brackets]


async def get_matches_for_tournament_raw(
    tournament_id: int, db: AsyncSession = Depends(get_db)
):
    """Get raw SQLAlchemy objects for export functionality"""
    result = await db.execute(
        select(Bracket)
        .filter(Bracket.tournament_id == tournament_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.athlete1)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.athlete2)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.matches)
            .joinedload(BracketMatch.match)
            .joinedload(Match.winner)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .order_by(
            Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast()
        )
    )

    return result.scalars().all()


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

        export_updated_at = tournament.export_last_updated_at
        if export_updated_at is not None and file_mtime > export_updated_at:
            pass
        else:
            data = await get_matches_for_tournament_raw(tournament_id, session)
            await run_in_threadpool(generate_pdf, data, tournament_title)
    else:
        data = await get_matches_for_tournament_raw(tournament_id, session)
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


@router.get("/{tournament_id}/applications", response_model=List[ApplicationResponse])
async def get_applications(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.athlete),
            selectinload(Application.category),
        )
        .where(Application.tournament_id == tournament_id)
    )

    return result.scalars().all()


@router.post("/{tournament_id}/applications")
async def submit_application(
    tournament_id: int,
    data: ApplicationCreate,
    session: AsyncSession = Depends(get_db),
):
    existing = await session.execute(
        select(Application).where(
            Application.tournament_id == tournament_id,
            Application.athlete_id == data.athlete_id,
            Application.category_id == data.category_id,
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Application already exists")

    application = Application(
        tournament_id=tournament_id,
        category_id=data.category_id,
        athlete_id=data.athlete_id,
        status="pending",
    )
    session.add(application)
    await session.commit()
    return {"status": "ok"}
