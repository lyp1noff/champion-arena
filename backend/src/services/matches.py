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
    MatchStage,
    MatchStatus,
    Tournament,
    TournamentStatus,
)
from src.schemas import MatchFinishRequest, MatchScoreUpdate, MatchUpdate
from src.services.broadcast import broadcast

MatchId = UUID


def _match_loser_id(match: Match) -> int | None:
    if match.winner_id is None:
        return None
    if match.athlete1_id == match.winner_id:
        return match.athlete2_id
    if match.athlete2_id == match.winner_id:
        return match.athlete1_id
    return None


async def _ensure_repechage_generated(db: AsyncSession, bracket_id: int) -> None:
    bracket = await db.get(Bracket, bracket_id)
    if bracket is None or bracket.type != "single_elimination":
        return

    repechage_exists = await db.scalar(
        select(func.count())
        .select_from(Match)
        .join(BracketMatch, BracketMatch.match_id == Match.id)
        .where(
            BracketMatch.bracket_id == bracket_id,
            Match.stage == MatchStage.REPECHAGE.value,
        )
    )
    if repechage_exists:
        return

    final_bm = (
        await db.execute(
            select(BracketMatch)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                Match.round_type == "final",
            )
        )
    ).scalar_one_or_none()
    if final_bm is None:
        return

    final_match = await db.get(Match, final_bm.match_id)
    if final_match is None or final_match.athlete1_id is None or final_match.athlete2_id is None:
        return

    finished_main_rows = (
        await db.execute(
            select(BracketMatch, Match)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                Match.status == MatchStatus.FINISHED.value,
                Match.stage == MatchStage.MAIN.value,
                Match.round_type != "final",
            )
        )
    ).all()

    finalists: list[tuple[str, int]] = [("A", final_match.athlete1_id), ("B", final_match.athlete2_id)]
    max_round = await db.scalar(
        select(func.max(BracketMatch.round_number)).where(BracketMatch.bracket_id == bracket_id)
    )
    base_round = int(max_round or 0) + 1

    for side, finalist_id in finalists:
        losses: list[tuple[int, int]] = []
        for bm_row, match in finished_main_rows:
            if match.winner_id != finalist_id:
                continue
            loser_id = _match_loser_id(match)
            if loser_id is None:
                continue
            losses.append((bm_row.round_number, loser_id))

        losses.sort(key=lambda item: item[0])
        ordered_losers: list[int] = []
        seen = set()
        for _, loser in losses:
            if loser in seen:
                continue
            seen.add(loser)
            ordered_losers.append(loser)

        if len(ordered_losers) < 2:
            # No real repechage matches on this side; bronze is direct by regulation.
            continue

        for step in range(1, len(ordered_losers)):
            athlete1_id = ordered_losers[0] if step == 1 else None
            athlete2_id = ordered_losers[step]
            rep_match = Match(
                athlete1_id=athlete1_id,
                athlete2_id=athlete2_id,
                round_type=f"repechage_{side}_{step}",
                stage=MatchStage.REPECHAGE.value,
                repechage_side=side,
                repechage_step=step,
                status=MatchStatus.NOT_STARTED.value,
            )
            db.add(rep_match)
            await db.flush()
            rep_bm = BracketMatch(
                bracket_id=bracket_id,
                round_number=base_round + step - 1,
                position=1 if side == "A" else 2,
                match_id=rep_match.id,
                next_slot=1,
            )
            db.add(rep_bm)


async def _advance_repechage_winner(
    db: AsyncSession, bracket_id: int, winner_id: int, side: str | None, step: int | None
) -> None:
    if side is None or step is None:
        return
    next_bm = (
        await db.execute(
            select(BracketMatch)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                Match.stage == MatchStage.REPECHAGE.value,
                Match.repechage_side == side,
                Match.repechage_step == step + 1,
            )
        )
    ).scalar_one_or_none()
    if next_bm is None:
        return
    next_match = await db.get(Match, next_bm.match_id)
    if next_match is None:
        return
    next_match.athlete1_id = winner_id


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
        if match.stage == MatchStage.REPECHAGE.value and match.winner_id is not None:
            await _advance_repechage_winner(
                db,
                bm.bracket_id,
                match.winner_id,
                match.repechage_side,
                match.repechage_step,
            )
        else:
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

            await _ensure_repechage_generated(db, bm.bracket_id)

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
