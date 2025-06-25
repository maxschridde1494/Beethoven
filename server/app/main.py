import os, json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio

from app.db import init_db
from app.routes.detections import router as detection_router
from app.routes.websockets import router as websocket_router
from app.rtsp.stream import RTSPStreamManager
from app.roboflow.detector import RoboflowDetectorManager
from app.utils.handlers import setup_handlers
from app.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)

def start_streams(loop):
    """Initialize and start RTSP streams and detectors."""
    CAMERA_STREAMS = os.getenv('CAM_PROXY_CONFIG', '[]')
    camera_feeds = {}

    try:
        camera_config = json.loads(CAMERA_STREAMS)
        camera_feeds = {cam['name']: cam['stream_url'] for cam in camera_config}
    except json.JSONDecodeError:
        logger.error("Error: CAMERA_STREAMS environment variable is not valid JSON")
    except KeyError:
        logger.error("Error: Each camera config must have 'name' and 'stream_url' fields")

    # Get singleton managers
    stream_manager = RTSPStreamManager()
    detector_manager = RoboflowDetectorManager()
    confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.9"))
    logger.info(f"Confidence threshold: {confidence_threshold} (env: {os.getenv('CONFIDENCE_THRESHOLD')})")

    # Start streams and detectors
    for camera_id, url in camera_feeds.items():
        # Start stream
        stream = stream_manager.add_stream(camera_id, url)
        
        # # Start detector for this stream
        # detector_manager.add_detector(
        #     stream=stream,
        #     model_id=os.getenv("ROBOFLOW_MODEL_ID"),
        #     confidence_threshold=confidence_threshold,
        #     interval=float(os.getenv("INTERVAL", 1.0)),
        #     loop=loop
        # )

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    init_db()
    await setup_handlers() # Initialize signal handlers before starting streams
    start_streams(loop)
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
    StaticFiles(directory=SNAPSHOT_DIR),
    name="assets",
)

