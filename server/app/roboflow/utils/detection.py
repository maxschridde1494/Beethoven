import os, json, subprocess
import cv2
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from app.db import create_detection

from app.utils.logger import get_logger
from app.roboflow.client import create_client

logger = get_logger(__name__)

def run_initial_inference(run_id: int, camera_config: list):
    """Runs inference on a static image for each camera at startup."""
    init_model_id = os.getenv("ROBOFLOW_INIT_MODEL_ID")
    if not init_model_id:
        logger.info("No initial model ID provided, skipping initial inference.")
        return

    client = create_client()
    initial_predictions = {}
    derived_predictions = {}

    def _infer(cam_config):
        image_path = cam_config.get("initialization-img-path")
        camera_id = cam_config.get("name")
        if not image_path or not camera_id:
            return None, None
        
        if not os.path.exists(image_path):
            logger.error(f"Initial image not found at {image_path}")
            return camera_id, None

        try:
            image = cv2.imread(image_path)
            predictions = client.infer(image, model_id=init_model_id)
            if predictions and "predictions" in predictions:
                logger.info(f"Initial inference for {camera_id} got {len(predictions['predictions'])} predictions.")
                return camera_id, predictions["predictions"]
            else:
                logger.info(f"Initial inference for {camera_id} ran but returned no predictions.")
                return camera_id, []
        except Exception as e:
            logger.error(f"Error during initial inference for {camera_id}: {e}")
            return camera_id, None

    with ThreadPoolExecutor() as executor:
        results = executor.map(_infer, camera_config)
        
    current_time = datetime.now().isoformat()

    for result in results:
        if result:
            camera_id, predictions = result
            augmented_predictions = []
            for prediction in predictions:
                detection_data = {
                    "detection_id": str(prediction["detection_id"]),
                    "timestamp": current_time,
                    "model_id": init_model_id,
                    "camera_id": camera_id,
                    "x": prediction["x"],
                    "y": prediction["y"],
                    "width": prediction["width"],
                    "height": prediction["height"],
                    "confidence": prediction["confidence"],
                    "class_name": prediction["class"],
                    "class_id": prediction["class_id"],
                    "run_id": run_id
                }

                augmented_predictions.append(detection_data)

                create_detection(run_id, detection_data)

            if camera_id and augmented_predictions is not None:
                initial_predictions[camera_id] = augmented_predictions

    return initial_predictions

