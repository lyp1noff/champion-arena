from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel


class MatchUpdate(BaseModel):
    match_id: UUID
    score_athlete1: int | None
    score_athlete2: int | None
    status: str | None


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_tournaments: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, tournament_id: str) -> None:
        await websocket.accept()

        if tournament_id not in self.active_connections:
            self.active_connections[tournament_id] = set()

        self.active_connections[tournament_id].add(websocket)
        self.connection_tournaments[websocket] = tournament_id

    def disconnect(self, websocket: WebSocket) -> None:
        tournament_id = self.connection_tournaments.get(websocket)
        if tournament_id and tournament_id in self.active_connections:
            self.active_connections[tournament_id].discard(websocket)
            if not self.active_connections[tournament_id]:
                del self.active_connections[tournament_id]

        if websocket in self.connection_tournaments:
            del self.connection_tournaments[websocket]

        print(f"WebSocket disconnected from tournament {tournament_id}")

    async def broadcast_match_update(self, tournament_id: str, match_update: MatchUpdate) -> None:
        if tournament_id not in self.active_connections:
            return

        message = match_update.model_dump_json()
        disconnected_websockets = set()

        for websocket in self.active_connections[tournament_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending message to WebSocket: {e}")
                disconnected_websockets.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.disconnect(websocket)

        print(f"Broadcasted match update to {len(self.active_connections.get(tournament_id, set()))} connections")


# Global instance
websocket_manager = WebSocketManager()
