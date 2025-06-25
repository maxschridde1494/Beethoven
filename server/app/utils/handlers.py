"""
Signal handlers for the detection system.

This module contains all the handler functions that respond to various signals
in the detection system.
"""
import os, cv2, asyncio
from uuid import UUID

from app.utils.logger import get_logger
from app.models import Detection
from app.db import get_session
from app.utils.signals import snapshot_made, notes_detected, musical_events_created
from app.utils.music import detections_to_events

logger = get_logger(__name__)

async def handle_snapshot_storage(sender, frame, **kwargs):
    """Handle storing snapshots for high confidence detections."""
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        for detection in detections:
            # Format timestamp for filename
            timestamp_str = detection['timestamp'].strftime("%Y%m%d_%H%M%S")
            
            # Ensure snapshot directory exists
            model_id = os.getenv("ROBOFLOW_MODEL_ID", "").replace("/", "-")
            snapshot_dir = os.getenv("SNAPSHOT_DIR", "app/snapshots") + "/" + model_id
            os.makedirs(snapshot_dir, exist_ok=True)
            
            # Save the frame with detection info in filename
            filename = f"{timestamp_str}_{detection['camera_id']}_{detection['class_name']}_{detection['confidence']:.2f}.jpg"
            filepath = os.path.join(snapshot_dir, filename)
            
            # Save with good quality for detection images
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            await snapshot_made.send_async(
                sender, frame=frame, asset_path=filename
            )
        
    except Exception as e:
        logger.error(f"Error saving detection snapshots: {e}")

async def handle_detection_storage(sender, frame, **kwargs):
    """Handle storing detection metadata in the database."""
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        for detection_data in detections:
            # Convert UUID string to UUID object if needed
            if isinstance(detection_data['detection_id'], str):
                detection_data['detection_id'] = UUID(detection_data['detection_id'])
                
            # Create Detection model instance
            detection = Detection(**detection_data)
            
            with get_session() as session:
                session.add(detection)
                session.commit()
                
            # Log detection info
            logger.info(
                f"\n\nhandle_detection_storage:\nDetection {detection_data['detection_id']} at {detection_data['timestamp']}:\n\tcamera={detection_data['camera_id']}\n\tmodel={detection_data['model_id']}\n\tclass={detection_data['class_name']}({detection_data['class_id']})\n\tconf={detection_data['confidence']:.2f}\n\n"
            )
        
    except Exception as e:
        logger.error(f"Error handling detection storage: {e}")

async def handle_notes_detected(sender, frame, **kwargs):
    """Handle processing detections into musical notes."""
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        # Process each detection into musical events
        all_events = []
        for detection in detections:
            events = detections_to_events(detection)
            all_events.extend(events)
            
        # Emit the musical events created signal with the processed events
        await musical_events_created.send_async(
            sender, frame=frame, notes=all_events, t=asyncio.get_event_loop().time()
        )
        
        logger.info(f"Processed {len(detections)} detections into {len(all_events)} musical events")
        
    except Exception as e:
        logger.error(f"Error handling notes detection: {e}")

async def setup_handlers():
    """Initialize all signal handlers."""
    from app.utils.signals import (
        detection_made,
        high_confidence_detection_made,
        notes_detected,
    )
    
    # Connect handlers to signals
    detection_made.connect(handle_detection_storage)
    high_confidence_detection_made.connect(handle_snapshot_storage)
    notes_detected.connect(handle_notes_detected)