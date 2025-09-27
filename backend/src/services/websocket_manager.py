from typing import Dict, Set

from fastapi import WebSocket

from src.schemas import MatchUpdate


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_tournaments: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, tournament_id: int) -> None:
        self.active_connections.setdefault(tournament_id, set()).add(websocket)
        self.connection_tournaments[websocket] = tournament_id

    def disconnect(self, websocket: WebSocket) -> None:
        tournament_id = self.connection_tournaments.pop(websocket, None)
        if tournament_id is not None:
            conns = self.active_connections.get(tournament_id)
            if conns:
                conns.discard(websocket)
                if not conns:
                    del self.active_connections[tournament_id]

    async def broadcast_match_update(self, tournament_id: int, match_update: MatchUpdate) -> None:
        if tournament_id not in self.active_connections:
            return

        message = match_update.model_dump_json()
        disconnected_websockets: set[WebSocket] = set()

        for websocket in self.active_connections[tournament_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected_websockets.add(websocket)

        for ws in disconnected_websockets:
            self.disconnect(ws)


# Global instance
websocket_manager = WebSocketManager()
