from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Athlete(Base):
    __tablename__ = 'athletes'

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True)
    first_name = Column(String)
    gender = Column(String)
    birth_date = Column(Date)
    coach_id = Column(Integer, ForeignKey('coaches.id'))

    coach = relationship("Coach", back_populates="athletes")


class Coach(Base):
    __tablename__ = 'coaches'

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, index=True)
    first_name = Column(String)
    credentials = Column(String)

    athletes = relationship("Athlete", back_populates="coach")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(String)
    gender = Column(String)


class Tournament(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    registration_start_date = Column(Date)
    registration_end_date = Column(Date)
