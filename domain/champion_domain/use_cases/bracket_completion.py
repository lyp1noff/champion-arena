from dataclasses import dataclass

from champion_domain.use_cases.match_progression import is_bracket_finished


@dataclass(frozen=True)
class BracketCompletionDecision:
    is_finished: bool
    should_finish_bracket: bool


def decide_bracket_completion(
    total_matches: int | None,
    finished_matches: int | None,
    current_bracket_status: str | None,
    *,
    finished_status_value: str = "finished",
) -> BracketCompletionDecision:
    completed = is_bracket_finished(total_matches, finished_matches)
    if not completed:
        return BracketCompletionDecision(is_finished=False, should_finish_bracket=False)
    return BracketCompletionDecision(
        is_finished=True,
        should_finish_bracket=current_bracket_status != finished_status_value,
    )


def should_finish_tournament(unfinished_brackets_count: int | None) -> bool:
    return unfinished_brackets_count == 0
