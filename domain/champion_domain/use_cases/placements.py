from dataclasses import dataclass

from champion_domain.match_results import final_loser_id, match_loser_id


@dataclass(frozen=True)
class PlacementMatchInput:
    round_number: int
    stage: str
    status: str
    winner_id: int | None
    athlete1_id: int | None
    athlete2_id: int | None
    repechage_side: str | None
    repechage_step: int | None


@dataclass(frozen=True)
class BracketPlacements:
    place_1_id: int | None
    place_2_id: int | None
    place_3_a_id: int | None
    place_3_b_id: int | None


def compute_bracket_placements(
    rows: list[PlacementMatchInput],
    *,
    repechage_stage_value: str = "repechage",
    finished_status_value: str = "finished",
) -> BracketPlacements:
    if not rows:
        return BracketPlacements(None, None, None, None)

    main_rows = [row for row in rows if row.stage != repechage_stage_value]
    if not main_rows:
        return BracketPlacements(None, None, None, None)

    final_round = max(row.round_number for row in main_rows)
    final_match = next((row for row in main_rows if row.round_number == final_round), None)
    if final_match is None:
        return BracketPlacements(None, None, None, None)

    if final_match.status != finished_status_value or final_match.winner_id is None:
        return BracketPlacements(None, None, None, None)

    place_1_id = final_match.winner_id
    place_2_id = final_loser_id(final_match)

    def direct_bronze_from_main_side(finalist_id: int) -> int | None:
        losses: list[tuple[int, int]] = []
        for row in main_rows:
            if row.round_number >= final_round:
                continue
            if row.status != finished_status_value:
                continue
            if row.winner_id != finalist_id:
                continue
            loser_id = match_loser_id(row)
            if loser_id is None:
                continue
            losses.append((row.round_number, loser_id))
        if len(losses) != 1:
            return None
        return losses[0][1]

    def bronze_from_repechage_side(side: str, finalist_id: int) -> int | None:
        side_rows = [row for row in rows if row.stage == repechage_stage_value and row.repechage_side == side]
        if not side_rows:
            return direct_bronze_from_main_side(finalist_id)

        last_match = sorted(side_rows, key=lambda row: row.repechage_step or 0)[-1]
        if last_match.status != finished_status_value:
            return None
        return last_match.winner_id

    finalist_a = final_match.athlete1_id
    finalist_b = final_match.athlete2_id
    place_3_a_id = bronze_from_repechage_side("A", finalist_a) if finalist_a is not None else None
    place_3_b_id = bronze_from_repechage_side("B", finalist_b) if finalist_b is not None else None

    occupied = {place_1_id, place_2_id}
    if place_3_a_id in occupied:
        place_3_a_id = None
    if place_3_b_id in occupied or place_3_b_id == place_3_a_id:
        place_3_b_id = None

    return BracketPlacements(
        place_1_id=place_1_id,
        place_2_id=place_2_id,
        place_3_a_id=place_3_a_id,
        place_3_b_id=place_3_b_id,
    )
