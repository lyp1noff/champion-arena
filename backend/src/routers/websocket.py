import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Tournament
from src.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

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

        # Verify tournament exists
        stmt = select(Tournament).where(Tournament.id == tournament_id_int)
        result = await db.execute(stmt)
        tournament = result.scalar_one_or_none()

        if not tournament:
            await websocket.close(code=4004, reason="Tournament not found")
            return

        # Connect to WebSocket manager (use string version for consistency)
        await websocket_manager.connect(websocket, tournament_id)

        logger.info(f"WebSocket connected for tournament {tournament_id}")

        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for any message (ping/pong or close)
                data = await websocket.receive_text()
                # For now, we just echo back to keep connection alive
                await websocket.send_text(f"Echo: {data}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for tournament {tournament_id}")
        except Exception as e:
            logger.error(f"WebSocket error for tournament {tournament_id}: {e}")
        finally:
            websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
