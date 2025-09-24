from typing import Dict, Set

from fastapi import WebSocket

from src.schemas import MatchUpdate


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

    async def broadcast_match_update(self, tournament_id: str, match_update: MatchUpdate) -> None:
        if tournament_id not in self.active_connections:
            return

        message = match_update.model_dump_json()
        disconnected_websockets = set()

        for websocket in self.active_connections[tournament_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                disconnected_websockets.add(websocket)

        for websocket in disconnected_websockets:
            self.disconnect(websocket)


# Global instance
websocket_manager = WebSocketManager()
