import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Bracket, Match, OutboxItem, OutboxWorkerState, Tournament
from src.services.outbox import (
    create_bracket_upsert_outbox,
    create_match_scores_outbox,
    get_bracket_with_tournament_for_match,
)

router = APIRouter(prefix="/outbox", tags=["outbox"])

ACTIVE_STATUSES = ("pending", "processing", "retry_wait")


def _payload_metadata(payload: str | None) -> dict[str, Any]:
    try:
        envelope = json.loads(payload or "{}")
        item = envelope.get("items", [{}])[0]
    except (json.JSONDecodeError, AttributeError, IndexError, TypeError):
        return {}
    return {
        "edge_id": envelope.get("edge_id"),
        "external_tournament_id": envelope.get("tournament_id"),
        "event_id": item.get("event_id"),
        "seq": item.get("seq"),
        "item_type": item.get("type"),
        "aggregate_id": item.get("aggregate_id"),
        "aggregate_version": item.get("aggregate_version"),
    }


def _serialize_item(item: OutboxItem, tournament_name: str | None, include_payload: bool = False) -> dict[str, Any]:
    result = {
        "id": item.id,
        "tournament_id": item.tournament_id,
        "tournament_name": tournament_name,
        "match_id": item.match_id,
        "status": item.status,
        "retry_count": item.retry_count,
        "failure_kind": item.failure_kind,
        "error": item.error,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "last_attempt_at": item.last_attempt_at,
        "next_attempt_at": item.next_attempt_at,
        "lease_until": item.lease_until,
        "resolved_at": item.resolved_at,
        **_payload_metadata(item.payload),
    }
    if include_payload:
        try:
            result["payload"] = json.loads(item.payload or "null")
        except json.JSONDecodeError:
            result["payload"] = item.payload
    return result


async def _status_count(db: AsyncSession, status: str) -> int:
    value = await db.scalar(select(func.count()).select_from(OutboxItem).where(OutboxItem.status == status))
    return int(value or 0)


@router.get("/status")
async def get_outbox_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    total = int(await db.scalar(select(func.count()).select_from(OutboxItem)) or 0)
    pending = await _status_count(db, "pending")
    processing = await _status_count(db, "processing")
    retry_wait = await _status_count(db, "retry_wait")
    dead_letter_count = await db.scalar(
        select(func.count())
        .select_from(OutboxItem)
        .where(OutboxItem.status == "dead_letter", OutboxItem.resolved_at.is_(None))
    )
    dead_letter = int(dead_letter_count or 0)
    succeeded = await _status_count(db, "success")
    oldest_pending_at = await db.scalar(
        select(func.min(OutboxItem.created_at)).where(OutboxItem.status.in_(ACTIVE_STATUSES))
    )
    worker = await db.get(OutboxWorkerState, 1)
    now = datetime.now(UTC)
    worker_alive = bool(worker and worker.heartbeat_at and worker.heartbeat_at >= now - timedelta(seconds=15))

    return {
        "total": total,
        "pending": pending,
        "succeeded": succeeded,
        "processing": processing,
        "retry_wait": retry_wait,
        "dead_letter": dead_letter,
        "outstanding": pending + processing + retry_wait,
        "oldest_pending_at": oldest_pending_at,
        "worker": {
            "alive": worker_alive,
            "status": worker.status if worker else "unknown",
            "heartbeat_at": worker.heartbeat_at if worker else None,
            "last_success_at": worker.last_success_at if worker else None,
            "last_error": worker.last_error if worker else None,
            "circuit_open_until": worker.circuit_open_until if worker else None,
        },
    }


@router.get("/items")
async def list_outbox_items(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters: list[Any] = []
    if status == "active":
        filters.append(OutboxItem.status.in_(ACTIVE_STATUSES))
    elif status == "attention":
        filters.extend((OutboxItem.status == "dead_letter", OutboxItem.resolved_at.is_(None)))
    elif status and status != "all":
        filters.append(OutboxItem.status == status)

    count_query = select(func.count()).select_from(OutboxItem)
    items_query = (
        select(OutboxItem, Tournament.name)
        .outerjoin(Tournament, Tournament.id == OutboxItem.tournament_id)
        .order_by(OutboxItem.created_at.desc(), OutboxItem.id.desc())
        .offset(offset)
        .limit(limit)
    )
    if filters:
        count_query = count_query.where(*filters)
        items_query = items_query.where(*filters)

    total = int(await db.scalar(count_query) or 0)
    rows = (await db.execute(items_query)).all()
    return {
        "total": total,
        "items": [_serialize_item(item, tournament_name) for item, tournament_name in rows],
    }


@router.post("/retry-all")
async def retry_all_outbox_items(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    result = await db.execute(
        update(OutboxItem)
        .where(OutboxItem.status == "retry_wait", OutboxItem.resolved_at.is_(None))
        .values(next_attempt_at=datetime.now(UTC), lease_until=None)
    )
    worker = await db.get(OutboxWorkerState, 1)
    if worker is not None:
        worker.circuit_open_until = datetime.now(UTC)
    await db.commit()
    return {"updated": int(getattr(result, "rowcount", 0) or 0)}


@router.get("/{item_id}")
async def get_outbox_item(item_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = (
        await db.execute(
            select(OutboxItem, Tournament.name)
            .outerjoin(Tournament, Tournament.id == OutboxItem.tournament_id)
            .where(OutboxItem.id == item_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Outbox item not found")
    return _serialize_item(row[0], row[1], include_payload=True)


@router.post("/{item_id}/retry")
async def retry_outbox_item(item_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    item = await db.get(OutboxItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Outbox item not found")
    if item.status != "retry_wait":
        raise HTTPException(status_code=409, detail="Only retryable delivery failures can be retried")
    item.status = "retry_wait"
    item.next_attempt_at = datetime.now(UTC)
    item.lease_until = None
    worker = await db.get(OutboxWorkerState, 1)
    if worker is not None:
        worker.circuit_open_until = datetime.now(UTC)
    await db.commit()
    return {"status": "scheduled"}


@router.post("/{item_id}/reconcile")
async def reconcile_outbox_item(item_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    item = await db.get(OutboxItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Outbox item not found")
    if item.status != "dead_letter" or item.resolved_at is not None:
        raise HTTPException(status_code=409, detail="Only unresolved dead-letter items can be reconciled")

    metadata = _payload_metadata(item.payload)
    item_type = metadata.get("item_type")
    aggregate_id = metadata.get("aggregate_id")
    new_item: OutboxItem | None = None

    if item_type == "match.upsert" and isinstance(aggregate_id, str):
        match = await db.scalar(select(Match).where(Match.external_id == aggregate_id))
        if match is None:
            raise HTTPException(status_code=409, detail="Current local match no longer exists")
        bracket = await get_bracket_with_tournament_for_match(match.id, db)
        if bracket is None:
            raise HTTPException(status_code=409, detail="Current local bracket no longer exists")
        new_item = await create_match_scores_outbox(match, bracket.version, db)
    elif item_type == "bracket.upsert":
        try:
            bracket_external_id = int(str(aggregate_id))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="Dead-letter aggregate id is invalid") from exc
        bracket = await db.scalar(select(Bracket).where(Bracket.external_id == bracket_external_id))
        if bracket is None:
            raise HTTPException(status_code=409, detail="Current local bracket no longer exists")
        new_item = await create_bracket_upsert_outbox(bracket, db)
    else:
        raise HTTPException(status_code=409, detail="This dead-letter item type cannot be reconciled")

    item.resolved_at = datetime.now(UTC)
    await db.commit()
    return {"status": "reconciled", "new_item_id": new_item.id}
