from .statuses import MatchStatus


def can_start_match(status: MatchStatus, athlete1_id: int | None, athlete2_id: int | None) -> tuple[bool, str | None]:
    if status != MatchStatus.NOT_STARTED:
        return False, "Match already started or finished"
    if athlete1_id is None or athlete2_id is None:
        return False, "Match has no athletes"
    return True, None


def can_finish_match(status: MatchStatus) -> tuple[bool, str | None]:
    if status != MatchStatus.STARTED:
        return False, "Match not started or already finished"
    return True, None


def can_update_scores(status: MatchStatus) -> tuple[bool, str | None]:
    if status != MatchStatus.STARTED:
        return False, "Cannot update scores of not started match"
    return True, None
