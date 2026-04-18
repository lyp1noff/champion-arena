MATCH_STATUS_NOT_STARTED = "not_started"
MATCH_STATUS_STARTED = "started"


def can_start_match(status: str, athlete1_id: int | None, athlete2_id: int | None) -> tuple[bool, str | None]:
    if status != MATCH_STATUS_NOT_STARTED:
        return False, "Match already started or finished"
    if athlete1_id is None or athlete2_id is None:
        return False, "Match has no athletes"
    return True, None


def can_finish_match(status: str) -> tuple[bool, str | None]:
    if status != MATCH_STATUS_STARTED:
        return False, "Match not started or already finished"
    return True, None


def can_update_scores(status: str) -> tuple[bool, str | None]:
    if status != MATCH_STATUS_STARTED:
        return False, "Cannot update scores of not started match"
    return True, None
