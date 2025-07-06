"""
State management for the application using FastAPI's application state.
"""
from typing import Dict, List
from fastapi import FastAPI

from app.utils.logger import get_logger

logger = get_logger(__name__)

def set_initial_predictions(app: FastAPI, predictions: Dict[str, List[dict]]):
    """Sets the initial predictions in the application state, keyed by camera_id."""
    app.state.initial_predictions = predictions

def get_initial_predictions(app: FastAPI) -> Dict[str, List[dict]]:
    """Gets the initial predictions from the application state."""
    return getattr(app.state, 'initial_predictions', {})

def get_run_id(app: FastAPI) -> int:
    """Gets the current run ID from the application state."""
    return getattr(app.state, 'run_id', 0)

def set_run_id(app: FastAPI, run_id: int):
    """Sets the current run ID in the application state."""
    app.state.run_id = run_id