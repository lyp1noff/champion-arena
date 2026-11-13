"""Background process that pushes dirty brackets to Arena.

Loop: pick up to SYNC_BATCH_SIZE dirty brackets, send their current state in one
request per tournament, record the per-bracket results. Network or HTTP errors
pause the loop with exponential backoff; the operator UI can cut the wait short
by setting ``sync_worker_state.next_attempt_at`` to now.
"""

import asyncio
import signal
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import httpx

from src.config import (
    EXTERNAL_API_TOKEN,
    EXTERNAL_API_URL,
    SYNC_BATCH_SIZE,
    SYNC_HTTP_TIMEOUT_SECONDS,
    SYNC_INTERVAL_SECONDS,
)
from src.database import SessionLocal, engine
from src.logger import logger
from src.models import SyncWorkerState
from src.services.sync_push import (
    PendingBracket,
    SyncTransportError,
    interpret_response,
    load_pending,
    make_request,
    record_results,
    retry_delay,
)
from src.statuses import SyncWorkerPhase

HEARTBEAT_SECONDS = 5.0


class WorkerStatus:
    """Persists the worker phase for the UI, writing only on change or every few seconds."""

    def __init__(self) -> None:
        self._written: tuple[str, str | None, datetime | None] | None = None
        self._written_at = 0.0

    async def next_attempt_at(self) -> datetime | None:
        async with SessionLocal() as db:
            state = await db.get(SyncWorkerState, 1)
            return state.next_attempt_at if state else None

    async def set(
        self,
        phase: SyncWorkerPhase,
        *,
        error: str | None = None,
        next_attempt_at: datetime | None = None,
        delivered: bool = False,
    ) -> None:
        loop_time = asyncio.get_running_loop().time()
        key = (phase.value, error, next_attempt_at)
        if key == self._written and not delivered and loop_time - self._written_at < HEARTBEAT_SECONDS:
            return
        now = datetime.now(UTC)
        async with SessionLocal() as db, db.begin():
            state = await db.get(SyncWorkerState, 1, with_for_update=True)
            if state is None:
                state = SyncWorkerState(id=1)
                db.add(state)
            state.heartbeat_at = now
            state.phase = phase.value
            state.last_error = error
            if phase != SyncWorkerPhase.OFFLINE or next_attempt_at is not None:
                state.next_attempt_at = next_attempt_at
            if delivered:
                state.last_success_at = now
        self._written, self._written_at = key, loop_time


async def _wait(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=max(0.0, seconds))
    except TimeoutError:
        pass


async def _send(client: httpx.AsyncClient, tournament_arena_id: int, items: list[PendingBracket]) -> None:
    headers = {"Authorization": f"Bearer {EXTERNAL_API_TOKEN}"} if EXTERNAL_API_TOKEN else {}
    try:
        response = await client.put(
            f"{EXTERNAL_API_URL.rstrip('/')}/sync/brackets",
            json=make_request(tournament_arena_id, items),
            headers=headers,
        )
    except httpx.HTTPError as exc:
        raise SyncTransportError(f"Network error: {exc!r}") from exc
    results = interpret_response(response, items)
    async with SessionLocal() as db:
        await record_results(db, items, results)
    for item in items:
        result = results[item.arena_id]
        if result.status != "applied":
            logger.warning("Bracket %s v%s %s: %s", item.arena_id, item.version, result.status, result.reason)


async def sync_once(client: httpx.AsyncClient) -> int:
    """Send one batch. Returns the number of brackets sent (0 when nothing is dirty)."""
    async with SessionLocal() as db:
        pending = await load_pending(db, SYNC_BATCH_SIZE)
    by_tournament: dict[int, list[PendingBracket]] = defaultdict(list)
    for item in pending:
        by_tournament[item.tournament_arena_id].append(item)
    for tournament_arena_id, items in by_tournament.items():
        await _send(client, tournament_arena_id, items)
    return len(pending)


async def run_worker(stop: asyncio.Event) -> None:
    status = WorkerStatus()
    failures = 0
    await status.set(SyncWorkerPhase.IDLE)
    logger.info("Sync worker started: %s", EXTERNAL_API_URL)

    async with httpx.AsyncClient(timeout=SYNC_HTTP_TIMEOUT_SECONDS) as client:
        try:
            while not stop.is_set():
                retry_at = await status.next_attempt_at()
                if failures and retry_at is not None and retry_at > datetime.now(UTC):
                    await _wait(stop, min(SYNC_INTERVAL_SECONDS, (retry_at - datetime.now(UTC)).total_seconds()))
                    continue
                try:
                    sent = await sync_once(client)
                except SyncTransportError as exc:
                    failures += 1
                    retry_at = datetime.now(UTC) + timedelta(seconds=retry_delay(failures))
                    await status.set(SyncWorkerPhase.OFFLINE, error=str(exc), next_attempt_at=retry_at)
                    logger.warning("Sync failed (attempt %s), retry at %s: %s", failures, retry_at.isoformat(), exc)
                    continue
                if sent:
                    failures = 0
                    await status.set(SyncWorkerPhase.SENDING, delivered=True)
                    logger.info("Synced %s bracket(s)", sent)
                    continue  # more may be waiting
                failures = 0
                await status.set(SyncWorkerPhase.IDLE)
                await _wait(stop, SYNC_INTERVAL_SECONDS)
        except Exception:
            logger.exception("Sync worker crashed")
            raise
        finally:
            await status.set(SyncWorkerPhase.STOPPED)
            await engine.dispose()
            logger.info("Sync worker stopped")


def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for signal_name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal_name, stop.set)
    try:
        loop.run_until_complete(run_worker(stop))
    finally:
        loop.close()


if __name__ == "__main__":
    main()
