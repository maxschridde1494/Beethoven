"""
Utility functions for detection data handling and serialization.

This module provides reusable functions for retrieving and serializing detection data
using FastAPI's jsonable_encoder for consistent handling across REST and WebSocket endpoints.
"""
from typing import List
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select, desc

from app.models.detection import Detection
from app.db import get_session


def get_recent_detections(limit: int = 10) -> List[Detection]:
    """Get recent detections for consistent data retrieval."""
    with get_session() as session:
        result = session.execute(
            select(Detection).order_by(desc(Detection.timestamp)).limit(limit)
        )
        return result.scalars().all()


def serialize_detections(detections: List[Detection]) -> List[dict]:
    """Serialize detections using FastAPI's jsonable_encoder."""
    return jsonable_encoder(detections)


def create_detection_objects_from_data(detections_data: List[dict]) -> List[Detection]:
    """Convert detection dictionaries to Detection objects for consistent serialization."""
    detection_objects = []
    for detection_data in detections_data:
        try:
            # Create Detection object from the data
            detection = Detection(**detection_data)
            detection_objects.append(detection)
        except Exception as e:
            # Log error but continue processing other detections
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error creating Detection object: {e}")
            continue
    return detection_objects