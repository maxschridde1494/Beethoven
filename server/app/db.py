from sqlmodel import SQLModel, Session, create_engine, select
from uuid import UUID
from app.models.detection import Detection
from app.utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@db:5432/beethoven"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

def create_detection(run_id: int, data: dict) -> Detection:
    """Creates and stores a detection event."""
    detection_data = data.copy()
    # TODO: enhance data model to store key_number and note_name from detection_data
    detection_data.pop('key_number', None)
    detection_data.pop('note_name', None)
    
    if isinstance(detection_data.get('detection_id'), str):
        detection_data['detection_id'] = UUID(detection_data['detection_id'])

    detection_data['run_id'] = run_id
    
    detection = Detection(**detection_data)
    
    with get_session() as session:
        session.add(detection)
        session.commit()
        session.refresh(detection)
        
    return detection

def get_next_run_id() -> int:
    """
    Determines the next run_id by finding the maximum run_id in the detections table
    and incrementing it. If the table is empty, starts at 1.
    """
    try:
        with get_session() as session:
            result = session.exec(select(Detection.run_id).order_by(Detection.run_id.desc()).limit(1))
            max_run_id = result.first()
            logger.info(f"max_run_id: {max_run_id}")
            return (max_run_id or 0) + 1
    except Exception as e:
        logger.error(f"Error getting next run_id: {e}")
        return 1