from typing import Dict, List
from fastapi import WebSocket


# Simple in-memory connection manager for WebSocket push
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}


async def connect(self, user_id: int, websocket: WebSocket):
    await websocket.accept()
    self.active_connections[user_id] = websocket


def disconnect(self, user_id: int):
    if user_id in self.active_connections:
        del self.active_connections[user_id]


async def send_personal_message(self, user_id: int, message: str):
    ws = self.active_connections.get(user_id)
    if ws:
        await ws.send_text(message)


async def broadcast(self, message: str):
    for ws in list(self.active_connections.values()):
        await ws.send_text(message)


manager = ConnectionManager()