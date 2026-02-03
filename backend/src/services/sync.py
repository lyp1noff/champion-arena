from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from champion_domain import derive_bracket_state_from_status
from champion_domain.use_cases import parse_structure_payload
from src.models import Bracket, BracketMatch, BracketParticipant, Match, SyncEdgeState, SyncInboxEvent
from src.schemas import (
    MatchFinishRequest,
    MatchScoreUpdate,
    SyncCommandEvent,
    SyncCommandsRequest,
    SyncCommandsResponse,
    SyncConflict,
    SyncStatusResponse,
)
from src.services.matches import finish_match as finish_match_service
from src.services.matches import start_match as start_match_service
from src.services.matches import update_match_scores as update_match_scores_service
from src.services.matches import update_match_status as update_match_status_service


class SyncApplyConflict(Exception):
    def __init__(self, reason: str, expected_version: int | None = None, received_version: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.expected_version = expected_version
        self.received_version = received_version




def _is_idempotent_http_conflict(event_type: str, detail: str) -> bool:
    normalized = detail.lower()
    if event_type == "match.started":
        return "already in progress" in normalized or "already finished" in normalized
    if event_type == "match.finished":
        return "already finished" in normalized
    if event_type == "match.score_updated":
        return "cannot update scores" in normalized or "not started" in normalized
    return False

async def _get_or_create_edge_state(db: AsyncSession, edge_id: str) -> SyncEdgeState:
    edge_state = await db.get(SyncEdgeState, edge_id)
    if edge_state is None:
        edge_state = SyncEdgeState(edge_id=edge_id, last_applied_seq=0)
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


async def _apply_match_event(db: AsyncSession, event: SyncCommandEvent) -> int:
    try:
        match_id = UUID(event.aggregate_id)
    except ValueError as exc:
        raise SyncApplyConflict("invalid_aggregate_id") from exc

    bracket_id, current_version = await _match_bracket_state(db, match_id)
    expected_version = current_version + 1
    if event.aggregate_version != expected_version:
        raise SyncApplyConflict(
            "version_conflict",
            expected_version=expected_version,
            received_version=event.aggregate_version,
        )

    if event.event_type == "match.started":
        await start_match_service(db, match_id)
    elif event.event_type == "match.score_updated":
        payload = event.payload
        await update_match_scores_service(
            db,
            match_id,
            MatchScoreUpdate(
                score_athlete1=payload.get("score_athlete1"),
                score_athlete2=payload.get("score_athlete2"),
            ),
        )
    elif event.event_type == "match.finished":
        payload = event.payload
        winner_id = payload.get("winner_id")
        score_athlete1 = payload.get("score_athlete1")
        score_athlete2 = payload.get("score_athlete2")
        if not isinstance(winner_id, int) or not isinstance(score_athlete1, int) or not isinstance(score_athlete2, int):
            raise SyncApplyConflict("invalid_payload")
        await finish_match_service(
            db,
            match_id,
            MatchFinishRequest(
                score_athlete1=score_athlete1,
                score_athlete2=score_athlete2,
                winner_id=winner_id,
            ),
        )
    elif event.event_type == "match.status_updated":
        status = event.payload.get("status")
        if not isinstance(status, str):
            raise SyncApplyConflict("invalid_payload")
        await update_match_status_service(db, match_id, status)
    else:
        raise SyncApplyConflict("unsupported_event_type")

    return bracket_id


async def _apply_bracket_structure_rebuilt_event(db: AsyncSession, event: SyncCommandEvent) -> int:
    try:
        bracket_id = int(event.aggregate_id)
    except ValueError as exc:
        raise SyncApplyConflict("invalid_aggregate_id") from exc

    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        raise SyncApplyConflict("aggregate_not_found")

    expected_version = bracket.version + 1
    if event.aggregate_version != expected_version:
        raise SyncApplyConflict(
            "version_conflict",
            expected_version=expected_version,
            received_version=event.aggregate_version,
        )

    try:
        participants, matches, payload_state = parse_structure_payload(event.payload)
    except ValueError as exc:
        raise SyncApplyConflict(str(exc)) from exc

    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))
    await db.execute(delete(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))

    for participant in sorted(participants, key=lambda item: item.seed):
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

    bracket.version = event.aggregate_version
    payload_status = event.payload.get("status")
    if isinstance(payload_status, str):
        bracket.status = payload_status
    if payload_state is not None:
        bracket.state = payload_state
    else:
        bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)

    return bracket_id


async def _apply_event(db: AsyncSession, event: SyncCommandEvent) -> int:
    if event.aggregate_type == "match":
        return await _apply_match_event(db, event)
    if event.aggregate_type == "bracket" and event.event_type == "bracket.structure_rebuilt":
        return await _apply_bracket_structure_rebuilt_event(db, event)
    raise SyncApplyConflict("unsupported_aggregate_type")


async def apply_commands(db: AsyncSession, payload: SyncCommandsRequest) -> SyncCommandsResponse:
    accepted: list[int] = []
    duplicates: list[int] = []
    conflicts: list[SyncConflict] = []

    edge_state = await _get_or_create_edge_state(db, payload.edge_id)
    await db.commit()

    for event in sorted(payload.events, key=lambda item: item.seq):
        existing = await db.execute(
            select(SyncInboxEvent).where(
                SyncInboxEvent.edge_id == payload.edge_id,
                SyncInboxEvent.seq == event.seq,
            )
        )
        if existing.scalar_one_or_none() is not None:
            duplicates.append(event.seq)
            continue

        inbox_event = SyncInboxEvent(
            event_id=event.event_id,
            edge_id=payload.edge_id,
            seq=event.seq,
            applied=False,
        )
        db.add(inbox_event)
        await db.flush()

        try:
            await _apply_event(db, event)
        except SyncApplyConflict as exc:
            inbox_event.error = exc.reason
            conflicts.append(
                SyncConflict(
                    seq=event.seq,
                    reason=exc.reason,
                    expected_version=exc.expected_version,
                    received_version=exc.received_version,
                )
            )
            await db.commit()
            continue
        except HTTPException as exc:
            detail = str(exc.detail)
            if _is_idempotent_http_conflict(event.event_type, detail):
                inbox_event.applied = True
                inbox_event.error = None
                edge_state.last_applied_seq = max(edge_state.last_applied_seq, event.seq)
                accepted.append(event.seq)
                await db.commit()
                continue

            inbox_event.error = detail
            conflicts.append(SyncConflict(seq=event.seq, reason=detail))
            await db.commit()
            continue
        except Exception:
            inbox_event.error = "apply_failed"
            conflicts.append(SyncConflict(seq=event.seq, reason="apply_failed"))
            await db.commit()
            continue

        inbox_event.applied = True
        inbox_event.error = None
        edge_state.last_applied_seq = max(edge_state.last_applied_seq, event.seq)
        accepted.append(event.seq)
        await db.commit()

    return SyncCommandsResponse(
        accepted=accepted,
        duplicates=duplicates,
        conflicts=conflicts,
        last_applied_seq=edge_state.last_applied_seq,
    )


async def get_status(db: AsyncSession, edge_id: str) -> SyncStatusResponse:
    edge_state = await _get_or_create_edge_state(db, edge_id)
    await db.commit()
    return SyncStatusResponse(
        edge_id=edge_state.edge_id,
        last_applied_seq=edge_state.last_applied_seq,
        server_time=datetime.now(UTC),
    )
