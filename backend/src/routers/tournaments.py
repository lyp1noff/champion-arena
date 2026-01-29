from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
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
from src.services.import_competitors import import_competitors_from_cbr
from src.services.tournaments import approve_all_applications as approve_all_applications_service
from src.services.tournaments import approve_application as approve_application_service
from src.services.tournaments import create_tournament as create_tournament_service
from src.services.tournaments import delete_tournament as delete_tournament_service
from src.services.tournaments import generate_brackets_export_file as generate_brackets_export_file_service
from src.services.tournaments import get_applications as get_applications_service
from src.services.tournaments import get_matches_for_tournament_full as get_matches_for_tournament_full_service
from src.services.tournaments import get_participant_count_per_coach as get_participant_count_per_coach_service
from src.services.tournaments import get_tournament as get_tournament_service
from src.services.tournaments import get_tournament_brackets as get_tournament_brackets_service
from src.services.tournaments import list_tournaments as list_tournaments_service
from src.services.tournaments import regenerate_tournament as regenerate_tournament_service
from src.services.tournaments import remove_competitor as remove_competitor_service
from src.services.tournaments import start_tournament as start_tournament_service
from src.services.tournaments import submit_application as submit_application_service
from src.services.tournaments import update_tournament as update_tournament_service
from src.services.tournaments import update_tournament_status as update_tournament_status_service

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
) -> PaginatedTournamentResponse:
    tournaments, total = await list_tournaments_service(db, page, limit, order_by, order, search)
    return PaginatedTournamentResponse(
        data=[TournamentResponse.model_validate(tournament) for tournament in tournaments],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)) -> TournamentResponse:
    tournament = await get_tournament_service(db, id)
    return TournamentResponse.model_validate(tournament)


@router.post("", response_model=TournamentResponse, dependencies=[Depends(get_current_user)])
async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)) -> TournamentResponse:
    new_tournament = await create_tournament_service(db, tournament)
    return TournamentResponse.model_validate(new_tournament)


@router.put("/{id}", response_model=TournamentResponse, dependencies=[Depends(get_current_user)])
async def update_tournament(
    id: int, tournament_update: TournamentUpdate, db: AsyncSession = Depends(get_db)
) -> TournamentResponse:
    tournament = await update_tournament_service(db, id, tournament_update)
    return TournamentResponse.model_validate(tournament)


@router.delete("/{id}", dependencies=[Depends(get_current_user)], status_code=204)
async def delete_tournament(id: int, db: AsyncSession = Depends(get_db)) -> None:
    await delete_tournament_service(db, id)


@router.get("/{tournament_id}/brackets", response_model=list[BracketResponse])
async def get_all_brackets(
    tournament_id: int,
    sorted: bool = Query(True, description="Sort brackets by tatami and start_time"),
    db: AsyncSession = Depends(get_db),
) -> list[BracketResponse]:
    brackets = await get_tournament_brackets_service(db, tournament_id, sorted)
    return [BracketResponse.model_validate(bracket) for bracket in brackets]


# CLI ONLY
@router.get("/{tournament_id}/coaches/participants")
async def get_participant_count_per_coach(
    tournament_id: int, db: AsyncSession = Depends(get_db)
) -> list[dict[str, int | str]]:
    return await get_participant_count_per_coach_service(db, tournament_id)


@router.get(
    "/{tournament_id}/matches_full",
    response_model=list[BracketMatchesFull],
    dependencies=[Depends(get_current_user)],
)
async def get_matches_for_tournament_full(
    tournament_id: int, db: AsyncSession = Depends(get_db)
) -> list[BracketMatchesFull]:
    brackets = await get_matches_for_tournament_full_service(db, tournament_id)
    return [BracketMatchesFull.model_validate(bracket) for bracket in brackets]


@router.post("/{tournament_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_tournament(tournament_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await regenerate_tournament_service(db, tournament_id)
    return {"status": "ok"}


@router.get("/{tournament_id}/export_file", dependencies=[Depends(get_current_user)])
async def generate_brackets_export_file(tournament_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    return await generate_brackets_export_file_service(db, tournament_id)


@router.post("/{tournament_id}/import", dependencies=[Depends(get_current_user)])
async def import_competitors(
    tournament_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        content = await file.read()
        return await import_competitors_from_cbr(db, tournament_id, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while importing competitors: {str(e)}")


@router.get("/{id}/status")
async def get_tournament_status(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    tournament = await get_tournament_service(db, id)
    return {"status": tournament.status}


@router.patch("/{id}/status", dependencies=[Depends(get_current_user)])
async def update_tournament_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> TournamentResponse:
    tournament = await update_tournament_status_service(db, id, status)
    return TournamentResponse.model_validate(tournament)


@router.post("/{id}/start", dependencies=[Depends(get_current_user)])
async def start_tournament(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await start_tournament_service(db, id)
    return {"status": "ok"}


@router.get("/{tournament_id}/applications", response_model=list[ApplicationResponse])
async def get_applications(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    applications = await get_applications_service(db, tournament_id)
    return [ApplicationResponse.model_validate(app) for app in applications]


@router.post("/{tournament_id}/applications")
async def submit_application(
    tournament_id: int,
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await submit_application_service(db, tournament_id, data)
    return {"status": "ok"}


@router.post(
    "/{tournament_id}/applications/{application_id}/approve",
    dependencies=[Depends(get_current_user)],
)
async def add_participant_from_application(
    tournament_id: int,
    application_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    bracket_id = await approve_application_service(db, tournament_id, application_id)
    await regenerate_matches_endpoint(bracket_id, db)
    return {"status": "ok"}


@router.post(
    "/{tournament_id}/applications/approve-all",
    dependencies=[Depends(get_current_user)],
)
async def approve_all_applications(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    approved_count, updated_bracket_ids = await approve_all_applications_service(db, tournament_id)
    if approved_count == 0:
        return {"status": "no applications to approve"}
    for bracket_id in updated_bracket_ids:
        await regenerate_matches_endpoint(bracket_id, db)
    return {"status": "ok", "approved": approved_count}


@router.delete("/participants/{participant_id}", dependencies=[Depends(get_current_user)])
async def remove_competitor(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    bracket_id = await remove_competitor_service(db, participant_id)
    if bracket_id:
        await regenerate_matches_endpoint(bracket_id, db)
    return {"status": "ok"}
