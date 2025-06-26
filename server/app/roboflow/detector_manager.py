"""
Singleton manager for Roboflow detectors.
"""

from typing import Dict, List, Optional
import asyncio
from app.streams.ffmpeg_stream import FFmpegStream
from app.roboflow.multi_model_detector import RoboflowMultiModelDetector
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RoboflowDetectorManager:
    """Singleton manager for multiple RoboflowDetector instances."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.detectors: Dict[str, RoboflowMultiModelDetector] = {}
        self._initialized = True
        
    def add_detector(
        self,
        stream: FFmpegStream,
        model_ids: List[str],
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Add a detector for a stream.
        
        Args:
            stream: FFmpegStream to monitor
            model_ids: Roboflow model IDs
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
        """
        camera_id = stream.camera_id
        
        if camera_id in self.detectors:
            logger.warning(f"Detector for {camera_id} already exists, stopping old one")
            self.stop_detector(camera_id)
            
        detector = RoboflowMultiModelDetector(
            stream=stream,
            model_ids=model_ids,
            confidence_threshold=confidence_threshold,
            interval=interval,
            loop=loop
        )
        
        detector.start()
        self.detectors[camera_id] = detector
        logger.info(f"Detector {camera_id} started! (models: {model_ids}, confidence: {confidence_threshold}, interval: {interval}s)")
        
    def stop_detector(self, camera_id: str) -> None:
        """Stop a specific detector."""
        if detector := self.detectors.get(camera_id):
            detector.stop()
            del self.detectors[camera_id]
            
    def stop_all(self) -> None:
        """Stop all detectors."""
        for camera_id in list(self.detectors.keys()):
            self.stop_detector(camera_id) 