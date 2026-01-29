from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import asc, desc, distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from src.schemas import ApplicationCreate, TournamentCreate, TournamentUpdate
from src.services.brackets import regenerate_tournament_brackets, reorder_seeds_and_get_next
from src.services.export_file import generate_pdf
from src.utils import sanitize_filename


async def list_tournaments(
    db: AsyncSession,
    page: int,
    limit: int,
    order_by: str,
    order: str,
    search: str | None,
) -> tuple[list[Tournament], int]:
    valid_order_fields = {"id", "name", "location", "start_date", "end_date"}
    order_by = order_by if order_by in valid_order_fields else "id"

    order_column = (
        desc(getattr(Tournament, order_by)) if order.lower() == "desc" else asc(getattr(Tournament, order_by))
    )
    offset = (page - 1) * limit

    filters = [Tournament.name.ilike(f"%{search}%")] if search else []

    total = await db.scalar(select(func.count(Tournament.id)).where(*filters))

    result = await db.execute(select(Tournament).where(*filters).order_by(order_column).offset(offset).limit(limit))
    tournaments = list(result.scalars().all())
    return tournaments, total or 0


async def get_tournament(db: AsyncSession, tournament_id: int) -> Tournament:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def create_tournament(db: AsyncSession, tournament: TournamentCreate) -> Tournament:
    try:
        new_tournament = Tournament(**tournament.model_dump())
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Tournament with these details already exists")
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while creating the tournament")


async def update_tournament(db: AsyncSession, tournament_id: int, update_data: TournamentUpdate) -> Tournament:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    try:
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(tournament, key, value)

        await db.commit()
        await db.refresh(tournament)
        return tournament
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Tournament with these details already exists")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while updating the tournament")


async def delete_tournament(db: AsyncSession, tournament_id: int) -> None:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    try:
        await db.delete(tournament)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete tournament due to existing dependencies")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while deleting the tournament")


async def get_tournament_brackets(db: AsyncSession, tournament_id: int, sorted_brackets: bool) -> list[Bracket]:
    query = (
        select(Bracket)
        .filter_by(tournament_id=tournament_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )

    if sorted_brackets:
        query = query.order_by(Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    else:
        query = query.order_by(Bracket.category_id.asc().nullslast())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_participant_count_per_coach(db: AsyncSession, tournament_id: int) -> list[dict[str, int | str]]:
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


async def get_matches_for_tournament_full(db: AsyncSession, tournament_id: int) -> list[Bracket]:
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

    return list(result.scalars().all())


async def get_matches_for_tournament_raw(db: AsyncSession, tournament_id: int) -> list[Bracket]:
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
        .order_by(Bracket.day.asc(), Bracket.tatami.asc().nullslast(), Bracket.start_time.asc().nullslast())
    )

    return list(result.scalars().all())


async def regenerate_tournament(db: AsyncSession, tournament_id: int) -> None:
    await regenerate_tournament_brackets(db, tournament_id)


async def generate_brackets_export_file(db: AsyncSession, tournament_id: int) -> dict[str, str]:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    tournament_title = f"{tournament.name} - {tournament.start_date.strftime('%d.%m.%Y')}"
    final_filename = f"{sanitize_filename(tournament_title)}.pdf"
    final_path = Path("pdf_storage") / final_filename

    if final_path.exists():
        file_mtime = datetime.fromtimestamp(final_path.stat().st_mtime, UTC)
        export_updated_at = tournament.export_last_updated_at
        if export_updated_at is not None and file_mtime > export_updated_at:
            return {"filename": final_filename}

    brackets = await get_matches_for_tournament_raw(db, tournament_id)
    result = generate_pdf(brackets, tournament_title)
    if isinstance(result, dict):
        raise HTTPException(status_code=400, detail=result.get("detail", "Failed to generate"))
    return {"filename": Path(result).name}


async def update_tournament_status(db: AsyncSession, tournament_id: int, status: str) -> Tournament:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    if status not in [s.value for s in TournamentStatus]:
        raise HTTPException(400, f"Invalid status: {status}")

    try:
        tournament.status = status
        await db.commit()
        await db.refresh(tournament)
        return tournament
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while updating tournament status")


async def start_tournament(db: AsyncSession, tournament_id: int) -> None:
    tournament = await db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    if tournament.status != TournamentStatus.UPCOMING.value:
        raise HTTPException(400, "Tournament already started or finished")

    try:
        tournament.status = TournamentStatus.STARTED.value
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while starting the tournament")


async def get_applications(db: AsyncSession, tournament_id: int) -> list[Application]:
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Application.category),
        )
        .where(Application.tournament_id == tournament_id)
    )
    return list(result.scalars().all())


async def submit_application(db: AsyncSession, tournament_id: int, data: ApplicationCreate) -> None:
    existing = await db.execute(
        select(Application).where(
            Application.tournament_id == tournament_id,
            Application.athlete_id == data.athlete_id,
            Application.category_id == data.category_id,
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Application already exists")

    try:
        application = Application(
            tournament_id=tournament_id,
            category_id=data.category_id,
            athlete_id=data.athlete_id,
            status="pending",
        )
        db.add(application)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid tournament, athlete, or category")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while submitting the application")


async def approve_application(db: AsyncSession, tournament_id: int, application_id: int) -> int:
    app = await db.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    bracket_result = await db.execute(
        select(Bracket).where(
            Bracket.tournament_id == app.tournament_id,
            Bracket.category_id == app.category_id,
        )
    )
    bracket = bracket_result.scalars().first()
    if not bracket:
        bracket = Bracket(
            tournament_id=app.tournament_id,
            category_id=app.category_id,
        )
        db.add(bracket)
        await db.commit()
        await db.refresh(bracket)

    existing = await db.execute(
        select(BracketParticipant).where(
            BracketParticipant.bracket_id == bracket.id,
            BracketParticipant.athlete_id == app.athlete_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Athlete already in bracket")

    result = await db.execute(
        select(BracketParticipant.seed)
        .where(BracketParticipant.bracket_id == bracket.id)
        .order_by(BracketParticipant.seed.desc())
        .limit(1)
    )
    max_seed = result.scalar() or 0
    new_seed = (max_seed or 0) + 1

    participant = BracketParticipant(
        bracket_id=bracket.id,
        athlete_id=app.athlete_id,
        seed=new_seed,
    )
    db.add(participant)

    app.status = ApplicationStatus.APPROVED.value

    try:
        await db.commit()
        return bracket.id
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while approving the application")


async def approve_all_applications(db: AsyncSession, tournament_id: int) -> tuple[int, set[int]]:
    query = select(Application).where(Application.tournament_id == tournament_id)
    query = query.where(Application.status == ApplicationStatus.PENDING.value)
    applications_result = await db.execute(query)
    applications = applications_result.scalars().all()
    if not applications:
        return 0, set()

    apps_by_category: dict[int, list[Application]] = defaultdict(list)
    for app in applications:
        apps_by_category[app.category_id].append(app)

    updated_bracket_ids: set[int] = set()
    for category_id, apps in apps_by_category.items():
        bracket_result = await db.execute(
            select(Bracket).where(
                Bracket.tournament_id == tournament_id,
                Bracket.category_id == category_id,
            )
        )
        bracket = bracket_result.scalars().first()
        if not bracket:
            bracket = Bracket(
                tournament_id=tournament_id,
                category_id=category_id,
            )
            db.add(bracket)
            await db.commit()
            await db.refresh(bracket)

        max_seed_result = await db.execute(
            select(BracketParticipant.seed)
            .where(BracketParticipant.bracket_id == bracket.id)
            .order_by(BracketParticipant.seed.desc())
            .limit(1)
        )
        max_seed = max_seed_result.scalar() or 0
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

    try:
        await db.commit()
        return len(applications), updated_bracket_ids
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while approving applications")


async def remove_competitor(db: AsyncSession, participant_id: int) -> int | None:
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

    try:
        await db.delete(participant)
        await reorder_seeds_and_get_next(db, participant.bracket_id)

        if tournament_id and category_id and athlete_id:
            apps = await db.execute(
                select(Application).where(
                    Application.tournament_id == tournament_id,
                    Application.athlete_id == athlete_id,
                )
            )
            for app in apps.scalars().all():
                await db.delete(app)

        await db.commit()
        return bracket_id
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while removing the competitor")
