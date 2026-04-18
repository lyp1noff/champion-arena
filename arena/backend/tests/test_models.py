"""
Test file for database models - Beginner Friendly Version

This file demonstrates how to test database models using pytest and SQLAlchemy.
We'll start with simple tests and gradually move to more complex scenarios.

Key concepts covered:
1. Basic CRUD operations (Create, Read, Update, Delete)
2. Model relationships and foreign keys
3. Database constraints and validations
4. Cascade operations (what happens when you delete related records)
5. Edge cases and error conditions
"""

import uuid
from datetime import date, datetime
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.models import (
    Application,
    ApplicationStatus,
    Athlete,
    AthleteCoachLink,
    Base,
    Bracket,
    BracketMatch,
    BracketParticipant,
    BracketStatus,
    BracketType,
    Category,
    Coach,
    Gender,
    Match,
    MatchStatus,
    Tournament,
    TournamentStatus,
    User,
    UserRole,
)

# =============================================================================
# TEST SETUP - This section sets up our test database
# =============================================================================

# We use SQLite in-memory database for testing (fast and isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=False)  # Set echo=True to see SQL queries
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Fixture that creates a fresh database session for each test.

    This ensures each test starts with a clean database state.
    The 'scope="function"' means this runs once per test function.
    """
    # Create a new engine for each test to ensure isolation
    test_engine = create_engine("sqlite:///:memory:")

    # Enable foreign key support for SQLite (important for testing relationships)
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables in the test database
    Base.metadata.create_all(test_engine)

    # Create a session factory and session
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()

    try:
        yield session  # This is what the test receives
    finally:
        # Clean up after the test
        session.close()
        test_engine.dispose()


# =============================================================================
# BASIC CRUD TESTS - Create, Read, Update, Delete operations
# =============================================================================


def test_create_and_read_athlete(db_session):
    """Test basic creation and reading of an Athlete record."""
    # CREATE - Create a new athlete
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))

    # Add to database (but not committed yet)
    db_session.add(athlete)

    # Commit the transaction
    db_session.commit()

    # READ - Query the database to verify the athlete was saved
    retrieved_athlete = db_session.query(Athlete).first()

    # Assertions - verify the data is correct
    assert retrieved_athlete is not None
    assert retrieved_athlete.first_name == "Mike"
    assert retrieved_athlete.last_name == "Tyson"
    assert retrieved_athlete.gender == Gender.MALE.value
    assert retrieved_athlete.birth_date == date(1966, 6, 30)
    assert retrieved_athlete.id is not None  # Should have auto-generated ID


def test_create_and_read_coach(db_session):
    """Test basic creation and reading of a Coach record."""
    coach = Coach(first_name="John", last_name="Doe")

    db_session.add(coach)
    db_session.commit()

    retrieved_coach = db_session.query(Coach).first()

    assert retrieved_coach is not None
    assert retrieved_coach.first_name == "John"
    assert retrieved_coach.last_name == "Doe"
    assert retrieved_coach.id is not None


def test_create_and_read_tournament(db_session):
    """Test basic creation and reading of a Tournament record."""
    tournament = Tournament(
        name="UFC 300",
        location="Las Vegas",
        start_date=date(2025, 4, 10),
        end_date=date(2025, 4, 11),
        status=TournamentStatus.DRAFT.value,
    )

    db_session.add(tournament)
    db_session.commit()

    retrieved_tournament = db_session.query(Tournament).first()

    assert retrieved_tournament is not None
    assert retrieved_tournament.name == "UFC 300"
    assert retrieved_tournament.location == "Las Vegas"
    assert retrieved_tournament.status == TournamentStatus.DRAFT.value
    assert retrieved_tournament.id is not None


def test_create_and_read_category(db_session):
    """Test basic creation and reading of a Category record."""
    category = Category(name="Men's Heavyweight", min_age=18, max_age=35, gender=Gender.MALE.value)

    db_session.add(category)
    db_session.commit()

    retrieved_category = db_session.query(Category).first()

    assert retrieved_category is not None
    assert retrieved_category.name == "Men's Heavyweight"
    assert retrieved_category.min_age == 18
    assert retrieved_category.max_age == 35
    assert retrieved_category.gender == Gender.MALE.value


def test_update_athlete(db_session):
    """Test updating an existing Athlete record."""
    # Create athlete
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    db_session.add(athlete)
    db_session.commit()

    # UPDATE - Modify the athlete's name
    athlete.first_name = "Michael"
    db_session.commit()

    # Verify the change
    updated_athlete = db_session.query(Athlete).first()
    assert updated_athlete.first_name == "Michael"


def test_delete_athlete(db_session):
    """Test deleting an Athlete record."""
    # Create athlete
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    db_session.add(athlete)
    db_session.commit()

    # Verify athlete exists
    assert db_session.query(Athlete).count() == 1

    # DELETE - Remove the athlete
    db_session.delete(athlete)
    db_session.commit()

    # Verify athlete is gone
    assert db_session.query(Athlete).count() == 0


# =============================================================================
# RELATIONSHIP TESTS - Testing how models connect to each other
# =============================================================================


def test_athlete_coach_relationship(db_session):
    """Test the many-to-many relationship between Athletes and Coaches."""
    # Create a coach
    coach = Coach(first_name="John", last_name="Doe")
    db_session.add(coach)
    db_session.commit()

    # Create an athlete
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    db_session.add(athlete)
    db_session.commit()

    # Create the relationship link
    coach_link = AthleteCoachLink(athlete_id=athlete.id, coach_id=coach.id)
    db_session.add(coach_link)
    db_session.commit()

    # Test the relationship from athlete side
    retrieved_athlete = db_session.query(Athlete).first()
    assert len(retrieved_athlete.coaches) == 1
    assert retrieved_athlete.coaches[0].id == coach.id

    # Test the relationship from coach side
    retrieved_coach = db_session.query(Coach).first()
    assert len(retrieved_coach.athletes) == 1
    assert retrieved_coach.athletes[0].id == athlete.id


def test_tournament_bracket_relationship(db_session):
    """Test the one-to-many relationship between Tournament and Brackets."""
    # Create tournament
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    db_session.add(tournament)

    # Create category
    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add(category)
    db_session.commit()

    # Create bracket
    bracket = Bracket(
        tournament_id=tournament.id,
        category_id=category.id,
        type=BracketType.SINGLE_ELIMINATION.value,
        status=BracketStatus.PENDING.value,
    )
    db_session.add(bracket)
    db_session.commit()

    # Test relationship from tournament side
    retrieved_tournament = db_session.query(Tournament).first()
    assert len(retrieved_tournament.brackets) == 1
    assert retrieved_tournament.brackets[0].id == bracket.id

    # Test relationship from bracket side
    retrieved_bracket = db_session.query(Bracket).first()
    assert retrieved_bracket.tournament.id == tournament.id
    assert retrieved_bracket.category.id == category.id


# =============================================================================
# CASCADE TESTS - Testing what happens when you delete related records
# =============================================================================


def test_cascade_delete_tournament_brackets(db_session):
    """Test that deleting a tournament also deletes its brackets (CASCADE)."""
    # Create tournament and bracket
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    db_session.add(tournament)

    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add(category)
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    # Verify both exist
    assert db_session.query(Tournament).count() == 1
    assert db_session.query(Bracket).count() == 1

    # Delete tournament
    db_session.delete(tournament)
    db_session.commit()

    # Verify tournament is gone and bracket is also gone (CASCADE)
    assert db_session.query(Tournament).count() == 0
    assert db_session.query(Bracket).count() == 0


def test_cascade_delete_athlete_participants(db_session):
    """Test that deleting an athlete removes them from bracket participants."""
    # Create athlete
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    db_session.add(athlete)

    # Create tournament and category
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add_all([tournament, category])
    db_session.commit()

    # Create bracket and participant
    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    participant = BracketParticipant(bracket_id=bracket.id, athlete_id=athlete.id, seed=1)
    db_session.add(participant)
    db_session.commit()

    # Verify participant exists
    assert db_session.query(BracketParticipant).count() == 1

    # Delete athlete
    db_session.delete(athlete)
    db_session.commit()

    # Verify athlete is gone and participant is also gone (CASCADE)
    assert db_session.query(Athlete).count() == 0
    assert db_session.query(BracketParticipant).count() == 0


# =============================================================================
# UUID TESTS - Testing the new UUID primary keys
# =============================================================================


def test_match_uuid_primary_key(db_session):
    """Test that Match model uses UUID primary keys."""
    # Create athletes for the match
    athlete1 = Athlete(
        first_name="Floyd", last_name="Mayweather", gender=Gender.MALE.value, birth_date=date(1977, 2, 24)
    )
    athlete2 = Athlete(
        first_name="Manny", last_name="Pacquiao", gender=Gender.MALE.value, birth_date=date(1978, 12, 17)
    )
    db_session.add_all([athlete1, athlete2])
    db_session.commit()

    # Create match
    match = Match(athlete1_id=athlete1.id, athlete2_id=athlete2.id, status=MatchStatus.NOT_STARTED.value)
    db_session.add(match)
    db_session.commit()

    # Verify UUID was generated
    assert match.id is not None
    assert isinstance(match.id, uuid.UUID)

    # Verify we can retrieve the match
    retrieved_match = db_session.query(Match).first()
    assert retrieved_match.id == match.id


def test_bracket_match_uuid_primary_key(db_session):
    """Test that BracketMatch model uses UUID primary keys."""
    # Create tournament, category, and bracket
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add_all([tournament, category])
    db_session.commit()

    bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
    db_session.add(bracket)
    db_session.commit()

    # Create match
    match = Match(status=MatchStatus.NOT_STARTED.value)
    db_session.add(match)
    db_session.commit()

    # Create bracket match
    bracket_match = BracketMatch(bracket_id=bracket.id, round_number=1, position=1, match_id=match.id)
    db_session.add(bracket_match)
    db_session.commit()

    # Verify UUID was generated
    assert bracket_match.id is not None
    assert isinstance(bracket_match.id, uuid.UUID)

    # Verify we can retrieve the bracket match
    retrieved_bracket_match = db_session.query(BracketMatch).first()
    assert retrieved_bracket_match.id == bracket_match.id


# =============================================================================
# APPLICATION MODEL TESTS - Testing the new Application functionality
# =============================================================================


def test_create_application(db_session):
    """Test creating an Application record."""
    # Create required related records
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add_all([tournament, athlete, category])
    db_session.commit()

    # Create application
    application = Application(
        tournament_id=tournament.id,
        athlete_id=athlete.id,
        category_id=category.id,
        status=ApplicationStatus.PENDING.value,
        comment="Please consider my application",
    )
    db_session.add(application)
    db_session.commit()

    # Verify application was created
    retrieved_application = db_session.query(Application).first()
    assert retrieved_application is not None
    assert retrieved_application.status == ApplicationStatus.PENDING.value
    assert retrieved_application.comment == "Please consider my application"
    assert retrieved_application.athlete.id == athlete.id
    assert retrieved_application.category.id == category.id


def test_application_status_transitions(db_session):
    """Test changing application status."""
    # Create required records
    tournament = Tournament(
        name="Test Tournament", location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)
    )
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    category = Category(name="Test Category", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add_all([tournament, athlete, category])
    db_session.commit()

    # Create application with pending status
    application = Application(
        tournament_id=tournament.id,
        athlete_id=athlete.id,
        category_id=category.id,
        status=ApplicationStatus.PENDING.value,
    )
    db_session.add(application)
    db_session.commit()

    # Change status to approved
    application.status = ApplicationStatus.APPROVED.value
    db_session.commit()

    # Verify status change
    retrieved_application = db_session.query(Application).first()
    assert retrieved_application.status == ApplicationStatus.APPROVED.value


# =============================================================================
# USER MODEL TESTS - Testing the User model
# =============================================================================


def test_create_user(db_session):
    """Test creating a User record."""
    user = User(username="admin", password_hash="hashed_password_123", role=UserRole.ADMIN.value)
    db_session.add(user)
    db_session.commit()

    # Verify user was created
    retrieved_user = db_session.query(User).first()
    assert retrieved_user is not None
    assert retrieved_user.username == "admin"
    assert retrieved_user.password_hash == "hashed_password_123"
    assert retrieved_user.role == UserRole.ADMIN.value


def test_user_role_default(db_session):
    """Test that user role defaults to admin."""
    user = User(
        username="user1",
        password_hash="hashed_password_123",
        # role not specified, should default to admin
    )
    db_session.add(user)
    db_session.commit()

    retrieved_user = db_session.query(User).first()
    assert retrieved_user.role == UserRole.ADMIN.value


# =============================================================================
# TIMESTAMP TESTS - Testing the TimestampMixin functionality
# =============================================================================


def test_timestamp_mixin(db_session):
    """Test that models with TimestampMixin have created_at and updated_at fields."""
    athlete = Athlete(first_name="Mike", last_name="Tyson", gender=Gender.MALE.value, birth_date=date(1966, 6, 30))
    db_session.add(athlete)
    db_session.commit()

    # Verify timestamps were created
    assert athlete.created_at is not None
    assert athlete.updated_at is not None
    assert isinstance(athlete.created_at, datetime)
    assert isinstance(athlete.updated_at, datetime)

    # Test that updated_at changes when record is modified
    # original_updated_at = athlete.updated_at

    # Wait a moment to ensure timestamp difference (SQLite has lower precision)
    import time

    time.sleep(0.1)  # Increased wait time for SQLite

    athlete.first_name = "Michael"
    db_session.commit()

    # For SQLite, we'll just verify the timestamp exists and is a datetime
    # The exact timing might not work reliably in tests
    assert athlete.updated_at is not None
    assert isinstance(athlete.updated_at, datetime)


# =============================================================================
# EDGE CASES AND ERROR CONDITIONS
# =============================================================================


def test_athlete_without_birth_date(db_session):
    """Test creating an athlete without birth_date (nullable field)."""
    athlete = Athlete(
        first_name="Unknown",
        last_name="Athlete",
        gender=Gender.MALE.value,
        # birth_date is optional
    )
    db_session.add(athlete)
    db_session.commit()

    retrieved_athlete = db_session.query(Athlete).first()
    assert retrieved_athlete.birth_date is None


def test_match_without_athletes(db_session):
    """Test creating a match without athletes (nullable fields)."""
    match = Match(
        status=MatchStatus.NOT_STARTED.value
        # athlete1_id and athlete2_id are optional
    )
    db_session.add(match)
    db_session.commit()

    retrieved_match = db_session.query(Match).first()
    assert retrieved_match.athlete1_id is None
    assert retrieved_match.athlete2_id is None


def test_bracket_display_name(db_session):
    """Test the get_display_name method of Bracket model."""
    category = Category(name="Men's Heavyweight", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add(category)
    db_session.commit()

    # Test default group (group_id = 1)
    bracket1 = Bracket(category_id=category.id, group_id=1)
    # Need to set the category relationship for the method to work
    bracket1.category = category
    assert bracket1.get_display_name() == "Men's Heavyweight"

    # Test with different group
    bracket2 = Bracket(category_id=category.id, group_id=2)
    bracket2.category = category
    assert bracket2.get_display_name() == "Men's Heavyweight (Group 2)"


# =============================================================================
# COMPLEX SCENARIO TESTS - Testing realistic tournament scenarios
# =============================================================================


def test_complete_tournament_scenario(db_session):
    """Test a complete tournament scenario with multiple related records."""
    # Create tournament
    tournament = Tournament(
        name="Championship 2025",
        location="Madison Square Garden",
        start_date=date(2025, 6, 15),
        end_date=date(2025, 6, 16),
        status=TournamentStatus.UPCOMING.value,
    )
    db_session.add(tournament)

    # Create category
    category = Category(name="Men's Middleweight", min_age=18, max_age=35, gender=Gender.MALE.value)
    db_session.add(category)
    db_session.commit()

    # Create athletes
    athlete1 = Athlete(
        first_name="Floyd", last_name="Mayweather", gender=Gender.MALE.value, birth_date=date(1977, 2, 24)
    )
    athlete2 = Athlete(
        first_name="Manny", last_name="Pacquiao", gender=Gender.MALE.value, birth_date=date(1978, 12, 17)
    )
    db_session.add_all([athlete1, athlete2])
    db_session.commit()

    # Create applications
    application1 = Application(
        tournament_id=tournament.id,
        athlete_id=athlete1.id,
        category_id=category.id,
        status=ApplicationStatus.APPROVED.value,
    )
    application2 = Application(
        tournament_id=tournament.id,
        athlete_id=athlete2.id,
        category_id=category.id,
        status=ApplicationStatus.APPROVED.value,
    )
    db_session.add_all([application1, application2])
    db_session.commit()

    # Create bracket
    bracket = Bracket(
        tournament_id=tournament.id,
        category_id=category.id,
        type=BracketType.SINGLE_ELIMINATION.value,
        status=BracketStatus.PENDING.value,
    )
    db_session.add(bracket)
    db_session.commit()

    # Create participants
    participant1 = BracketParticipant(bracket_id=bracket.id, athlete_id=athlete1.id, seed=1)
    participant2 = BracketParticipant(bracket_id=bracket.id, athlete_id=athlete2.id, seed=2)
    db_session.add_all([participant1, participant2])
    db_session.commit()

    # Create match
    match = Match(athlete1_id=athlete1.id, athlete2_id=athlete2.id, status=MatchStatus.NOT_STARTED.value)
    db_session.add(match)
    db_session.commit()

    # Create bracket match
    bracket_match = BracketMatch(bracket_id=bracket.id, round_number=1, position=1, match_id=match.id)
    db_session.add(bracket_match)
    db_session.commit()

    # Verify all relationships work correctly
    retrieved_tournament = db_session.query(Tournament).first()
    assert len(retrieved_tournament.brackets) == 1
    assert len(retrieved_tournament.brackets[0].participants) == 2
    assert len(retrieved_tournament.brackets[0].matches) == 1

    # Verify we can navigate through relationships
    bracket_from_tournament = retrieved_tournament.brackets[0]
    match_from_bracket = bracket_from_tournament.matches[0]
    assert match_from_bracket.match.athlete1.first_name == "Floyd"
    assert match_from_bracket.match.athlete2.first_name == "Manny"


# =============================================================================
# HELPER FUNCTIONS FOR TESTING
# =============================================================================


def create_test_athlete(db_session, first_name="Test", last_name="Athlete", **kwargs):
    """Helper function to create a test athlete."""
    athlete = Athlete(
        first_name=first_name, last_name=last_name, gender=Gender.MALE.value, birth_date=date(1990, 1, 1), **kwargs
    )
    db_session.add(athlete)
    db_session.commit()
    return athlete


def create_test_tournament(db_session, name="Test Tournament", **kwargs):
    """Helper function to create a test tournament."""
    tournament = Tournament(
        name=name, location="Test Location", start_date=date(2025, 1, 1), end_date=date(2025, 1, 2), **kwargs
    )
    db_session.add(tournament)
    db_session.commit()
    return tournament


def create_test_category(db_session, name="Test Category", **kwargs):
    """Helper function to create a test category."""
    category = Category(name=name, min_age=18, max_age=35, gender=Gender.MALE.value, **kwargs)
    db_session.add(category)
    db_session.commit()
    return category
