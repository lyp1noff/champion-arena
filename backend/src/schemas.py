from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Optional


class AthleteBase(BaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: date
    coach_id: Optional[int] = None


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


class CoachBase(BaseModel):
    last_name: str
    first_name: str
    credentials: Optional[str] = None


class CoachCreate(CoachBase):
    pass


class CoachResponse(CoachBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    age: int
    gender: str


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


class TournamentUpdate(TournamentBase):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None


class BracketParticipant(BaseModel):
    seed: int
    last_name: str
    first_name: str


class TournamentBracket(BaseModel):
    category: str
    participants: List[BracketParticipant]


# class BracketBase(BaseModel):
#     tournament_id: int
#     category_id: int


# class BracketCreate(BracketBase):
#     pass


# class BracketResponse(BracketBase):
#     id: int

#     model_config = ConfigDict(from_attributes=True)


# class BracketParticipantBase(BaseModel):
#     bracket_id: int
#     athlete_id: Optional[int] = None
#     seed: int


# class BracketParticipantCreate(BracketParticipantBase):
#     pass


# class BracketParticipantResponse(BracketParticipantBase):
#     id: int

#     model_config = ConfigDict(from_attributes=True)


# class BracketMatchBase(BaseModel):
#     bracket_id: int
#     round_number: int
#     position: int
#     athlete1_id: Optional[int] = None
#     athlete2_id: Optional[int] = None
#     winner_id: Optional[int] = None
#     is_finished: bool


# class BracketMatchCreate(BracketMatchBase):
#     pass


# class BracketMatchResponse(BracketMatchBase):
#     id: int

#     model_config = ConfigDict(from_attributes=True)
