from champion_domain.use_cases.bracket_rebuild import PlannedMatch
from champion_domain.use_cases.round_robin import SeededParticipant, plan_round_robin_bracket
from champion_domain.use_cases.single_elimination import plan_single_elimination_bracket


def plan_bracket_matches(bracket_type: str, participants: list[SeededParticipant]) -> list[PlannedMatch]:
    ordered = sorted(participants, key=lambda item: item.seed)

    if bracket_type == "single_elimination":
        athlete_ids = [item.athlete_id for item in ordered if item.athlete_id is not None]
        rounds = plan_single_elimination_bracket(athlete_ids)
        return [match for round_items in rounds for match in round_items]

    if bracket_type == "round_robin":
        round_robin_matches = plan_round_robin_bracket(ordered)
        return [
            PlannedMatch(
                round_number=item.round_number,
                position=item.position,
                round_type=item.round_type,
                athlete1_id=item.athlete1_id,
                athlete2_id=item.athlete2_id,
                status="not_started",
                winner_id=None,
                next_slot=None,
            )
            for item in round_robin_matches
        ]

    raise ValueError("unsupported_bracket_type")
