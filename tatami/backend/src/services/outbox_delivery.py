import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import and_, or_, select

from src.config import EXTERNAL_API_TOKEN, EXTERNAL_API_URL, OUTBOX_HTTP_TIMEOUT_SECONDS, OUTBOX_LEASE_SECONDS
from src.database import SessionLocal
from src.models import OutboxItem, OutboxWorkerState


@dataclass(frozen=True)
class ClaimedOutboxItem:
    id: int
    payload: str | None
    retry_count: int


class DeliveryFailure(Exception):
    def __init__(self, message: str, *, retryable: bool, kind: str) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.kind = kind


def retry_delay(attempt: int, *, jitter: float | None = None) -> float:
    bounded_attempt = max(1, attempt)
    base_seconds: int = min(60, 2 << min(bounded_attempt - 1, 5))
    random_jitter = random.uniform(0.0, 1.0) if jitter is None else jitter
    return float(base_seconds) + random_jitter


def classify_sync_response(response: httpx.Response) -> None:
    body_text = response.text.strip()
    if 200 <= response.status_code < 300:
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise DeliveryFailure("invalid sync response", retryable=True, kind="protocol") from exc
        if not isinstance(body, dict):
            raise DeliveryFailure("invalid sync response shape", retryable=True, kind="protocol")
        if body.get("accepted") or body.get("duplicates"):
            return
        conflicts = body.get("conflicts") or []
        if conflicts:
            first_conflict = conflicts[0]
            reason = first_conflict.get("reason", "unknown") if isinstance(first_conflict, dict) else "unknown"
            raise DeliveryFailure(f"sync conflict: {reason}", retryable=False, kind="application")
        raise DeliveryFailure("sync response has no accepted/duplicates", retryable=True, kind="protocol")

    message = f"status {response.status_code}"
    if body_text:
        message = f"{message}: {body_text}"
    if response.status_code == 408:
        raise DeliveryFailure(message, retryable=True, kind="timeout")
    if response.status_code == 429:
        raise DeliveryFailure(message, retryable=True, kind="rate_limit")
    if response.status_code >= 500 or response.status_code == 409:
        raise DeliveryFailure(message, retryable=True, kind="server")
    if response.status_code in {401, 403, 404}:
        raise DeliveryFailure(message, retryable=True, kind="configuration")
    raise DeliveryFailure(message, retryable=False, kind="http_rejection")


class OutboxRepository:
    async def claim_next(self) -> ClaimedOutboxItem | None:
        now = datetime.now(UTC)
        async with SessionLocal() as db, db.begin():
            item = await db.scalar(
                select(OutboxItem)
                .where(
                    OutboxItem.resolved_at.is_(None),
                    or_(
                        OutboxItem.status == "pending",
                        and_(
                            OutboxItem.status == "retry_wait",
                            or_(OutboxItem.next_attempt_at.is_(None), OutboxItem.next_attempt_at <= now),
                        ),
                        and_(
                            OutboxItem.status == "processing",
                            or_(OutboxItem.lease_until.is_(None), OutboxItem.lease_until <= now),
                        ),
                    ),
                )
                .order_by(OutboxItem.created_at.asc(), OutboxItem.id.asc())
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if item is None:
                return None
            item.status = "processing"
            item.last_attempt_at = now
            item.next_attempt_at = None
            item.lease_until = now + timedelta(seconds=OUTBOX_LEASE_SECONDS)
            await db.flush()
            return ClaimedOutboxItem(id=item.id, payload=item.payload, retry_count=item.retry_count)

    async def mark_success(self, item_id: int) -> None:
        async with SessionLocal() as db, db.begin():
            item = await db.get(OutboxItem, item_id, with_for_update=True)
            if item is None:
                return
            item.status = "success"
            item.error = None
            item.failure_kind = None
            item.next_attempt_at = None
            item.lease_until = None

    async def mark_retry_wait(self, item_id: int, failure: DeliveryFailure, next_attempt_at: datetime) -> None:
        async with SessionLocal() as db, db.begin():
            item = await db.get(OutboxItem, item_id, with_for_update=True)
            if item is None:
                return
            item.status = "retry_wait"
            item.retry_count += 1
            item.error = str(failure)
            item.failure_kind = failure.kind
            item.next_attempt_at = next_attempt_at
            item.lease_until = None

    async def mark_dead_letter(self, item_id: int, failure: DeliveryFailure) -> None:
        async with SessionLocal() as db, db.begin():
            item = await db.get(OutboxItem, item_id, with_for_update=True)
            if item is None:
                return
            item.status = "dead_letter"
            item.error = str(failure)
            item.failure_kind = failure.kind
            item.next_attempt_at = None
            item.lease_until = None

    async def worker_state(self) -> OutboxWorkerState | None:
        async with SessionLocal() as db:
            return await db.get(OutboxWorkerState, 1)

    async def heartbeat(
        self,
        status: str,
        *,
        last_error: str | None = None,
        circuit_open_until: datetime | None = None,
        delivered: bool = False,
        clear_error: bool = False,
    ) -> None:
        async with SessionLocal() as db, db.begin():
            state = await db.get(OutboxWorkerState, 1, with_for_update=True)
            if state is None:
                state = OutboxWorkerState(id=1)
                db.add(state)
            state.heartbeat_at = datetime.now(UTC)
            state.status = status
            state.circuit_open_until = circuit_open_until
            if last_error is not None:
                state.last_error = last_error
            elif clear_error:
                state.last_error = None
            if delivered:
                state.last_success_at = datetime.now(UTC)


class OutboxTransport:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=OUTBOX_HTTP_TIMEOUT_SECONDS)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def deliver(self, item: ClaimedOutboxItem) -> None:
        if not item.payload:
            raise DeliveryFailure("outbox payload is empty", retryable=False, kind="invalid_payload")
        headers = {"Content-Type": "application/json"}
        if EXTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {EXTERNAL_API_TOKEN}"
        try:
            response = await self._client.post(
                f"{EXTERNAL_API_URL.rstrip('/')}/sync/upserts",
                content=item.payload,
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise DeliveryFailure(f"network error: {exc}", retryable=True, kind="timeout") from exc
        except httpx.HTTPError as exc:
            raise DeliveryFailure(f"network error: {exc}", retryable=True, kind="network") from exc
        classify_sync_response(response)
