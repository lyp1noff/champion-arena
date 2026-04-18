from typing import Protocol, overload


class SupportsMatchResult(Protocol):
    @property
    def winner_id(self) -> int | None: ...

    @property
    def athlete1_id(self) -> int | None: ...

    @property
    def athlete2_id(self) -> int | None: ...


@overload
def match_loser_id(match_or_winner: SupportsMatchResult) -> int | None: ...


@overload
def match_loser_id(match_or_winner: int | None, athlete1_id: int | None, athlete2_id: int | None) -> int | None: ...


def match_loser_id(
    match_or_winner: SupportsMatchResult | int | None,
    athlete1_id: int | None = None,
    athlete2_id: int | None = None,
) -> int | None:
    if athlete1_id is None and athlete2_id is None and not isinstance(match_or_winner, int | type(None)):
        winner_id = match_or_winner.winner_id
        athlete1_id = match_or_winner.athlete1_id
        athlete2_id = match_or_winner.athlete2_id
    else:
        winner_id = match_or_winner if isinstance(match_or_winner, int | type(None)) else match_or_winner.winner_id

    if winner_id is None:
        return None
    if athlete1_id == winner_id:
        return athlete2_id
    if athlete2_id == winner_id:
        return athlete1_id
    return None


def final_loser_id(
    match_or_winner: SupportsMatchResult | int | None,
    athlete1_id: int | None = None,
    athlete2_id: int | None = None,
) -> int | None:
    if athlete1_id is None and athlete2_id is None:
        if isinstance(match_or_winner, int | type(None)):
            return None
        return match_loser_id(match_or_winner)
    winner_id = match_or_winner if isinstance(match_or_winner, int | type(None)) else match_or_winner.winner_id
    return match_loser_id(winner_id, athlete1_id, athlete2_id)
