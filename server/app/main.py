import os, json, subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio

from app.db import init_db, get_next_run_id
from app.routes.detections import router as detection_router
from app.routes.websockets import router as websocket_router
from app.streams.ffmpeg_stream import StreamManager
from app.roboflow.detector_manager import RoboflowDetectorManager
from app.utils.handlers import setup_handlers
from app.utils.logger import get_logger
from app.state import set_run_id, set_relative_positions
from app.roboflow.utils.relative_position import infer_relative_positions

load_dotenv()

logger = get_logger(__name__)
ffmpeg_processes = []

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
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ffmpeg_processes.append(process)

def start_streams(app: FastAPI,loop, camera_config: list):
    """Initialize and start RTSP streams and detectors."""
    camera_feeds = {}

    try:
        camera_feeds = {cam['name']: cam['stream_url'] for cam in camera_config}
    except KeyError:
        logger.error("Error: Each camera config must have 'name' and 'stream_url' fields")

    # Get singleton managers
    stream_manager = StreamManager()
    detector_manager = RoboflowDetectorManager(app)
    model_ids_str = os.getenv("ROBOFLOW_MODEL_ID", "")
    model_ids = [model_id.strip() for model_id in model_ids_str.split(',') if model_id.strip()]

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
                interval=float(os.getenv("INTERVAL", 1.0)),
                loop=loop
            )

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    init_db()
    await setup_handlers(app) # Pass app instance to setup_handlers
    
    camera_config = []
    try:
        camera_config_str = os.getenv('CAM_PROXY_CONFIG', '[]')
        camera_config = json.loads(camera_config_str)
        
    except json.JSONDecodeError:
        logger.error("Error: CAM_PROXY_CONFIG environment variable is not valid JSON")

    run_id = get_next_run_id()
    set_run_id(app, run_id)  # Pass app instance to set_run_id
    relative_positions = infer_relative_positions(run_id, camera_config)
    if relative_positions:
        set_relative_positions(app, relative_positions)  # Pass app instance to set_relative_positions
        logger.info(f"Relative positions inference complete for cameras: {list(relative_positions.keys())}")

    start_streams(app, loop, camera_config)
    
    yield
    
    logger.info("Shutting down application...")

    # Stop detector and stream managers
    RoboflowDetectorManager(app).stop_all()
    StreamManager().stop_all()
    logger.info("Detector and stream managers stopped.")

    # Terminate all FFmpeg subprocesses
    if ffmpeg_processes:
        logger.info(f"Terminating {len(ffmpeg_processes)} FFmpeg subprocess(es)...")
        for process in ffmpeg_processes:
            process.terminate()
        
        # Wait for all processes to terminate
        for process in ffmpeg_processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"FFmpeg process {process.pid} did not terminate in time, killing it.")
                process.kill()
        logger.info("All FFmpeg subprocesses terminated.")

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

app.mount(
    "/assets",
    StaticFiles(directory="app/assets"),
    name="assets",
)
