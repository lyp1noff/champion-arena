from typing import Optional, List
from src.models import Athlete, Match, Bracket
from src.schemas import (
    BracketMatchAthlete,
    MatchSchema,
    BracketResponse,
    BracketParticipantSchema,
)


def serialize_athlete(athlete: Optional[Athlete]) -> Optional[BracketMatchAthlete]:
    if not athlete:
        return None
    return BracketMatchAthlete(
        id=athlete.id,
        first_name=athlete.first_name,
        last_name=athlete.last_name,
        coach_last_name=athlete.coach.last_name if athlete.coach else None,
    )


def serialize_match(match: Optional[Match]) -> Optional[MatchSchema]:
    if not match:
        return None
    return MatchSchema(
        id=match.id,
        round_type=match.round_type,
        athlete1=serialize_athlete(match.athlete1),
        athlete2=serialize_athlete(match.athlete2),
        winner=serialize_athlete(match.winner),
        score_athlete1=match.score_athlete1,
        score_athlete2=match.score_athlete2,
        is_finished=match.is_finished,
    )


def serialize_bracket(bracket: Bracket) -> BracketResponse:
    return BracketResponse(
        id=bracket.id,
        tournament_id=bracket.tournament_id,
        category=bracket.category.name,
        type=bracket.type,
        start_time=bracket.start_time,
        tatami=bracket.tatami,
        participants=[
            BracketParticipantSchema(
                seed=p.seed,
                first_name=p.athlete.first_name,
                last_name=p.athlete.last_name,
                coach_last_name=p.athlete.coach.last_name if p.athlete.coach else None,
            )
            for p in sorted(bracket.participants, key=lambda x: x.seed)
            if p.athlete
        ],
    )
