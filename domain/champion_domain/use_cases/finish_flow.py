from dataclasses import dataclass

from champion_domain.use_cases.bracket_completion import (
    BracketCompletionDecision,
    decide_bracket_completion,
)
from champion_domain.use_cases.finish_runtime import decide_finish_runtime
from champion_domain.use_cases.match_progression import ProgressionAction
from champion_domain.use_cases.repechage_runtime import should_publish_structure_after_match_finish


@dataclass(frozen=True)
class FinishFlowRuntimeDecision:
    progression_action: ProgressionAction | None
    attempt_generate_repechage: bool


@dataclass(frozen=True)
class FinishFlowPostDecision:
    publish_structure: bool
    completion: BracketCompletionDecision


def decide_finish_flow_runtime(
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
) -> FinishFlowRuntimeDecision:
    runtime = decide_finish_runtime(
        origin=origin,
        stage=stage,
        current_round_number=current_round_number,
        current_position=current_position,
        explicit_next_slot=explicit_next_slot,
        repechage_side=repechage_side,
        repechage_step=repechage_step,
        allow_implicit_main_slot=allow_implicit_main_slot,
        main_rounds=main_rounds,
        repechage_stage_value=repechage_stage_value,
    )
    return FinishFlowRuntimeDecision(
        progression_action=runtime.progression_action,
        attempt_generate_repechage=runtime.attempt_generate_repechage,
    )


def decide_finish_flow_post(
    *,
    is_repechage_match: bool,
    generated_repechage: bool,
    total_matches: int | None,
    finished_matches: int | None,
    current_bracket_status: str | None,
    finished_status_value: str = "finished",
) -> FinishFlowPostDecision:
    return FinishFlowPostDecision(
        publish_structure=should_publish_structure_after_match_finish(
            is_repechage_match=is_repechage_match,
            generated_repechage=generated_repechage,
        ),
        completion=decide_bracket_completion(
            total_matches=total_matches,
            finished_matches=finished_matches,
            current_bracket_status=current_bracket_status,
            finished_status_value=finished_status_value,
        ),
    )
