from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.logger import logger
from src.models import (
    Athlete,
    AthleteCoachLink,
    Bracket,
    BracketMatch,
    BracketStatus,
    Match,
    MatchStatus,
    Tournament,
    TournamentStatus,
)
from src.schemas import MatchFinishRequest, MatchScoreUpdate, MatchUpdate
from src.services.broadcast import broadcast

MatchId = UUID


async def broadcast_match_update(match: Match, db: AsyncSession) -> None:
    try:
        bracket_match_stmt = (
            select(BracketMatch).options(selectinload(BracketMatch.bracket)).where(BracketMatch.match_id == match.id)
        )
        bracket_match_result = await db.execute(bracket_match_stmt)
        bracket_match = bracket_match_result.scalar_one_or_none()

        if bracket_match and bracket_match.bracket:
            match_update = MatchUpdate(
                match_id=match.id,
                score_athlete1=match.score_athlete1,
                score_athlete2=match.score_athlete2,
                status=match.status,
            )
            await broadcast.publish(
                channel=f"tournament:{bracket_match.bracket.tournament_id}", message=match_update.model_dump_json()
            )
    except Exception as exc:
        logger.error(f"Error broadcasting match update: {exc}")


async def get_match(db: AsyncSession, match_id: MatchId) -> Match:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == match_id)
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Match not found")
    return match


async def start_match(db: AsyncSession, match_id: MatchId) -> Match:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.bracket_match).selectinload(BracketMatch.bracket).selectinload(Bracket.tournament),
        )
        .where(Match.id == match_id)
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

    bracket = match.bracket_match.bracket if match.bracket_match else None
    if bracket and bracket.status != BracketStatus.FINISHED.value:
        bracket.status = BracketStatus.STARTED.value
        tournament = bracket.tournament
        if tournament and tournament.status != TournamentStatus.FINISHED.value:
            tournament.status = TournamentStatus.STARTED.value

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match


async def finish_match(db: AsyncSession, match_id: MatchId, result: MatchFinishRequest) -> Match:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == match_id)
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
    match.ended_at = datetime.now(UTC)

    bm_result = await db.execute(select(BracketMatch).where(BracketMatch.match_id == match.id))
    bm = bm_result.scalar_one_or_none()

    if bm:
        next_position = (bm.position + 1) // 2
        next_bm = (
            await db.execute(
                select(BracketMatch).where(
                    BracketMatch.bracket_id == bm.bracket_id,
                    BracketMatch.round_number == bm.round_number + 1,
                    BracketMatch.position == next_position,
                )
            )
        ).scalar_one_or_none()

        if next_bm:
            next_match = await db.get(Match, next_bm.match_id)
            if next_match:
                if bm.position % 2 == 1:
                    next_match.athlete1_id = match.winner_id
                else:
                    next_match.athlete2_id = match.winner_id

        total_in_bracket = await db.scalar(
            select(func.count()).select_from(BracketMatch).where(BracketMatch.bracket_id == bm.bracket_id)
        )
        finished_in_bracket = await db.scalar(
            select(func.count())
            .select_from(Match)
            .join(BracketMatch, BracketMatch.match_id == Match.id)
            .where(
                BracketMatch.bracket_id == bm.bracket_id,
                Match.status == MatchStatus.FINISHED.value,
            )
        )

        if total_in_bracket and finished_in_bracket == total_in_bracket:
            bracket = await db.get(Bracket, bm.bracket_id)
            if bracket and bracket.status != BracketStatus.FINISHED.value:
                bracket.status = BracketStatus.FINISHED.value
                unfinished_brackets = await db.scalar(
                    select(func.count())
                    .select_from(Bracket)
                    .where(
                        Bracket.tournament_id == bracket.tournament_id,
                        Bracket.status != BracketStatus.FINISHED.value,
                    )
                )
                if unfinished_brackets == 0:
                    tournament = await db.get(Tournament, bracket.tournament_id)
                    if tournament and tournament.status != TournamentStatus.FINISHED.value:
                        tournament.status = TournamentStatus.FINISHED.value

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match


async def update_match_scores(db: AsyncSession, match_id: MatchId, scores: MatchScoreUpdate) -> Match:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == match_id)
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
    await broadcast_match_update(match, db)
    return match


async def update_match_status(db: AsyncSession, match_id: MatchId, status: str) -> Match:
    stmt = (
        select(Match)
        .options(
            selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
            selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        )
        .where(Match.id == match_id)
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
    await broadcast_match_update(match, db)
    return match
