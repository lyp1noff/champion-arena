import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.schemas import MatchFinishRequest, MatchSchema, MatchScoreUpdate
from src.services.matches import finish_match as finish_match_service
from src.services.matches import get_match as get_match_service
from src.services.matches import start_match as start_match_service
from src.services.matches import update_match_scores as update_match_scores_service

router = APIRouter(prefix="/matches", tags=["Matches"], dependencies=[Depends(get_current_user)])


@router.get("/{id}")
async def get_match(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    match = await get_match_service(db, id)
    return MatchSchema.model_validate(match)

@router.post("/{id}/start")
async def start_match(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    match = await start_match_service(db, id)
    return MatchSchema.model_validate(match)
@router.post("/{id}/finish")
async def finish_match(
    id: uuid.UUID,
    result: MatchFinishRequest,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    match = await finish_match_service(db, id, result)
    return MatchSchema.model_validate(match)


@router.patch("/{id}/scores")
async def update_match_scores(
    id: uuid.UUID,
    scores: MatchScoreUpdate,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    match = await update_match_scores_service(db, id, scores)
    return MatchSchema.model_validate(match)
