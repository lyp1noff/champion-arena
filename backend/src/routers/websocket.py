from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from src.services.broadcast import broadcast

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/tournament/{tournament_id}")
async def websocket_endpoint(websocket: WebSocket, tournament_id: int) -> None:
    await websocket.accept()
    try:
        async with broadcast.subscribe(channel=f"tournament:{tournament_id}") as subscriber:
            async for event in subscriber:  # type: ignore
                if event is None:
                    continue
                await websocket.send_text(event.message)
    except WebSocketDisconnect:
        pass
