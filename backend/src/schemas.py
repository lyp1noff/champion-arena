import uuid
from datetime import UTC, date, datetime, time
from typing import Any, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field

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
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, populate_by_name=True)


class AthleteBase(CustomBaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: Optional[date] = None


class AthleteCreate(AthleteBase):
    coaches_id: list[int] = []


class AthleteResponse(AthleteBase):
    id: int
    coach_links: list[Any] = Field(default_factory=list, exclude=True)

    @computed_field
    @property
    def coaches_id(self) -> list[int]:
        return [link.coach.id for link in self.coach_links if getattr(link, "coach", None) is not None]

    @computed_field
    @property
    def coaches_last_name(self) -> list[str]:
        return [link.coach.last_name for link in self.coach_links if getattr(link, "coach", None) is not None]

    @computed_field
    @property
    def age(self) -> Optional[int]:
        if self.birth_date is None:
            return None
        return int((datetime.now(UTC).date() - self.birth_date).days // 365)


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


class ApplicationResponse(CustomBaseModel):
    id: int
    tournament_id: int
    athlete_id: int
    category_id: int
    status: str
    comment: Optional[str] = None
    athlete: AthleteResponse
    category: CategoryResponse


class ApplicationCreate(BaseModel):
    tournament_id: int
    athlete_id: int
    category_id: int
    comment: Optional[str] = None


class BracketBase(CustomBaseModel):
    category: str = Field(validation_alias=AliasPath("category", "name"))
    type: str
    start_time: Optional[time] = None
    day: Optional[int] = None
    tatami: Optional[int] = None
    group_id: Optional[int] = 1
    display_name: Optional[str] = None
    status: str


class BracketParticipantSchema(CustomBaseModel):
    id: int
    athlete_id: int
    seed: int
    athlete: Any = Field(default=None, exclude=True)

    @computed_field
    @property
    def first_name(self) -> str:
        athlete = self.athlete
        return athlete.first_name if athlete is not None else ""

    @computed_field
    @property
    def last_name(self) -> str:
        athlete = self.athlete
        return athlete.last_name if athlete is not None else ""

    @computed_field
    @property
    def coaches_last_name(self) -> list[str]:
        athlete = self.athlete
        if athlete is None:
            return []
        return [link.coach.last_name for link in athlete.coach_links if getattr(link, "coach", None) is not None]


class BracketInfoResponse(BracketBase):
    id: int
    tournament_id: int


class BracketResponse(BracketBase):
    id: int
    tournament_id: int
    participants_raw: list[Any] = Field(default_factory=list, validation_alias="participants", exclude=True)

    @computed_field
    @property
    def participants(self) -> list[BracketParticipantSchema]:
        participants = [
            BracketParticipantSchema.model_validate(participant)
            for participant in self.participants_raw
            if getattr(participant, "athlete_id", None) is not None
        ]
        return sorted(participants, key=lambda participant: participant.seed)


class BracketUpdateSchema(CustomBaseModel):
    type: Optional[str] = None
    start_time: Optional[time] = None
    day: Optional[int] = None
    tatami: Optional[int] = None
    group_id: Optional[int] = None
    category_id: Optional[int] = None


class BracketMatchAthlete(CustomBaseModel):
    id: int
    first_name: str
    last_name: str
    coach_links: list[Any] = Field(default_factory=list, exclude=True)

    @computed_field
    @property
    def coaches_last_name(self) -> list[str]:
        return [link.coach.last_name for link in self.coach_links if getattr(link, "coach", None) is not None]


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
    bracket_id: int = Field(validation_alias="id")
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
    day: Optional[int] = 1
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
