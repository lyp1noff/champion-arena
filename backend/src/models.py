import enum
import uuid
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class TournamentStatus(enum.Enum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    STARTED = "started"
    FINISHED = "finished"


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BracketType(enum.Enum):
    SINGLE_ELIMINATION = "single_elimination"
    ROUND_ROBIN = "round_robin"


class BracketStatus(enum.Enum):
    PENDING = "pending"
    STARTED = "started"
    FINISHED = "finished"


class MatchStatus(enum.Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    FINISHED = "finished"


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), default=func.now())

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.ADMIN.value)


class Athlete(Base, TimestampMixin):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(10))
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    coach_links: Mapped[list["AthleteCoachLink"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")
    coaches: Mapped[list["Coach"]] = relationship(
        secondary="athlete_coach_links", back_populates="athletes", viewonly=True
    )
    brackets: Mapped[list["BracketParticipant"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")


class Coach(Base, TimestampMixin):
    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    first_name: Mapped[str] = mapped_column(String(100), index=True)

    athlete_links: Mapped[list["AthleteCoachLink"]] = relationship(back_populates="coach", cascade="all, delete-orphan")
    athletes: Mapped[list["Athlete"]] = relationship(
        secondary="athlete_coach_links", back_populates="coaches", viewonly=True
    )


class AthleteCoachLink(Base, TimestampMixin):
    __tablename__ = "athlete_coach_links"
    __table_args__ = (UniqueConstraint("athlete_id", "coach_id", name="uix_athlete_coach"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id", ondelete="CASCADE"), index=True)

    athlete: Mapped["Athlete"] = relationship(back_populates="coach_links")
    coach: Mapped["Coach"] = relationship(back_populates="athlete_links")


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    min_age: Mapped[int] = mapped_column()
    max_age: Mapped[int] = mapped_column()
    gender: Mapped[str] = mapped_column(String(10))

    brackets: Mapped[list["Bracket"]] = relationship(back_populates="category")


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournaments"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="check_tournament_dates"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=TournamentStatus.DRAFT.value)
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    registration_start_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    registration_end_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    export_last_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    brackets: Mapped[list["Bracket"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("athlete_id", "category_id", "tournament_id", name="uix_application_unique"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), index=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=ApplicationStatus.PENDING.value)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    athlete: Mapped["Athlete"] = relationship()
    category: Mapped["Category"] = relationship()


class Bracket(Base, TimestampMixin):
    __tablename__ = "brackets"
    __table_args__ = (
        UniqueConstraint("tournament_id", "category_id", "group_id", name="uix_tournament_category_group"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    group_id: Mapped[int] = mapped_column(default=1)
    type: Mapped[str] = mapped_column(String(50), default=BracketType.SINGLE_ELIMINATION.value)
    start_time: Mapped[time] = mapped_column(Time, default=lambda: time(9, 0))
    day: Mapped[int] = mapped_column(default=1)
    tatami: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(20), default=BracketStatus.PENDING.value)

    def get_display_name(self) -> str:
        """Generate display name combining category name and group number"""
        category_name = self.category.name if self.category else "Unknown Category"
        # Check if group_id is set and not equal to 1
        group_id = getattr(self, "group_id", None)
        if group_id is not None and group_id != 1:
            return f"{category_name} (Group {group_id})"
        return category_name

    tournament: Mapped["Tournament"] = relationship(back_populates="brackets")
    category: Mapped["Category"] = relationship(back_populates="brackets")
    matches: Mapped[list["BracketMatch"]] = relationship(back_populates="bracket", cascade="all, delete-orphan")
    participants: Mapped[list["BracketParticipant"]] = relationship(
        back_populates="bracket", cascade="all, delete-orphan"
    )


class BracketParticipant(Base):
    __tablename__ = "bracket_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bracket_id: Mapped[int] = mapped_column(ForeignKey("brackets.id", ondelete="CASCADE"), index=True)
    athlete_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    seed: Mapped[int] = mapped_column()

    bracket: Mapped["Bracket"] = relationship(back_populates="participants")
    athlete: Mapped[Optional["Athlete"]] = relationship(back_populates="brackets")


class BracketMatch(Base):
    __tablename__ = "bracket_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bracket_id: Mapped[int] = mapped_column(ForeignKey("brackets.id", ondelete="CASCADE"), index=True)
    round_number: Mapped[int] = mapped_column()
    position: Mapped[int] = mapped_column()
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    next_slot: Mapped[Optional[int]] = mapped_column(nullable=True)

    bracket: Mapped["Bracket"] = relationship(back_populates="matches")
    match: Mapped["Match"] = relationship(back_populates="bracket_match", cascade="all, delete", single_parent=True)


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    athlete1_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    athlete2_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    winner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score_athlete1: Mapped[Optional[int]] = mapped_column(nullable=True)
    score_athlete2: Mapped[Optional[int]] = mapped_column(nullable=True)
    round_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.NOT_STARTED.value)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    athlete1: Mapped[Optional["Athlete"]] = relationship(foreign_keys=[athlete1_id])
    athlete2: Mapped[Optional["Athlete"]] = relationship(foreign_keys=[athlete2_id])
    winner: Mapped[Optional["Athlete"]] = relationship(foreign_keys=[winner_id])
    bracket_match: Mapped[Optional["BracketMatch"]] = relationship(back_populates="match", uselist=False)
