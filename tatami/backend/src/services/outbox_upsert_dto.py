from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from champion_domain.use_cases import StructureMatch, StructureParticipant
from pydantic import BaseModel


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


class StructureParticipantPayloadDTO(BaseModel):
    athlete_id: int | None = None
    seed: int


class StructureMatchPayloadDTO(BaseModel):
    id: str
    round_number: int
    position: int
    next_slot: int | None = None
    round_type: str
    stage: str
    repechage_side: str | None = None
    repechage_step: int | None = None
    status: str
    athlete1_id: int | None = None
    athlete2_id: int | None = None
    winner_id: int | None = None
    score_athlete1: int | None = None
    score_athlete2: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class BracketUpsertPayloadDTO(BaseModel):
    type: str
    group_id: int = 1
    status: str | None = None
    state: str | None = None
    participants: list[StructureParticipantPayloadDTO]
    matches: list[StructureMatchPayloadDTO]


class SyncUpsertItemDTO(BaseModel):
    event_id: UUID
    seq: int
    type: str
    aggregate_id: str
    aggregate_version: int
    occurred_at: datetime
    payload: dict[str, Any]


class SyncUpsertsEnvelopeDTO(BaseModel):
    edge_id: str
    tournament_id: int
    items: list[SyncUpsertItemDTO]


def make_match_upsert_payload(
    *,
    athlete1_id: int | None,
    athlete2_id: int | None,
    winner_id: int | None,
    round_type: str | None,
    stage: str,
    repechage_side: str | None,
    repechage_step: int | None,
    score_athlete1: int | None,
    score_athlete2: int | None,
    status: str,
    started_at: datetime | None,
    ended_at: datetime | None,
) -> dict[str, Any]:
    return MatchUpsertPayloadDTO(
        athlete1_id=athlete1_id,
        athlete2_id=athlete2_id,
        winner_id=winner_id,
        round_type=round_type,
        stage=stage,
        repechage_side=repechage_side,
        repechage_step=repechage_step,
        score_athlete1=score_athlete1,
        score_athlete2=score_athlete2,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
    ).model_dump(mode="json")


def make_bracket_upsert_payload(
    *,
    bracket_type: str,
    group_id: int,
    status: str | None,
    state: str | None,
    participants: list[StructureParticipant],
    matches: list[StructureMatch],
) -> dict[str, Any]:
    payload_participants = [
        StructureParticipantPayloadDTO(
            athlete_id=item.athlete_id,
            seed=item.seed,
        )
        for item in participants
    ]
    payload_matches = [
        StructureMatchPayloadDTO(
            id=str(item.id),
            round_number=item.round_number,
            position=item.position,
            next_slot=item.next_slot,
            round_type=item.round_type or "round",
            stage=item.stage,
            repechage_side=item.repechage_side,
            repechage_step=item.repechage_step,
            status=item.status,
            athlete1_id=item.athlete1_id,
            athlete2_id=item.athlete2_id,
            winner_id=item.winner_id,
            score_athlete1=item.score_athlete1,
            score_athlete2=item.score_athlete2,
            started_at=item.started_at,
            ended_at=item.ended_at,
        )
        for item in matches
    ]
    return BracketUpsertPayloadDTO(
        type=bracket_type,
        group_id=group_id,
        status=status,
        state=state,
        participants=payload_participants,
        matches=payload_matches,
    ).model_dump(mode="json")


def make_sync_upserts_envelope(
    *,
    edge_id: str,
    tournament_id: int,
    event_id: UUID,
    seq: int,
    item_type: str,
    aggregate_id: str,
    aggregate_version: int,
    occurred_at: datetime,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return SyncUpsertsEnvelopeDTO(
        edge_id=edge_id,
        tournament_id=tournament_id,
        items=[
            SyncUpsertItemDTO(
                event_id=event_id,
                seq=seq,
                type=item_type,
                aggregate_id=aggregate_id,
                aggregate_version=aggregate_version,
                occurred_at=occurred_at,
                payload=payload,
            )
        ],
    ).model_dump(mode="json")
