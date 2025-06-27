import os, json, subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import cv2
from datetime import datetime

from app.db import init_db, create_detection, get_next_run_id
from app.routes.detections import router as detection_router
from app.routes.websockets import router as websocket_router
from app.streams.ffmpeg_stream import StreamManager
from app.roboflow.detector_manager import RoboflowDetectorManager
from app.utils.handlers import setup_handlers
from app.utils.logger import get_logger
from app.roboflow.client import create_client
from app.state import set_run_id, set_initial_predictions

load_dotenv()

logger = get_logger(__name__)

def _start_ffmpeg_stream_to_mediamtx(camera_id: str, video_path: str):
    """Starts a background ffmpeg process to stream a video file to MediaMTX."""
    if not os.path.exists(video_path):
        logger.error(f"Video file not found at {video_path}, cannot stream.")
        return

    rtsp_url = f"rtsp://rtsp-proxy:8554/{camera_id}"
    command = [
        "ffmpeg",
        "-re",
        "-i", video_path,
        "-c:v", "copy",     # Copy video without re-encoding
        "-an",             # Disable audio
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        rtsp_url,
    ]
    logger.info(f"Starting ffmpeg stream for {camera_id} from {video_path} to {rtsp_url}")
    # Run ffmpeg in the background, ignoring its output
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_initial_inference(camera_config: list):
    """Runs inference on a static image for each camera at startup."""
    init_model_id = os.getenv("ROBOFLOW_INIT_MODEL_ID")
    if not init_model_id:
        logger.info("No initial model ID provided, skipping initial inference.")
        return

    client = create_client()
    initial_predictions = {}

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
    run_id = get_next_run_id()
    set_run_id(run_id)

    for result in results:
        if result:
            camera_id, predictions = result
            for prediction in predictions:
                detection_data = {
                    "detection_id": prediction["detection_id"],
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

                create_detection(run_id, detection_data)

            if camera_id and predictions is not None:
                initial_predictions[camera_id] = predictions

    if initial_predictions:
        set_initial_predictions(initial_predictions)
        logger.info(f"Initial inference complete for cameras: {list(initial_predictions.keys())}")


def start_streams(loop, camera_config: list):
    """Initialize and start RTSP streams and detectors."""
    camera_feeds = {}

    try:
        camera_feeds = {cam['name']: cam['stream_url'] for cam in camera_config}
    except KeyError:
        logger.error("Error: Each camera config must have 'name' and 'stream_url' fields")

    # Get singleton managers
    stream_manager = StreamManager()
    detector_manager = RoboflowDetectorManager()
    confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.9"))
    model_ids_str = os.getenv("ROBOFLOW_MODEL_ID", "")
    model_ids = [model_id.strip() for model_id in model_ids_str.split(',') if model_id.strip()]

    logger.info(f"Confidence threshold: {confidence_threshold} (env: {os.getenv('CONFIDENCE_THRESHOLD')})")
    logger.info(f"Roboflow Model IDs: {model_ids}")


    # Start streams and detectors
    for camera_id, url in camera_feeds.items():
        # If the url is a local file path, start a separate ffmpeg process to stream it to mediamtx
        is_local_file = not url.startswith("rtsp://")
        if is_local_file:
            _start_ffmpeg_stream_to_mediamtx(camera_id, url)

        # Start stream (for analysis)
        stream = stream_manager.add_stream(camera_id, url)
        
        # Start detector for this stream
        if model_ids:
            detector_manager.add_detector(
                stream=stream,
                model_ids=model_ids,
                confidence_threshold=confidence_threshold,
                interval=float(os.getenv("INTERVAL", 1.0)),
                loop=loop
            )

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    init_db()
    await setup_handlers() # Initialize signal handlers before starting streams
    
    camera_config = []
    try:
        camera_config_str = os.getenv('CAM_PROXY_CONFIG', '[]')
        camera_config = json.loads(camera_config_str)
    except json.JSONDecodeError:
        logger.error("Error: CAM_PROXY_CONFIG environment variable is not valid JSON")

    run_initial_inference(camera_config)
    start_streams(loop, camera_config)
    yield

app = FastAPI(root_path="/api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection_router)
app.include_router(websocket_router)

@app.get("/")
def root():
    return {"status": "Pet Tracker API is running"}

SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "app/snapshots")
app.mount(
    "/assets",
    StaticFiles(directory="app/assets"),
    name="assets",
)

