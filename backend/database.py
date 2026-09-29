from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from  backend.models import Base

# Creates a local SQLite database file named 'buvette.db' in the root directory
DATABASE_URL = "sqlite:///buvette.db"

# echo=False prevents SQLAlchemy from printing every raw SQL query to the terminal
engine = create_engine(DATABASE_URL, echo=False)

# SessionLocal is the factory for creating database sessions (workspaces)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Generates all tables mapped in models.py if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    print("Database 'buvette.db' and tables created successfully.")

if __name__ == "__main__":
    init_db()