from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExternalTournamentSchema(CustomBaseModel):
    id: int
    status: str
    name: str
    location: str
    start_date: date
    end_date: date
    registration_start_date: date
    registration_end_date: date
    image_url: Optional[str] = None


class ExternalAthleteSchema(CustomBaseModel):
    id: int
    last_name: str
    first_name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    coaches_last_name: list[str] = []


class GetCurrentTournamentRequest(CustomBaseModel):
    current_tournament_id: Optional[int]


class SetCurrentTournamentRequest(BaseModel):
    current_tournament_id: int


class TournamentSchema(CustomBaseModel):
    id: int
    external_id: int
    name: str
    location: str
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime


class BracketSchema(CustomBaseModel):
    id: int
    external_id: int
    tournament_id: int
    category: str
    type: str
    tatami: Optional[int] = None
    group_id: int = 1
    start_time: Optional[str] = None
    day: Optional[int] = None
    status: Optional[str]
    state: Optional[str] = "draft"
    version: int = 1
    display_name: Optional[str]


class AthleteSchema(CustomBaseModel):
    id: int
    external_id: int
    first_name: str
    last_name: str
    coaches_last_name: str


class BracketParticipantSchema(CustomBaseModel):
    id: int
    bracket_id: int
    athlete_id: Optional[int]
    seed: int
    athlete: Optional[AthleteSchema] = None


class BracketParticipantAddSchema(BaseModel):
    athlete_external_id: int
    seed: Optional[int] = None


class BracketParticipantMoveSchema(BaseModel):
    participant_id: int
    target_bracket_id: int
    target_seed: Optional[int] = None


class BracketParticipantSeedUpdateSchema(BaseModel):
    seed: int


class MatchSchema(CustomBaseModel):
    id: int
    external_id: str
    round_type: Optional[str] = None
    stage: Optional[str] = None
    repechage_side: Optional[str] = None
    repechage_step: Optional[int] = None
    athlete1: Optional[AthleteSchema]
    athlete2: Optional[AthleteSchema]
    winner_id: Optional[int]
    score_athlete1: Optional[int]
    score_athlete2: Optional[int]
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class MatchWithBracketSchema(MatchSchema):
    bracket_display_name: str


class BracketMatchSchema(CustomBaseModel):
    id: int
    external_id: str
    round_number: int
    position: int
    match: MatchSchema
    next_slot: Optional[int] = None


class UpdateMatchScoresSchema(BaseModel):
    score_athlete1: Optional[int] = None
    score_athlete2: Optional[int] = None


class FinishMatchSchema(BaseModel):
    score_athlete1: int
    score_athlete2: int
    winner_id: int


class TimetableEntrySchema(CustomBaseModel):
    id: int
    tournament_id: int
    bracket_id: Optional[int]
    entry_type: str
    title: Optional[str] = None
    notes: Optional[str] = None
    day: int
    tatami: int
    start_time: time
    end_time: time
    order_index: int


class TimetableEntryCreateSchema(BaseModel):
    entry_type: str
    day: int
    tatami: int
    start_time: time
    end_time: time
    order_index: int
    title: Optional[str] = None
    notes: Optional[str] = None
    bracket_id: Optional[int] = None


class TimetableReplaceSchema(BaseModel):
    entries: list[TimetableEntryCreateSchema]
