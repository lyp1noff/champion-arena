from dataclasses import dataclass

from champion_domain.match_results import match_loser_id


@dataclass(frozen=True)
class FinishedMainMatch:
    round_number: int
    winner_id: int | None
    athlete1_id: int | None
    athlete2_id: int | None


@dataclass(frozen=True)
class PlannedRepechageMatch:
    side: str
    step: int
    round_number: int
    position: int
    athlete1_id: int | None
    athlete2_id: int | None


@dataclass(frozen=True)
class RepechageAdvanceTarget:
    side: str
    step: int


@dataclass(frozen=True)
class RepechageGenerationResult:
    plans: list["PlannedRepechageMatch"]
    max_step_by_side: dict[str, int]


def compute_repechage_advance_target(side: str | None, step: int | None) -> RepechageAdvanceTarget | None:
    if side is None or step is None:
        return None
    normalized_side = side.upper()
    if normalized_side not in {"A", "B"}:
        return None
    if step < 1:
        return None
    return RepechageAdvanceTarget(side=normalized_side, step=step + 1)


def build_repechage_plan(
    finalist_a_id: int,
    finalist_b_id: int,
    finished_main_matches: list[FinishedMainMatch],
    base_round: int,
) -> list[PlannedRepechageMatch]:
    plans: list[PlannedRepechageMatch] = []

    for side, finalist_id, position in (("A", finalist_a_id, 1), ("B", finalist_b_id, 2)):
        losses: list[tuple[int, int]] = []
        for item in finished_main_matches:
            if item.winner_id != finalist_id:
                continue
            loser_id = match_loser_id(item.winner_id, item.athlete1_id, item.athlete2_id)
            if loser_id is None:
                continue
            losses.append((item.round_number, loser_id))

        losses.sort(key=lambda pair: pair[0])
        ordered_losers: list[int] = []
        seen: set[int] = set()
        for _, loser in losses:
            if loser in seen:
                continue
            seen.add(loser)
            ordered_losers.append(loser)

        if len(ordered_losers) < 2:
            continue

        for step in range(1, len(ordered_losers)):
            plans.append(
                PlannedRepechageMatch(
                    side=side,
                    step=step,
                    round_number=base_round + step - 1,
                    position=position,
                    athlete1_id=ordered_losers[0] if step == 1 else None,
                    athlete2_id=ordered_losers[step],
                )
            )

    return plans


def should_generate_repechage(
    bracket_type: str,
    main_rounds: int,
    has_repechage_matches: bool,
    finalist_a_id: int | None,
    finalist_b_id: int | None,
) -> bool:
    if bracket_type != "single_elimination":
        return False
    if has_repechage_matches:
        return False
    if main_rounds < 2:
        return False
    return finalist_a_id is not None and finalist_b_id is not None


def should_attempt_repechage_generation_on_finish(
    origin: str,
    stage: str,
    *,
    repechage_stage_value: str = "repechage",
) -> bool:
    return origin == "local" and stage != repechage_stage_value


def should_publish_structure_after_match_finish(
    *,
    is_repechage_match: bool,
    generated_repechage: bool,
) -> bool:
    return (not is_repechage_match) and generated_repechage


def plan_repechage_generation(
    finalist_a_id: int,
    finalist_b_id: int,
    finished_main_matches: list[FinishedMainMatch],
    base_round: int,
) -> RepechageGenerationResult:
    plans = build_repechage_plan(
        finalist_a_id=finalist_a_id,
        finalist_b_id=finalist_b_id,
        finished_main_matches=finished_main_matches,
        base_round=base_round,
    )
    max_step_by_side: dict[str, int] = {}
    for plan in plans:
        max_step_by_side[plan.side] = max(max_step_by_side.get(plan.side, 0), plan.step)
    return RepechageGenerationResult(
        plans=plans,
        max_step_by_side=max_step_by_side,
    )
