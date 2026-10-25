# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Database Connection & Session Management (backend/core/database.py)

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone
from backend.core.config import settings

def utc_now() -> datetime:
    """Return timezone-naive UTC datetime for consistent SQLite storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Ensure sqlite data directory exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    parent_dir = Path(db_path).parent
    if parent_dir and not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)

# Create Engine
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Enable SQLite Foreign Keys and Write-Ahead Logging (WAL)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that yields a database session and safely closes it upon request completion."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
