"""SQLAlchemy database setup and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import DATABASE_URL


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    """Create all tables defined in models, and migrate existing tables."""
    import app.models  # noqa: F401 — ensure all models are imported
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Add missing columns to existing tables (SQLite doesn't auto-alter)."""
    from sqlalchemy import text, inspect

    inspector = inspect(engine)

    # Define migrations: (table_name, column_name, column_sql)
    migrations = [
        ("monitored_hosts", "max_retries", "INTEGER DEFAULT 3"),
        ("monitored_hosts", "retry_interval", "INTEGER DEFAULT 30"),
        ("monitored_hosts", "monitor_type", "VARCHAR(20) DEFAULT 'ping'"),
        ("monitored_hosts", "port", "INTEGER"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            if table in inspector.get_table_names():
                existing_columns = [c["name"] for c in inspector.get_columns(table)]
                if column not in existing_columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    print(f"  Migration: added {table}.{column}")

        # Remove unique constraint on monitored_hosts.ip_address (allow multiple monitors per IP)
        if "monitored_hosts" in inspector.get_table_names():
            indexes = inspector.get_indexes("monitored_hosts")
            for idx in indexes:
                if idx.get("unique") and "ip_address" in idx.get("column_names", []):
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {idx['name']}"))
                        print(f"  Migration: dropped unique index {idx['name']} on monitored_hosts.ip_address")
                    except Exception:
                        pass  # Index may not exist or be unnamed

        conn.commit()


from contextlib import contextmanager


@contextmanager
def get_session():
    """
    Get a database session as a context manager.

    Usage:
        with get_session() as session:
            ...
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_direct():
    """
    Get a database session directly. Caller is responsible for closing.

    Usage:
        session = get_session_direct()
        try:
            ...
        finally:
            session.close()
    """
    return SessionLocal()
