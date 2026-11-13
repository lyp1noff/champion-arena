from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Bracket, SyncWorkerState, Tournament
from src.services.sync_push import is_blocked, is_dirty, mark_for_resend, needs_sending

router = APIRouter(prefix="/sync", tags=["sync"])

WORKER_ALIVE_SECONDS = 20
BracketFilter = Literal["pending", "attention", "all"]


def _state(bracket: Bracket) -> str:
    dirty = bracket.version > (bracket.synced_version or 0)
    if not dirty:
        return "synced"
    if bracket.sync_blocked_version is not None and bracket.version <= bracket.sync_blocked_version:
        return "attention"
    return "pending"


async def _count(db: AsyncSession, *conditions: Any) -> int:
    return int(await db.scalar(select(func.count()).select_from(Bracket).where(*conditions)) or 0)


@router.get("/status")
async def get_sync_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    worker = await db.get(SyncWorkerState, 1)
    alive = bool(worker and worker.heartbeat_at >= datetime.now(UTC) - timedelta(seconds=WORKER_ALIVE_SECONDS)) and (
        worker is not None and worker.phase != "stopped"
    )
    oldest_pending_at = await db.scalar(select(func.min(Bracket.updated_at)).where(needs_sending()))
    return {
        "total": await _count(db),
        "synced": await _count(db, ~is_dirty()),
        "pending": await _count(db, needs_sending()),
        "attention": await _count(db, is_dirty(), is_blocked()),
        "oldest_pending_at": oldest_pending_at,
        "worker": {
            "alive": alive,
            "phase": worker.phase if worker else "unknown",
            "heartbeat_at": worker.heartbeat_at if worker else None,
            "last_success_at": worker.last_success_at if worker else None,
            "last_error": worker.last_error if worker else None,
            "next_attempt_at": worker.next_attempt_at if worker else None,
        },
    }


@router.get("/brackets")
async def list_sync_brackets(
    status: BracketFilter = Query("pending"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    conditions: list[Any] = []
    if status == "pending":
        conditions = [needs_sending()]
    elif status == "attention":
        conditions = [is_dirty(), is_blocked()]
    total = await _count(db, *conditions)
    rows = (
        await db.execute(
            select(Bracket, Tournament.name)
            .join(Tournament, Tournament.id == Bracket.tournament_id)
            .where(*conditions)
            .order_by(Bracket.updated_at.desc(), Bracket.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return {
        "total": total,
        "items": [
            {
                "bracket_id": bracket.external_id,
                "name": bracket.display_name or bracket.category,
                "tournament_name": tournament_name,
                "status": bracket.status,
                "state": _state(bracket),
                "version": bracket.version,
                "synced_version": bracket.synced_version,
                "synced_at": bracket.synced_at,
                "updated_at": bracket.updated_at,
                "error": bracket.sync_error,
                "remote_version": bracket.sync_remote_version,
            }
            for bracket, tournament_name in rows
        ],
    }


@router.post("/retry")
async def retry_now(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """End the worker's backoff wait so it tries Arena immediately."""
    worker = await db.get(SyncWorkerState, 1)
    if worker is not None:
        worker.next_attempt_at = datetime.now(UTC)
        await db.commit()
    return {"status": "ok"}


@router.post("/brackets/{bracket_id}/resend")
async def resend_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Send this bracket's current local state again, overriding a newer Arena version if needed."""
    bracket = await db.scalar(select(Bracket).where(Bracket.external_id == bracket_id))
    if bracket is None:
        raise HTTPException(status_code=404, detail=f"Bracket {bracket_id} not found")
    mark_for_resend(bracket)
    worker = await db.get(SyncWorkerState, 1)
    if worker is not None:
        worker.next_attempt_at = datetime.now(UTC)
    await db.commit()
    return {"status": "ok", "bracket_id": bracket_id, "version": bracket.version}
