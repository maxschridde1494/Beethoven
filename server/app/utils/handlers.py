"""
Signal handlers for the detection system.

This module contains all the handler functions that respond to various signals
in the detection system.
"""
# import asyncio
from uuid import UUID

from app.utils.logger import get_logger
from app.models import Detection
from app.db import create_detection
from app.state import get_run_id
# from app.utils.signals import musical_events_created
# from app.utils.music import detections_to_events

logger = get_logger(__name__)

async def handle_detections_storage(sender, frame, camera_id, **kwargs):
    """Handle storing detection metadata in the database."""
    # logger.info(f"handle_detections_storage: {kwargs}")
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        for detection_data in detections:
            create_detection(get_run_id(), detection_data)
        
    except Exception as e:
        logger.error(f"Error handling detection storage: {e}")


async def setup_handlers():
    """Initialize all signal handlers."""
    logger.info("Signal handlers connected.")
    from app.utils.signals import detection_made
    
    # Connect handlers to signals
    # detection_made.connect(handle_detections_storage)
    # detection_made.connect(handle_detections_to_musical_events)

# async def handle_detections_to_musical_events(sender, frame, camera_id, **kwargs):
#     """Handle processing detections into musical notes."""
#     logger.info(f"handle_detections_to_musical_events: {kwargs}")
#     try:
#         detections = kwargs.get('detections', [])
#         if not detections:
#             return
            
#         # Process each detection into musical events
#         all_events = []
#         for detection in detections:
#             events = detections_to_events(detection)
#             all_events.extend(events)
            
#         # Emit the musical events created signal with the processed events
#         await musical_events_created.send_async(
#             sender, frame=frame, camera_id=camera_id, notes=all_events, t=asyncio.get_event_loop().time()
#         )
        
#         logger.info(f"Processed {len(detections)} detections into {len(all_events)} musical events")
        
#     except Exception as e:
#         logger.error(f"Error handling notes detection: {e}")