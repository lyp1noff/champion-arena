"""Tatami -> Arena state sync.

Tatami sends the full current state of every bracket it changed. Arena applies a
snapshot when its version is not older than the stored one, updating matches in
place. Re-sending the same snapshot is harmless, so there is no event log, no
sequence numbers and no ordering to preserve: the latest snapshot always wins.
"""

from typing import Any
from uuid import UUID

from champion_domain import (
    BracketStatus,
    MatchStatus,
    PlacementMatchInput,
    TournamentStatus,
    compute_bracket_placements,
)
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
from src.models import Athlete, Bracket, BracketMatch, BracketParticipant, Match, Tournament
from src.schemas import (
    SyncBracket,
    SyncBracketResult,
    SyncBracketsRequest,
    SyncBracketsResponse,
    SyncMatch,
)
from src.services.live import publish_bracket_changes

MATCH_FIELDS = (
    "athlete1_id",
    "athlete2_id",
    "winner_id",
    "score_athlete1",
    "score_athlete2",
    "round_type",
    "stage",
    "repechage_side",
    "repechage_step",
    "status",
    "started_at",
    "ended_at",
)
SLOT_FIELDS = ("round_number", "position", "next_slot")


class SyncRejected(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _match_values(item: SyncMatch) -> dict[str, Any]:
    values = {field: getattr(item, field) for field in MATCH_FIELDS}
    values["status"] = item.status.value
    values["stage"] = item.stage or "main"
    return values


def _assign(target: object, values: dict[str, Any]) -> bool:
    changed = False
    for field, value in values.items():
        if getattr(target, field) != value:
            setattr(target, field, value)
            changed = True
    return changed


async def _check_athletes(db: AsyncSession, snapshot: SyncBracket) -> None:
    ids = {p.athlete_id for p in snapshot.participants}
    for item in snapshot.matches:
        ids.update((item.athlete1_id, item.athlete2_id, item.winner_id))
    ids.discard(None)
    if not ids:
        return
    found = set((await db.scalars(select(Athlete.id).where(Athlete.id.in_(ids)))).all())
    missing = sorted(i for i in ids if i is not None and i not in found)
    if missing:
        raise SyncRejected(f"unknown_athletes:{','.join(map(str, missing[:5]))}")


async def _sync_participants(db: AsyncSession, bracket_id: int, snapshot: SyncBracket) -> bool:
    current = (await db.scalars(select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))).all()
    incoming = sorted((p.seed, p.athlete_id or 0) for p in snapshot.participants)
    if sorted((p.seed, p.athlete_id or 0) for p in current) == incoming:
        return False
    await db.execute(delete(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))
    db.add_all(
        BracketParticipant(bracket_id=bracket_id, athlete_id=p.athlete_id, seed=p.seed) for p in snapshot.participants
    )
    return True


async def _sync_matches(db: AsyncSession, bracket_id: int, snapshot: SyncBracket) -> bool:
    rows = (
        await db.execute(
            select(BracketMatch, Match)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(BracketMatch.bracket_id == bracket_id)
        )
    ).all()
    existing: dict[UUID, tuple[BracketMatch, Match]] = {match.id: (bm, match) for bm, match in rows}

    incoming_ids = [item.id for item in snapshot.matches]
    if len(set(incoming_ids)) != len(incoming_ids):
        raise SyncRejected("duplicate_match_ids")

    changed = False
    for item in snapshot.matches:
        slot = {field: getattr(item, field) for field in SLOT_FIELDS}
        if item.id in existing:
            bm, match = existing[item.id]
            changed |= _assign(bm, slot)
            changed |= _assign(match, _match_values(item))
            continue
        if await db.get(Match, item.id) is not None:
            raise SyncRejected("match_belongs_to_other_bracket")
        db.add(Match(id=item.id, **_match_values(item)))
        db.add(BracketMatch(bracket_id=bracket_id, match_id=item.id, **slot))
        changed = True

    removed = [match_id for match_id in existing if match_id not in set(incoming_ids)]
    if removed:
        await db.execute(delete(BracketMatch).where(BracketMatch.match_id.in_(removed)))
        await db.execute(delete(Match).where(Match.id.in_(removed)))
        changed = True
    return changed


async def _recompute_placements(db: AsyncSession, bracket: Bracket) -> None:
    rows = (
        await db.execute(
            select(BracketMatch, Match)
            .join(Match, Match.id == BracketMatch.match_id)
            .where(BracketMatch.bracket_id == bracket.id)
        )
    ).all()
    placements = compute_bracket_placements(
        [
            PlacementMatchInput(
                round_number=bm.round_number,
                stage=match.stage,
                status=match.status,
                winner_id=match.winner_id,
                athlete1_id=match.athlete1_id,
                athlete2_id=match.athlete2_id,
                repechage_side=match.repechage_side,
                repechage_step=match.repechage_step,
            )
            for bm, match in rows
        ],
        repechage_stage_value="repechage",
        finished_status_value=MatchStatus.FINISHED.value,
    )
    bracket.place_1_id = placements.place_1_id
    bracket.place_2_id = placements.place_2_id
    bracket.place_3_a_id = placements.place_3_a_id
    bracket.place_3_b_id = placements.place_3_b_id


async def _apply_bracket(db: AsyncSession, tournament_id: int, snapshot: SyncBracket) -> tuple[SyncBracketResult, bool]:
    bracket = await db.get(Bracket, snapshot.bracket_id, with_for_update=True)
    if bracket is None or bracket.tournament_id != tournament_id:
        raise SyncRejected("bracket_not_found")
    if snapshot.version < bracket.version:
        return SyncBracketResult(bracket_id=bracket.id, status="stale", version=bracket.version), False

    await _check_athletes(db, snapshot)

    changed = _assign(bracket, {"type": snapshot.type, "group_id": snapshot.group_id, "status": snapshot.status.value})
    changed |= await _sync_participants(db, bracket.id, snapshot)
    changed |= await _sync_matches(db, bracket.id, snapshot)
    bracket.version = snapshot.version
    await db.flush()
    if changed:
        await _recompute_placements(db, bracket)
    return SyncBracketResult(bracket_id=bracket.id, status="applied", version=bracket.version), changed


async def _refresh_tournament_status(db: AsyncSession, tournament_id: int) -> None:
    tournament = await db.get(Tournament, tournament_id)
    if tournament is None or tournament.status == TournamentStatus.FINISHED.value:
        return
    rows = await db.execute(
        select(Bracket.status, func.count()).where(Bracket.tournament_id == tournament_id).group_by(Bracket.status)
    )
    counts: dict[str, int] = {str(status): int(count) for status, count in rows.all()}
    total = sum(counts.values())
    finished = counts.get(BracketStatus.FINISHED.value, 0)
    if total and finished == total:
        tournament.status = TournamentStatus.FINISHED.value
    elif finished or counts.get(BracketStatus.STARTED.value, 0):
        tournament.status = TournamentStatus.STARTED.value


async def apply_brackets(db: AsyncSession, payload: SyncBracketsRequest) -> SyncBracketsResponse:
    if await db.get(Tournament, payload.tournament_id) is None:
        return SyncBracketsResponse(
            results=[
                SyncBracketResult(bracket_id=item.bracket_id, status="rejected", reason="tournament_not_found")
                for item in payload.brackets
            ]
        )

    results: list[SyncBracketResult] = []
    changed_ids: list[int] = []
    for snapshot in payload.brackets:
        try:
            # One savepoint per bracket: a bad snapshot must not block the rest of the batch.
            async with db.begin_nested():
                result, changed = await _apply_bracket(db, payload.tournament_id, snapshot)
        except SyncRejected as exc:
            result, changed = (
                SyncBracketResult(bracket_id=snapshot.bracket_id, status="rejected", reason=exc.reason),
                False,
            )
        except Exception:
            logger.exception("Sync apply failed: edge=%s bracket=%s", payload.edge_id, snapshot.bracket_id)
            result, changed = (
                SyncBracketResult(bracket_id=snapshot.bracket_id, status="rejected", reason="apply_failed"),
                False,
            )
        results.append(result)
        if changed:
            changed_ids.append(snapshot.bracket_id)

    if changed_ids:
        await _refresh_tournament_status(db, payload.tournament_id)
    await db.commit()

    rejected = [r for r in results if r.status != "applied"]
    if rejected:
        logger.warning("Sync from %s: %d/%d not applied: %s", payload.edge_id, len(rejected), len(results), rejected)
    if changed_ids:
        await publish_bracket_changes(db, payload.tournament_id, changed_ids)
    return SyncBracketsResponse(results=results)
