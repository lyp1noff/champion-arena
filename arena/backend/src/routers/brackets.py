from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.logger import logger
from src.models import Bracket, BracketType
from src.schemas import (
    BracketCreateSchema,
    BracketDeleteRequest,
    BracketInfoResponse,
    BracketMatchResponse,
    BracketResponse,
    BracketUpdateSchema,
    ParticipantMoveSchema,
    ParticipantReorderSchema,
)
from src.services.brackets import create_bracket as create_bracket_service
from src.services.brackets import delete_bracket as delete_bracket_service
from src.services.brackets import get_all_brackets as get_all_brackets_service
from src.services.brackets import get_bracket as get_bracket_service
from src.services.brackets import get_bracket_matches as get_bracket_matches_service
from src.services.brackets import move_participant as move_participant_service
from src.services.brackets import (
    regenerate_bracket_matches,
    regenerate_round_bracket_matches,
)
from src.services.brackets import reorder_participants as reorder_participants_service
from src.services.brackets import start_bracket as start_bracket_service
from src.services.brackets import update_bracket as update_bracket_service
from src.services.brackets import update_bracket_status as update_bracket_status_service

router = APIRouter(prefix="/brackets", tags=["Brackets"])


@router.get("", response_model=list[BracketResponse])
async def get_all_brackets(db: AsyncSession = Depends(get_db)) -> list[BracketResponse]:
    brackets = await get_all_brackets_service(db)
    return [BracketResponse.model_validate(bracket) for bracket in brackets]


@router.get("/{bracket_id}", response_model=BracketResponse)
async def get_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)) -> BracketResponse:
    bracket = await get_bracket_service(db, bracket_id)
    return BracketResponse.model_validate(bracket)


@router.put("/{bracket_id}", dependencies=[Depends(get_current_user)])
async def update_bracket(
    bracket_id: int,
    update_data: BracketUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketInfoResponse:
    bracket, type_changed = await update_bracket_service(db, bracket_id, update_data)

    if type_changed:
        await regenerate_matches_endpoint(bracket_id, db)

    return BracketInfoResponse.model_validate(bracket)


@router.get("/{bracket_id}/matches", response_model=list[BracketMatchResponse])
async def get_bracket_matches(bracket_id: int, db: AsyncSession = Depends(get_db)) -> list[BracketMatchResponse]:
    matches = await get_bracket_matches_service(db, bracket_id)
    return [BracketMatchResponse.model_validate(match) for match in matches]


@router.post("/{bracket_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_matches_endpoint(
    bracket_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        result = await db.execute(select(Bracket.type, Bracket.tournament_id).where(Bracket.id == bracket_id))
        bracket_data = result.first()
        if not bracket_data:
            raise HTTPException(status_code=404, detail="Bracket not found")

        bracket_type, tournament_id = bracket_data
        if bracket_type == BracketType.ROUND_ROBIN.value:
            await regenerate_round_bracket_matches(db, bracket_id, tournament_id)
        elif bracket_type == BracketType.SINGLE_ELIMINATION.value:
            await regenerate_bracket_matches(db, bracket_id, tournament_id)
        else:
            logger.warning(f"Bracket type: {bracket_type} not supported")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate: {str(e)}")


@router.post("/participants/move", dependencies=[Depends(get_current_user)])
async def move_participant(
    move_data: ParticipantMoveSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await move_participant_service(db, move_data)

    # Regenerate matches for both brackets
    await regenerate_matches_endpoint(move_data.from_bracket_id, db)
    await regenerate_matches_endpoint(move_data.to_bracket_id, db)

    return {"status": "ok"}


@router.post("/participants/reorder", dependencies=[Depends(get_current_user)])
async def reorder_participants(
    reorder_data: ParticipantReorderSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await reorder_participants_service(db, reorder_data)
    return {"status": "ok"}


@router.post("/create", dependencies=[Depends(get_current_user)])
async def create_bracket(
    bracket_data: BracketCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketResponse:
    bracket_full = await create_bracket_service(db, bracket_data)
    return BracketResponse.model_validate(bracket_full)


@router.post("/{bracket_id}/delete", dependencies=[Depends(get_current_user)])
async def delete_bracket(
    bracket_id: int,
    data: BracketDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await delete_bracket_service(db, bracket_id, data)

    if data.target_bracket_id:
        await regenerate_matches_endpoint(data.target_bracket_id, db)

    return {"status": "ok"}


@router.get("/{id}/status")
async def get_bracket_status(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    bracket = await db.get(Bracket, id)
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    return {"status": bracket.status}


@router.patch("/{id}/status", dependencies=[Depends(get_current_user)])
async def update_bracket_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> BracketResponse:
    bracket = await update_bracket_status_service(db, id, status)
    return BracketResponse.model_validate(bracket)


@router.post("/{id}/start", dependencies=[Depends(get_current_user)])
async def start_bracket(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await start_bracket_service(db, id)
    return {"status": "ok"}
