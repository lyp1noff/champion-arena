from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient

from src.models import Athlete, Bracket, BracketParticipant


@pytest.mark.asyncio
async def test_athlete_response_includes_computed_fields(client: AsyncClient) -> None:
    coach_payload = {"first_name": "Ivan", "last_name": "Petrov"}
    coach_response = await client.post("/coaches", json=coach_payload)
    assert coach_response.status_code == 200
    coach_id = coach_response.json()["id"]

    birth_date = (datetime.now(UTC).date() - timedelta(days=365 * 10)).isoformat()
    athlete_payload = {
        "first_name": "Oleg",
        "last_name": "Sidorov",
        "gender": "male",
        "birth_date": birth_date,
        "coaches_id": [coach_id],
    }
    create_response = await client.post("/athletes", json=athlete_payload)
    assert create_response.status_code == 200
    athlete_data = create_response.json()

    assert athlete_data["coaches_id"] == [coach_id]
    assert athlete_data["coaches_last_name"] == ["Petrov"]
    assert athlete_data["age"] is not None

    get_response = await client.get(f"/athletes/{athlete_data['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["coaches_id"] == [coach_id]
    assert fetched["coaches_last_name"] == ["Petrov"]


@pytest.mark.asyncio
async def test_bracket_response_participants_sorted_and_display_name(client: AsyncClient, db_session) -> None:
    category_response = await client.post(
        "/categories",
        json={"name": "U18 Kata", "min_age": 14, "max_age": 18, "gender": "female"},
    )
    assert category_response.status_code == 200
    category_id = category_response.json()["id"]

    tournament_payload = {
        "name": "Test Cup",
        "location": "Kyiv",
        "start_date": date(2025, 5, 10).isoformat(),
        "end_date": date(2025, 5, 11).isoformat(),
        "registration_start_date": date(2025, 4, 1).isoformat(),
        "registration_end_date": date(2025, 4, 30).isoformat(),
        "image_url": None,
    }
    tournament_response = await client.post("/tournaments", json=tournament_payload)
    assert tournament_response.status_code == 200
    tournament_id = tournament_response.json()["id"]

    bracket_payload = {
        "tournament_id": tournament_id,
        "category_id": category_id,
        "group_id": 2,
        "type": "single_elimination",
    }
    bracket_response = await client.post("/brackets/create", json=bracket_payload)
    assert bracket_response.status_code == 200
    bracket_id = bracket_response.json()["id"]

    athlete_1 = Athlete(first_name="Anna", last_name="Koval", gender="female", birth_date=date(2010, 1, 1))
    athlete_2 = Athlete(first_name="Olha", last_name="Bondar", gender="female", birth_date=date(2011, 2, 2))
    db_session.add_all([athlete_1, athlete_2])
    await db_session.flush()

    participants = [
        BracketParticipant(bracket_id=bracket_id, athlete_id=athlete_2.id, seed=2),
        BracketParticipant(bracket_id=bracket_id, athlete_id=athlete_1.id, seed=1),
    ]
    db_session.add_all(participants)
    await db_session.commit()

    response = await client.get(f"/brackets/{bracket_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["display_name"] == "U18 Kata (Group 2)"
    assert [p["seed"] for p in data["participants"]] == [1, 2]


@pytest.mark.asyncio
async def test_bracket_and_tournament_responses_include_placements(client: AsyncClient, db_session) -> None:
    category_response = await client.post(
        "/categories",
        json={"name": "Senior Kumite", "min_age": 18, "max_age": 35, "gender": "male"},
    )
    assert category_response.status_code == 200
    category_id = category_response.json()["id"]

    tournament_response = await client.post(
        "/tournaments",
        json={
            "name": "Placements API Cup",
            "location": "Lviv",
            "start_date": date(2025, 7, 10).isoformat(),
            "end_date": date(2025, 7, 11).isoformat(),
            "registration_start_date": date(2025, 6, 1).isoformat(),
            "registration_end_date": date(2025, 6, 30).isoformat(),
            "image_url": None,
        },
    )
    assert tournament_response.status_code == 200
    tournament_id = tournament_response.json()["id"]

    bracket_response = await client.post(
        "/brackets/create",
        json={
            "tournament_id": tournament_id,
            "category_id": category_id,
            "group_id": 1,
            "type": "single_elimination",
        },
    )
    assert bracket_response.status_code == 200
    bracket_id = bracket_response.json()["id"]

    athletes = [
        Athlete(first_name="A1", last_name="L1", gender="male", birth_date=date(2000, 1, 1)),
        Athlete(first_name="A2", last_name="L2", gender="male", birth_date=date(2000, 1, 1)),
        Athlete(first_name="A3", last_name="L3", gender="male", birth_date=date(2000, 1, 1)),
        Athlete(first_name="A4", last_name="L4", gender="male", birth_date=date(2000, 1, 1)),
    ]
    db_session.add_all(athletes)
    await db_session.flush()

    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    bracket.place_1_id = athletes[0].id
    bracket.place_2_id = athletes[1].id
    bracket.place_3_a_id = athletes[2].id
    bracket.place_3_b_id = athletes[3].id
    await db_session.commit()

    single_bracket_response = await client.get(f"/brackets/{bracket_id}")
    assert single_bracket_response.status_code == 200
    single_data = single_bracket_response.json()
    assert single_data["place_1"]["id"] == athletes[0].id
    assert single_data["place_2"]["id"] == athletes[1].id
    assert single_data["place_3_a"]["id"] == athletes[2].id
    assert single_data["place_3_b"]["id"] == athletes[3].id

    tournament_brackets_response = await client.get(f"/tournaments/{tournament_id}/brackets")
    assert tournament_brackets_response.status_code == 200
    data = tournament_brackets_response.json()
    assert len(data) == 1
    assert data[0]["place_1"]["id"] == athletes[0].id
    assert data[0]["place_2"]["id"] == athletes[1].id
    assert data[0]["place_3_a"]["id"] == athletes[2].id
    assert data[0]["place_3_b"]["id"] == athletes[3].id
