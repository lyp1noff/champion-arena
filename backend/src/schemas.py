from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Optional


class AthleteBase(BaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: date
    coach_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AthleteCreate(AthleteBase):
    pass


class AthleteResponse(AthleteBase):
    id: int
    coach_last_name: Optional[str] = None
    age: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AthleteUpdate(AthleteBase):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class PaginatedAthletesResponse(BaseModel):
    data: List[AthleteResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class CoachBase(BaseModel):
    last_name: str
    first_name: str
    credentials: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CoachCreate(CoachBase):
    pass


class CoachResponse(CoachBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    age: int
    gender: str

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TournamentBase(BaseModel):
    name: str
    location: str
    start_date: date
    end_date: date
    registration_start_date: date
    registration_end_date: date
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TournamentCreate(TournamentBase):
    pass


class TournamentResponse(TournamentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PaginatedTournamentResponse(BaseModel):
    data: List[TournamentResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class TournamentUpdate(TournamentBase):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class BracketParticipantSchema(BaseModel):
    seed: int
    last_name: str
    first_name: str

    model_config = ConfigDict(from_attributes=True)


class BracketResponse(BaseModel):
    id: int
    tournament_id: int
    category: str
    participants: List[BracketParticipantSchema]

    model_config = ConfigDict(from_attributes=True)


class BracketMatchResponse(BaseModel):
    id: int
    bracket_id: int
    round_number: int
    position: int
    athlete1_id: Optional[int] = None
    athlete2_id: Optional[int] = None
    winner_id: Optional[int] = None
    is_finished: bool

    model_config = ConfigDict(from_attributes=True)


class BracketMatchAthlete(BaseModel):
    id: int
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class BracketMatchResponse(BaseModel):
    id: int
    round_number: int
    position: int
    athlete1: Optional[BracketMatchAthlete]
    athlete2: Optional[BracketMatchAthlete]
    winner: Optional[BracketMatchAthlete]
    score_athlete1: Optional[int] = None
    score_athlete2: Optional[int] = None
    is_finished: bool

    model_config = ConfigDict(from_attributes=True)


class BracketMatchGroup(BaseModel):
    bracket_id: int
    category: str
    matches: List[BracketMatchResponse]
