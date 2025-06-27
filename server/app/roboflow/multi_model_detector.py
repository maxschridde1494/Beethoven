"""
Roboflow-based multi-model detector for processing media streams.
"""

import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.utils.logger import get_logger
from app.utils.signals import detection_made
from app.roboflow.client import create_client
from app.streams.ffmpeg_stream import FFmpegStream
from app.utils.benchmark import benchmark

logger = get_logger(__name__)


class RoboflowMultiModelDetector:
    """Monitors a stream and runs inference using multiple Roboflow models in parallel."""

    def __init__(
        self,
        stream: FFmpegStream,
        model_ids: List[str],
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """Initialize the multi-model detector.
        
        Args:
            stream: FFmpegStream to monitor
            model_ids: List of Roboflow model IDs (e.g., ["model/1", "model/2"])
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
            loop: asyncio.AbstractEventLoop to use for async operations
        """
        if not model_ids:
            raise ValueError("At least one model ID is required.")

        self.stream = stream
        self.model_ids = model_ids
        self.confidence_threshold = confidence_threshold
        self.interval = interval
        self.loop = loop

        if self.loop is None:
            raise ValueError("An asyncio event loop must be provided.")

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
        logger.info(f"[{self.camera_id}] multi-model detector started with models: {self.model_ids}")

    def stop(self) -> None:
        """Stop the detector thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

    @benchmark("infer_single_model")
    def _infer_single_model(self, frame: object, model_id: str) -> dict:
        """Run inference for a single model."""
        return self.client.infer(inference_input=frame, model_id=model_id)

    async def _process_predictions(self, predictions: List[dict], frame) -> None:
        """Process a list of predictions and emit appropriate signals."""
        current_time = datetime.now().isoformat()
        
        all_detections = []
        # high_confidence_detections = []
        
        for prediction in predictions:
            try:
                confidence = prediction["confidence"]
                
                detection_data = {
                    "detection_id": prediction["detection_id"],
                    "timestamp": current_time,
                    "model_id": self.model_ids[0],
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
                
                # if confidence > self.confidence_threshold:
                #     high_confidence_detections.append(detection_data)
                    
            except Exception as e:
                logger.error(f"Error processing prediction: {e}\n{prediction}")
        
        if all_detections:
            # logger.info(f"[DETECTOR {self.camera_id}] Sending detections: {all_detections}\n\nReceivers: {detection_made.receivers}")  # should be ≥ 2
            results = await detection_made.send_async(
                self, 
                frame=frame, 
                camera_id=self.camera_id, 
                detections=all_detections
            )
            # logger.info(f"[DETECTOR {self.camera_id}] Results: {results}")

    def _loop(self) -> None:
        """Main detection loop."""
        with ThreadPoolExecutor() as executor:
            while self.running:
                frame = self.stream.get_latest_frame()
                if frame is not None:
                    # logger.info(f"[DETECTOR {self.camera_id}] Processing frame")
                    try:
                        # Run inference for all models in parallel
                        futures = [executor.submit(self._infer_single_model, frame, model_id) for model_id in self.model_ids]
                        
                        all_predictions = []
                        for future in futures:
                            result = future.result()
                            if result and "predictions" in result:
                                all_predictions.extend(result["predictions"])

                        if all_predictions:
                            assert self.loop is not None
                            coro = self._process_predictions(all_predictions, frame)
                            # logger.info("detector loop: %s", id(self.loop))
                            asyncio.run_coroutine_threadsafe(coro, self.loop)
                                    
                    except Exception as e:
                        logger.error(f"Error processing frame: {e}")
                else:
                    logger.warning(f"[DETECTOR {self.camera_id}] No frame available")
                        
                time.sleep(self.interval) 