import os, json, subprocess
import cv2
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List

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

            if camera_id and augmented_predictions is not None:
                annotated_predictions = annotate_predictions(
                    augmented_predictions,        # your list of detection dicts
                    left_white_seed=seed_keys[camera_id]["white"],       # first visible white key = #13
                    left_black_seed=seed_keys[camera_id]["black"],       # first visible black key = #14
                    direction=seed_keys[camera_id]["direction"]
                )
                initial_predictions[camera_id] = annotated_predictions

    return initial_predictions

# seed_keys = {
#     "edge-left": {
#         "white": 9, # [1, 3, 4, 6, 8, 9, 11, 13, 15, 16, 18, 20, 21, 23, 25, 27, 28, 30, 32, 33, 35, 37, 39, 40, 42, 44, 45, 47, 49, 51, 52, 54, 56, 57, 59, 61, 63, 64, 66, 68, 69, 71, 73, 75, 76, 78, 80, 81, 83, 85, 87, 88]
#         "black": 2   # [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46, 48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]
#     },
#     "middle-left": {
#         "white": 13, # [1, 3, 4, 6, 8, 9, 11, 13, 15, 16, 18, 20, 21, 23, 25, 27, 28, 30, 32, 33, 35, 37, 39, 40, 42, 44, 45, 47, 49, 51, 52, 54, 56, 57, 59, 61, 63, 64, 66, 68, 69, 71, 73, 75, 76, 78, 80, 81, 83, 85, 87, 88]
#         "black": 19 # [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46, 48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]
#     }
# }

seed_keys = {
    "edge-left": {
        "white": 35,      # lowest visible white in this frame
        "black": 31,     # lowest visible black
        "direction": "rtl"
    },
    "middle-left": {
        "white": 56,
        "black": 50,
        "direction": "rtl"   # ⬅︎ change to rtl
    }
}
# ────────────────── keyboard metadata ──────────────────
_NOTE_NAMES: List[str] = (
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C C# D D# E F F# G G# "
    "A A# B  "
    "C"
).split()

NOTE_NAMES: Dict[int, str] = {i + 1: n for i, n in enumerate(_NOTE_NAMES)}

WHITE_KEYS = [k for k, n in NOTE_NAMES.items() if "#" not in n]
BLACK_KEYS = [k for k, n in NOTE_NAMES.items() if "#" in n]

# ────────────────── helper ──────────────────────────────
def _slice_from(
    seed: int,
    full: List[int],
    needed: int,
    forward: bool,
) -> List[int]:
    """
    Return `needed` items from `full`, beginning at `seed`
    and stepping either forward (ascending) or backward (descending).
    """
    try:
        idx = full.index(seed)
    except ValueError as e:
        raise ValueError(f"Seed {seed} not in valid key list") from e

    if forward:  # left-to-right → increasing numbers
        return full[idx : idx + needed]
    else:        # left-to-right → decreasing numbers
        slice_rev = full[: idx + 1][::-1]          # keys ≤ seed, reversed
        if needed > len(slice_rev):               # edge case: need to wrap
            slice_rev += full[idx + 1 :][::-1]
        return slice_rev[:needed]

# ────────────────── core routine ───────────────────────
def annotate_predictions(
    preds: List[Dict],
    *,
    left_white_seed: int,
    left_black_seed: int,
    direction: str = "ltr",        # "ltr" or "rtl"
) -> List[Dict]:
    """
    Augment each detection with 'key_number' and 'note_name'.

    Parameters
    ----------
    preds : list[dict]
        Each dict must have keys 'x' and 'class_name' ("wh" or "bl").
    left_white_seed : int
        Absolute piano key of the **left-most white** detection in view.
    left_black_seed : int
        Absolute piano key of the **left-most black** detection in view.
    direction : str
        "ltr" → numbers increase as x increases (normal keyboard photo).  
        "rtl" → numbers *decrease* as x increases (mirror / selfie camera).

    Returns
    -------
    list[dict]
        Same detections, plus 'key_number' and 'note_name', sorted by x.
    """
    if not preds:
        raise ValueError("predictions list is empty")

    forward = direction.lower() == "ltr"

    whites = sorted((p for p in preds if p["class_name"] == "wh"), key=lambda d: d["x"])
    blacks = sorted((p for p in preds if p["class_name"] == "bl"), key=lambda d: d["x"])

    white_seq = _slice_from(left_white_seed, WHITE_KEYS, len(whites), forward)
    black_seq = _slice_from(left_black_seed, BLACK_KEYS, len(blacks), forward)

    for det, k in zip(whites, white_seq):
        det["key_number"] = k
        det["note_name"] = NOTE_NAMES[k]

    for det, k in zip(blacks, black_seq):
        det["key_number"] = k
        det["note_name"] = NOTE_NAMES[k]

    # combine & resort overall
    return sorted(preds, key=lambda d: d["x"])
