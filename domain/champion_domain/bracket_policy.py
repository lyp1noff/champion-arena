from typing import Protocol
from .statuses import BracketStatus


def is_bracket_structurally_mutable(status: BracketStatus) -> bool:
    return status == BracketStatus.PENDING


class SupportsBracketVersion(Protocol):
    version: int | None


def bump_bracket_version(bracket: SupportsBracketVersion) -> None:
    bracket.version = int(bracket.version or 0) + 1
