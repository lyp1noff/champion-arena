from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from champion_domain import (
    FinishedMainMatch,
    PlacementMatchInput,
    ProgressionAction,
    bump_bracket_version,
    can_finish_match,
    can_start_match,
    can_update_scores,
    compute_bracket_placements,
    decide_finish_flow_post,
    decide_finish_flow_runtime,
    derive_bracket_state_from_status,
    plan_repechage_generation,
    should_finish_tournament,
    should_generate_repechage,
)
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

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


def _match_stmt(match_id: MatchId, include_bracket_context: bool = False) -> Select[tuple[Match]]:
    options = [
        selectinload(Match.athlete1).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        selectinload(Match.athlete2).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
        selectinload(Match.winner).selectinload(Athlete.coach_links).selectinload(AthleteCoachLink.coach),
    ]
    if include_bracket_context:
        options.append(
            selectinload(Match.bracket_match).selectinload(BracketMatch.bracket).selectinload(Bracket.tournament)
        )
    return select(Match).options(*options).where(Match.id == match_id)


async def _load_match_or_404(db: AsyncSession, match_id: MatchId, include_bracket_context: bool = False) -> Match:
    result = await db.execute(_match_stmt(match_id, include_bracket_context=include_bracket_context))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(404, "Match not found")
    return match


async def _apply_winner_to_next_match(
    db: AsyncSession,
    bm: BracketMatch,
    winner_id: int,
    action: ProgressionAction,
) -> None:
    if action.kind == "repechage":
        next_bm = (
            await db.execute(
                select(BracketMatch)
                .join(Match, Match.id == BracketMatch.match_id)
                .where(
                    BracketMatch.bracket_id == bm.bracket_id,
                    Match.stage == MatchStage.REPECHAGE.value,
                    Match.repechage_side == action.repechage_side,
                    Match.repechage_step == action.repechage_step,
                )
            )
        ).scalar_one_or_none()
        if next_bm is None:
            return
        next_match = await db.get(Match, next_bm.match_id)
        if next_match is not None:
            next_match.athlete1_id = winner_id
        return

    if action.kind == "main":
        if action.main_round_number is None or action.main_position is None:
            return
        next_bm = (
            await db.execute(
                select(BracketMatch).where(
                    BracketMatch.bracket_id == bm.bracket_id,
                    BracketMatch.round_number == action.main_round_number,
                    BracketMatch.position == action.main_position,
                )
            )
        ).scalar_one_or_none()
        if next_bm is None:
            return
        next_match = await db.get(Match, next_bm.match_id)
        if next_match is None or next_match.stage != MatchStage.MAIN.value:
            return
        if action.slot == 1:
            next_match.athlete1_id = winner_id
        else:
            next_match.athlete2_id = winner_id


async def _recompute_bracket_placements(db: AsyncSession, bracket_id: int) -> None:
    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        return

    rows = (
        await db.execute(
            select(BracketMatch, Match)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(BracketMatch.bracket_id == bracket_id)
        )
    ).all()
    placements = compute_bracket_placements(
        [
            PlacementMatchInput(
                round_number=bm.round_number,
                stage=match.stage,
                status=match.status,
                winner_id=match.winner_id,
                athlete1_id=match.athlete1_id,
                athlete2_id=match.athlete2_id,
                repechage_side=match.repechage_side,
                repechage_step=match.repechage_step,
            )
            for bm, match in rows
        ],
        repechage_stage_value=MatchStage.REPECHAGE.value,
        finished_status_value=MatchStatus.FINISHED.value,
    )

    bracket.place_1_id = placements.place_1_id
    bracket.place_2_id = placements.place_2_id
    bracket.place_3_a_id = placements.place_3_a_id
    bracket.place_3_b_id = placements.place_3_b_id


async def _ensure_repechage_generated(db: AsyncSession, bracket_id: int) -> bool:
    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        return False

    has_repechage_matches = bool(
        await db.scalar(
            select(func.count())
            .select_from(Match)
            .join(BracketMatch, BracketMatch.match_id == Match.id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                Match.stage == MatchStage.REPECHAGE.value,
            )
        )
    )

    max_main_round = await db.scalar(
        select(func.max(BracketMatch.round_number))
        .join(Match, Match.id == BracketMatch.match_id)
        .where(
            BracketMatch.bracket_id == bracket_id,
            Match.stage == MatchStage.MAIN.value,
        )
    )
    if max_main_round is None:
        return False
    main_rounds = int(max_main_round)

    final_bm = (
        await db.execute(
            select(BracketMatch)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                BracketMatch.round_number == max_main_round,
                Match.stage == MatchStage.MAIN.value,
            )
        )
    ).scalar_one_or_none()
    if final_bm is None:
        return False

    final_match = await db.get(Match, final_bm.match_id)
    finalist_a_id = final_match.athlete1_id if final_match is not None else None
    finalist_b_id = final_match.athlete2_id if final_match is not None else None
    if not should_generate_repechage(
        bracket_type=bracket.type,
        main_rounds=main_rounds,
        has_repechage_matches=has_repechage_matches,
        finalist_a_id=finalist_a_id,
        finalist_b_id=finalist_b_id,
    ):
        return False

    finished_main_rows = (
        await db.execute(
            select(BracketMatch, Match)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(
                BracketMatch.bracket_id == bracket_id,
                Match.status == MatchStatus.FINISHED.value,
                Match.stage != MatchStage.REPECHAGE.value,
                BracketMatch.round_number < max_main_round,
            )
        )
    ).all()

    finished_main_matches = [
        FinishedMainMatch(
            round_number=bm_row.round_number,
            winner_id=match.winner_id,
            athlete1_id=match.athlete1_id,
            athlete2_id=match.athlete2_id,
        )
        for bm_row, match in finished_main_rows
    ]

    max_round = await db.scalar(
        select(func.max(BracketMatch.round_number)).where(BracketMatch.bracket_id == bracket_id)
    )
    base_round = int(max_round or 0) + 1

    generation = plan_repechage_generation(
        finalist_a_id=finalist_a_id,
        finalist_b_id=finalist_b_id,
        finished_main_matches=finished_main_matches,
        base_round=base_round,
    )
    if not generation.plans:
        return False

    for plan in generation.plans:
        rep_match = Match(
            athlete1_id=plan.athlete1_id,
            athlete2_id=plan.athlete2_id,
            round_type="round",
            stage=MatchStage.REPECHAGE.value,
            repechage_side=plan.side,
            repechage_step=plan.step,
            status=MatchStatus.NOT_STARTED.value,
        )
        db.add(rep_match)
        await db.flush()
        rep_bm = BracketMatch(
            bracket_id=bracket_id,
            round_number=plan.round_number,
            position=plan.position,
            match_id=rep_match.id,
            next_slot=1 if plan.step < generation.max_step_by_side.get(plan.side, plan.step) else None,
        )
        db.add(rep_bm)
    return True


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
    return await _load_match_or_404(db, match_id)


async def start_match(db: AsyncSession, match_id: MatchId) -> Match:
    match = await _load_match_or_404(db, match_id, include_bracket_context=True)
    can_start, start_error = can_start_match(match.status, match.athlete1_id, match.athlete2_id)
    if not can_start:
        raise HTTPException(400, start_error)

    match.status = MatchStatus.STARTED.value
    match.started_at = datetime.now(UTC)
    match.score_athlete1 = 0
    match.score_athlete2 = 0

    bracket = match.bracket_match.bracket if match.bracket_match else None
    if bracket and bracket.status != BracketStatus.FINISHED.value:
        bracket.status = BracketStatus.STARTED.value
        bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)
        bump_bracket_version(bracket)
        tournament = bracket.tournament
        if tournament and tournament.status != TournamentStatus.FINISHED.value:
            tournament.status = TournamentStatus.STARTED.value

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match


async def finish_match(
    db: AsyncSession,
    match_id: MatchId,
    result: MatchFinishRequest,
    origin: Literal["local", "sync"] = "local",
) -> Match:
    match = await _load_match_or_404(db, match_id)
    can_finish, finish_error = can_finish_match(match.status)
    if not can_finish:
        raise HTTPException(400, finish_error)

    match.score_athlete1 = result.score_athlete1
    match.score_athlete2 = result.score_athlete2
    match.winner_id = result.winner_id
    match.status = MatchStatus.FINISHED.value
    match.ended_at = datetime.now(UTC)

    bm_result = await db.execute(select(BracketMatch).where(BracketMatch.match_id == match.id))
    bm = bm_result.scalar_one_or_none()

    if bm:
        bracket = await db.get(Bracket, bm.bracket_id)
        if bracket is not None:
            bump_bracket_version(bracket)
        runtime = decide_finish_flow_runtime(
            origin=origin,
            stage=match.stage,
            current_round_number=bm.round_number,
            current_position=bm.position,
            explicit_next_slot=bm.next_slot,
            repechage_side=match.repechage_side,
            repechage_step=match.repechage_step,
            allow_implicit_main_slot=False,
            repechage_stage_value=MatchStage.REPECHAGE.value,
        )
        action = runtime.progression_action

        if action is not None and match.winner_id is not None:
            await _apply_winner_to_next_match(
                db,
                bm,
                match.winner_id,
                action,
            )

        generated_repechage = False
        if runtime.attempt_generate_repechage:
            generated_repechage = await _ensure_repechage_generated(db, bm.bracket_id)
        await _recompute_bracket_placements(db, bm.bracket_id)

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

        post = decide_finish_flow_post(
            is_repechage_match=match.stage == MatchStage.REPECHAGE.value,
            generated_repechage=generated_repechage,
            total_matches=total_in_bracket,
            finished_matches=finished_in_bracket,
            current_bracket_status=bracket.status if bracket is not None else None,
            finished_status_value=BracketStatus.FINISHED.value,
        )
        if post.completion.should_finish_bracket:
            if bracket:
                bracket.status = BracketStatus.FINISHED.value
                bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)
                unfinished_brackets = await db.scalar(
                    select(func.count())
                    .select_from(Bracket)
                    .where(
                        Bracket.tournament_id == bracket.tournament_id,
                        Bracket.status != BracketStatus.FINISHED.value,
                    )
                )
                if should_finish_tournament(unfinished_brackets):
                    tournament = await db.get(Tournament, bracket.tournament_id)
                    if tournament and tournament.status != TournamentStatus.FINISHED.value:
                        tournament.status = TournamentStatus.FINISHED.value

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match


async def update_match_scores(db: AsyncSession, match_id: MatchId, scores: MatchScoreUpdate) -> Match:
    match = await _load_match_or_404(db, match_id)

    can_update, update_error = can_update_scores(match.status)
    if not can_update:
        raise HTTPException(400, update_error)

    if scores.score_athlete1 is not None:
        match.score_athlete1 = scores.score_athlete1
    if scores.score_athlete2 is not None:
        match.score_athlete2 = scores.score_athlete2

    bracket_id = await db.scalar(select(BracketMatch.bracket_id).where(BracketMatch.match_id == match.id))
    if bracket_id is not None:
        bracket = await db.get(Bracket, bracket_id)
        if bracket is not None:
            bump_bracket_version(bracket)

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match


async def update_match_status(db: AsyncSession, match_id: MatchId, status: str) -> Match:
    match = await _load_match_or_404(db, match_id)
    if status not in [s.value for s in MatchStatus]:
        raise HTTPException(400, f"Invalid status: {status}")

    match.status = status
    bracket_id = await db.scalar(select(BracketMatch.bracket_id).where(BracketMatch.match_id == match.id))
    if bracket_id is not None:
        bracket = await db.get(Bracket, bracket_id)
        if bracket is not None:
            bump_bracket_version(bracket)
            if status == MatchStatus.STARTED.value:
                bracket.state = derive_bracket_state_from_status(BracketStatus.STARTED.value, bracket.state)

    await db.commit()
    await db.refresh(match)
    await broadcast_match_update(match, db)
    return match
