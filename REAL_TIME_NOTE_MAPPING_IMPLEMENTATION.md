# Real-Time Note Mapping Implementation Summary

## Overview

The Beethoven project now supports **Real-Time Note Mapping**, enabling live key press detections to be mapped to specific MIDI note names using the initial calibration. This feature bridges the gap from computer vision to music notation, allowing the system to identify not just "a white key was pressed" but specifically "Middle C was pressed."

## Implementation Details

### 1. Made `seed_keys` Configurable

**What was changed:**
- Removed the hardcoded `seed_keys` dictionary from `server/app/roboflow/utils/detection.py`
- Added configuration parsing in `server/app/main.py` to load seed keys from the `CAM_PROXY_CONFIG` environment variable
- Added global `camera_seed_config` dictionary to store seed configuration for all cameras

**Configuration format:**
Each camera in `CAM_PROXY_CONFIG` now supports these additional fields:
```json
{
  "name": "middle-left",
  "stream_url": "app/assets/middle-left.mp4",
  "initialization-img-path": "app/assets/middle-left-static.jpg",
  "white_seed": 56,
  "black_seed": 50,
  "direction": "rtl"
}
```

Where:
- `white_seed`: Piano key number of the leftmost visible white key (1-88)
- `black_seed`: Piano key number of the leftmost visible black key (1-88)
- `direction`: "ltr" (left-to-right) or "rtl" (right-to-left) based on camera orientation

### 2. Updated Initial Inference

**What was changed:**
- Modified `run_initial_inference()` in `server/app/roboflow/utils/detection.py` to use environment-provided seeds instead of hardcoded values
- The function now looks up seed configuration for each camera and passes it to `annotate_predictions()`
- Added error handling for missing seed configuration

**Key changes:**
```python
# Find the camera configuration to get seed values
cam_config = next((cam for cam in camera_config if cam.get("name") == camera_id), None)
if cam_config and "white_seed" in cam_config and "black_seed" in cam_config:
    annotated_predictions = annotate_predictions(
        augmented_predictions,
        left_white_seed=cam_config["white_seed"],
        left_black_seed=cam_config["black_seed"],
        direction=cam_config.get("direction", "ltr")
    )
```

### 3. Real-Time Detection Annotation

**What was changed:**
- Updated `server/app/roboflow/multi_model_detector.py` to import and use `annotate_predictions`
- Added `seed_config` parameter to the `RoboflowMultiModelDetector` constructor
- Modified `_process_predictions()` method to annotate detections with note information before sending to WebSocket

**Key changes:**
```python
# Annotate detections with note information if seed config is available
if all_detections and self.seed_config:
    try:
        all_detections = annotate_predictions(
            all_detections,
            left_white_seed=self.seed_config["white_seed"],
            left_black_seed=self.seed_config["black_seed"],
            direction=self.seed_config.get("direction", "ltr")
        )
    except Exception as e:
        logger.error(f"Error annotating predictions for camera {self.camera_id}: {e}")
```

### 4. Detector Manager Integration

**What was changed:**
- Updated `server/app/roboflow/detector_manager.py` to pass seed configuration to detectors
- Added import of `get_camera_seed_config()` function to access global seed configuration
- Modified `add_detector()` method to look up and pass seed configuration for each camera

**Key changes:**
```python
# Get seed configuration for this camera
from app.main import get_camera_seed_config
seed_config = get_camera_seed_config().get(camera_id)

detector = RoboflowMultiModelDetector(
    stream=stream,
    model_ids=model_ids,
    interval=interval,
    loop=loop,
    seed_config=seed_config  # Pass seed config to detector
)
```

### 5. WebSocket Output Verification

**What was verified:**
- The existing WebSocket infrastructure in `server/app/routes/websockets.py` already handles the annotated detection data correctly
- The `detection_made` signal receives the annotated `all_detections` with `key_number` and `note_name` fields
- The frontend `BoundingBox` component already displays `note_name` if present

### 6. Documentation Updates

**What was updated:**
- Updated `.env.sample` to include comprehensive documentation for the new seed configuration fields
- Added examples showing how to configure local assets and RTSP streams with seed keys
- Added explanations for `white_seed`, `black_seed`, and `direction` parameters

## Frontend Integration

The frontend is already prepared to handle the new note mapping data:

- `client/src/components/BoundingBox/index.tsx` displays `note_name` and `key_number` fields
- The WebSocket client receives detection data with note information
- Bounding boxes show note names (e.g., "C4", "A#3") instead of just class names

## Configuration Examples

### Example 1: Local Video File
```json
CAM_PROXY_CONFIG=[
  {
    "name": "middle-left",
    "stream_url": "app/assets/middle-left.mp4",
    "initialization-img-path": "app/assets/middle-left-static.jpg",
    "white_seed": 56,
    "black_seed": 50,
    "direction": "rtl"
  }
]
```

### Example 2: RTSP Stream
```json
CAM_PROXY_CONFIG=[
  {
    "name": "edge-left",
    "stream_url": "rtsp://host.docker.internal:8554/edge-left",
    "initialization-img-path": "app/assets/edge-left-static.jpg",
    "white_seed": 35,
    "black_seed": 31,
    "direction": "rtl"
  }
]
```

## How It Works

1. **Startup Configuration**: The system loads seed configuration from `CAM_PROXY_CONFIG`
2. **Initial Calibration**: During startup, the system runs inference on static images and annotates them with note names using the seed configuration
3. **Real-Time Processing**: For each live detection, the system:
   - Processes the detection through the normal inference pipeline
   - Annotates the detection with `key_number` and `note_name` using the seed configuration
   - Sends the annotated detection via WebSocket to the frontend
4. **Frontend Display**: The frontend displays note names on bounding boxes overlaid on the video stream

## Benefits

- **Precise Note Identification**: Each key press is mapped to a specific piano key (1-88) and note name (e.g., "C4", "A#3")
- **Real-Time Performance**: Note mapping happens in real-time with minimal latency
- **Flexible Configuration**: Different cameras can have different seed configurations
- **Backward Compatibility**: Systems without seed configuration continue to work (without note mapping)
- **Error Handling**: Graceful handling of missing or invalid seed configurations

## Testing

To test the real-time note mapping:

1. Configure your `.env` file with proper seed values for your camera views
2. Start the system with `docker-compose up --build`
3. Open the web interface at `http://localhost:5173`
4. Play piano keys - the overlay should show specific note names (e.g., "C4") instead of generic class names ("wh", "bl")
5. Check the browser console for WebSocket messages that include `note_name` and `key_number` fields

## Future Enhancements

With real-time note mapping now implemented, the system is ready for:
- MIDI file generation from detected note sequences
- Sheet music transcription
- Real-time music notation display
- Performance analysis and feedback

This implementation provides the foundation for turning visual piano performance into structured musical data in real-time.