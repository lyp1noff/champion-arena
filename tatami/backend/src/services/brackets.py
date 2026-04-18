from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from champion_domain import SeededParticipant, is_bracket_structurally_mutable, plan_bracket_matches
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import EXTERNAL_API_TOKEN, EXTERNAL_API_URL
from src.models import Athlete, Bracket, BracketMatch, BracketParticipant, Match, TimetableEntry, Tournament
from src.services.outbox import create_bracket_upsert_outbox


async def get_bracket_by_external_id(db: AsyncSession, bracket_external_id: int) -> Bracket:
    result = await db.execute(
        select(Bracket)
        .where(Bracket.external_id == bracket_external_id)
        .options(selectinload(Bracket.participants).selectinload(BracketParticipant.athlete))
    )
    bracket = result.scalar_one_or_none()
    if bracket is None:
        raise HTTPException(status_code=404, detail=f"Bracket {bracket_external_id} not found")
    return bracket


def _ensure_bracket_editable(bracket: Bracket) -> None:
    if not is_bracket_structurally_mutable(bracket.state):
        raise HTTPException(status_code=409, detail="Running or finished bracket is structurally immutable")


async def _reorder_seeds(db: AsyncSession, bracket_id: int) -> None:
    result = await db.execute(
        select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id).order_by(
            BracketParticipant.seed.asc())
    )
    participants = result.scalars().all()
    for index, participant in enumerate(participants, start=1):
        participant.seed = index
    await db.flush()


async def _insert_participant(
        db: AsyncSession,
        *,
        bracket_id: int,
        athlete_id: int,
        target_seed: int | None,
) -> BracketParticipant:
    result = await db.execute(
        select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id).order_by(
            BracketParticipant.seed.asc())
    )
    participants = result.scalars().all()

    insert_seed = target_seed if target_seed is not None and target_seed > 0 else len(participants) + 1
    insert_seed = max(1, min(insert_seed, len(participants) + 1))

    for participant in reversed(participants):
        if participant.seed >= insert_seed:
            participant.seed += 1

    participant = BracketParticipant(
        bracket_id=bracket_id,
        athlete_id=athlete_id,
        seed=insert_seed,
    )
    db.add(participant)
    await db.flush()
    return participant


async def _clear_bracket_matches(db: AsyncSession, bracket_id: int) -> None:
    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))


async def regenerate_bracket(db: AsyncSession, bracket: Bracket) -> None:
    _ensure_bracket_editable(bracket)
    bracket.version = max(1, bracket.version + 1)

    await _clear_bracket_matches(db, bracket.id)

    result = await db.execute(
        select(BracketParticipant).where(BracketParticipant.bracket_id == bracket.id).order_by(
            BracketParticipant.seed.asc())
    )
    participants = result.scalars().all()
    seeded = [
        SeededParticipant(seed=participant.seed, athlete_id=participant.athlete_id)
        for participant in participants
        if participant.athlete_id is not None
    ]

    if len(seeded) < 2:
        await db.flush()
        return

    planned_matches = plan_bracket_matches(
        bracket_type=bracket.type,
        participants=seeded,
    )

    for planned in planned_matches:
        is_bye_win = planned.status == "finished" and planned.winner_id is not None
        match = Match(
            external_id=str(uuid4()),
            athlete1_id=planned.athlete1_id,
            athlete2_id=planned.athlete2_id,
            winner_id=planned.winner_id,
            round_type=planned.round_type,
            stage="main",
            status=planned.status,
            ended_at=datetime.now(timezone.utc) if is_bye_win else None,
        )
        db.add(match)
        await db.flush()

        db.add(
            BracketMatch(
                external_id=str(uuid4()),
                bracket_id=bracket.id,
                match_id=match.id,
                round_number=planned.round_number,
                position=planned.position,
                next_slot=planned.next_slot,
            )
        )

    await db.flush()


async def regenerate_brackets_and_enqueue_upserts(db: AsyncSession, brackets: Sequence[Bracket]) -> None:
    for bracket in brackets:
        await regenerate_bracket(db, bracket)
    for bracket in brackets:
        await create_bracket_upsert_outbox(bracket, db)


async def ensure_local_athlete(db: AsyncSession, athlete_external_id: int) -> Athlete:
    result = await db.execute(select(Athlete).where(Athlete.external_id == athlete_external_id))
    athlete = result.scalar_one_or_none()
    if athlete is not None:
        return athlete

    import httpx

    headers = {"Authorization": f"Bearer {EXTERNAL_API_TOKEN}"} if EXTERNAL_API_TOKEN else {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EXTERNAL_API_URL}/athletes/{athlete_external_id}", headers=headers)
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Athlete {athlete_external_id} not found on arena")
            response.raise_for_status()
            payload = response.json()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Arena athlete lookup failed: {exc.response.status_code}")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Arena athlete lookup failed: {str(exc)}")

    coaches = payload.get("coaches_last_name") or []
    athlete = Athlete(
        external_id=payload["id"],
        first_name=payload.get("first_name") or "",
        last_name=payload.get("last_name") or "",
        coaches_last_name=", ".join(coaches) if isinstance(coaches, list) else str(coaches),
    )
    db.add(athlete)
    await db.flush()
    return athlete


async def list_bracket_participants(db: AsyncSession, bracket_external_id: int) -> list[BracketParticipant]:
    bracket = await get_bracket_by_external_id(db, bracket_external_id)
    result = await db.execute(
        select(BracketParticipant)
        .where(BracketParticipant.bracket_id == bracket.id)
        .options(selectinload(BracketParticipant.athlete))
        .order_by(BracketParticipant.seed.asc())
    )
    return list(result.scalars().all())


async def add_participant_to_bracket(
        db: AsyncSession,
        *,
        bracket_external_id: int,
        athlete_external_id: int,
        seed: int | None,
) -> BracketParticipant:
    bracket = await get_bracket_by_external_id(db, bracket_external_id)
    _ensure_bracket_editable(bracket)

    athlete = await ensure_local_athlete(db, athlete_external_id)

    existing = await db.execute(
        select(BracketParticipant).where(
            BracketParticipant.bracket_id == bracket.id,
            BracketParticipant.athlete_id == athlete.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Athlete is already in this bracket")

    participant = await _insert_participant(db, bracket_id=bracket.id, athlete_id=athlete.id, target_seed=seed)
    participant_id = participant.id
    await regenerate_brackets_and_enqueue_upserts(db, [bracket])
    await db.commit()
    result = await db.execute(
        select(BracketParticipant)
        .where(BracketParticipant.id == participant_id)
        .options(selectinload(BracketParticipant.athlete))
    )
    created_participant = result.scalar_one_or_none()
    if created_participant is None:
        raise HTTPException(status_code=500, detail="Created participant could not be reloaded")
    return created_participant


async def remove_participant_from_bracket(
        db: AsyncSession,
        *,
        bracket_external_id: int,
        participant_id: int,
) -> None:
    bracket = await get_bracket_by_external_id(db, bracket_external_id)
    _ensure_bracket_editable(bracket)

    participant = await db.get(BracketParticipant, participant_id)
    if participant is None or participant.bracket_id != bracket.id:
        raise HTTPException(status_code=404, detail="Bracket participant not found")

    await db.delete(participant)
    await db.flush()
    await _reorder_seeds(db, bracket.id)
    await regenerate_brackets_and_enqueue_upserts(db, [bracket])
    await db.commit()


async def move_participant_between_brackets(
        db: AsyncSession,
        *,
        participant_id: int,
        target_bracket_external_id: int,
        target_seed: int | None,
) -> None:
    participant = await db.get(BracketParticipant, participant_id)
    if participant is None or participant.athlete_id is None:
        raise HTTPException(status_code=404, detail="Bracket participant not found")

    source_bracket = await db.get(Bracket, participant.bracket_id)
    if source_bracket is None:
        raise HTTPException(status_code=404, detail="Source bracket not found")
    target_bracket = await get_bracket_by_external_id(db, target_bracket_external_id)

    _ensure_bracket_editable(source_bracket)
    _ensure_bracket_editable(target_bracket)

    if source_bracket.id == target_bracket.id:
        raise HTTPException(status_code=400, detail="Source and target bracket must be different")

    existing = await db.execute(
        select(BracketParticipant).where(
            BracketParticipant.bracket_id == target_bracket.id,
            BracketParticipant.athlete_id == participant.athlete_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Athlete is already in the target bracket")

    athlete_id = participant.athlete_id
    await db.delete(participant)
    await db.flush()
    await _reorder_seeds(db, source_bracket.id)
    await _insert_participant(db, bracket_id=target_bracket.id, athlete_id=athlete_id, target_seed=target_seed)

    await regenerate_brackets_and_enqueue_upserts(db, [source_bracket, target_bracket])
    await db.commit()


async def update_participant_seed(
        db: AsyncSession,
        *,
        bracket_external_id: int,
        participant_id: int,
        seed: int,
) -> BracketParticipant:
    bracket = await get_bracket_by_external_id(db, bracket_external_id)
    _ensure_bracket_editable(bracket)

    participant = await db.get(BracketParticipant, participant_id)
    if participant is None or participant.bracket_id != bracket.id:
        raise HTTPException(status_code=404, detail="Bracket participant not found")

    if seed < 1:
        raise HTTPException(status_code=400, detail="Seed must be greater than zero")

    result = await db.execute(
        select(BracketParticipant).where(BracketParticipant.bracket_id == bracket.id).order_by(
            BracketParticipant.seed.asc())
    )
    participants = list(result.scalars().all())
    ordered = [item for item in participants if item.id != participant.id]
    insert_index = min(seed - 1, len(ordered))
    ordered.insert(insert_index, participant)

    for index, item in enumerate(ordered, start=1):
        item.seed = index

    await db.flush()
    await regenerate_brackets_and_enqueue_upserts(db, [bracket])
    await db.commit()

    reloaded = await db.execute(
        select(BracketParticipant)
        .where(BracketParticipant.id == participant_id)
        .options(selectinload(BracketParticipant.athlete))
    )
    updated = reloaded.scalar_one_or_none()
    if updated is None:
        raise HTTPException(status_code=500, detail="Updated participant could not be reloaded")
    return updated


async def list_timetable_entries(db: AsyncSession, tournament_external_id: int) -> list[TimetableEntry]:
    tournament_result = await db.execute(select(Tournament).where(Tournament.external_id == tournament_external_id))
    tournament = tournament_result.scalar_one_or_none()
    if tournament is None:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_external_id} not found")

    result = await db.execute(
        select(TimetableEntry)
        .where(TimetableEntry.tournament_id == tournament.id)
        .order_by(TimetableEntry.day.asc(), TimetableEntry.tatami.asc(), TimetableEntry.start_time.asc(),
                  TimetableEntry.order_index.asc())
    )
    return list(result.scalars().all())


async def replace_timetable_entries(
        db: AsyncSession,
        *,
        tournament_external_id: int,
        entries: list[dict[str, object]],
) -> list[TimetableEntry]:
    tournament_result = await db.execute(select(Tournament).where(Tournament.external_id == tournament_external_id))
    tournament = tournament_result.scalar_one_or_none()
    if tournament is None:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_external_id} not found")

    bracket_external_ids = [entry["bracket_id"] for entry in entries if entry.get("bracket_id") is not None]
    if len(bracket_external_ids) != len(set(bracket_external_ids)):
        raise HTTPException(status_code=400, detail="Duplicate bracket_id in timetable")

    bracket_by_external_id: dict[int, Bracket] = {}
    if bracket_external_ids:
        result = await db.execute(
            select(Bracket).where(Bracket.external_id.in_(bracket_external_ids), Bracket.tournament_id == tournament.id)
        )
        bracket_by_external_id = {bracket.external_id: bracket for bracket in result.scalars().all()}
        missing = sorted(set(int(item) for item in bracket_external_ids) - set(bracket_by_external_id))
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown bracket ids in timetable: {missing}")

    await db.execute(delete(TimetableEntry).where(TimetableEntry.tournament_id == tournament.id))

    created_entries: list[TimetableEntry] = []
    for entry in entries:
        bracket_external_id = entry.get("bracket_id")
        bracket = bracket_by_external_id.get(int(bracket_external_id)) if bracket_external_id is not None else None
        timetable_entry = TimetableEntry(
            tournament_id=tournament.id,
            bracket_id=bracket.id if bracket is not None else None,
            entry_type=str(entry["entry_type"]),
            title=entry.get("title"),
            notes=entry.get("notes"),
            day=int(entry["day"]),
            tatami=int(entry["tatami"]),
            start_time=entry["start_time"],
            end_time=entry["end_time"],
            order_index=int(entry["order_index"]),
        )
        db.add(timetable_entry)
        created_entries.append(timetable_entry)

    await db.commit()
    return await list_timetable_entries(db, tournament_external_id)
