from datetime import UTC, datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import asc, desc, distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import (
    Application,
    ApplicationStatus,
    Athlete,
    AthleteCoachLink,
    Bracket,
    BracketMatch,
    BracketParticipant,
    Coach,
    Match,
    Tournament,
    TournamentStatus,
)
from src.routers.brackets import regenerate_matches_endpoint
from src.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    BracketMatchesFull,
    BracketResponse,
    PaginatedTournamentResponse,
    TournamentCreate,
    TournamentResponse,
    TournamentUpdate,
)
from src.services.brackets import (
    regenerate_tournament_brackets,
    reorder_seeds_and_get_next,
)
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
        desc(getattr(Tournament, order_by)) if order.lower() == "desc" else asc(getattr(Tournament, order_by))
    )
    offset = (page - 1) * limit

    filters = [Tournament.name.ilike(f"%{search}%")] if search else []

    total = await db.scalar(select(func.count(Tournament.id)).where(*filters))

    result = await db.execute(select(Tournament).where(*filters).order_by(order_column).offset(offset).limit(limit))

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


@router.post("", response_model=TournamentResponse, dependencies=[Depends(get_current_user)])
async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_tournament = Tournament(**tournament.model_dump())
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Tournament with these details already exists")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=TournamentResponse, dependencies=[Depends(get_current_user)])
async def update_tournament(id: int, tournament_update: TournamentUpdate, db: AsyncSession = Depends(get_db)):
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
        .order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )
    brackets = result.scalars().all()
    return [serialize_bracket(b) for b in brackets]


# CLI ONLY
@router.get("/{tournament_id}/coaches/participants")
async def get_participant_count_per_coach(tournament_id: int, db: AsyncSession = Depends(get_db)):
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
async def get_matches_for_tournament_full(tournament_id: int, db: AsyncSession = Depends(get_db)):
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
        .order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )

    brackets = result.scalars().all()
    return [serialize_bracket_matches_full(bracket) for bracket in brackets]


async def get_matches_for_tournament_raw(tournament_id: int, db: AsyncSession = Depends(get_db)):
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
        .order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )

    return result.scalars().all()


@router.post("/{tournament_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_tournament(tournament_id: int, session: AsyncSession = Depends(get_db)):
    try:
        await regenerate_tournament_brackets(session, tournament_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tournament_id}/export_file", dependencies=[Depends(get_current_user)])
async def generate_brackets_export_file(tournament_id: int, session: AsyncSession = Depends(get_db)):
    tournament = await get_tournament(tournament_id, session)
    tournament_title = f"{tournament.name} - {tournament.start_date.strftime('%d.%m.%Y')}"
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


@router.get("/tournaments/{id}/status")
async def get_tournament_status(id: int, db: AsyncSession = Depends(get_db)):
    tournament = await db.get(Tournament, id)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    return {"status": tournament.status}


@router.patch("/tournaments/{id}/status", dependencies=[Depends(get_current_user)])
async def update_tournament_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    tournament = await db.get(Tournament, id)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    if status not in [s.value for s in TournamentStatus]:
        raise HTTPException(400, f"Invalid status: {status}")
    tournament.status = status
    await db.commit()
    await db.refresh(tournament)
    return tournament


@router.post("/tournaments/{id}/start", dependencies=[Depends(get_current_user)])
async def start_tournament(id: int, db: AsyncSession = Depends(get_db)):
    tournament = await db.get(Tournament, id)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    if tournament.status != TournamentStatus.UPCOMING.value:
        raise HTTPException(400, "Tournament already started or finished")

    tournament.status = TournamentStatus.STARTED.value
    await db.commit()
    return {"status": "ok"}


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


@router.post("/{tournament_id}/applications", response_model=List[ApplicationResponse])
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


@router.post(
    "/{tournament_id}/applications/{application_id}/approve",
    dependencies=[Depends(get_current_user)],
)
async def add_participant_from_application(
    tournament_id: int,
    application_id: int,
    db: AsyncSession = Depends(get_db),
):
    # 1. Find the application
    app = await db.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # 2. Find the bracket for this tournament/category
    bracket = await db.execute(
        select(Bracket).where(
            Bracket.tournament_id == app.tournament_id,
            Bracket.category_id == app.category_id,
        )
    )
    bracket = bracket.scalars().first()
    if not bracket:
        # Create bracket if not found
        bracket = Bracket(
            tournament_id=app.tournament_id,
            category_id=app.category_id,
        )
        db.add(bracket)
        await db.commit()
        await db.refresh(bracket)

    # 3. Check if already in bracket
    existing = await db.execute(
        select(BracketParticipant).where(
            BracketParticipant.bracket_id == bracket.id,
            BracketParticipant.athlete_id == app.athlete_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Athlete already in bracket")

    # 4. Find max seed
    result = await db.execute(
        select(BracketParticipant.seed)
        .where(BracketParticipant.bracket_id == bracket.id)
        .order_by(BracketParticipant.seed.desc())
        .limit(1)
    )
    max_seed = result.scalar() or 0
    new_seed = (max_seed or 0) + 1

    # 5. Add BracketParticipant
    participant = BracketParticipant(
        bracket_id=bracket.id,
        athlete_id=app.athlete_id,
        seed=new_seed,
    )
    db.add(participant)

    # 6. Update Application status
    app.status = ApplicationStatus.APPROVED.value
    await db.commit()

    # 7. Regenerate matches
    await regenerate_matches_endpoint(bracket.id, session=db)

    return {"status": "ok"}


@router.post(
    "/{tournament_id}/applications/approve-all",
    dependencies=[Depends(get_current_user)],
)
async def approve_all_applications(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
):
    # 1. Find all pending applications for the tournament (and category if provided)
    query = select(Application).where(Application.tournament_id == tournament_id)
    query = query.where(Application.status == ApplicationStatus.PENDING.value)
    result = await db.execute(query)
    applications = result.scalars().all()
    if not applications:
        return {"status": "no applications to approve"}

    # 2. Group by (category_id)
    from collections import defaultdict

    apps_by_category = defaultdict(list)
    for app in applications:
        apps_by_category[app.category_id].append(app)

    updated_bracket_ids = set()
    for category_id, apps in apps_by_category.items():
        # Find bracket for this tournament/category
        bracket = await db.execute(
            select(Bracket).where(
                Bracket.tournament_id == tournament_id,
                Bracket.category_id == category_id,
            )
        )
        bracket = bracket.scalars().first()
        if not bracket:
            # Create bracket if not found
            bracket = Bracket(
                tournament_id=tournament_id,
                category_id=category_id,
            )
            db.add(bracket)
            await db.commit()
            await db.refresh(bracket)
        # Find max seed
        result = await db.execute(
            select(BracketParticipant.seed)
            .where(BracketParticipant.bracket_id == bracket.id)
            .order_by(BracketParticipant.seed.desc())
            .limit(1)
        )
        max_seed = result.scalar() or 0
        # Add each application as participant if not already present
        for i, app in enumerate(apps):
            existing = await db.execute(
                select(BracketParticipant).where(
                    BracketParticipant.bracket_id == bracket.id,
                    BracketParticipant.athlete_id == app.athlete_id,
                )
            )
            if existing.scalars().first():
                continue
            participant = BracketParticipant(
                bracket_id=bracket.id,
                athlete_id=app.athlete_id,
                seed=max_seed + i + 1,
            )
            db.add(participant)
            app.status = ApplicationStatus.APPROVED.value
        updated_bracket_ids.add(bracket.id)
    await db.commit()
    # Regenerate matches for all updated brackets
    for bracket_id in updated_bracket_ids:
        await regenerate_matches_endpoint(bracket_id, session=db)
    return {"status": "ok", "approved": len(applications)}


@router.delete("/participants/{participant_id}", dependencies=[Depends(get_current_user)])
async def remove_competitor(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BracketParticipant)
        .options(selectinload(BracketParticipant.bracket))
        .where(BracketParticipant.id == participant_id)
    )
    participant = result.scalars().first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    bracket_id = participant.bracket_id
    athlete_id = participant.athlete_id
    tournament_id = participant.bracket.tournament_id if participant.bracket else None
    category_id = participant.bracket.category_id if participant.bracket else None

    await db.delete(participant)

    await reorder_seeds_and_get_next(db, participant.bracket_id)

    if tournament_id and category_id and athlete_id:
        apps = await db.execute(
            # TO-DO: Fix by adding BracketParticipant id to Application after approval
            select(Application).where(
                Application.tournament_id == tournament_id,
                Application.athlete_id == athlete_id,
            )
        )
        for app in apps.scalars().all():
            await db.delete(app)

    await db.commit()

    if bracket_id:
        await regenerate_matches_endpoint(bracket_id, session=db)

    return {"status": "ok"}
