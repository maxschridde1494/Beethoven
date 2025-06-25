from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@db:5432/beethoven"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)