from __future__ import annotations

from typing import Any

from champion_domain import MatchEventPayload
from pydantic import BaseModel, ValidationError


class MatchScoreUpdatedPayloadDTO(BaseModel):
    score_athlete1: int | None = None
    score_athlete2: int | None = None


class MatchFinishedPayloadDTO(BaseModel):
    winner_id: int
    score_athlete1: int
    score_athlete2: int


class MatchStatusUpdatedPayloadDTO(BaseModel):
    status: str


def parse_match_payload_dto(event_type: str, payload: dict[str, Any]) -> MatchEventPayload:
    try:
        if event_type == "match.started":
            return MatchEventPayload()
        if event_type == "match.score_updated":
            score_payload = MatchScoreUpdatedPayloadDTO.model_validate(payload)
            return MatchEventPayload(
                score_athlete1=score_payload.score_athlete1,
                score_athlete2=score_payload.score_athlete2,
            )
        if event_type == "match.finished":
            finish_payload = MatchFinishedPayloadDTO.model_validate(payload)
            return MatchEventPayload(
                winner_id=finish_payload.winner_id,
                score_athlete1=finish_payload.score_athlete1,
                score_athlete2=finish_payload.score_athlete2,
            )
        if event_type == "match.status_updated":
            status_payload = MatchStatusUpdatedPayloadDTO.model_validate(payload)
            return MatchEventPayload(status=status_payload.status)
    except ValidationError as exc:
        raise ValueError("invalid_payload") from exc

    raise ValueError("unsupported_event_type")
