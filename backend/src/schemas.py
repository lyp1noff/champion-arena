import uuid
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.models import BracketType, MatchStatus


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


# TODO: ensure that all models are using this base model
class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AthleteBase(CustomBaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: Optional[date] = None


class AthleteCreate(AthleteBase):
    coaches_id: list[int] = []


class AthleteResponse(AthleteBase):
    coaches_id: list[int] = []
    coaches_last_name: list[str] = []
    age: Optional[int] = None
    id: int


class AthleteUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    coaches_id: list[int] = []


class PaginatedAthletesResponse(CustomBaseModel):
    data: list[AthleteResponse]
    total: int
    page: int
    limit: int


class CoachBase(CustomBaseModel):
    last_name: str
    first_name: str
    credentials: Optional[str] = None


class CoachCreate(CoachBase):
    pass


class CoachResponse(CoachBase):
    id: int


class CategoryBase(CustomBaseModel):
    name: str
    min_age: int
    max_age: int
    gender: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int


class TournamentBase(CustomBaseModel):
    name: str
    location: str
    start_date: date
    end_date: date
    registration_start_date: date
    registration_end_date: date
    image_url: Optional[str] = None


class TournamentCreate(TournamentBase):
    pass


class TournamentResponse(TournamentBase):
    id: int
    status: str


class PaginatedTournamentResponse(CustomBaseModel):
    data: list[TournamentResponse]
    total: int
    page: int
    limit: int


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None
    image_url: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    tournament_id: int
    athlete_id: int
    category_id: int
    status: str
    comment: Optional[str] = None
    athlete: AthleteResponse
    category: CategoryResponse

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    tournament_id: int
    athlete_id: int
    category_id: int
    comment: Optional[str] = None


class BracketBase(CustomBaseModel):
    category: str
    type: str
    start_time: Optional[time] = None
    tatami: Optional[int] = None
    group_id: Optional[int] = 1
    display_name: Optional[str] = None
    status: str


class BracketParticipantSchema(CustomBaseModel):
    id: int
    athlete_id: int
    seed: int
    last_name: str
    first_name: str
    coaches_last_name: list[str] = []


class BracketInfoResponse(BracketBase):
    id: int
    tournament_id: int

    class Config:
        from_attributes = True


class BracketResponse(BracketBase):
    id: int
    tournament_id: int
    participants: list[BracketParticipantSchema]


class BracketUpdateSchema(CustomBaseModel):
    type: Optional[str] = None
    start_time: Optional[time] = None
    tatami: Optional[int] = None
    group_id: Optional[int] = None
    category_id: Optional[int] = None


class BracketMatchAthlete(CustomBaseModel):
    id: int
    first_name: str
    last_name: str
    coaches_last_name: list[str] = []


class MatchSchema(CustomBaseModel):
    id: uuid.UUID
    round_type: Optional[str] = None
    athlete1: Optional[BracketMatchAthlete]
    athlete2: Optional[BracketMatchAthlete]
    winner: Optional[BracketMatchAthlete]
    score_athlete1: Optional[int] = None
    score_athlete2: Optional[int] = None
    status: MatchStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class MatchScoreUpdate(BaseModel):
    score_athlete1: Optional[int] = None
    score_athlete2: Optional[int] = None


class MatchFinishRequest(BaseModel):
    score_athlete1: int
    score_athlete2: int
    winner_id: int


class BracketMatchResponse(CustomBaseModel):
    id: uuid.UUID
    round_number: int
    position: int
    match: MatchSchema
    next_slot: Optional[int] = None


class BracketMatchesFull(BracketBase):
    bracket_id: int
    matches: list[BracketMatchResponse]


class ParticipantMoveSchema(BaseModel):
    participant_id: int
    from_bracket_id: int
    to_bracket_id: int


class ParticipantReorderSchema(BaseModel):
    bracket_id: int
    participant_updates: list[dict[str, int]]  # list of {participant_id: int, new_seed: int}


class BracketCreateSchema(BaseModel):
    tournament_id: int
    category_id: int
    group_id: int = 1
    type: Optional[str] = BracketType.SINGLE_ELIMINATION.value
    start_time: Optional[time] = None
    tatami: Optional[int] = None


class BracketDeleteRequest(BaseModel):
    target_bracket_id: Optional[int] = None


class CategoryCreateSchema(BaseModel):
    name: str
    age: int
    gender: str


class MatchUpdate(BaseModel):
    match_id: uuid.UUID
    score_athlete1: int | None
    score_athlete2: int | None
    status: str | None
