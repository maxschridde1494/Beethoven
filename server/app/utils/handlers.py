"""
Signal handlers for the detection system.

This module contains all the handler functions that respond to various signals
in the detection system.
"""
# import asyncio
import os
from uuid import UUID
from datetime import datetime
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
        
        # Process each detection through the transcriber
        for detection_data in detections:
            note_name = detection_data.get('note_name')
            key_number = detection_data.get('key_number')
            
            # Only process detections that have note information
            if note_name and key_number:
                transcriber.ingest_detection(
                    note_name=note_name,
                    key_number=key_number,
                    camera_id=camera_id,
                    timestamp=datetime.now()
                )
        
        logger.debug(f"Ingested {len([d for d in detections if d.get('note_name') and d.get('key_number')])} "
                    f"detections into transcriber from camera {camera_id}")
        
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