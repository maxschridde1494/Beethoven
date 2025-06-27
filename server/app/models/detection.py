"""
Detection model for storing pet detection events.

This model represents a single pet detection event from the Roboflow model,
including position, confidence, and metadata.
"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class Detection(SQLModel, table=True):
    """A single pet detection event."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Detection metadata
    detection_id: UUID = Field(description="Unique identifier for this detection from Roboflow")
    timestamp: datetime = Field(description="When the detection was made")
    model_id: str = Field(description="ID of the Roboflow model that made the detection")
    
    # Camera info
    camera_id: str = Field(description="ID of the camera that captured this detection")
    
    # Detection details
    x: float = Field(description="X coordinate of detection center")
    y: float = Field(description="Y coordinate of detection center")
    width: float = Field(description="Width of detection bounding box")
    height: float = Field(description="Height of detection bounding box")
    confidence: float = Field(description="Confidence score of the detection")
    
    # Classification
    class_name: str = Field(description="Class name of detected object (e.g. 'pets')")
    class_id: int = Field(description="Numeric ID of the detected class") 
    run_id: int = Field(description="ID of the run that made the detection")