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
        interval: float = 1.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Add a detector for a stream.
        
        Args:
            stream: FFmpegStream to monitor
            model_ids: Roboflow model IDs
            interval: Seconds between inference runs
            loop: asyncio event loop
        """
        camera_id = stream.camera_id
        
        if camera_id in self.detectors:
            logger.warning(f"Detector for {camera_id} already exists, stopping old one")
            self.stop_detector(camera_id)
        
        # Get seed configuration for this camera
        try:
            from app.main import get_camera_seed_config
            seed_config = get_camera_seed_config().get(camera_id)
            if seed_config:
                logger.info(f"Using seed configuration for camera {camera_id}: {seed_config}")
            else:
                logger.warning(f"No seed configuration found for camera {camera_id}. Real-time note mapping will be disabled.")
        except ImportError:
            logger.warning(f"Could not import seed configuration. Real-time note mapping will be disabled for camera {camera_id}")
            seed_config = None
            
        detector = RoboflowMultiModelDetector(
            stream=stream,
            model_ids=model_ids,
            interval=interval,
            loop=loop,
            seed_config=seed_config
        )
        
        detector.start()
        self.detectors[camera_id] = detector
        logger.info(f"Detector {camera_id} started! (models: {model_ids}, interval: {interval}s)")
        
    def stop_detector(self, camera_id: str) -> None:
        """Stop a specific detector."""
        if detector := self.detectors.get(camera_id):
            detector.stop()
            del self.detectors[camera_id]
            
    def stop_all(self) -> None:
        """Stop all detectors."""
        for camera_id in list(self.detectors.keys()):
            self.stop_detector(camera_id) 