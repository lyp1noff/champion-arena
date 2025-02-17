import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from src.database import Base
from src.models import Athlete, Coach, Tournament, Bracket, BracketParticipant, BracketMatch, Category

# Создаём тестовую БД в памяти (SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фикстура для создания тестовой БД
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)  # Создаём таблицы
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)  # Удаляем таблицы после теста


# 1️⃣ Тест создания атлета и тренера
def test_create_athlete_and_coach(db_session):
    coach = Coach(first_name="John", last_name="Doe", credentials="Expert")
    db_session.add(coach)
    db_session.commit()

    athlete = Athlete(
        first_name="Mike", last_name="Tyson", gender="M",
        birth_date=date(1966, 6, 30), coach_id=coach.id
    )
    db_session.add(athlete)
    db_session.commit()

    retrieved_athlete = db_session.query(Athlete).first()
    assert retrieved_athlete is not None
    assert retrieved_athlete.first_name == "Mike"
    assert retrieved_athlete.coach.id == coach.id


# 2️⃣ Тест удаления атлета и проверки `BracketParticipant`
def test_delete_athlete(db_session):
    athlete = Athlete(first_name="Conor", last_name="McGregor", gender="M", birth_date=date(1988, 7, 14))
    db_session.add(athlete)
    db_session.commit()

    bracket = Bracket(tournament_id=None, category_id=None)  # Временно `None`, т.к. турниры ещё не созданы
    db_session.add(bracket)
    db_session.commit()

    participant = BracketParticipant(bracket_id=bracket.id, athlete_id=athlete.id, seed=1)
    db_session.add(participant)
    db_session.commit()

    db_session.delete(athlete)
    db_session.commit()

    remaining_participants = db_session.query(BracketParticipant).all()
    assert len(remaining_participants) == 0  # Должно удалиться `CASCADE`


# 3️⃣ Тест удаления турнира и проверки `Bracket`
def test_delete_tournament(db_session):
    tournament = Tournament(
        name="UFC 300", location="Las Vegas",
        start_date=date(2025, 4, 10), end_date=date(2025, 4, 11),
        registration_start_date=date(2025, 3, 1), registration_end_date=date(2025, 3, 20)
    )
    db_session.add(tournament)
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=None)
    db_session.add(bracket)
    db_session.commit()

    db_session.delete(tournament)
    db_session.commit()

    remaining_brackets = db_session.query(Bracket).all()
    assert len(remaining_brackets) == 0  # Должно удалиться `CASCADE`


# 4️⃣ Тест добавления и удаления матчей
def test_create_and_delete_match(db_session):
    athlete1 = Athlete(first_name="Floyd", last_name="Mayweather", gender="M", birth_date=date(1977, 2, 24))
    athlete2 = Athlete(first_name="Manny", last_name="Pacquiao", gender="M", birth_date=date(1978, 12, 17))
    db_session.add_all([athlete1, athlete2])
    db_session.commit()

    bracket = Bracket(tournament_id=None, category_id=None)
    db_session.add(bracket)
    db_session.commit()

    match = BracketMatch(
        bracket_id=bracket.id,
        round_number=1,
        position=1,
        athlete1_id=athlete1.id,
        athlete2_id=athlete2.id,
        is_finished=False
    )
    db_session.add(match)
    db_session.commit()

    db_session.delete(athlete1)
    db_session.commit()

    remaining_matches = db_session.query(BracketMatch).all()
    assert len(remaining_matches) == 1  # Матч должен остаться
    assert remaining_matches[0].athlete1_id is None
