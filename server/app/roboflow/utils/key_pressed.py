from typing import Dict, List
from app.utils.logger import get_logger

logger = get_logger(__name__)

def compute_iou(box1: dict, box2: dict) -> float:
    """Compute Intersection-over-Union between two bounding boxes."""
    # Each box dict has center coords and size: {"x": cx, "y": cy, "width": w, "height": h}
    x1_a = box1["x"] - box1["width"] / 2
    y1_a = box1["y"] - box1["height"] / 2
    x2_a = box1["x"] + box1["width"] / 2
    y2_a = box1["y"] + box1["height"] / 2

    x1_b = box2["x"] - box2["width"] / 2
    y1_b = box2["y"] - box2["height"] / 2
    x2_b = box2["x"] + box2["width"] / 2
    y2_b = box2["y"] + box2["height"] / 2

    # Intersection bounds
    inter_x1 = max(x1_a, x1_b)
    inter_y1 = max(y1_a, y1_b)
    inter_x2 = min(x2_a, x2_b)
    inter_y2 = min(y2_a, y2_b)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    # Areas of each box
    area_a = box1["width"] * box1["height"]
    area_b = box2["width"] * box2["height"]

    # IoU computation
    union_area = area_a + area_b - inter_area
    return (inter_area / union_area) if union_area > 0 else 0.0

def annotate_predictions(pressed_key_predictions: List[Dict], 
                         reference_keys: List[Dict], 
                         iou_threshold: float = 0.1) -> List[Dict]:
    """
    Augment each pressed-key detection with 'key_number' and 'note_name' by 
    matching it to the nearest reference key from calibration.
    """
    if pressed_key_predictions is None:
        pressed_key_predictions = []
    # If no detections, return empty (or raise if you prefer strict handling)
    if not pressed_key_predictions:
        return []
    for pressed in pressed_key_predictions:
        best_iou = 0.0
        best_match = None
        # Consider only reference keys of the same color class for accuracy
        for ref in reference_keys:
            iou = compute_iou(pressed, ref)
            if iou > best_iou:
                best_iou = iou
                best_match = ref
        # Assign note metadata if a sufficiently overlapping reference key is found
        if best_match and best_iou >= iou_threshold:
            pressed["key_number"] = best_match["key_number"]
            pressed["note_name"] = best_match["note_name"]
        else:
            pressed["key_number"] = None
            pressed["note_name"] = None
    # Return the list sorted by horizontal position for consistency
    return sorted(pressed_key_predictions, key=lambda d: d["x"])
