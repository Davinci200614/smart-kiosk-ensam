from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base

DEFAULT_DATABASE_URL = "sqlite:///buvette.db"

engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def configure_database(database_url: str = DEFAULT_DATABASE_URL) -> None:
    """Configure the shared engine and session factory for the application."""
    global engine, SessionLocal

    if engine is not None:
        engine.dispose()
    engine = create_engine(database_url, echo=False)
    SessionLocal.configure(bind=engine)


def init_db():
    """Generates all tables mapped in models.py if they don't already exist."""
    if engine is None:
        configure_database()
    assert engine is not None
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()