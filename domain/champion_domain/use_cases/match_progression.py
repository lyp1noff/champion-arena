from dataclasses import dataclass


@dataclass(frozen=True)
class AdvancementTarget:
    round_number: int
    position: int
    slot: int


def compute_advancement_target(
    current_round_number: int,
    current_position: int,
    explicit_next_slot: int | None = None,
) -> AdvancementTarget:
    next_round = current_round_number + 1
    next_position = (current_position + 1) // 2

    slot = explicit_next_slot if explicit_next_slot in (1, 2) else 1 if current_position % 2 == 1 else 2

    return AdvancementTarget(round_number=next_round, position=next_position, slot=slot)


def is_bracket_finished(total_matches: int | None, finished_matches: int | None) -> bool:
    if total_matches is None or finished_matches is None:
        return False
    return total_matches > 0 and finished_matches == total_matches


@dataclass(frozen=True)
class NextMatchTarget:
    kind: str
    round_number: int | None = None
    position: int | None = None
    slot: int | None = None
    repechage_side: str | None = None
    repechage_step: int | None = None


@dataclass(frozen=True)
class ProgressionAction:
    kind: str
    slot: int | None = None
    main_round_number: int | None = None
    main_position: int | None = None
    repechage_side: str | None = None
    repechage_step: int | None = None
    repechage_round_number: int | None = None
    repechage_position: int | None = None


def compute_next_match_target(
    stage: str,
    current_round_number: int,
    current_position: int,
    explicit_next_slot: int | None,
    repechage_side: str | None = None,
    repechage_step: int | None = None,
    allow_implicit_main_slot: bool = False,
) -> NextMatchTarget | None:
    if stage == "repechage":
        from champion_domain.use_cases.repechage_runtime import compute_repechage_advance_target

        rep_target = compute_repechage_advance_target(repechage_side, repechage_step)
        if rep_target is None:
            return None
        return NextMatchTarget(
            kind="repechage",
            repechage_side=rep_target.side,
            repechage_step=rep_target.step,
        )

    if stage != "main":
        return None

    if explicit_next_slot is None and not allow_implicit_main_slot:
        return None

    target = compute_advancement_target(
        current_round_number=current_round_number,
        current_position=current_position,
        explicit_next_slot=explicit_next_slot,
    )
    return NextMatchTarget(
        kind="main",
        round_number=target.round_number,
        position=target.position,
        slot=target.slot,
    )


def compute_progression_action(
    stage: str,
    current_round_number: int,
    current_position: int,
    explicit_next_slot: int | None,
    repechage_side: str | None = None,
    repechage_step: int | None = None,
    allow_implicit_main_slot: bool = False,
    main_rounds: int | None = None,
) -> ProgressionAction | None:
    target = compute_next_match_target(
        stage=stage,
        current_round_number=current_round_number,
        current_position=current_position,
        explicit_next_slot=explicit_next_slot,
        repechage_side=repechage_side,
        repechage_step=repechage_step,
        allow_implicit_main_slot=allow_implicit_main_slot,
    )
    if target is None:
        return None

    if target.kind == "main":
        return ProgressionAction(
            kind="main",
            slot=target.slot,
            main_round_number=target.round_number,
            main_position=target.position,
        )

    repechage_round_number: int | None = None
    if main_rounds is not None and target.repechage_step is not None:
        repechage_round_number = main_rounds + target.repechage_step

    return ProgressionAction(
        kind="repechage",
        repechage_side=target.repechage_side,
        repechage_step=target.repechage_step,
        repechage_round_number=repechage_round_number,
        repechage_position=current_position,
    )
