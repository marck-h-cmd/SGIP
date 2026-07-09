from typing import List, Dict, Any
from fastapi import WebSocket
import json


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[str, Any] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "client_id": client_id
        }
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client"""
        await websocket.send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send an alert to all clients"""
        message = {
            "type": "ALERT",
            "data": alert
        }
        await self.broadcast(message)
    
    async def send_telemetry_update(self, reading: Dict[str, Any]):
        """Send telemetry update to all clients"""
        message = {
            "type": "TELEMETRY_UPDATE",
            "data": reading
        }
        await self.broadcast(message)
    
    async def send_incident_update(self, incident: Dict[str, Any]):
        """Send incident update to all clients"""
        message = {
            "type": "INCIDENT_UPDATE",
            "data": incident
        }
        await self.broadcast(message)