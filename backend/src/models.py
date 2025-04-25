from datetime import date
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
)
from sqlalchemy.orm import relationship, declared_attr
from src.database import Base


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
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")


class Athlete(Base, TimestampMixin):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    coach_id = Column(
        Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True
    )

    coach = relationship("Coach", back_populates="athletes")
    brackets = relationship(
        "BracketParticipant",
        back_populates="athlete",
    )


class Coach(Base, TimestampMixin):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True, nullable=False)
    first_name = Column(String, index=True, nullable=False)

    athletes = relationship(
        "Athlete",
        back_populates="coach",
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)

    brackets = relationship("Bracket", back_populates="category")


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    registration_start_date = Column(Date, nullable=True)
    registration_end_date = Column(Date, nullable=True)
    image_url = Column(String, nullable=True)

    brackets = relationship(
        "Bracket",
        back_populates="tournament",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Bracket(Base):
    __tablename__ = "brackets"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer,
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type = Column(String, nullable=False)
    start_time = Column(Time, nullable=True)
    tatami = Column(Integer, nullable=True)

    tournament = relationship(
        "Tournament", back_populates="brackets", passive_deletes=True
    )
    category = relationship("Category", back_populates="brackets", passive_deletes=True)
    matches = relationship(
        "BracketMatch", back_populates="bracket", cascade="all, delete-orphan"
    )
    participants = relationship(
        "BracketParticipant", back_populates="bracket", cascade="all, delete-orphan"
    )


class BracketParticipant(Base):
    __tablename__ = "bracket_participants"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(
        Integer,
        ForeignKey("brackets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    seed = Column(Integer, nullable=False)

    bracket = relationship(
        "Bracket", back_populates="participants", passive_deletes=True
    )
    athlete = relationship("Athlete", back_populates="brackets", passive_deletes=True)


class BracketMatch(Base):
    __tablename__ = "bracket_matches"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(
        Integer, ForeignKey("brackets.id", ondelete="CASCADE"), nullable=False
    )
    round_number = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    next_slot = Column(Integer, nullable=True)

    bracket = relationship("Bracket", back_populates="matches", passive_deletes=True)
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
        Integer, ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True
    )
    athlete2_id = Column(
        Integer, ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True
    )
    winner_id = Column(
        Integer, ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True
    )
    score_athlete1 = Column(Integer, nullable=True)
    score_athlete2 = Column(Integer, nullable=True)
    is_finished = Column(Boolean, default=False)
    round_type = Column(String, nullable=True)

    athlete1 = relationship("Athlete", foreign_keys=[athlete1_id], passive_deletes=True)
    athlete2 = relationship("Athlete", foreign_keys=[athlete2_id], passive_deletes=True)
    winner = relationship("Athlete", foreign_keys=[winner_id], passive_deletes=True)

    bracket_match = relationship("BracketMatch", back_populates="match", uselist=False)
