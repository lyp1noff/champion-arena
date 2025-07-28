import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import date
from src.database import Base
from src.models import (
    Athlete,
    Coach,
    AthleteCoachLink,
    Tournament,
    Bracket,
    BracketParticipant,
    BracketMatch,
    Category,
    Match,
)

# Создаём тестовую БД в памяти (SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Фикстура для создания тестовой БД
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# 1️⃣ Тест создания атлета и тренера
def test_create_athlete_and_coach(db_session):
    coach = Coach(first_name="John", last_name="Doe")
    db_session.add(coach)
    db_session.commit()

    athlete = Athlete(
        first_name="Mike", last_name="Tyson", gender="M", birth_date=date(1966, 6, 30)
    )
    db_session.add(athlete)
    db_session.commit()

    # Create coach link
    coach_link = AthleteCoachLink(athlete_id=athlete.id, coach_id=coach.id)
    db_session.add(coach_link)
    db_session.commit()

    retrieved_athlete = db_session.query(Athlete).first()
    assert retrieved_athlete is not None
    assert retrieved_athlete.first_name == "Mike"
    assert len(retrieved_athlete.coaches) == 1
    assert retrieved_athlete.coaches[0].id == coach.id


# 2️⃣ Тест удаления атлета и проверки `BracketParticipant`
def test_delete_athlete(db_session):
    athlete = Athlete(
        first_name="Conor",
        last_name="McGregor",
        gender="M",
        birth_date=date(1988, 7, 14),
    )
    db_session.add(athlete)
    db_session.commit()

    # Create tournament and category for bracket
    tournament = Tournament(
        name="Test Tournament",
        location="Test Location",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )
    category = Category(name="Test Category", age=25, gender="M")
    db_session.add_all([tournament, category])
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    participant = BracketParticipant(
        bracket_id=bracket.id, athlete_id=athlete.id, seed=1
    )
    db_session.add(participant)
    db_session.commit()

    db_session.delete(athlete)
    db_session.commit()

    remaining_participants = db_session.query(BracketParticipant).all()
    assert len(remaining_participants) == 0  # Должно удалиться `CASCADE`


# 3️⃣ Тест удаления турнира и проверки `Bracket`
def test_delete_tournament(db_session):
    tournament = Tournament(
        name="UFC 300",
        location="Las Vegas",
        start_date=date(2025, 4, 10),
        end_date=date(2025, 4, 11),
        registration_start_date=date(2025, 3, 1),
        registration_end_date=date(2025, 3, 20),
    )
    db_session.add(tournament)
    db_session.commit()

    category = Category(name="Test Category", age=25, gender="M")
    db_session.add(category)
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    db_session.delete(tournament)
    db_session.commit()

    remaining_brackets = db_session.query(Bracket).all()
    assert len(remaining_brackets) == 0  # Должно удалиться `CASCADE`


# 4️⃣ Тест добавления и удаления матчей
def test_create_and_delete_match(db_session):
    athlete1 = Athlete(
        first_name="Floyd",
        last_name="Mayweather",
        gender="M",
        birth_date=date(1977, 2, 24),
    )
    athlete2 = Athlete(
        first_name="Manny",
        last_name="Pacquiao",
        gender="M",
        birth_date=date(1978, 12, 17),
    )
    db_session.add_all([athlete1, athlete2])
    db_session.commit()

    # Create tournament and category for bracket
    tournament = Tournament(
        name="Test Tournament",
        location="Test Location",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )
    category = Category(name="Test Category", age=25, gender="M")
    db_session.add_all([tournament, category])
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    # Create the Match object and assign athletes
    match = Match(athlete1_id=athlete1.id, athlete2_id=athlete2.id, is_finished=False)
    db_session.add(match)
    db_session.commit()

    # Create BracketMatch referencing the Match
    bracket_match = BracketMatch(
        bracket_id=bracket.id, round_number=1, position=1, match_id=match.id
    )
    db_session.add(bracket_match)
    db_session.commit()

    db_session.delete(athlete1)
    db_session.commit()

    # Refresh the match object from the database
    match_from_db = db_session.query(Match).filter_by(id=match.id).one()

    remaining_matches = db_session.query(BracketMatch).all()
    assert len(remaining_matches) == 1  # Матч должен остаться
    assert match_from_db.athlete1_id is None
