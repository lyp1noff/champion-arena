from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Boolean,
    DateTime,
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


class Athlete(Base, TimestampMixin):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    gender = Column(String)
    birth_date = Column(Date)
    coach_id = Column(
        Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True
    )

    coach = relationship("Coach", back_populates="athletes")
    brackets = relationship("BracketParticipant", back_populates="athlete")
    # matches_as_athlete1 = relationship(
    #     "Match",
    #     foreign_keys="Match.athlete1_id",
    #     back_populates="athlete1",
    #     passive_deletes=True,
    # )
    # matches_as_athlete2 = relationship(
    #     "Match",
    #     foreign_keys="Match.athlete2_id",
    #     back_populates="athlete2",
    #     passive_deletes=True,
    # )
    # matches_won = relationship(
    #     "Match",
    #     foreign_keys="Match.winner_id",
    #     back_populates="winner",
    #     passive_deletes=True,
    # )
    tournaments = relationship("TournamentParticipant", back_populates="athlete")


class Coach(Base, TimestampMixin):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True)
    first_name = Column(String, index=True)
    # credentials = Column(String, nullable=True)

    athletes = relationship("Athlete", back_populates="coach")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)

    brackets = relationship("Bracket", back_populates="category")


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    registration_start_date = Column(Date, nullable=True)
    registration_end_date = Column(Date, nullable=True)
    image_url = Column(String, nullable=True)

    brackets = relationship("Bracket", back_populates="tournament")
    participants = relationship("TournamentParticipant", back_populates="tournament")


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    tournament = relationship(
        "Tournament", back_populates="participants", passive_deletes=True
    )
    athlete = relationship("Athlete", back_populates="tournaments")


class Bracket(Base):
    __tablename__ = "brackets"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)

    tournament = relationship(
        "Tournament", back_populates="brackets", passive_deletes=True
    )
    category = relationship("Category", back_populates="brackets", passive_deletes=True)
    matches = relationship("BracketMatch", back_populates="bracket")
    participants = relationship("BracketParticipant", back_populates="bracket")


class BracketParticipant(Base):
    __tablename__ = "bracket_participants"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(
        Integer, ForeignKey("brackets.id", ondelete="CASCADE"), index=True
    )
    athlete_id = Column(
        Integer,
        ForeignKey("athletes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    seed = Column(Integer)

    bracket = relationship(
        "Bracket", back_populates="participants", passive_deletes=True
    )
    athlete = relationship("Athlete", back_populates="brackets", passive_deletes=True)


class BracketMatch(Base):
    __tablename__ = "bracket_matches"

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(Integer, ForeignKey("brackets.id", ondelete="CASCADE"))
    round_number = Column(Integer)
    position = Column(Integer)

    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"))
    # next_match_id = Column(Integer, ForeignKey("bracket_matches.id"), nullable=True)
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
