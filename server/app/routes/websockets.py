from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import Set
from datetime import datetime

from app.utils.logger import get_logger
from app.state import get_initial_predictions

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

from app.utils.signals import detection_made
_clients: Set[WebSocket] = set()

async def broadcast_to_clients(clients: Set[WebSocket], data: dict):
    """Helper to broadcast a JSON message to a set of WebSocket clients."""
    for websocket in list(clients):
        # logger.info(f"[WS] sending to {websocket}")
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"{type(e)} error sending data to client: {e}")

async def get_initial_data(websocket: WebSocket):
    """Get the initial data for a new websocket connection."""
    return {
        "initial_predictions": get_initial_predictions(websocket.app),
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    logger.info(f"New client connected: {websocket}")
    
    # Send initial data
    initial_data = await get_initial_data(websocket)
    await websocket.send_json({
        "timestamp": datetime.now().isoformat(),
        "status": "connected",
        "message": "connection_made",
        "data": initial_data
    })

    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "status": "active",
                "message": "ping"
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        _clients.remove(websocket)

@detection_made.connect
async def publish_detection(sender, frame, camera_id, **kw):
    # Broadcast to general clients
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "detection_made",
        "data": {
            "camera_id": camera_id,
            **kw
        }
    })