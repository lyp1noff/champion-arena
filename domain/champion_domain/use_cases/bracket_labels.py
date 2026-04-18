import math
from dataclasses import dataclass

from champion_domain.bracket_generation import get_round_type


@dataclass(frozen=True)
class MatchClassification:
    is_repechage: bool
    stage: str
    round_type: str
    repechage_side: str | None
    repechage_step: int | None


def compute_main_rounds(participants_count: int | None) -> int:
    if participants_count is None or participants_count < 2:
        return 0
    return int(math.ceil(math.log2(participants_count)))


def classify_bracket_match(round_number: int, position: int, main_rounds: int) -> MatchClassification:
    is_repechage = main_rounds > 0 and round_number > main_rounds
    if is_repechage:
        return MatchClassification(
            is_repechage=True,
            stage="repechage",
            round_type="round",
            repechage_side="A" if position == 1 else "B",
            repechage_step=round_number - main_rounds,
        )

    round_type = "round"
    if main_rounds > 0:
        round_type = get_round_type(round_number - 1, main_rounds)
    return MatchClassification(
        is_repechage=False,
        stage="main",
        round_type=round_type,
        repechage_side=None,
        repechage_step=None,
    )
