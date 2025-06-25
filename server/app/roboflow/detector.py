"""
Roboflow-based pet detector for processing RTSP streams.

This module provides:
- RoboflowDetector: Monitors a single RTSP stream and runs inference
- RoboflowDetectorManager: Manages multiple detectors (singleton)
"""

import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
import asyncio

from app.utils.logger import get_logger
from app.utils.signals import detection_made, high_confidence_detection_made, notes_detected
from app.roboflow.client import create_client
from app.rtsp.stream import RTSPStream

logger = get_logger(__name__)


class RoboflowDetector:
    """Monitors an RTSP stream and runs Roboflow inference."""

    def __init__(
        self,
        stream: RTSPStream,
        model_id: str,
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        loop: asyncio.AbstractEventLoop = None,
    ):
        """Initialize the detector.
        
        Args:
            stream: RTSPStream to monitor
            model_id: Roboflow model ID (e.g., "home-pet-detection/3")
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
            loop: asyncio.AbstractEventLoop to use for async operations
        """
        self.stream = stream
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.interval = interval
        self.loop = loop

        # State
        self.running = False
        self.client = create_client()
        self.thread: Optional[threading.Thread] = None
        
        # Set camera_id as an attribute for signal handlers
        self.camera_id = stream.camera_id

    def start(self) -> None:
        """Start the detector thread."""
        if self.running:
            logger.warning(f"Detector for {self.camera_id} already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info(f"[{self.camera_id}] detector started")

    def stop(self) -> None:
        """Stop the detector thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

    async def _process_predictions(self, predictions: List[dict], frame) -> None:
        """Process a list of predictions and emit appropriate signals.
        
        Args:
            predictions: List of prediction dictionaries from Roboflow
            frame: The frame the predictions were made on
        """
        current_time = datetime.now()
        
        # Process all predictions together
        all_detections = []
        high_confidence_detections = []
        
        for prediction in predictions:
            try:
                # Extract basic prediction data
                confidence = prediction["confidence"]
                
                # Prepare complete detection data
                detection_data = {
                    "detection_id": prediction["detection_id"],
                    "timestamp": current_time,
                    "model_id": self.model_id,
                    "camera_id": self.camera_id,
                    "x": prediction["x"],
                    "y": prediction["y"],
                    "width": prediction["width"],
                    "height": prediction["height"],
                    "confidence": confidence,
                    "class_name": prediction["class"],
                    "class_id": prediction["class_id"]
                }
                
                all_detections.append(detection_data)
                
                # Collect high confidence detections
                if confidence > self.confidence_threshold:
                    high_confidence_detections.append(detection_data)
                    
            except Exception as e:
                logger.error(f"Error processing prediction: {e}\n{prediction}")
        
        # Emit signals for all detections
        if all_detections:
            await detection_made.send_async(
                self, frame=frame, detections=all_detections
            )
        
        # Emit high confidence signal if any high confidence detections
        if high_confidence_detections:
            await high_confidence_detection_made.send_async(
                self, frame=frame, detections=high_confidence_detections
            )
        
        # Emit notes detected signal for all detections
        if all_detections:
            await notes_detected.send_async(
                self, frame=frame, detections=all_detections
            )

    def _loop(self) -> None:
        """Main detection loop."""
        while self.running:
            frame = self.stream.get_latest_frame()
            if frame is not None:
                try:
                    # Run inference
                    prediction = self.client.infer(
                        inference_input=frame,
                        model_id=self.model_id
                    )

                    # Check for predictions
                    if predictions := prediction.get("predictions", []):
                        coro = self._process_predictions(predictions, frame)
                        asyncio.run_coroutine_threadsafe(coro, self.loop)
                                
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    
            time.sleep(self.interval)


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
            
        self.detectors: Dict[str, RoboflowDetector] = {}
        self._initialized = True
        
    def add_detector(
        self,
        stream: RTSPStream,
        model_id: str,
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        """Add a detector for a stream.
        
        Args:
            stream: RTSPStream to monitor
            model_id: Roboflow model ID
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
        """
        camera_id = stream.camera_id
        
        if camera_id in self.detectors:
            logger.warning(f"Detector for {camera_id} already exists, stopping old one")
            self.stop_detector(camera_id)
            
        detector = RoboflowDetector(
            stream=stream,
            model_id=model_id,
            confidence_threshold=confidence_threshold,
            interval=interval,
            loop=loop
        )
        
        detector.start()
        self.detectors[camera_id] = detector
        logger.info(f"Detector {camera_id} started! (model: {model_id}, confidence: {confidence_threshold}, interval: {interval}s)")
        
    def stop_detector(self, camera_id: str) -> None:
        """Stop a specific detector."""
        if detector := self.detectors.get(camera_id):
            detector.stop()
            del self.detectors[camera_id]
            
    def stop_all(self) -> None:
        """Stop all detectors."""
        for camera_id in list(self.detectors.keys()):
            self.stop_detector(camera_id) 