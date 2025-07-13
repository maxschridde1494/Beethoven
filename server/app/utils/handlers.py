"""
Signal handlers for the detection system.

This module contains all the handler functions that respond to various signals
in the detection system.
"""
# import asyncio
import os
from uuid import UUID
from fastapi import FastAPI

from app.utils.logger import get_logger
from app.db import create_detection
from app.state import get_run_id

logger = get_logger(__name__)

# Store the app instance for use in handlers
_app_instance: FastAPI = None

def set_app_instance(app: FastAPI):
    """Set the app instance for use in handlers."""
    global _app_instance
    _app_instance = app

async def handle_detections_storage(sender, frame, camera_id, **kwargs):
    """Handle storing detection metadata in the database."""
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        for detection_data in detections:
            create_detection(get_run_id(_app_instance), detection_data)
        
    except Exception as e:
        logger.error(f"Error handling detection storage: {e}")


async def handle_music_transcription(sender, frame, camera_id, **kwargs):
    """Handle music transcription by processing detections through StreamingTranscriber."""
    try:
        detections = kwargs.get('detections', [])
        if not detections:
            return
            
        # Import here to avoid circular imports
        from app.sheetmusic.streaming_transcriber import get_transcriber
        
        # Get the global transcriber instance
        transcriber = get_transcriber()
        
        # Process the detections through the transcriber
        result = transcriber.process_detections(detections)
        
        # Log transcription activity
        if result.get('new_notes') or result.get('updated_notes'):
            logger.debug(f"Music transcription processed {result.get('processed_count', 0)} detections "
                        f"from camera {camera_id}: {len(result.get('new_notes', []))} new notes, "
                        f"{len(result.get('updated_notes', []))} updated notes")
        
    except Exception as e:
        logger.error(f"Error handling music transcription: {e}")


async def setup_handlers(app: FastAPI):
    """Initialize all signal handlers."""
    set_app_instance(app)
    logger.info("Signal handlers connected.")
    from app.utils.signals import detection_made

    # Always connect the music transcription handler
    detection_made.connect(handle_music_transcription)
    logger.info("Music transcription handler connected.")

    if os.getenv("DATABASE_PERSIST_DETECTIONS") == "true":
        # Connect handlers to signals
        detection_made.connect(handle_detections_storage)
        logger.info("Database persistence handler connected.")
    else:
        logger.info("DATABASE_PERSIST_DETECTIONS is not set, skipping detection storage.")

    # Start the transcriber
    from app.sheetmusic.streaming_transcriber import start_transcriber
    start_transcriber()
    logger.info("StreamingTranscriber started.")