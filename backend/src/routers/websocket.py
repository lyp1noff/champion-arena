from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Tournament
from src.services.websocket_manager import websocket_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/tournament/{tournament_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    tournament_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        try:
            tournament_id_int = int(tournament_id)
        except ValueError:
            await websocket.close(code=4000, reason="Invalid tournament ID")
            return

        stmt = select(Tournament).where(Tournament.id == tournament_id_int)
        result = await db.execute(stmt)
        tournament = result.scalar_one_or_none()

        if not tournament:
            await websocket.close(code=4004, reason="Tournament not found")
            return

        await websocket_manager.connect(websocket, tournament_id)

        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
        finally:
            websocket_manager.disconnect(websocket)

    except Exception:
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
