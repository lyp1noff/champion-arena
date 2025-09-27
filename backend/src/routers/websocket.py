from fastapi import APIRouter, WebSocket
from sqlalchemy import select
from starlette.websockets import WebSocketDisconnect

from src.database import get_async_session
from src.models import Tournament
from src.services.websocket_manager import websocket_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/tournament/{tournament_id}")
async def websocket_endpoint(websocket: WebSocket, tournament_id: str) -> None:
    await websocket.accept()  # принять сразу, иначе браузер даст "failed"

    try:
        tournament_id_int = int(tournament_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid tournament ID")
        return

    async with get_async_session() as db:
        stmt = select(Tournament).where(Tournament.id == tournament_id_int)
        result = await db.execute(stmt)
        tournament = result.scalar_one_or_none()

    if not tournament:
        await websocket.close(code=4004, reason="Tournament not found")
        return

    await websocket_manager.connect(websocket, tournament_id_int)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
    finally:
        websocket_manager.disconnect(websocket)
