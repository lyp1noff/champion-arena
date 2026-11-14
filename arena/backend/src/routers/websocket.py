import asyncio

from fastapi import APIRouter, WebSocket
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from src.schemas import WsSubscribe
from src.services.broadcast import broadcast
from src.services.live import split_message, tournament_channel

router = APIRouter(tags=["WebSocket"])


async def _receive_subscriptions(websocket: WebSocket, subscribed: set[int]) -> None:
    """Read client messages until disconnect; `subscribe` replaces the wanted bracket set."""
    while True:
        text = await websocket.receive_text()
        try:
            message = WsSubscribe.model_validate_json(text)
        except ValidationError:
            continue
        subscribed.clear()
        subscribed.update(message.bracket_ids)


async def _forward_events(websocket: WebSocket, tournament_id: int, subscribed: set[int]) -> None:
    async with broadcast.subscribe(channel=tournament_channel(tournament_id)) as subscriber:
        async for event in subscriber:  # type: ignore
            if event is None:
                continue
            wire = split_message(event.message)
            if wire.state is not None and wire.bracket_id in subscribed:
                await websocket.send_text(wire.state)
            else:
                await websocket.send_text(wire.header)


@router.websocket("/ws/tournament/{tournament_id}")
async def websocket_endpoint(websocket: WebSocket, tournament_id: int) -> None:
    await websocket.accept()
    subscribed: set[int] = set()
    tasks = [
        asyncio.create_task(_receive_subscriptions(websocket, subscribed)),
        asyncio.create_task(_forward_events(websocket, tournament_id, subscribed)),
    ]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(result, (WebSocketDisconnect, RuntimeError)):
                raise result
