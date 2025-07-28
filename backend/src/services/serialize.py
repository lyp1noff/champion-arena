from typing import Optional
from src.models import Athlete, Match, Bracket, BracketMatch
from src.schemas import (
    BracketMatchAthlete,
    MatchSchema,
    BracketResponse,
    BracketParticipantSchema,
    BracketMatchResponse,
    BracketMatchesFull,
)


def serialize_athlete(athlete: Optional[Athlete]) -> Optional[BracketMatchAthlete]:
    if not athlete:
        return None

    # Get coach names from the many-to-many relationship
    coaches_last_name = [
        link.coach.last_name for link in athlete.coach_links if link.coach is not None
    ]

    return BracketMatchAthlete(
        id=athlete.id,
        first_name=athlete.first_name,
        last_name=athlete.last_name,
        coaches_last_name=coaches_last_name,
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


def serialize_bracket_match(match: BracketMatch) -> BracketMatchResponse:
    return BracketMatchResponse(
        id=match.id,
        round_number=match.round_number,
        position=match.position,
        match=serialize_match(match.match),
        next_slot=match.next_slot,
    )


def serialize_bracket_matches_full(bracket: Bracket) -> BracketMatchesFull:
    matches = [
        BracketMatchResponse(
            id=bm.id,
            round_number=bm.round_number,
            position=bm.position,
            match=serialize_match(bm.match),
            next_slot=bm.next_slot,
        )
        for bm in bracket.matches
    ]

    return BracketMatchesFull(
        bracket_id=bracket.id,
        category=bracket.category.name if bracket.category else None,
        type=bracket.type,
        start_time=bracket.start_time,
        tatami=bracket.tatami,
        group_id=bracket.group_id,
        display_name=bracket.get_display_name(),
        matches=matches,
    )


def serialize_bracket(bracket: Bracket) -> BracketResponse:
    return BracketResponse(
        id=bracket.id,
        tournament_id=bracket.tournament_id,
        category=bracket.category.name,
        type=bracket.type,
        start_time=bracket.start_time,
        tatami=bracket.tatami,
        group_id=bracket.group_id,
        display_name=bracket.get_display_name(),
        participants=[
            BracketParticipantSchema(
                id=p.id,
                athlete_id=p.athlete.id,
                seed=p.seed,
                first_name=p.athlete.first_name,
                last_name=p.athlete.last_name,
                coaches_last_name=[
                    link.coach.last_name
                    for link in p.athlete.coach_links
                    if link.coach is not None
                ],
            )
            for p in sorted(bracket.participants, key=lambda x: x.seed)
            if p.athlete
        ],
    )
