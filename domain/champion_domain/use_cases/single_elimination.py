from dataclasses import replace

from champion_domain.use_cases.bracket_rebuild import PlannedMatch, plan_single_elimination
from champion_domain.use_cases.match_progression import compute_advancement_target


def resolve_bye_advancements(planned_rounds: list[list[PlannedMatch]]) -> list[list[PlannedMatch]]:
    if not planned_rounds:
        return []

    index_by_round_and_position: dict[tuple[int, int], PlannedMatch] = {}
    for round_items in planned_rounds:
        for match in round_items:
            index_by_round_and_position[(match.round_number, match.position)] = match

    for round_items in planned_rounds[:-1]:
        for current in round_items:
            if current.status != "finished" or current.winner_id is None:
                continue

            target = compute_advancement_target(
                current_round_number=current.round_number,
                current_position=current.position,
                explicit_next_slot=current.next_slot,
            )
            next_match = index_by_round_and_position.get((target.round_number, target.position))
            if next_match is None:
                continue

            if target.slot == 1:
                patched = replace(next_match, athlete1_id=current.winner_id)
            else:
                patched = replace(next_match, athlete2_id=current.winner_id)

            index_by_round_and_position[(patched.round_number, patched.position)] = patched

    return [
        [index_by_round_and_position[(match.round_number, match.position)] for match in round_items]
        for round_items in planned_rounds
    ]


def plan_single_elimination_bracket(athlete_ids: list[int]) -> list[list[PlannedMatch]]:
    return resolve_bye_advancements(plan_single_elimination(athlete_ids))
