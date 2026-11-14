"""Live bracket updates over WebSocket.

A change is published once per bracket to the tournament channel, carrying the
bracket's full state. Each WebSocket connection then forwards either that state
(if the viewer has the bracket open) or a tiny header (id, status, version) so
list badges update without any HTTP request.
"""

import json
from functools import lru_cache
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
from src.schemas import BracketHeader, BracketMatchResponse, BracketResponse, BracketsUpdated, BracketState
from src.services.brackets import get_bracket, get_bracket_matches
from src.services.broadcast import broadcast

CHANGED_TYPE = "bracket_changed"


def tournament_channel(tournament_id: int) -> str:
    return f"tournament:{tournament_id}"


async def publish_bracket_changes(db: AsyncSession, tournament_id: int, bracket_ids: list[int]) -> None:
    """Call after commit. Never raises: a failed broadcast must not fail the write."""
    for bracket_id in dict.fromkeys(bracket_ids):
        try:
            bracket = await get_bracket(db, bracket_id, fresh=True)
            matches = await get_bracket_matches(db, bracket_id, fresh=True)
            state = BracketState(
                bracket=BracketResponse.model_validate(bracket),
                matches=[BracketMatchResponse.model_validate(m) for m in matches],
            )
            header = BracketsUpdated(
                bracket_ids=[bracket.id],
                brackets=[BracketHeader(id=bracket.id, status=bracket.status, version=bracket.version)],
            )
            message = _dumps(
                {
                    "type": CHANGED_TYPE,
                    "bracket_id": bracket.id,
                    "header": header.model_dump(mode="json"),
                    "state": state.model_dump(mode="json"),
                }
            )
            await broadcast.publish(channel=tournament_channel(tournament_id), message=message)
        except Exception as exc:
            logger.error(f"Error publishing bracket {bracket_id} update: {exc}")


def _dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class WireMessage(NamedTuple):
    bracket_id: int | None
    header: str
    state: str | None


@lru_cache(maxsize=64)
def split_message(message: str) -> WireMessage:
    """Parse a published message once per worker (every connection gets the same str)."""
    try:
        data = json.loads(message)
    except ValueError:
        return WireMessage(None, message, None)
    if not isinstance(data, dict) or data.get("type") != CHANGED_TYPE:
        return WireMessage(None, message, None)
    return WireMessage(int(data["bracket_id"]), _dumps(data["header"]), _dumps(data["state"]))
