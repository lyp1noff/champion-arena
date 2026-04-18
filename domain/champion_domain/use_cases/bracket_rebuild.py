import math
from dataclasses import dataclass

from champion_domain.bracket_generation import distribute_byes_safely, get_round_type


@dataclass(frozen=True)
class PlannedMatch:
    round_number: int
    position: int
    round_type: str
    athlete1_id: int | None
    athlete2_id: int | None
    status: str
    winner_id: int | None
    next_slot: int | None


def plan_single_elimination(athlete_ids: list[int]) -> list[list[PlannedMatch]]:
    num_players = len(athlete_ids)
    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_rounds = int(math.log2(next_power_of_two))

    rounds: list[list[PlannedMatch]] = [[] for _ in range(total_rounds)]

    first_round_pairs = distribute_byes_safely(athlete_ids)
    for position, (a1, a2) in enumerate(first_round_pairs, start=1):
        bye = (a1 is None) != (a2 is None)
        rounds[0].append(
            PlannedMatch(
                round_number=1,
                position=position,
                round_type=get_round_type(0, total_rounds),
                athlete1_id=a1,
                athlete2_id=a2,
                status="finished" if bye else "not_started",
                winner_id=(a1 or a2) if bye else None,
                next_slot=None,
            )
        )

    for round_num in range(2, total_rounds + 1):
        num_matches = 2 ** (total_rounds - round_num)
        for pos in range(1, num_matches + 1):
            rounds[round_num - 1].append(
                PlannedMatch(
                    round_number=round_num,
                    position=pos,
                    round_type=get_round_type(round_num - 1, total_rounds),
                    athlete1_id=None,
                    athlete2_id=None,
                    status="not_started",
                    winner_id=None,
                    next_slot=None,
                )
            )

    for round_index in range(total_rounds - 1):
        updated_round: list[PlannedMatch] = []
        for i, planned in enumerate(rounds[round_index]):
            updated_round.append(
                PlannedMatch(
                    round_number=planned.round_number,
                    position=planned.position,
                    round_type=planned.round_type,
                    athlete1_id=planned.athlete1_id,
                    athlete2_id=planned.athlete2_id,
                    status=planned.status,
                    winner_id=planned.winner_id,
                    next_slot=1 if i % 2 == 0 else 2,
                )
            )
        rounds[round_index] = updated_round

    return rounds
