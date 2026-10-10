import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from champion_domain import MatchStatus

from src.models import Athlete, Bracket, BracketMatch, BracketStatus, Category, Match, Tournament


async def _seed_match(db_session):
    category = Category(name="Sync Category", min_age=18, max_age=35, gender="male")
    tournament = Tournament(
        name="Sync Cup",
        location="Kyiv",
        start_date=date(2026, 2, 3),
        end_date=date(2026, 2, 4),
        registration_start_date=date(2026, 1, 1),
        registration_end_date=date(2026, 1, 20),
        image_url=None,
    )
    athlete_1 = Athlete(first_name="A", last_name="One", gender="male", birth_date=date(2000, 1, 1))
    athlete_2 = Athlete(first_name="B", last_name="Two", gender="male", birth_date=date(2000, 2, 2))
    db_session.add_all([category, tournament, athlete_1, athlete_2])
    await db_session.flush()

    bracket = Bracket(
        tournament_id=tournament.id,
        category_id=category.id,
        status=BracketStatus.PENDING.value,
        version=1,
    )
    db_session.add(bracket)
    await db_session.flush()

    match = Match(athlete1_id=athlete_1.id, athlete2_id=athlete_2.id)
    db_session.add(match)
    await db_session.flush()

    db_session.add(
        BracketMatch(
            bracket_id=bracket.id,
            round_number=1,
            position=1,
            match_id=match.id,
            next_slot=None,
        )
    )
    await db_session.commit()
    return bracket.id, match.id


@pytest.mark.asyncio
async def test_sync_status_initializes_edge_state(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    response = await client.get(f"/sync/status/edge-node-1?tournament_id={bracket.tournament_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["edge_id"] == "edge-node-1"
    assert payload["last_applied_seq"] == 0


@pytest.mark.asyncio
async def test_sync_upserts_advance_seq_on_apply_error(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    response = await client.post(
        "/sync/upserts",
        json={
            "edge_id": "edge-node-2-error",
            "tournament_id": bracket.tournament_id,
            "items": [
                {
                    "event_id": str(uuid.uuid4()),
                    "seq": 1,
                    "type": "unknown.upsert",
                    "aggregate_id": str(uuid.uuid4()),
                    "aggregate_version": 1,
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "payload": {},
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] == []
    assert payload["duplicates"] == []
    assert payload["last_applied_seq"] == 1
    assert payload["conflicts"][0]["reason"] == "unsupported_upsert_type"


@pytest.mark.asyncio
async def test_running_bracket_is_immutable_for_structural_update(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    bracket.status = BracketStatus.STARTED.value
    await db_session.commit()

    response = await client.put(f"/brackets/{bracket_id}", json={"group_id": 2})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_sync_upserts_retry_unapplied_event_then_deduplicate(client: AsyncClient, db_session) -> None:
    bracket_id, existing_match_id = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    existing_match = await db_session.get(Match, existing_match_id)
    assert existing_match is not None
    missing_match_id = uuid.uuid4()
    item = {
        "event_id": str(uuid.uuid4()),
        "seq": 1,
        "type": "match.upsert",
        "aggregate_id": str(missing_match_id),
        "aggregate_version": 2,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": {"status": MatchStatus.NOT_STARTED.value},
    }
    request_payload = {"edge_id": "edge-node-dup", "tournament_id": bracket.tournament_id, "items": [item]}
    first = await client.post("/sync/upserts", json=request_payload)
    assert first.status_code == 200
    assert first.json()["conflicts"][0]["reason"] == "aggregate_not_found"

    db_session.add(
        Match(
            id=missing_match_id,
            athlete1_id=existing_match.athlete1_id,
            athlete2_id=existing_match.athlete2_id,
            status=MatchStatus.NOT_STARTED.value,
        )
    )
    db_session.add(
        BracketMatch(
            bracket_id=bracket_id,
            round_number=1,
            position=2,
            match_id=missing_match_id,
            next_slot=None,
        )
    )
    await db_session.commit()

    second = await client.post("/sync/upserts", json=request_payload)
    assert second.status_code == 200
    assert second.json()["accepted"] == [1]
    assert second.json()["conflicts"][0]["reason"] == "seq_gap"

    third = await client.post("/sync/upserts", json=request_payload)
    assert third.status_code == 200
    assert third.json()["duplicates"] == [1]
