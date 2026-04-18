from dataclasses import dataclass


@dataclass(frozen=True)
class SeededParticipant:
    seed: int
    athlete_id: int | None


@dataclass(frozen=True)
class PlannedRoundRobinMatch:
    round_number: int
    position: int
    athlete1_id: int
    athlete2_id: int
    round_type: str = "group"


def plan_round_robin_bracket(participants: list[SeededParticipant]) -> list[PlannedRoundRobinMatch]:
    if len(participants) < 2:
        return []

    ordered = list(participants)
    participant_count = len(ordered)
    if participant_count % 2 != 0:
        ordered.append(SeededParticipant(seed=participant_count + 1, athlete_id=None))
        participant_count += 1

    players = list(range(participant_count))
    planned: list[PlannedRoundRobinMatch] = []
    position = 1

    for _ in range(participant_count - 1):
        mid = participant_count // 2
        for idx in range(mid):
            p1_idx, p2_idx = players[idx], players[participant_count - 1 - idx]
            p1 = ordered[p1_idx]
            p2 = ordered[p2_idx]
            if p1.athlete_id is None or p2.athlete_id is None:
                continue
            athlete1_id = p1.athlete_id if p1.seed < p2.seed else p2.athlete_id
            athlete2_id = p2.athlete_id if p1.seed < p2.seed else p1.athlete_id
            planned.append(
                PlannedRoundRobinMatch(
                    round_number=1,
                    position=position,
                    athlete1_id=athlete1_id,
                    athlete2_id=athlete2_id,
                )
            )
            position += 1

        players = [players[0]] + [players[-1]] + players[1:-1]

    return planned
