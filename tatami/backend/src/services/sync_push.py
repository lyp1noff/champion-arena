"""Tatami -> Arena state sync.

Every local change bumps ``Bracket.version``. A bracket is dirty while
``version > synced_version``; the sync worker sends the *current* state of dirty
brackets to Arena in batches. Ten score changes made offline therefore become one
request, and there is nothing to keep in order: the latest state always wins.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import ColumnElement, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import EDGE_ID
from src.models import Athlete, Bracket, BracketMatch, BracketParticipant, Match


@dataclass(frozen=True)
class PendingBracket:
    local_id: int
    arena_id: int
    tournament_arena_id: int
    version: int
    snapshot: dict[str, Any]


@dataclass(frozen=True)
class SyncResult:
    status: str  # applied | stale | rejected
    version: int | None
    reason: str | None


class SyncTransportError(Exception):
    """Arena could not be reached or answered with something other than results. Retried with backoff."""


def is_dirty() -> ColumnElement[bool]:
    return Bracket.version > func.coalesce(Bracket.synced_version, 0)


def is_blocked() -> ColumnElement[bool]:
    return and_(Bracket.sync_blocked_version.is_not(None), Bracket.version <= Bracket.sync_blocked_version)


def needs_sending() -> ColumnElement[bool]:
    return and_(is_dirty(), or_(Bracket.sync_blocked_version.is_(None), Bracket.version > Bracket.sync_blocked_version))


def retry_delay(attempt: int, *, jitter: float | None = None) -> float:
    base = min(60, 2 << min(max(1, attempt) - 1, 5))
    return float(base) + (random.uniform(0.0, 1.0) if jitter is None else jitter)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


async def build_snapshots(db: AsyncSession, bracket_ids: list[int]) -> list[PendingBracket]:
    # Versions are read first; matches loaded afterwards can only be newer, never older,
    # so a snapshot is never marked synced with stale content.
    brackets = (
        await db.scalars(
            select(Bracket)
            .where(Bracket.id.in_(bracket_ids))
            .options(
                selectinload(Bracket.tournament),
                selectinload(Bracket.participants).selectinload(BracketParticipant.athlete),
                selectinload(Bracket.matches).selectinload(BracketMatch.match).selectinload(Match.athlete1),
                selectinload(Bracket.matches).selectinload(BracketMatch.match).selectinload(Match.athlete2),
            )
        )
    ).all()

    winner_ids = {bm.match.winner_id for b in brackets for bm in b.matches if bm.match and bm.match.winner_id}
    external_by_local: dict[int, int] = {}
    if winner_ids:
        rows = await db.execute(select(Athlete.id, Athlete.external_id).where(Athlete.id.in_(winner_ids)))
        external_by_local = {local: external for local, external in rows.all()}

    pending = []
    for bracket in brackets:
        matches = []
        for bm in sorted(bracket.matches, key=lambda item: (item.round_number, item.position)):
            match = bm.match
            if match is None:
                continue
            matches.append(
                {
                    "id": match.external_id,
                    "round_number": bm.round_number,
                    "position": bm.position,
                    "next_slot": bm.next_slot,
                    "round_type": match.round_type,
                    "stage": match.stage or "main",
                    "repechage_side": match.repechage_side,
                    "repechage_step": match.repechage_step,
                    "status": match.status,
                    "athlete1_id": match.athlete1.external_id if match.athlete1 else None,
                    "athlete2_id": match.athlete2.external_id if match.athlete2 else None,
                    "winner_id": external_by_local.get(match.winner_id) if match.winner_id else None,
                    "score_athlete1": match.score_athlete1,
                    "score_athlete2": match.score_athlete2,
                    "started_at": _iso(match.started_at),
                    "ended_at": _iso(match.ended_at),
                }
            )
        snapshot = {
            "bracket_id": bracket.external_id,
            "version": bracket.version,
            "type": bracket.type,
            "group_id": bracket.group_id or 1,
            "status": bracket.status or "pending",
            "participants": [
                {"athlete_id": p.athlete.external_id if p.athlete else None, "seed": p.seed}
                for p in sorted(bracket.participants, key=lambda item: item.seed)
            ],
            "matches": matches,
        }
        pending.append(
            PendingBracket(
                local_id=bracket.id,
                arena_id=bracket.external_id,
                tournament_arena_id=bracket.tournament.external_id,
                version=bracket.version,
                snapshot=snapshot,
            )
        )
    return pending


async def load_pending(db: AsyncSession, limit: int) -> list[PendingBracket]:
    ids = (
        await db.scalars(
            select(Bracket.id).where(needs_sending()).order_by(Bracket.updated_at, Bracket.id).limit(limit)
        )
    ).all()
    return await build_snapshots(db, list(ids)) if ids else []


def make_request(tournament_arena_id: int, items: list[PendingBracket]) -> dict[str, Any]:
    return {"edge_id": EDGE_ID, "tournament_id": tournament_arena_id, "brackets": [item.snapshot for item in items]}


def interpret_response(response: httpx.Response, items: list[PendingBracket]) -> dict[int, SyncResult]:
    if not 200 <= response.status_code < 300:
        detail = response.text.strip()[:300]
        raise SyncTransportError(f"Arena HTTP {response.status_code}" + (f": {detail}" if detail else ""))
    try:
        body = response.json()
        results = {
            int(entry["bracket_id"]): SyncResult(
                status=str(entry["status"]), version=entry.get("version"), reason=entry.get("reason")
            )
            for entry in body["results"]
        }
    except (ValueError, KeyError, TypeError) as exc:
        raise SyncTransportError(f"Unexpected Arena response: {response.text[:300]}") from exc
    missing = [item.arena_id for item in items if item.arena_id not in results]
    if missing:
        raise SyncTransportError(f"Arena response has no result for brackets {missing}")
    return results


async def record_results(db: AsyncSession, items: list[PendingBracket], results: dict[int, SyncResult]) -> None:
    now = datetime.now(UTC)
    for item in items:
        result = results[item.arena_id]
        if result.status == "applied":
            values: dict[str, Any] = {
                "synced_version": func.greatest(func.coalesce(Bracket.synced_version, 0), item.version),
                "synced_at": now,
                "sync_error": None,
                "sync_blocked_version": None,
                "sync_remote_version": None,
            }
        elif result.status == "stale":
            values = {
                "sync_error": f"Arena has a newer version (v{result.version}) of this bracket",
                "sync_blocked_version": item.version,
                "sync_remote_version": result.version,
            }
        else:
            values = {
                "sync_error": result.reason or result.status,
                "sync_blocked_version": item.version,
                "sync_remote_version": None,
            }
        # Only sync columns: a concurrent local change keeps its version bump and stays dirty.
        await db.execute(update(Bracket).where(Bracket.id == item.local_id).values(**values))
    await db.commit()


def mark_for_resend(bracket: Bracket) -> None:
    """Send the current state again, overriding an Arena "stale" answer if there was one."""
    if bracket.sync_remote_version is not None and bracket.sync_remote_version >= bracket.version:
        bracket.version = bracket.sync_remote_version + 1
    bracket.synced_version = None
    bracket.sync_blocked_version = None
    bracket.sync_remote_version = None
    bracket.sync_error = None
