import math


def get_round_type(round_index: int, total_rounds: int) -> str:
    if round_index == total_rounds - 1:
        return "final"
    if round_index == total_rounds - 2:
        return "semifinal"
    if round_index == total_rounds - 3:
        return "quarterfinal"
    return "round"


def distribute_byes_safely(athlete_ids: list[int]) -> list[tuple[int | None, int | None]]:
    num_players = len(athlete_ids)
    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_matches = next_power_of_two // 2
    byes_needed = next_power_of_two - num_players

    pairs: list[tuple[int | None, int | None]] = []
    ids = athlete_ids.copy()

    bye_positions = set()
    if byes_needed > 0:
        step = total_matches / byes_needed
        for k in range(byes_needed):
            pos = round(k * step)
            bye_positions.add(pos)

    idx = 0
    for match_idx in range(total_matches):
        if match_idx in bye_positions and idx < len(ids):
            pairs.append((ids[idx], None))
            idx += 1
        else:
            a1 = ids[idx] if idx < len(ids) else None
            a2 = ids[idx + 1] if (idx + 1) < len(ids) else None
            pairs.append((a1, a2))
            idx += 2

    return pairs


def split_evenly[T](athletes: list[T], max_per_group: int = 4) -> list[list[T]]:
    n = len(athletes)
    min_groups = math.ceil(n / max_per_group)
    base_size = n // min_groups
    extra = n % min_groups

    groups: list[list[T]] = []
    start = 0
    for i in range(min_groups):
        size = base_size + (1 if i < extra else 0)
        groups.append(athletes[start : start + size])
        start += size
    return groups
