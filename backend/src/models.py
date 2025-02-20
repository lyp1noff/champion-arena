from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime, func
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
    __tablename__ = 'athletes'

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    gender = Column(String)
    birth_date = Column(Date)
    coach_id = Column(Integer, ForeignKey('coaches.id'), nullable=True)

    coach = relationship("Coach", back_populates="athletes")
    brackets = relationship("BracketParticipant", back_populates="athlete", cascade="all, delete")
    matches_as_athlete1 = relationship("BracketMatch", foreign_keys=lambda: [BracketMatch.athlete1_id], back_populates="athlete1")
    matches_as_athlete2 = relationship("BracketMatch", foreign_keys=lambda: [BracketMatch.athlete2_id], back_populates="athlete2")
    matches_won = relationship("BracketMatch", foreign_keys=lambda: [BracketMatch.winner_id], back_populates="winner")

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class Coach(Base, TimestampMixin):
    __tablename__ = 'coaches'

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True)
    first_name = Column(String, index=True)
    credentials = Column(String, nullable=True)

    athletes = relationship("Athlete", back_populates="coach")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)

    brackets = relationship("Bracket", back_populates="category")


class Tournament(Base, TimestampMixin):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    registration_start_date = Column(Date)
    registration_end_date = Column(Date)

    brackets = relationship("Bracket", back_populates="tournament", cascade="all, delete")


class Bracket(Base):
    __tablename__ = 'brackets'

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'), index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), index=True)

    tournament = relationship("Tournament", back_populates="brackets")
    category = relationship("Category", back_populates="brackets")
    matches = relationship("BracketMatch", back_populates="bracket", cascade="all, delete")
    participants = relationship("BracketParticipant", back_populates="bracket", cascade="all, delete")


class BracketParticipant(Base):
    __tablename__ = 'bracket_participants'

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(Integer, ForeignKey('brackets.id', ondelete="CASCADE"), index=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id', ondelete="SET NULL"), index=True)
    seed = Column(Integer)

    bracket = relationship("Bracket", back_populates="participants")
    athlete = relationship("Athlete", back_populates="brackets")


class BracketMatch(Base):
    __tablename__ = 'bracket_matches'

    id = Column(Integer, primary_key=True, index=True)
    bracket_id = Column(Integer, ForeignKey('brackets.id', ondelete="CASCADE"), index=True)
    round_number = Column(Integer)
    position = Column(Integer)
    athlete1_id = Column(Integer, ForeignKey('athletes.id', ondelete="SET NULL"), nullable=True, index=True)
    athlete2_id = Column(Integer, ForeignKey('athletes.id', ondelete="SET NULL"), nullable=True, index=True)
    winner_id = Column(Integer, ForeignKey('athletes.id', ondelete="SET NULL"), nullable=True, index=True)

    is_finished = Column(Boolean, default=False)

    bracket = relationship("Bracket", back_populates="matches")
    athlete1 = relationship("Athlete", foreign_keys=[athlete1_id], back_populates="matches_as_athlete1")
    athlete2 = relationship("Athlete", foreign_keys=[athlete2_id], back_populates="matches_as_athlete2")
    winner = relationship("Athlete", foreign_keys=[winner_id], back_populates="matches_won")
