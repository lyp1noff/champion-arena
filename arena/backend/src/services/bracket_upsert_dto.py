from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from champion_domain import (
    StructureMatchInput,
    StructureParticipantInput,
    build_structure_match,
    build_structure_participants,
    compute_main_rounds,
)
from champion_domain.use_cases import StructureMatch, StructureParticipant
from pydantic import BaseModel, Field, ValidationError


class StructureParticipantDTO(BaseModel):
    athlete_id: int | None = None
    seed: int = Field(ge=1)


class StructureMatchDTO(BaseModel):
    id: UUID
    round_number: int = Field(ge=1)
    position: int = Field(ge=1)
    next_slot: int | None = None
    round_type: str | None = None
    stage: str = "main"
    status: str
    athlete1_id: int | None = None
    athlete2_id: int | None = None
    winner_id: int | None = None
    score_athlete1: int | None = None
    score_athlete2: int | None = None
    repechage_side: str | None = None
    repechage_step: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class BracketStructureSnapshotDTO(BaseModel):
    status: str | None = None
    participants: list[StructureParticipantDTO]
    matches: list[StructureMatchDTO]
    state: str | None = None


def parse_structure_payload_dto(
    payload: dict[str, Any],
) -> tuple[list[StructureParticipant], list[StructureMatch], str | None, str | None]:
    try:
        snapshot = BracketStructureSnapshotDTO.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("invalid_payload") from exc

    participants = build_structure_participants(
        StructureParticipantInput(
            athlete_id=item.athlete_id,
            seed=item.seed,
        )
        for item in snapshot.participants
    )
    participant_count = sum(1 for item in participants if item.athlete_id is not None)
    main_rounds = compute_main_rounds(participant_count)

    matches = [
        build_structure_match(
            input_data=StructureMatchInput(
                id=str(item.id),
                round_number=item.round_number,
                position=item.position,
                next_slot=item.next_slot,
                status=item.status,
                athlete1_id=item.athlete1_id,
                athlete2_id=item.athlete2_id,
                winner_id=item.winner_id,
                score_athlete1=item.score_athlete1,
                score_athlete2=item.score_athlete2,
                started_at=item.started_at,
                ended_at=item.ended_at,
            ),
            main_rounds=main_rounds,
        )
        for item in snapshot.matches
    ]
    return participants, matches, snapshot.state, snapshot.status
