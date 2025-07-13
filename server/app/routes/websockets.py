from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
import asyncio
from typing import Set
from datetime import datetime

from app.utils.logger import get_logger
from app.state import get_relative_positions
from app.utils.detection_utils import (
    serialize_detections,
    create_detection_objects_from_data
)

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

from app.utils.signals import detection_made, music_transcribed
_clients: Set[WebSocket] = set()



async def broadcast_to_clients(clients: Set[WebSocket], data: dict):
    """Helper to broadcast a JSON message to a set of WebSocket clients."""
    for websocket in list(clients):
        # logger.info(f"[WS] sending to {websocket}")
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"{type(e)} error sending data to client: {e}")
            # Remove disconnected clients
            clients.discard(websocket)


async def get_initial_data(websocket: WebSocket):
    """Get initial data to send to a new client."""
    try:
        from app.sheetmusic.streaming_transcriber import get_transcriber
        transcriber = get_transcriber()
        
        return {
            "relative_positions": get_relative_positions(websocket.app),
            "active_notes": transcriber.get_active_notes(),
            "transcriber_stats": transcriber.get_stats(),
            "recent_transcriptions": transcriber.get_recent_transcriptions(limit=10)
        }
    except Exception as e:
        logger.error(f"Error getting initial data: {e}")
        return {
            "relative_positions": get_relative_positions(websocket.app),
            "active_notes": [],
            "transcriber_stats": {},
            "recent_transcriptions": []
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
    """Publish detection data to WebSocket clients using jsonable_encoder."""
    detections_data = kw.get('detections', [])
    
    # Convert detection dictionaries to Detection objects for consistent serialization
    detection_objects = create_detection_objects_from_data(detections_data)
    
    # Use jsonable_encoder to serialize the Detection objects
    serialized_detections = serialize_detections(detection_objects)
    
    # Broadcast to general clients
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "detection_made",
        "data": {
            "camera_id": camera_id,
            "detections": serialized_detections
        }
    })

@music_transcribed.connect
async def publish_music_transcription(sender, **kw):
    """Publish music transcription data to WebSocket clients."""
    transcription_data = kw.get('transcription_data', {})
    notes_count = kw.get('notes_count', 0)
    
    # Broadcast transcription update to all clients
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "music_transcribed",
        "data": {
            "transcription": transcription_data,
            "notes_count": notes_count
        }
    })
    
    logger.debug(f"Published music transcription to {len(_clients)} clients: {notes_count} notes")