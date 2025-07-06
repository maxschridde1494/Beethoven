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


async def setup_handlers(app: FastAPI):
    """Initialize all signal handlers."""
    set_app_instance(app)
    logger.info("Signal handlers connected.")
    from app.utils.signals import detection_made

    if os.getenv("DATABASE_PERSIST_DETECTIONS") == "true":
        # Connect handlers to signals
        detection_made.connect(handle_detections_storage)
    else:
        logger.info("DATABASE_PERSIST_DETECTIONS is not set, skipping detection storage.")