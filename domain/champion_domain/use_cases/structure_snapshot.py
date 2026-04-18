from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from champion_domain.use_cases.bracket_labels import classify_bracket_match
from champion_domain.use_cases.structure_rebuild import StructureMatch, StructureParticipant


@dataclass(frozen=True)
class StructureParticipantInput:
    athlete_id: int | None
    seed: int


@dataclass(frozen=True)
class StructureMatchInput:
    id: str
    round_number: int
    position: int
    next_slot: int | None
    status: str
    athlete1_id: int | None
    athlete2_id: int | None
    winner_id: int | None
    score_athlete1: int | None
    score_athlete2: int | None
    started_at: datetime | None
    ended_at: datetime | None


def build_structure_participant(input_data: StructureParticipantInput) -> StructureParticipant:
    return StructureParticipant(
        athlete_id=input_data.athlete_id,
        seed=input_data.seed,
    )


def build_structure_participants(items: Iterable[StructureParticipantInput]) -> list[StructureParticipant]:
    return [build_structure_participant(item) for item in items]


def build_structure_match(input_data: StructureMatchInput, main_rounds: int) -> StructureMatch:
    classification = classify_bracket_match(
        round_number=input_data.round_number,
        position=input_data.position,
        main_rounds=main_rounds,
    )
    return StructureMatch(
        id=UUID(str(input_data.id)),
        round_number=input_data.round_number,
        position=input_data.position,
        next_slot=input_data.next_slot,
        round_type=classification.round_type,
        stage=classification.stage,
        status=input_data.status,
        athlete1_id=input_data.athlete1_id,
        athlete2_id=input_data.athlete2_id,
        winner_id=input_data.winner_id,
        score_athlete1=input_data.score_athlete1,
        score_athlete2=input_data.score_athlete2,
        repechage_side=classification.repechage_side,
        repechage_step=classification.repechage_step,
        started_at=input_data.started_at,
        ended_at=input_data.ended_at,
    )
