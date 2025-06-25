"""
Roboflow integration package for pet detection.

This package provides components for using Roboflow's inference API:
- Client factory for shared client initialization
- Image detector for processing video frames
"""

from app.roboflow.client import create_client

__all__ = [
    "create_client"
] 