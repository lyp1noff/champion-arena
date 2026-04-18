from typing import Protocol

BRACKET_STATE_RUNNING = "running"
BRACKET_STATE_FINISHED = "finished"
BRACKET_STATUS_STARTED = "started"
BRACKET_STATUS_FINISHED = "finished"

IMMUTABLE_BRACKET_STATES = {BRACKET_STATE_RUNNING, BRACKET_STATE_FINISHED}


def is_bracket_structurally_mutable(state: str) -> bool:
    return state not in IMMUTABLE_BRACKET_STATES


class SupportsBracketVersion(Protocol):
    version: int | None


def bump_bracket_version(bracket: SupportsBracketVersion) -> None:
    bracket.version = int(bracket.version or 0) + 1


def derive_bracket_state_from_status(status: str, current_state: str) -> str:
    if status == BRACKET_STATUS_STARTED:
        return BRACKET_STATE_RUNNING
    if status == BRACKET_STATUS_FINISHED:
        return BRACKET_STATE_FINISHED
    return current_state
