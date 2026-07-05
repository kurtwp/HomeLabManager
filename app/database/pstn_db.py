"""SQLAlchemy database setup for PSTN/Telephony module (separate pstn.db)."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager


class PSTNBase(DeclarativeBase):
    """Base class for all PSTN models."""
    pass


pstn_engine = create_engine(
    "sqlite:///./pstn.db",
    connect_args={"check_same_thread": False},
    echo=False,
)

PSTNSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pstn_engine)


@event.listens_for(pstn_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_pstn_db():
    """Create all PSTN tables."""
    import app.models.pstn  # noqa: F401 — ensure models imported
    PSTNBase.metadata.create_all(bind=pstn_engine)


@contextmanager
def get_pstn_session():
    """Get a PSTN database session as a context manager."""
    session = PSTNSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_pstn_session_direct():
    """Get a PSTN database session directly. Caller is responsible for closing."""
    return PSTNSessionLocal()
