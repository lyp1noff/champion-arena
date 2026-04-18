from datetime import UTC, datetime
from uuid import UUID

from champion_domain import derive_bracket_state_from_status
from champion_domain import compute_bracket_placements, PlacementMatchInput
from pydantic import BaseModel, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
from src.models import Athlete, Bracket, BracketMatch, BracketParticipant, Match, SyncEdgeState, SyncInboxEvent
from src.schemas import (
    MatchUpdate,
    SyncConflict,
    SyncStatusResponse,
    SyncUpsertItem,
    SyncUpsertsRequest,
    SyncUpsertsResponse,
)
from src.services.broadcast import broadcast
from src.services.bracket_upsert_dto import parse_structure_payload_dto


class SyncApplyConflict(Exception):
    def __init__(self, reason: str, expected_version: int | None = None, received_version: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.expected_version = expected_version
        self.received_version = received_version


class MatchUpsertPayloadDTO(BaseModel):
    athlete1_id: int | None = None
    athlete2_id: int | None = None
    winner_id: int | None = None
    round_type: str | None = None
    stage: str = "main"
    repechage_side: str | None = None
    repechage_step: int | None = None
    score_athlete1: int | None = None
    score_athlete2: int | None = None
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None


async def _get_or_create_edge_state(db: AsyncSession, edge_id: str, tournament_id: int) -> SyncEdgeState:
    edge_state = await db.get(SyncEdgeState, (edge_id, tournament_id))
    if edge_state is None:
        edge_state = SyncEdgeState(edge_id=edge_id, tournament_id=tournament_id, last_applied_seq=0)
        db.add(edge_state)
        await db.flush()
    return edge_state


async def _match_bracket_state(db: AsyncSession, match_id: UUID) -> tuple[int, int]:
    result = await db.execute(
        select(Bracket.id, Bracket.version)
        .join(BracketMatch, BracketMatch.bracket_id == Bracket.id)
        .where(BracketMatch.match_id == match_id)
    )
    row = result.first()
    if row is None:
        raise SyncApplyConflict("aggregate_not_found")
    return int(row[0]), int(row[1])


async def _resolve_athlete_id(db: AsyncSession, athlete_id: int | None) -> int | None:
    if athlete_id is None:
        return None
    athlete = await db.get(Athlete, athlete_id)
    if athlete is None:
        raise SyncApplyConflict("aggregate_not_found")
    return athlete.id


async def _broadcast_sync_refresh(tournament_id: int, match_id: str) -> None:
    try:
        await broadcast.publish(
            channel=f"tournament:{tournament_id}",
            message=MatchUpdate(
                match_id=match_id,
                score_athlete1=None,
                score_athlete2=None,
                status=None,
            ).model_dump_json(),
        )
    except Exception as exc:
        logger.error(f"Error broadcasting sync update: {exc}")


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
        repechage_stage_value="repechage",
        finished_status_value="finished",
    )

    bracket.place_1_id = placements.place_1_id
    bracket.place_2_id = placements.place_2_id
    bracket.place_3_a_id = placements.place_3_a_id
    bracket.place_3_b_id = placements.place_3_b_id


async def _apply_match_upsert(db: AsyncSession, item: SyncUpsertItem) -> tuple[int, int, str]:
    try:
        match_id = UUID(item.aggregate_id)
    except ValueError as exc:
        raise SyncApplyConflict("invalid_aggregate_id") from exc

    match = await db.get(Match, match_id)
    if match is None:
        raise SyncApplyConflict("aggregate_not_found")

    try:
        payload = MatchUpsertPayloadDTO.model_validate(item.payload)
    except ValidationError as exc:
        raise SyncApplyConflict("invalid_payload") from exc

    bracket_id, current_version = await _match_bracket_state(db, match_id)
    if item.aggregate_version < current_version:
        raise SyncApplyConflict(
            "version_conflict",
            expected_version=current_version,
            received_version=item.aggregate_version,
        )

    match.athlete1_id = await _resolve_athlete_id(db, payload.athlete1_id)
    match.athlete2_id = await _resolve_athlete_id(db, payload.athlete2_id)
    match.winner_id = await _resolve_athlete_id(db, payload.winner_id)
    match.round_type = payload.round_type
    match.stage = payload.stage
    match.repechage_side = payload.repechage_side
    match.repechage_step = payload.repechage_step
    match.score_athlete1 = payload.score_athlete1
    match.score_athlete2 = payload.score_athlete2
    match.status = payload.status
    match.started_at = payload.started_at
    match.ended_at = payload.ended_at

    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        raise SyncApplyConflict("aggregate_not_found")
    bracket.version = max(bracket.version, item.aggregate_version)
    if match.status in {"started", "finished"} and bracket.status != "finished":
        bracket.status = "started"
        bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)
    await _recompute_bracket_placements(db, bracket_id)
    return bracket_id, bracket.tournament_id, str(match.id)


async def _apply_bracket_upsert(db: AsyncSession, item: SyncUpsertItem) -> tuple[int, int, str]:
    try:
        bracket_id = int(item.aggregate_id)
    except ValueError as exc:
        raise SyncApplyConflict("invalid_aggregate_id") from exc

    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        raise SyncApplyConflict("aggregate_not_found")

    if item.aggregate_version < bracket.version:
        raise SyncApplyConflict(
            "version_conflict",
            expected_version=bracket.version,
            received_version=item.aggregate_version,
        )

    try:
        participants, matches, payload_state, payload_status = parse_structure_payload_dto(item.payload)
    except ValueError as exc:
        raise SyncApplyConflict(str(exc)) from exc

    bracket.type = str(item.payload.get("type") or bracket.type)
    bracket.group_id = int(item.payload.get("group_id") or bracket.group_id)
    bracket.version = item.aggregate_version
    if isinstance(payload_status, str):
        bracket.status = payload_status
    if payload_state is not None:
        bracket.state = payload_state
    else:
        bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)

    bracket.place_1_id = None
    bracket.place_2_id = None
    bracket.place_3_a_id = None
    bracket.place_3_b_id = None

    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))
    await db.execute(delete(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))

    for participant in sorted(participants, key=lambda entry: entry.seed):
        await _resolve_athlete_id(db, participant.athlete_id)
        db.add(
            BracketParticipant(
                bracket_id=bracket_id,
                athlete_id=participant.athlete_id,
                seed=participant.seed,
            )
        )

    for planned_match in matches:
        db.add(
            Match(
                id=planned_match.id,
                athlete1_id=planned_match.athlete1_id,
                athlete2_id=planned_match.athlete2_id,
                winner_id=planned_match.winner_id,
                score_athlete1=planned_match.score_athlete1,
                score_athlete2=planned_match.score_athlete2,
                round_type=planned_match.round_type,
                stage=planned_match.stage,
                repechage_side=planned_match.repechage_side,
                repechage_step=planned_match.repechage_step,
                status=planned_match.status,
                started_at=planned_match.started_at,
                ended_at=planned_match.ended_at,
            )
        )
        db.add(
            BracketMatch(
                round_number=planned_match.round_number,
                position=planned_match.position,
                next_slot=planned_match.next_slot,
                bracket_id=bracket_id,
                match_id=planned_match.id,
            )
        )
    await db.flush()
    await _recompute_bracket_placements(db, bracket_id)
    return bracket_id, bracket.tournament_id, f"bracket:{bracket_id}"


async def _apply_upsert(db: AsyncSession, item: SyncUpsertItem) -> tuple[int, int, str]:
    if item.type == "match.upsert":
        return await _apply_match_upsert(db, item)
    if item.type == "bracket.upsert":
        return await _apply_bracket_upsert(db, item)
    raise SyncApplyConflict("unsupported_upsert_type")


async def get_status(db: AsyncSession, edge_id: str, tournament_id: int) -> SyncStatusResponse:
    edge_state = await _get_or_create_edge_state(db, edge_id, tournament_id)
    await db.commit()
    return SyncStatusResponse(
        edge_id=edge_state.edge_id,
        tournament_id=edge_state.tournament_id,
        last_applied_seq=edge_state.last_applied_seq,
        server_time=datetime.now(UTC),
    )


async def apply_upserts(db: AsyncSession, payload: SyncUpsertsRequest) -> SyncUpsertsResponse:
    accepted: list[int] = []
    duplicates: list[int] = []
    conflicts: list[SyncConflict] = []

    edge_state = await _get_or_create_edge_state(db, payload.edge_id, payload.tournament_id)
    await db.commit()

    for item in sorted(payload.items, key=lambda entry: entry.seq):
        existing = await db.execute(
            select(SyncInboxEvent).where(
                SyncInboxEvent.edge_id == payload.edge_id,
                SyncInboxEvent.tournament_id == payload.tournament_id,
                SyncInboxEvent.seq == item.seq,
            )
        )
        if existing.scalar_one_or_none() is not None:
            duplicates.append(item.seq)
            continue

        expected_seq = edge_state.last_applied_seq + 1
        if item.seq != expected_seq:
            # Seq is diagnostic only for upsert flow; keep a warning trail without blocking the payload.
            conflicts.append(SyncConflict(seq=item.seq, reason="seq_gap"))

        inbox_event = SyncInboxEvent(
            event_id=item.event_id,
            edge_id=payload.edge_id,
            tournament_id=payload.tournament_id,
            seq=item.seq,
            applied=False,
        )
        db.add(inbox_event)
        await db.flush()

        try:
            bracket_id, tournament_id, broadcast_match_id = await _apply_upsert(db, item)
        except SyncApplyConflict as exc:
            inbox_event.error = exc.reason
            conflicts.append(
                SyncConflict(
                    seq=item.seq,
                    reason=exc.reason,
                    expected_version=exc.expected_version,
                    received_version=exc.received_version,
                )
            )
            edge_state.last_applied_seq = max(edge_state.last_applied_seq, item.seq)
            await db.commit()
            continue
        except Exception:
            inbox_event.error = "apply_failed"
            conflicts.append(SyncConflict(seq=item.seq, reason="apply_failed"))
            edge_state.last_applied_seq = max(edge_state.last_applied_seq, item.seq)
            await db.commit()
            continue

        inbox_event.applied = True
        inbox_event.error = None
        edge_state.last_applied_seq = max(edge_state.last_applied_seq, item.seq)
        accepted.append(item.seq)
        await db.commit()
        await _broadcast_sync_refresh(tournament_id, broadcast_match_id)

    return SyncUpsertsResponse(
        accepted=accepted,
        duplicates=duplicates,
        conflicts=conflicts,
        last_applied_seq=edge_state.last_applied_seq,
    )
