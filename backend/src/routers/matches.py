import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import (
    Athlete,
    AthleteCoachLink,
    BracketMatch,
    Match,
    MatchStatus,
)
from src.schemas import MatchFinishRequest, MatchSchema, MatchScoreUpdate
from src.services.serialize import serialize_match

router = APIRouter(prefix="/matches", tags=["Matches"], dependencies=[Depends(get_current_user)])


@router.get("/{id}")
async def get_match(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == id)
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Match not found")
    return serialize_match(match)


@router.post("/{id}/start")
async def start_match(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == id)
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, "Match not found")
    if match.status != MatchStatus.NOT_STARTED.value:
        raise HTTPException(400, "Match already started or finished")
    if match.athlete1_id is None or match.athlete2_id is None:
        raise HTTPException(400, "Match has no athletes")

    match.status = MatchStatus.STARTED.value
    match.started_at = datetime.now(UTC)
    match.score_athlete1 = 0
    match.score_athlete2 = 0

    await db.commit()
    await db.refresh(match)

    return serialize_match(match)


@router.post("/{id}/finish")
async def finish_match(
    id: uuid.UUID,
    result: MatchFinishRequest,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == id)
    )
    result_query = await db.execute(stmt)
    match = result_query.scalar_one_or_none()

    if not match:
        raise HTTPException(404, "Match not found")
    if match.status != MatchStatus.STARTED.value:
        raise HTTPException(400, "Match not started or already finished")

    match.score_athlete1 = result.score_athlete1
    match.score_athlete2 = result.score_athlete2
    match.winner_id = result.winner_id
    match.status = MatchStatus.FINISHED.value

    bm_result = await db.execute(select(BracketMatch).where(BracketMatch.match_id == match.id))
    bm = bm_result.scalar_one_or_none()

    if bm:
        next_position = (bm.position + 1) // 2
        next_bm_result = await db.execute(
            select(BracketMatch).where(
                BracketMatch.bracket_id == bm.bracket_id,
                BracketMatch.round_number == bm.round_number + 1,
                BracketMatch.position == next_position,
            )
        )
        next_bm = next_bm_result.scalar_one_or_none()

        if next_bm:
            next_match = await db.get(Match, next_bm.match_id)
            if next_match:
                if bm.position % 2 == 1:
                    next_match.athlete1_id = match.winner_id
                else:
                    next_match.athlete2_id = match.winner_id

        match.ended_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(match)

    return serialize_match(match)


@router.patch("/{id}/scores")
async def update_match_scores(
    id: uuid.UUID,
    scores: MatchScoreUpdate,
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == id)
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, "Match not found")

    if match.status != MatchStatus.STARTED.value:
        raise HTTPException(400, "Cannot update scores of not started match")

    if scores.score_athlete1 is not None:
        match.score_athlete1 = scores.score_athlete1
    if scores.score_athlete2 is not None:
        match.score_athlete2 = scores.score_athlete2

    await db.commit()
    await db.refresh(match)

    return serialize_match(match)


# TODO: only for admin
@router.patch("/{id}/status")
async def update_match_status(
    id: uuid.UUID,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> MatchSchema:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == id)
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, "Match not found")
    if status not in [s.value for s in MatchStatus]:
        raise HTTPException(400, f"Invalid status: {status}")

    match.status = status
    await db.commit()
    await db.refresh(match)

    return serialize_match(match)
