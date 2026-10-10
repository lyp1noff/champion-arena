from enum import StrEnum


class TournamentStatus(StrEnum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    STARTED = "started"
    FINISHED = "finished"


class ApplicationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BracketStatus(StrEnum):
    PENDING = "pending"
    STARTED = "started"
    FINISHED = "finished"


class MatchStatus(StrEnum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    FINISHED = "finished"


TOURNAMENT_STATUS_TRANSITIONS: dict[TournamentStatus, frozenset[TournamentStatus]] = {
    TournamentStatus.DRAFT: frozenset({TournamentStatus.UPCOMING}),
    TournamentStatus.UPCOMING: frozenset({TournamentStatus.STARTED}),
    TournamentStatus.STARTED: frozenset({TournamentStatus.FINISHED}),
    TournamentStatus.FINISHED: frozenset(),
}

BRACKET_STATUS_TRANSITIONS: dict[BracketStatus, frozenset[BracketStatus]] = {
    BracketStatus.PENDING: frozenset({BracketStatus.STARTED}),
    BracketStatus.STARTED: frozenset({BracketStatus.FINISHED}),
    BracketStatus.FINISHED: frozenset(),
}

MATCH_STATUS_TRANSITIONS: dict[MatchStatus, frozenset[MatchStatus]] = {
    MatchStatus.NOT_STARTED: frozenset({MatchStatus.STARTED}),
    MatchStatus.STARTED: frozenset({MatchStatus.FINISHED}),
    MatchStatus.FINISHED: frozenset(),
}
