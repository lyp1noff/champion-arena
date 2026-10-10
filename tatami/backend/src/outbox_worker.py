import asyncio
import signal
from datetime import UTC, datetime, timedelta

from src.config import OUTBOX_POLL_INTERVAL_SECONDS
from src.database import engine
from src.logger import logger
from src.services.outbox_delivery import DeliveryFailure, OutboxRepository, OutboxTransport, retry_delay
from src.statuses import OutboxWorkerPhase


async def _wait(stop: asyncio.Event, timeout: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=timeout)
    except TimeoutError:
        pass


async def run_worker(stop: asyncio.Event) -> None:
    repository = OutboxRepository()
    transport = OutboxTransport()
    await repository.heartbeat(OutboxWorkerPhase.IDLE, clear_error=True)
    logger.info("Outbox worker started")

    try:
        while not stop.is_set():
            state = await repository.worker_state()
            now = datetime.now(UTC)
            if state and state.circuit_open_until and state.circuit_open_until > now:
                await repository.heartbeat(OutboxWorkerPhase.OFFLINE_WAIT, circuit_open_until=state.circuit_open_until)
                await _wait(stop, min(OUTBOX_POLL_INTERVAL_SECONDS, (state.circuit_open_until - now).total_seconds()))
                continue

            item = await repository.claim_next()
            if item is None:
                await repository.heartbeat(OutboxWorkerPhase.IDLE)
                await _wait(stop, OUTBOX_POLL_INTERVAL_SECONDS)
                continue

            await repository.heartbeat(OutboxWorkerPhase.WORKING)
            try:
                await transport.deliver(item)
            except DeliveryFailure as failure:
                if failure.retryable:
                    delay = retry_delay(item.retry_count + 1)
                    retry_at = datetime.now(UTC) + timedelta(seconds=delay)
                    await repository.mark_retry_wait(item.id, failure, retry_at)
                    await repository.heartbeat(
                        OutboxWorkerPhase.OFFLINE_WAIT,
                        last_error=str(failure),
                        circuit_open_until=retry_at,
                    )
                    logger.warning("Outbox item %s will retry in %.1fs: %s", item.id, delay, failure)
                else:
                    await repository.mark_dead_letter(item.id, failure)
                    await repository.heartbeat(OutboxWorkerPhase.IDLE, last_error=str(failure))
                    logger.error("Outbox item %s moved to dead letter: %s", item.id, failure)
                continue

            await repository.mark_success(item.id)
            await repository.heartbeat(OutboxWorkerPhase.IDLE, delivered=True, clear_error=True)
            logger.info("Outbox item %s delivered", item.id)
    finally:
        await repository.heartbeat(OutboxWorkerPhase.STOPPED)
        await transport.close()
        await engine.dispose()
        logger.info("Outbox worker stopped")


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
