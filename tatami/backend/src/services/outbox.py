import json
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import uuid4

from champion_domain import (
    StructureMatchInput,
    StructureParticipantInput,
    build_structure_match,
    build_structure_participants,
    compute_main_rounds,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import EDGE_ID, EXTERNAL_API_URL
from src.models import Athlete, Bracket, BracketMatch, BracketParticipant, Match, OutboxItem
from src.services.outbox_upsert_dto import (
    make_bracket_upsert_payload,
    make_match_upsert_payload,
    make_sync_upserts_envelope,
)


async def get_bracket_with_tournament_for_match(match_id: int, db: AsyncSession) -> Optional[Bracket]:
    """Get the bracket for a match with tournament preloaded."""
    bm_result = await db.execute(
        select(BracketMatch)
        .where(BracketMatch.match_id == match_id)
        .options(selectinload(BracketMatch.bracket).selectinload(Bracket.tournament))
    )
    bm = bm_result.scalar_one_or_none()
    if bm is None or bm.bracket is None:
        return None
    return bm.bracket


async def get_bracket_with_tournament(bracket_id: int, db: AsyncSession) -> Optional[Bracket]:
    result = await db.execute(
        select(Bracket).where(Bracket.id == bracket_id).options(selectinload(Bracket.tournament))
    )
    return result.scalar_one_or_none()


async def create_outbox_entry(
    db: AsyncSession,
    item_type: str,
    aggregate_id: str,
    aggregate_version: int,
    payload: Optional[dict[str, Any]] = None,
    local_tournament_id: Optional[int] = None,
    external_tournament_id: Optional[int] = None,
    match_id: Optional[int] = None,
) -> OutboxItem:
    """Create an outbox entry that targets master /sync/upserts API."""
    if local_tournament_id is None:
        raise ValueError("local_tournament_id is required for sync upserts")
    if external_tournament_id is None:
        raise ValueError("external_tournament_id is required for sync upserts")

    outbox_item = OutboxItem(
        tournament_id=local_tournament_id,
        match_id=match_id,
        endpoint=f"{EXTERNAL_API_URL}/sync/upserts",
        method="POST",
        payload=None,
        status="pending",
        retry_count=0,
        max_retries=30,
    )

    db.add(outbox_item)
    await db.flush()

    envelope = make_sync_upserts_envelope(
        edge_id=EDGE_ID,
        tournament_id=external_tournament_id,
        event_id=uuid4(),
        seq=outbox_item.id,
        item_type=item_type,
        aggregate_id=aggregate_id,
        aggregate_version=aggregate_version,
        occurred_at=datetime.now(UTC),
        payload=payload or {},
    )
    outbox_item.payload = json.dumps(envelope)
    await db.flush()

    return outbox_item


async def create_match_start_outbox(match: Match, aggregate_version: int, db: AsyncSession) -> OutboxItem:
    """Create outbox entry with full match state."""
    bracket = await get_bracket_with_tournament_for_match(match.id, db)
    tournament = bracket.tournament if bracket is not None else None
    athlete1 = await db.get(Athlete, match.athlete1_id) if match.athlete1_id is not None else None
    athlete2 = await db.get(Athlete, match.athlete2_id) if match.athlete2_id is not None else None

    return await create_outbox_entry(
        db=db,
        item_type="match.upsert",
        aggregate_id=match.external_id,
        aggregate_version=aggregate_version,
        payload=make_match_upsert_payload(
            athlete1_id=athlete1.external_id if athlete1 else None,
            athlete2_id=athlete2.external_id if athlete2 else None,
            winner_id=None,
            round_type=match.round_type,
            stage=match.stage,
            repechage_side=match.repechage_side,
            repechage_step=match.repechage_step,
            score_athlete1=match.score_athlete1,
            score_athlete2=match.score_athlete2,
            status=match.status,
            started_at=match.started_at,
            ended_at=match.ended_at,
        ),
        local_tournament_id=tournament.id if tournament else None,
        external_tournament_id=tournament.external_id if tournament else None,
        match_id=match.id,
    )


async def create_match_finish_outbox(
    match: Match,
    winner_external_id: int,
    score_athlete1: int,
    score_athlete2: int,
    aggregate_version: int,
    db: AsyncSession,
) -> OutboxItem:
    """Create outbox entry with full match state after finish."""
    bracket = await get_bracket_with_tournament_for_match(match.id, db)
    tournament = bracket.tournament if bracket is not None else None
    athlete1 = await db.get(Athlete, match.athlete1_id) if match.athlete1_id is not None else None
    athlete2 = await db.get(Athlete, match.athlete2_id) if match.athlete2_id is not None else None

    return await create_outbox_entry(
        db=db,
        item_type="match.upsert",
        aggregate_id=match.external_id,
        aggregate_version=aggregate_version,
        payload=make_match_upsert_payload(
            athlete1_id=athlete1.external_id if athlete1 else None,
            athlete2_id=athlete2.external_id if athlete2 else None,
            winner_id=winner_external_id,
            round_type=match.round_type,
            stage=match.stage,
            repechage_side=match.repechage_side,
            repechage_step=match.repechage_step,
            score_athlete1=score_athlete1,
            score_athlete2=score_athlete2,
            status=match.status,
            started_at=match.started_at,
            ended_at=match.ended_at,
        ),
        local_tournament_id=tournament.id if tournament else None,
        external_tournament_id=tournament.external_id if tournament else None,
        match_id=match.id,
    )


async def create_match_scores_outbox(match: Match, aggregate_version: int, db: AsyncSession) -> OutboxItem:
    """Create outbox entry with full match state after score update."""
    bracket = await get_bracket_with_tournament_for_match(match.id, db)
    tournament = bracket.tournament if bracket is not None else None
    athlete1 = await db.get(Athlete, match.athlete1_id) if match.athlete1_id is not None else None
    athlete2 = await db.get(Athlete, match.athlete2_id) if match.athlete2_id is not None else None
    winner = await db.get(Athlete, match.winner_id) if match.winner_id is not None else None

    return await create_outbox_entry(
        db=db,
        item_type="match.upsert",
        aggregate_id=match.external_id,
        aggregate_version=aggregate_version,
        payload=make_match_upsert_payload(
            athlete1_id=athlete1.external_id if athlete1 else None,
            athlete2_id=athlete2.external_id if athlete2 else None,
            winner_id=winner.external_id if winner else None,
            round_type=match.round_type,
            stage=match.stage,
            repechage_side=match.repechage_side,
            repechage_step=match.repechage_step,
            score_athlete1=match.score_athlete1,
            score_athlete2=match.score_athlete2,
            status=match.status,
            started_at=match.started_at,
            ended_at=match.ended_at,
        ),
        local_tournament_id=tournament.id if tournament else None,
        external_tournament_id=tournament.external_id if tournament else None,
        match_id=match.id,
    )


async def create_bracket_upsert_outbox(bracket: Bracket, db: AsyncSession) -> OutboxItem:
    """Create outbox entry with full bracket state."""
    bracket_with_tournament = await get_bracket_with_tournament(bracket.id, db)
    tournament = bracket_with_tournament.tournament if bracket_with_tournament is not None else None

    participants_result = await db.execute(
        select(BracketParticipant)
        .where(BracketParticipant.bracket_id == bracket.id)
        .options(selectinload(BracketParticipant.athlete))
        .order_by(BracketParticipant.seed.asc())
    )
    participants = participants_result.scalars().all()

    matches_result = await db.execute(
        select(BracketMatch)
        .where(BracketMatch.bracket_id == bracket.id)
        .options(
            selectinload(BracketMatch.match).selectinload(Match.athlete1),
            selectinload(BracketMatch.match).selectinload(Match.athlete2),
        )
        .order_by(BracketMatch.round_number.asc(), BracketMatch.position.asc())
    )
    bracket_matches = matches_result.scalars().all()

    participants_count = await db.scalar(
        select(func.count())
        .select_from(BracketParticipant)
        .where(BracketParticipant.bracket_id == bracket.id, BracketParticipant.athlete_id.is_not(None))
    )
    count = int(participants_count) if participants_count is not None else None
    main_rounds = compute_main_rounds(count)

    payload_participants = build_structure_participants(
        StructureParticipantInput(
            athlete_id=participant.athlete.external_id if participant.athlete else None,
            seed=participant.seed,
        )
        for participant in participants
    )

    payload_matches = []
    for bm in bracket_matches:
        match = bm.match
        if match is None:
            continue

        winner_external_id: int | None = None
        if match.winner_id is not None:
            winner = await db.get(Athlete, match.winner_id)
            winner_external_id = winner.external_id if winner else None

        payload_matches.append(
            build_structure_match(
                input_data=StructureMatchInput(
                    id=match.external_id,
                    round_number=bm.round_number,
                    position=bm.position,
                    next_slot=bm.next_slot,
                    status=match.status,
                    athlete1_id=match.athlete1.external_id if match.athlete1 else None,
                    athlete2_id=match.athlete2.external_id if match.athlete2 else None,
                    winner_id=winner_external_id,
                    score_athlete1=match.score_athlete1,
                    score_athlete2=match.score_athlete2,
                    started_at=match.started_at,
                    ended_at=match.ended_at,
                ),
                main_rounds=main_rounds,
            )
        )

    payload = make_bracket_upsert_payload(
        bracket_type=bracket.type,
        group_id=bracket.group_id,
        status=bracket.status,
        state=bracket.state,
        participants=payload_participants,
        matches=payload_matches,
    )

    return await create_outbox_entry(
        db=db,
        item_type="bracket.upsert",
        aggregate_id=str(bracket.external_id),
        aggregate_version=bracket.version,
        payload=payload,
        local_tournament_id=tournament.id if tournament else None,
        external_tournament_id=tournament.external_id if tournament else None,
        match_id=None,
    )
