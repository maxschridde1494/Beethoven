from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import Set
from datetime import datetime
import os
from sqlmodel import Session, select
from app.utils.logger import get_logger
from app.models import Detection
from app.db import get_session
from app.utils.signals import high_confidence_detection_made, detection_made, snapshot_made, musical_events_created
from app.state import get_initial_predictions

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

from app.utils.signals import high_confidence_detection_made, detection_made, snapshot_made, notes_detected
_clients: Set[WebSocket] = set()
_prediction_clients: Set[WebSocket] = set()

async def broadcast_to_clients(clients: Set[WebSocket], data: dict):
    """Helper to broadcast a JSON message to a set of WebSocket clients."""
    for websocket in list(clients):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"{type(e)} error sending data to client: {e}")

async def get_initial_data():
    """Get the initial data for a new websocket connection."""
    # Get last 10 detections
    with get_session() as session:
        result = session.execute(
            select(Detection)
            .order_by(Detection.timestamp.desc())
            .limit(10)
        )
        detections = result.scalars().all()
        
        # Convert timestamps to ISO format for JSON serialization
        detections_data = []
        for detection in detections:
            detection_dict = {
                "id": detection.id,
                "detection_id": str(detection.detection_id),
                "timestamp": detection.timestamp.isoformat(),
                "model_id": detection.model_id,
                "camera_id": detection.camera_id,
                "x": detection.x,
                "y": detection.y,
                "width": detection.width,
                "height": detection.height,
                "confidence": detection.confidence,
                "class_name": detection.class_name,
                "class_id": detection.class_id
            }
            detections_data.append(detection_dict)

    # Get last 5 snapshots from the snapshots directory
    snapshot_dir = os.getenv("SNAPSHOT_DIR", "app/snapshots")
    snapshots = []
    try:
        # List all files in snapshot directory
        files = os.listdir(snapshot_dir)
        # Filter for jpg files and sort by name (which includes timestamp)
        snapshots = sorted(
            [f for f in files if f.endswith('.jpg')],
            reverse=True
        )[:5]
    except Exception as e:
        logger.error(f"Error reading snapshots directory: {e}")

    return {
        "last_10_detections": detections_data,
        "last_5_snapshots": snapshots,
        "initial_predictions": get_initial_predictions(),
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    logger.info(f"New client connected: {websocket}")
    
    # Send initial data
    initial_data = await get_initial_data()
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

@router.websocket("/ws/predictions")
async def predictions_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _prediction_clients.add(websocket)
    logger.info(f"New prediction client connected: {websocket}")
    try:
        while True:
            await asyncio.sleep(60)  # Keep connection alive
            await websocket.send_json({"message": "ping"})
    except WebSocketDisconnect:
        logger.info("Prediction client disconnected")
        _prediction_clients.remove(websocket)

# broadcast on every detection
@high_confidence_detection_made.connect
async def publish_high_confidence(sender, frame, **kw):
    kw["timestamp"] = kw["timestamp"].isoformat()
    
    # Broadcast to general clients
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "high_confidence_detection_made",
        "data": kw
    })
    
    # Broadcast to prediction clients
    await broadcast_to_clients(_prediction_clients, {
        "timestamp": datetime.now().isoformat(),
        "message": "high_confidence_detection",
        "data": kw
    })

@detection_made.connect
async def publish_detection(sender, frame, **kw):
    kw["timestamp"] = kw["timestamp"].isoformat()

    # Broadcast to general clients
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "detection_made",
        "data": kw
    })
    
    # Broadcast to prediction clients
    await broadcast_to_clients(_prediction_clients, {
        "timestamp": datetime.now().isoformat(),
        "message": "detection",
        "data": kw
    })

@snapshot_made.connect
async def publish_snapshot(sender, frame, **kw):
    await broadcast_to_clients(_clients, {
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "message": "snapshot_made",
        "data": {"asset_path": kw["asset_path"]}
    })

# music21 notation

from music21 import stream, note
score = stream.Score()
part  = stream.Part()
score.append(part)
GRID = 0.25   # quarterLength of a 16th-note at q=120

def snap(offset):
    return round(offset / GRID) * GRID

start  = asyncio.get_event_loop().time()
@musical_events_created.connect
async def ws_notation(sender, frame, **kw):
    rel = snap(kw["t"] - start)

    for note_event in kw["notes"]:
        note_time, note_midi, note_on = note_event
        if note_on:
            n = note.Note(midi=note_midi)
            n.offset = rel + note_time
            part.insert(n)
        else:
            # Find the note to turn off
            for n in part.notes:
                if n.pitch.midi == note_midi and n.duration.quarterLength == 0:
                    n.duration.quarterLength = (rel + note_time) - n.offset
                    break
            
    # every 2 sixteenths push update
    if rel % (2*GRID) == 0:
        xml = score.write('musicxml')

        await broadcast_to_clients(_clients, {
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "message": "snapshot_made",
            "data": {"xml": xml}
        })