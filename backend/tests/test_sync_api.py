import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from src.models import Athlete, Bracket, BracketMatch, BracketState, BracketStatus, Category, Match, Tournament


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
        state=BracketState.DRAFT.value,
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
async def test_sync_status_initializes_edge_state(client: AsyncClient) -> None:
    response = await client.get("/sync/status/edge-node-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["edge_id"] == "edge-node-1"
    assert payload["last_applied_seq"] == 0


@pytest.mark.asyncio
async def test_sync_commands_reject_out_of_order(client: AsyncClient) -> None:
    response = await client.post(
        "/sync/commands",
        json={
            "edge_id": "edge-node-2",
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "seq": 2,
                    "event_type": "match.started",
                    "aggregate_type": "match",
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
    assert payload["last_applied_seq"] == 0
    assert payload["conflicts"][0]["reason"] == "out_of_order"


@pytest.mark.asyncio
async def test_sync_commands_apply_match_events_and_increment_version(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)

    start_event = {
        "event_id": str(uuid.uuid4()),
        "seq": 1,
        "event_type": "match.started",
        "aggregate_type": "match",
        "aggregate_id": str(match_id),
        "aggregate_version": 2,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": {},
    }
    start_response = await client.post("/sync/commands", json={"edge_id": "edge-node-3", "events": [start_event]})
    assert start_response.status_code == 200
    assert start_response.json()["accepted"] == [1]

    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    assert bracket.version == 2
    assert bracket.state == BracketState.RUNNING.value

    score_event = {
        "event_id": str(uuid.uuid4()),
        "seq": 2,
        "event_type": "match.score_updated",
        "aggregate_type": "match",
        "aggregate_id": str(match_id),
        "aggregate_version": 3,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": {"score_athlete1": 1, "score_athlete2": 0},
    }
    score_response = await client.post("/sync/commands", json={"edge_id": "edge-node-3", "events": [score_event]})
    assert score_response.status_code == 200
    assert score_response.json()["accepted"] == [2]

    duplicate_response = await client.post("/sync/commands", json={"edge_id": "edge-node-3", "events": [score_event]})
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["duplicates"] == [2]

    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    assert bracket.version == 3


@pytest.mark.asyncio
async def test_running_bracket_is_immutable_for_structural_update(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    bracket.state = BracketState.RUNNING.value
    bracket.status = BracketStatus.STARTED.value
    await db_session.commit()

    response = await client.put(f"/brackets/{bracket_id}", json={"group_id": 2})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_sync_commands_apply_bracket_structure_rebuilt_event(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)

    participants = (await db_session.execute(select(Athlete).order_by(Athlete.id.asc()))).scalars().all()
    assert len(participants) >= 2

    rebuilt_match_id = str(uuid.uuid4())
    rebuild_event = {
        "event_id": str(uuid.uuid4()),
        "seq": 1,
        "event_type": "bracket.structure_rebuilt",
        "aggregate_type": "bracket",
        "aggregate_id": str(bracket_id),
        "aggregate_version": 2,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": {
            "state": "locked",
            "status": "pending",
            "participants": [
                {"athlete_id": participants[0].id, "seed": 1},
                {"athlete_id": participants[1].id, "seed": 2},
            ],
            "matches": [
                {
                    "id": rebuilt_match_id,
                    "round_number": 1,
                    "position": 1,
                    "next_slot": None,
                    "round_type": "final",
                    "stage": "main",
                    "status": "not_started",
                    "athlete1_id": participants[0].id,
                    "athlete2_id": participants[1].id,
                    "winner_id": None,
                    "score_athlete1": None,
                    "score_athlete2": None,
                    "repechage_side": None,
                    "repechage_step": None,
                    "started_at": None,
                    "ended_at": None,
                }
            ],
        },
    }

    response = await client.post("/sync/commands", json={"edge_id": "edge-node-5", "events": [rebuild_event]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] == [1]
    assert payload["conflicts"] == []

    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    assert bracket.version == 2
    assert bracket.state == "locked"

    match_count = await db_session.scalar(
        select(func.count()).select_from(BracketMatch).where(BracketMatch.bracket_id == bracket_id)
    )
    assert match_count == 1

    rebuilt_match = await db_session.get(Match, uuid.UUID(rebuilt_match_id))
    assert rebuilt_match is not None
