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
        ("devices", "purchase_date", "DATETIME"),
        ("devices", "warranty_expiry", "DATETIME"),
        ("devices", "eol_date", "DATETIME"),
        ("notes", "is_archived", "INTEGER DEFAULT 0"),
        ("notes", "archived_ip", "VARCHAR(45)"),
        ("notes", "archived_hostname", "VARCHAR(255)"),
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
            # Check if the unique constraint still exists
            unique_constraints = inspector.get_unique_constraints("monitored_hosts")
            has_ip_unique = any(
                "ip_address" in (uc.get("column_names", []))
                for uc in unique_constraints
            )
            if has_ip_unique:
                # SQLite can't DROP constraints — must recreate the table
                try:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS monitored_hosts_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ip_address VARCHAR(45) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            monitor_type VARCHAR(20) DEFAULT 'ping',
                            port INTEGER,
                            check_interval INTEGER DEFAULT 60,
                            max_retries INTEGER DEFAULT 3,
                            retry_interval INTEGER DEFAULT 30,
                            is_enabled BOOLEAN DEFAULT 1,
                            current_status VARCHAR(20) DEFAULT 'unknown',
                            last_check DATETIME,
                            last_seen_up DATETIME,
                            last_seen_down DATETIME,
                            consecutive_failures INTEGER DEFAULT 0,
                            total_checks INTEGER DEFAULT 0,
                            total_up INTEGER DEFAULT 0,
                            created_at DATETIME
                        )
                    """))
                    conn.execute(text("""
                        INSERT INTO monitored_hosts_new
                        SELECT id, ip_address, name, monitor_type, port, check_interval,
                               max_retries, retry_interval, is_enabled, current_status,
                               last_check, last_seen_up, last_seen_down, consecutive_failures,
                               total_checks, total_up, created_at
                        FROM monitored_hosts
                    """))
                    conn.execute(text("DROP TABLE monitored_hosts"))
                    conn.execute(text("ALTER TABLE monitored_hosts_new RENAME TO monitored_hosts"))
                    print("  Migration: removed unique constraint on monitored_hosts.ip_address")
                except Exception as e:
                    print(f"  Migration warning (unique constraint): {e}")

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
