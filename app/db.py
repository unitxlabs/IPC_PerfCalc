import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings


DATABASE_URL = f"sqlite:///{settings.sqlite_path}"

# check_same_thread=False allows SQLite to be used with FastAPI's threading model
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Ensure SQLite enforces foreign key constraints (needed for ON DELETE CASCADE)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: D401
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def get_db():
    """FastAPI dependency that yields a session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
