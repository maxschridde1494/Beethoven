"""
Global state for the application.
"""
from typing import Dict, Any, List
from sqlmodel import Session, select, func
from app.db import get_session
from app.models.detection import Detection
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This dictionary will hold the application's global state.
# For example, it can store initialization results or other shared data.
app_state: Dict[str, Any] = {
    "initial_predictions": {},
}

def set_initial_predictions(predictions: Dict[str, List[dict]]):
    """Sets the initial predictions in the global state, keyed by camera_id."""
    app_state["initial_predictions"] = predictions

def get_initial_predictions() -> Dict[str, List[dict]]:
    """Gets the initial predictions from the global state."""
    return app_state.get("initial_predictions", {})

def get_run_id() -> int:
    return app_state.get("run_id", 0)

def set_run_id(run_id: int):
    app_state["run_id"] = run_id