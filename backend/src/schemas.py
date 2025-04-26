from pydantic import BaseModel, ConfigDict
from datetime import date, time
from typing import List, Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AthleteBase(CustomBaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: Optional[date] = None
    coach_id: Optional[int] = None


class AthleteCreate(AthleteBase):
    pass


class AthleteResponse(AthleteBase):
    id: int
    coach_last_name: Optional[str] = None
    age: Optional[int] = None


class AthleteUpdate(AthleteBase):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class PaginatedAthletesResponse(CustomBaseModel):
    data: List[AthleteResponse]
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
    age: int
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


class PaginatedTournamentResponse(CustomBaseModel):
    data: List[TournamentResponse]
    total: int
    page: int
    limit: int


class TournamentUpdate(TournamentBase):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None


class BracketBase(CustomBaseModel):
    tournament_id: int
    category: str
    type: str
    start_time: Optional[time] = None
    tatami: Optional[int] = None


class BracketParticipantSchema(CustomBaseModel):
    seed: int
    last_name: str
    first_name: str
    coach_last_name: str


class BracketResponse(BracketBase):
    id: int
    participants: List[BracketParticipantSchema]


class BracketUpdateSchema(CustomBaseModel):
    type: Optional[str] = None
    start_time: Optional[time] = None
    tatami: Optional[int] = None


class BracketMatchAthlete(CustomBaseModel):
    id: int
    first_name: str
    last_name: str
    coach_last_name: str


class MatchSchema(CustomBaseModel):
    id: int
    round_type: Optional[str] = None
    athlete1: Optional[BracketMatchAthlete]
    athlete2: Optional[BracketMatchAthlete]
    winner: Optional[BracketMatchAthlete]
    score_athlete1: Optional[int] = None
    score_athlete2: Optional[int] = None
    is_finished: bool


class BracketMatchResponse(CustomBaseModel):
    id: int
    round_number: int
    position: int
    match: Optional[MatchSchema]
    next_slot: Optional[int] = None


class BracketMatchGroup(CustomBaseModel):
    bracket_id: int
    category: str
    type: Optional[str] = None
    matches: List[BracketMatchResponse]
