from dataclasses import dataclass

from champion_domain.use_cases.match_progression import ProgressionAction, compute_progression_action
from champion_domain.use_cases.repechage_runtime import should_attempt_repechage_generation_on_finish


@dataclass(frozen=True)
class FinishRuntimeDecision:
    progression_action: ProgressionAction | None
    attempt_generate_repechage: bool


def decide_finish_runtime(
    *,
    origin: str,
    stage: str,
    current_round_number: int,
    current_position: int,
    explicit_next_slot: int | None,
    repechage_side: str | None = None,
    repechage_step: int | None = None,
    allow_implicit_main_slot: bool = False,
    main_rounds: int | None = None,
    repechage_stage_value: str = "repechage",
) -> FinishRuntimeDecision:
    progression_action = compute_progression_action(
        stage=stage,
        current_round_number=current_round_number,
        current_position=current_position,
        explicit_next_slot=explicit_next_slot,
        repechage_side=repechage_side,
        repechage_step=repechage_step,
        allow_implicit_main_slot=allow_implicit_main_slot,
        main_rounds=main_rounds,
    )
    return FinishRuntimeDecision(
        progression_action=progression_action,
        attempt_generate_repechage=should_attempt_repechage_generation_on_finish(
            origin=origin,
            stage=stage,
            repechage_stage_value=repechage_stage_value,
        ),
    )
