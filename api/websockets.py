from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        text_message = json.dumps(message)
        stale_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text_message)
            except Exception:
                stale_connections.append(connection)
        for conn in stale_connections:
            self.disconnect(conn)

manager = ConnectionManager()

@router.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect the client to send much, but we need to keep the connection open
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
