from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Boolean,
    DateTime,
    Time,
    func,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, declared_attr
from src.database import Base
import enum
from datetime import time


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BracketType(enum.Enum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"


class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now())

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.ADMIN.value)


class Athlete(Base, TimestampMixin):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False)
    birth_date = Column(Date, nullable=True)

    coach_links = relationship(
        "AthleteCoachLink",
        back_populates="athlete",
        cascade="all, delete-orphan",
    )

    coaches = relationship(
        "Coach",
        secondary="athlete_coach_links",
        back_populates="athletes",
        viewonly=True,
    )

    brackets = relationship(
        "BracketParticipant",
        back_populates="athlete",
        cascade="all, delete-orphan",
    )


class Coach(Base, TimestampMixin):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(100), index=True, nullable=False)
    first_name = Column(String(100), index=True, nullable=False)

    athlete_links = relationship(
        "AthleteCoachLink",
        back_populates="coach",
        cascade="all, delete-orphan",
    )

    athletes = relationship(
        "Athlete",
        secondary="athlete_coach_links",
        back_populates="coaches",
        viewonly=True,
    )


class AthleteCoachLink(Base, TimestampMixin):
    __tablename__ = "athlete_coach_links"
    __table_args__ = (
        UniqueConstraint("athlete_id", "coach_id", name="uix_athlete_coach"),
    )

    id = Column(Integer, primary_key=True)
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coach_id = Column(
        Integer,
        ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    athlete = relationship("Athlete", back_populates="coach_links")
    coach = relationship("Coach", back_populates="athlete_links")


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)

    brackets = relationship("Bracket", back_populates="category")


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_tournament_dates"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    location = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    registration_start_date = Column(Date, nullable=True)
    registration_end_date = Column(Date, nullable=True)
    image_url = Column(String(500), nullable=True)
    export_last_updated_at = Column(DateTime(timezone=True), nullable=True)

    brackets = relationship(
        "Bracket", back_populates="tournament", cascade="all, delete-orphan"
    )


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "athlete_id", "category_id", "tournament_id", name="uix_application_unique"
        ),
    )

    id = Column(Integer, primary_key=True)
    tournament_id = Column(
        Integer,
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), default=ApplicationStatus.PENDING.value)
    comment = Column(String(500), nullable=True)

    athlete = relationship("Athlete")
    category = relationship("Category")


class Bracket(Base, TimestampMixin):
    __tablename__ = "brackets"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "category_id",
            "group_id",
            name="uix_tournament_category_group",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer,
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    group_id = Column(Integer, nullable=False, default=1)
    type = Column(
        String(50), nullable=False, default=BracketType.SINGLE_ELIMINATION.value
    )
    start_time = Column(Time, nullable=False, default=lambda: time(9, 0))
    tatami = Column(Integer, nullable=False, default=1)

    tournament = relationship("Tournament", back_populates="brackets")
    category = relationship("Category", back_populates="brackets")
    matches = relationship(
        "BracketMatch", back_populates="bracket", cascade="all, delete-orphan"
    )
    participants = relationship(
        "BracketParticipant", back_populates="bracket", cascade="all, delete-orphan"
    )

    def get_display_name(self) -> str:
        """Generate display name combining category name and group number"""
        category_name = self.category.name if self.category else "Unknown Category"
        # Check if group_id is set and not equal to 1
        group_id = getattr(self, "group_id", None)
        if group_id is not None and group_id != 1:
            return f"{category_name} (Group {group_id})"
        return category_name


class BracketParticipant(Base):
    __tablename__ = "bracket_participants"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(
        Integer,
        ForeignKey("brackets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    seed = Column(Integer, nullable=False)

    bracket = relationship("Bracket", back_populates="participants")
    athlete = relationship("Athlete", back_populates="brackets")


class BracketMatch(Base):
    __tablename__ = "bracket_matches"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(
        Integer,
        ForeignKey("brackets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    match_id = Column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    next_slot = Column(Integer, nullable=True)

    bracket = relationship("Bracket", back_populates="matches")
    match = relationship(
        "Match",
        back_populates="bracket_match",
        cascade="all, delete",
        single_parent=True,
    )


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    athlete1_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    athlete2_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    winner_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    score_athlete1 = Column(Integer, nullable=True)
    score_athlete2 = Column(Integer, nullable=True)
    is_finished = Column(Boolean, default=False)
    round_type = Column(String(50), nullable=True)

    athlete1 = relationship("Athlete", foreign_keys=[athlete1_id])
    athlete2 = relationship("Athlete", foreign_keys=[athlete2_id])
    winner = relationship("Athlete", foreign_keys=[winner_id])

    bracket_match = relationship("BracketMatch", back_populates="match", uselist=False)
