from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient

from src.models import Athlete, BracketParticipant


async def _create_bracket_with_participants(
    client: AsyncClient, db_session, participants_count: int
) -> tuple[int, list[int]]:
    category_response = await client.post(
        "/categories",
        json={"name": "U18 Kumite", "min_age": 14, "max_age": 18, "gender": "male"},
    )
    assert category_response.status_code == 200
    category_id = category_response.json()["id"]

    tournament_response = await client.post(
        "/tournaments",
        json={
            "name": "Placements Cup",
            "location": "Kyiv",
            "start_date": date(2025, 6, 10).isoformat(),
            "end_date": date(2025, 6, 11).isoformat(),
            "registration_start_date": date(2025, 5, 1).isoformat(),
            "registration_end_date": date(2025, 5, 31).isoformat(),
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
        Athlete(
            first_name=f"A{i}",
            last_name=f"L{i}",
            gender="male",
            birth_date=date(2010, 1, 1),
        )
        for i in range(1, participants_count + 1)
    ]
    db_session.add_all(athletes)
    await db_session.flush()

    participants = [
        BracketParticipant(bracket_id=bracket_id, athlete_id=athlete.id, seed=index)
        for index, athlete in enumerate(athletes, start=1)
    ]
    db_session.add_all(participants)
    await db_session.commit()

    regenerate_response = await client.post(f"/brackets/{bracket_id}/regenerate")
    assert regenerate_response.status_code == 200

    return bracket_id, [athlete.id for athlete in athletes]


async def _get_bracket_matches(client: AsyncClient, bracket_id: int) -> list[dict[str, Any]]:
    response = await client.get(f"/brackets/{bracket_id}/matches")
    assert response.status_code == 200
    return response.json()


async def _start_and_finish_with_athlete1(client: AsyncClient, match_id: str, athlete1_id: int) -> None:
    start_response = await client.post(f"/matches/{match_id}/start")
    assert start_response.status_code == 200

    finish_response = await client.post(
        f"/matches/{match_id}/finish",
        json={"score_athlete1": 1, "score_athlete2": 0, "winner_id": athlete1_id},
    )
    assert finish_response.status_code == 200


@pytest.mark.asyncio
async def test_placements_not_assigned_until_repechage_finished(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _create_bracket_with_participants(client, db_session, participants_count=8)

    while True:
        matches = await _get_bracket_matches(client, bracket_id)
        pending_main = [
            bm for bm in matches if bm["match"]["stage"] != "repechage" and bm["match"]["status"] != "finished"
        ]
        if not pending_main:
            break

        current_round = min(bm["round_number"] for bm in pending_main)
        current_round_matches = [bm for bm in pending_main if bm["round_number"] == current_round]
        for bm in current_round_matches:
            athlete1 = bm["match"]["athlete1"]
            assert athlete1 is not None
            await _start_and_finish_with_athlete1(client, bm["match"]["id"], athlete1["id"])

    bracket_response = await client.get(f"/brackets/{bracket_id}")
    assert bracket_response.status_code == 200
    bracket = bracket_response.json()
    assert bracket["place_1"] is not None
    assert bracket["place_2"] is not None
    assert bracket["place_3_a"] is None
    assert bracket["place_3_b"] is None

    matches_after_final = await _get_bracket_matches(client, bracket_id)
    repechage_matches = [bm for bm in matches_after_final if bm["match"]["stage"] == "repechage"]
    assert len(repechage_matches) == 2

    for bm in repechage_matches:
        athlete1 = bm["match"]["athlete1"]
        assert athlete1 is not None
        await _start_and_finish_with_athlete1(client, bm["match"]["id"], athlete1["id"])

    final_bracket_response = await client.get(f"/brackets/{bracket_id}")
    assert final_bracket_response.status_code == 200
    final_bracket = final_bracket_response.json()
    assert final_bracket["place_1"] is not None
    assert final_bracket["place_2"] is not None
    assert final_bracket["place_3_a"] is not None
    assert final_bracket["place_3_b"] is not None


@pytest.mark.asyncio
async def test_direct_bronze_for_small_single_elimination(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _create_bracket_with_participants(client, db_session, participants_count=4)

    while True:
        matches = await _get_bracket_matches(client, bracket_id)
        pending_main = [
            bm for bm in matches if bm["match"]["stage"] != "repechage" and bm["match"]["status"] != "finished"
        ]
        if not pending_main:
            break

        current_round = min(bm["round_number"] for bm in pending_main)
        current_round_matches = [bm for bm in pending_main if bm["round_number"] == current_round]
        for bm in current_round_matches:
            athlete1 = bm["match"]["athlete1"]
            assert athlete1 is not None
            await _start_and_finish_with_athlete1(client, bm["match"]["id"], athlete1["id"])

    final_matches = await _get_bracket_matches(client, bracket_id)
    assert not [bm for bm in final_matches if bm["match"]["stage"] == "repechage"]

    bracket_response = await client.get(f"/brackets/{bracket_id}")
    assert bracket_response.status_code == 200
    bracket = bracket_response.json()
    assert bracket["place_1"] is not None
    assert bracket["place_2"] is not None
    assert bracket["place_3_a"] is not None
    assert bracket["place_3_b"] is not None


@pytest.mark.asyncio
async def test_final_winner_does_not_enter_repechage(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _create_bracket_with_participants(client, db_session, participants_count=8)

    while True:
        matches = await _get_bracket_matches(client, bracket_id)
        pending_main = [
            bm for bm in matches if bm["match"]["stage"] != "repechage" and bm["match"]["status"] != "finished"
        ]
        if not pending_main:
            break

        current_round = min(bm["round_number"] for bm in pending_main)
        current_round_matches = [bm for bm in pending_main if bm["round_number"] == current_round]
        for bm in current_round_matches:
            athlete1 = bm["match"]["athlete1"]
            assert athlete1 is not None
            await _start_and_finish_with_athlete1(client, bm["match"]["id"], athlete1["id"])

    bracket_response = await client.get(f"/brackets/{bracket_id}")
    assert bracket_response.status_code == 200
    bracket = bracket_response.json()
    assert bracket["place_1"] is not None
    final_winner_id = bracket["place_1"]["id"]

    matches_after_final = await _get_bracket_matches(client, bracket_id)
    repechage_matches = [bm for bm in matches_after_final if bm["match"]["stage"] == "repechage"]
    assert repechage_matches

    for bm in repechage_matches:
        athlete1 = bm["match"]["athlete1"]
        athlete2 = bm["match"]["athlete2"]
        if athlete1 is not None:
            assert athlete1["id"] != final_winner_id
        if athlete2 is not None:
            assert athlete2["id"] != final_winner_id
