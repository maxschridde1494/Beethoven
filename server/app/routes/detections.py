# app/routers/detections.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.models.detection import Detection
from app.db import get_session as open_session   # sync helper from db.py

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
def list_detections(session: Session = Depends(get_db)):
    result = session.execute(select(Detection).order_by(Detection.timestamp.desc()).limit(10))
    # result = session.execute(select(Detection))
    return result.scalars().all()