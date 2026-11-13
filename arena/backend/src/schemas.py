import uuid
from datetime import UTC, date, datetime, time
from typing import Annotated, Any, Literal, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints, computed_field

from champion_domain import ApplicationStatus, BracketStatus, MatchStatus, TournamentStatus
from src.models import BracketType


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class OrmResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, populate_by_name=True)


class AthleteBase(OrmResponseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: Optional[date] = None


class AthleteCreate(AthleteBase):
    coaches_id: list[int] = []


class AthleteResponse(AthleteBase):
    id: int
    coach_links: list[Any] = Field(default_factory=list, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coaches_id(self) -> list[int]:
        return [link.coach.id for link in self.coach_links if getattr(link, "coach", None) is not None]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coaches_last_name(self) -> list[str]:
        return [link.coach.last_name for link in self.coach_links if getattr(link, "coach", None) is not None]

    @computed_field  # type: ignore[prop-decorator]
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


class PaginatedAthletesResponse(OrmResponseModel):
    data: list[AthleteResponse]
    total: int
    page: int
    limit: int


CoachName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
CoachFirstName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class CoachBase(OrmResponseModel):
    last_name: CoachName
    first_name: CoachFirstName = ""


class CoachCreate(CoachBase):
    pass


class CoachUpdate(CoachBase):
    pass


class CoachResponse(CoachBase):
    id: int
    athlete_count: int = 0


class CategoryBase(OrmResponseModel):
    name: str
    min_age: int
    max_age: int
    gender: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int


class TournamentBase(OrmResponseModel):
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
    status: TournamentStatus


class PaginatedTournamentResponse(OrmResponseModel):
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


class ApplicationResponse(OrmResponseModel):
    id: int
    tournament_id: int
    athlete_id: int
    category_id: int
    status: ApplicationStatus
    comment: Optional[str] = None
    athlete: AthleteResponse
    category: CategoryResponse


class ApplicationCreate(BaseModel):
    tournament_id: int
    athlete_id: int
    category_id: int
    comment: Optional[str] = None


class BracketMatchAthlete(OrmResponseModel):
    id: int
    first_name: str
    last_name: str
    coach_links: list[Any] = Field(default_factory=list, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coaches_last_name(self) -> list[str]:
        return [link.coach.last_name for link in self.coach_links if getattr(link, "coach", None) is not None]


class BracketBase(OrmResponseModel):
    category: str = Field(validation_alias=AliasPath("category", "name"))
    type: str
    group_id: Optional[int] = 1
    display_name: Optional[str] = None
    status: BracketStatus
    version: int
    place_1: Optional[BracketMatchAthlete] = Field(default=None, validation_alias="place_1_athlete")
    place_2: Optional[BracketMatchAthlete] = Field(default=None, validation_alias="place_2_athlete")
    place_3_a: Optional[BracketMatchAthlete] = Field(default=None, validation_alias="place_3_a_athlete")
    place_3_b: Optional[BracketMatchAthlete] = Field(default=None, validation_alias="place_3_b_athlete")


class BracketParticipantSchema(OrmResponseModel):
    id: int
    athlete_id: int
    seed: int
    athlete: Any = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def first_name(self) -> str:
        athlete = self.athlete
        return athlete.first_name if athlete is not None else ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_name(self) -> str:
        athlete = self.athlete
        return athlete.last_name if athlete is not None else ""

    @computed_field  # type: ignore[prop-decorator]
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def participants(self) -> list[BracketParticipantSchema]:
        participants = [
            BracketParticipantSchema.model_validate(participant)
            for participant in self.participants_raw
            if getattr(participant, "athlete_id", None) is not None
        ]
        return sorted(participants, key=lambda participant: participant.seed)


class BracketUpdateSchema(BaseModel):
    type: Optional[str] = None
    group_id: Optional[int] = None
    category_id: Optional[int] = None


class MatchSchema(OrmResponseModel):
    id: uuid.UUID
    round_type: Optional[str] = None
    stage: Optional[str] = None
    repechage_side: Optional[str] = None
    repechage_step: Optional[int] = None
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


class BracketMatchResponse(OrmResponseModel):
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


class BracketDeleteRequest(BaseModel):
    target_bracket_id: Optional[int] = None


class TimetableEntryBase(OrmResponseModel):
    tournament_id: int
    entry_type: str
    day: int
    tatami: int
    start_time: time
    end_time: time
    order_index: int
    title: Optional[str] = None
    notes: Optional[str] = None
    bracket_id: Optional[int] = None
    bracket: Any = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bracket_display_name(self) -> Optional[str]:
        if self.bracket is None:
            return None
        return getattr(self.bracket, "display_name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bracket_type(self) -> Optional[str]:
        if self.bracket is None:
            return None
        return getattr(self.bracket, "type", None)


class TimetableEntryResponse(TimetableEntryBase):
    id: int


class TimetableEntryCreate(BaseModel):
    entry_type: str
    day: int = Field(ge=1)
    tatami: int = Field(ge=1)
    start_time: time
    end_time: time
    order_index: int = Field(ge=1)
    title: Optional[str] = None
    notes: Optional[str] = None
    bracket_id: Optional[int] = None


class TimetableReplace(BaseModel):
    entries: list[TimetableEntryCreate]


class BootstrapAthlete(BaseModel):
    """Minimal athlete roster entry Tatami needs to pick athletes while offline."""

    id: int
    first_name: str
    last_name: str
    coaches_last_name: list[str] = Field(default_factory=list)


class TournamentBootstrapSnapshot(OrmResponseModel):
    tournament: TournamentResponse
    brackets: list[BracketResponse]
    bracket_matches: list[BracketMatchesFull]
    timetable_entries: list[TimetableEntryResponse]
    athletes: list[BootstrapAthlete] = Field(default_factory=list)


class CategoryCreateSchema(BaseModel):
    name: str
    age: int
    gender: str


class SyncParticipant(BaseModel):
    athlete_id: int | None = None
    seed: int


class SyncMatch(BaseModel):
    id: uuid.UUID
    round_number: int
    position: int
    next_slot: int | None = None
    round_type: str | None = None
    stage: str = "main"
    repechage_side: str | None = None
    repechage_step: int | None = None
    status: MatchStatus
    athlete1_id: int | None = None
    athlete2_id: int | None = None
    winner_id: int | None = None
    score_athlete1: int | None = None
    score_athlete2: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class SyncBracket(BaseModel):
    """Full current state of one bracket as Tatami sees it (Arena ids on the wire)."""

    bracket_id: int
    version: int = Field(ge=1)
    type: str
    group_id: int = 1
    status: BracketStatus
    participants: list[SyncParticipant]
    matches: list[SyncMatch]


class SyncBracketsRequest(BaseModel):
    edge_id: str = Field(min_length=1, max_length=100)
    tournament_id: int = Field(ge=1)
    brackets: list[SyncBracket] = Field(max_length=100)


SyncResultStatus = Literal["applied", "stale", "rejected"]


class SyncBracketResult(BaseModel):
    bracket_id: int
    status: SyncResultStatus
    version: int | None = None
    reason: str | None = None


class SyncBracketsResponse(BaseModel):
    results: list[SyncBracketResult]


class BracketsUpdated(BaseModel):
    """WebSocket message: these brackets changed, refetch them if shown."""

    type: Literal["brackets_updated"] = "brackets_updated"
    bracket_ids: list[int]
