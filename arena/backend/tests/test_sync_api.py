import uuid
from datetime import UTC, date, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
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


async def _ids(db_session, bracket_id: int, match_id: uuid.UUID) -> tuple[int, int, int]:
    bracket = await db_session.get(Bracket, bracket_id)
    match = await db_session.get(Match, match_id)
    assert bracket is not None and match is not None
    assert match.athlete1_id is not None and match.athlete2_id is not None
    return bracket.tournament_id, match.athlete1_id, match.athlete2_id


def _snapshot(bracket_id: int, version: int, matches: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {
        "bracket_id": bracket_id,
        "version": version,
        "type": "single_elimination",
        "group_id": 1,
        "status": extra.get("status", "started"),
        "participants": extra.get("participants", []),
        "matches": matches,
    }


def _match(match_id: uuid.UUID, a1: int, a2: int, **fields: Any) -> dict[str, Any]:
    return {
        "id": str(match_id),
        "round_number": 1,
        "position": 1,
        "next_slot": None,
        "round_type": "final",
        "stage": "main",
        "status": MatchStatus.STARTED.value,
        "athlete1_id": a1,
        "athlete2_id": a2,
        **fields,
    }


async def _put(client: AsyncClient, tournament_id: int, *brackets: dict[str, Any]) -> list[dict[str, Any]]:
    response = await client.put(
        "/sync/brackets", json={"edge_id": "edge-1", "tournament_id": tournament_id, "brackets": list(brackets)}
    )
    assert response.status_code == 200
    return response.json()["results"]


@pytest.mark.asyncio
async def test_snapshot_updates_match_in_place_and_sets_placements(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)
    tournament_id, a1, a2 = await _ids(db_session, bracket_id, match_id)
    finished = _match(
        match_id,
        a1,
        a2,
        status=MatchStatus.FINISHED.value,
        winner_id=a2,
        score_athlete1=1,
        score_athlete2=3,
        ended_at=datetime.now(UTC).isoformat(),
    )
    participants = [{"athlete_id": a1, "seed": 1}, {"athlete_id": a2, "seed": 2}]

    results = await _put(client, tournament_id, _snapshot(bracket_id, 2, [finished], participants=participants))

    assert results == [{"bracket_id": bracket_id, "status": "applied", "version": 2, "reason": None}]
    db_session.expire_all()
    match = await db_session.get(Match, match_id)
    bracket = await db_session.get(Bracket, bracket_id)
    assert match is not None and bracket is not None
    assert (match.status, match.winner_id, match.score_athlete2, match.round_type) == ("finished", a2, 3, "final")
    assert (bracket.version, bracket.status, bracket.place_1_id, bracket.place_2_id) == (2, "started", a2, a1)


@pytest.mark.asyncio
async def test_resending_same_snapshot_is_idempotent(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)
    tournament_id, a1, a2 = await _ids(db_session, bracket_id, match_id)
    snapshot = _snapshot(bracket_id, 3, [_match(match_id, a1, a2, score_athlete1=2)])

    first = await _put(client, tournament_id, snapshot)
    second = await _put(client, tournament_id, snapshot)

    assert first[0]["status"] == second[0]["status"] == "applied"
    rows = (await db_session.execute(select(BracketMatch).where(BracketMatch.bracket_id == bracket_id))).all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_older_snapshot_is_stale_and_changes_nothing(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)
    tournament_id, a1, a2 = await _ids(db_session, bracket_id, match_id)
    await _put(client, tournament_id, _snapshot(bracket_id, 5, [_match(match_id, a1, a2, score_athlete1=4)]))

    results = await _put(client, tournament_id, _snapshot(bracket_id, 4, [_match(match_id, a1, a2, score_athlete1=1)]))

    assert results[0]["status"] == "stale"
    assert results[0]["version"] == 5
    db_session.expire_all()
    match = await db_session.get(Match, match_id)
    assert match is not None and match.score_athlete1 == 4


@pytest.mark.asyncio
async def test_bad_snapshot_is_rejected_without_blocking_the_batch(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)
    tournament_id, a1, a2 = await _ids(db_session, bracket_id, match_id)
    unknown_bracket = _snapshot(999_999, 1, [])
    unknown_athlete = _snapshot(bracket_id, 2, [_match(match_id, a1, 987_654)])
    good = _snapshot(bracket_id, 2, [_match(match_id, a1, a2, score_athlete1=7)])

    results = await _put(client, tournament_id, unknown_bracket, unknown_athlete, good)

    assert [(r["status"], r["reason"]) for r in results] == [
        ("rejected", "bracket_not_found"),
        ("rejected", "unknown_athletes:987654"),
        ("applied", None),
    ]
    db_session.expire_all()
    match = await db_session.get(Match, match_id)
    assert match is not None and match.score_athlete1 == 7


@pytest.mark.asyncio
async def test_structure_change_adds_and_removes_matches(client: AsyncClient, db_session) -> None:
    bracket_id, match_id = await _seed_match(db_session)
    tournament_id, a1, a2 = await _ids(db_session, bracket_id, match_id)
    new_ids = [uuid.uuid4(), uuid.uuid4()]
    matches = [
        _match(new_ids[0], a1, a2, round_type="group", status=MatchStatus.NOT_STARTED.value),
        _match(new_ids[1], a2, a1, round_type="group", position=2, status=MatchStatus.NOT_STARTED.value),
    ]

    results = await _put(client, tournament_id, _snapshot(bracket_id, 2, matches, status="pending"))

    assert results[0]["status"] == "applied"
    rows = (await db_session.scalars(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id))).all()
    assert sorted(rows) == sorted(new_ids)
    assert await db_session.get(Match, match_id) is None


@pytest.mark.asyncio
async def test_running_bracket_is_immutable_for_structural_update(client: AsyncClient, db_session) -> None:
    bracket_id, _ = await _seed_match(db_session)
    bracket = await db_session.get(Bracket, bracket_id)
    assert bracket is not None
    bracket.status = BracketStatus.STARTED.value
    await db_session.commit()

    response = await client.put(f"/brackets/{bracket_id}", json={"group_id": 2})
    assert response.status_code == 409
