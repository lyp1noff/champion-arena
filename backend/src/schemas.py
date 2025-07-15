from pydantic import BaseModel, ConfigDict
from datetime import date, time, datetime
from typing import List, Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AthleteBase(CustomBaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: Optional[date] = None
    # coaches_id: List[int] = []


class AthleteCreate(AthleteBase):
    coaches_id: List[int] = []


class AthleteResponse(AthleteBase):
    id: int
    coaches_last_name: List[str] = []
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


class ApplicationResponse(BaseModel):
    id: int
    tournament_id: int
    athlete_id: int
    category_id: int
    status: str
    athlete: AthleteResponse
    category: CategoryResponse
    created_at: datetime


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


class BracketParticipantSchema(CustomBaseModel):
    athlete_id: int
    seed: int
    last_name: str
    first_name: str
    coaches_last_name: List[str] = []


class BracketResponse(BracketBase):
    id: int
    tournament_id: int
    participants: List[BracketParticipantSchema]


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
    coaches_last_name: List[str] = []


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
    match: MatchSchema
    next_slot: Optional[int] = None


class BracketMatchesFull(BracketBase):
    bracket_id: int
    matches: List[BracketMatchResponse]


class ParticipantMoveSchema(BaseModel):
    athlete_id: int
    from_bracket_id: int
    to_bracket_id: int
    new_seed: int


class ParticipantReorderSchema(BaseModel):
    bracket_id: int
    participant_updates: List[
        dict[str, int]
    ]  # List of {athlete_id: int, new_seed: int}


class BracketCreateSchema(BaseModel):
    tournament_id: int
    category_id: int
    group_id: int = 1
    type: str = "single_elimination"
    start_time: Optional[time] = None
    tatami: Optional[int] = None


class CategoryCreateSchema(BaseModel):
    name: str
    age: int
    gender: str
