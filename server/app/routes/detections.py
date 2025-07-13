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


# ───────── transcription endpoints ──────────────────────────────────────────
@router.get("/transcription/active-notes")
def get_active_notes():
    """Get currently active notes from the transcriber."""
    try:
        from app.sheetmusic.streaming_transcriber import get_transcriber
        transcriber = get_transcriber()
        return {
            "active_notes": transcriber.get_active_notes(),
            "count": len(transcriber.get_active_notes())
        }
    except Exception as e:
        return {"error": str(e), "active_notes": [], "count": 0}


@router.get("/transcription/recent")
def get_recent_transcriptions(limit: int = 50):
    """Get recent transcribed notes."""
    try:
        from app.sheetmusic.streaming_transcriber import get_transcriber
        transcriber = get_transcriber()
        recent = transcriber.get_recent_transcriptions(limit=limit)
        return {
            "transcriptions": recent,
            "count": len(recent),
            "limit": limit
        }
    except Exception as e:
        return {"error": str(e), "transcriptions": [], "count": 0}


@router.get("/transcription/stats")
def get_transcription_stats():
    """Get transcriber statistics."""
    try:
        from app.sheetmusic.streaming_transcriber import get_transcriber
        transcriber = get_transcriber()
        return transcriber.get_stats()
    except Exception as e:
        return {"error": str(e), "running": False}


@router.post("/transcription/clear")
def clear_transcription_history():
    """Clear transcription history (useful for testing)."""
    try:
        from app.sheetmusic.streaming_transcriber import get_transcriber
        transcriber = get_transcriber()
        transcriber.clear_history()
        return {"message": "Transcription history cleared successfully"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to clear history"}