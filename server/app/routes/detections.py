# app/routers/detections.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.models.detection import Detection
from app.db import get_session as open_session   # sync helper from db.py
from app.utils.detection_utils import get_recent_detections

router = APIRouter(prefix="", tags=["Detections"])

# ───────── dependency ──────────────────────────────────────────────────────
def get_db() -> Session:
    """FastAPI dependency that yields a synchronous DB session."""
    with open_session() as session:
        yield session



# ───────── endpoints ───────────────────────────────────────────────────────
@router.post("/detections")
def create_detection(
    detection: Detection,
    session: Session = Depends(get_db),
):
    session.add(detection)
    session.commit()
    session.refresh(detection)
    return detection


@router.get("/detections", response_model=list[Detection])
def list_detections():
    """List recent detections using the same logic as WebSocket for consistency."""
    return get_recent_detections()