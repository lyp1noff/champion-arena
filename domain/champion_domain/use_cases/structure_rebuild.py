from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class StructureParticipant:
    athlete_id: int | None
    seed: int


@dataclass(frozen=True)
class StructureMatch:
    id: UUID
    round_number: int
    position: int
    next_slot: int | None
    round_type: str | None
    stage: str
    status: str
    athlete1_id: int | None
    athlete2_id: int | None
    winner_id: int | None
    score_athlete1: int | None
    score_athlete2: int | None
    repechage_side: str | None
    repechage_step: int | None
    started_at: datetime | None
    ended_at: datetime | None
