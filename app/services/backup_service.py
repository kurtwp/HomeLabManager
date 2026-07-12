"""Backup and restore service — SQLite database file operations."""

import shutil
import os
from datetime import datetime, timezone
from pathlib import Path

from config import DATABASE_URL


def _get_db_path() -> Path:
    """Extract the file path from the SQLite DATABASE_URL."""
    # DATABASE_URL format: sqlite:///./home_lab_manager.db
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    return Path(db_path)


def get_backup_dir() -> Path:
    """Get or create the backups directory."""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def create_backup() -> dict:
    """
    Create a backup of the SQLite database.

    Returns:
        {"success": bool, "filename": str, "size_bytes": int, "error": str|None}
    """
    try:
        db_path = _get_db_path()
        if not db_path.exists():
            return {"success": False, "filename": "", "size_bytes": 0,
                    "error": f"Database file not found: {db_path}"}

        backup_dir = get_backup_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        # Copy the database file
        shutil.copy2(str(db_path), str(backup_path))

        # Also copy WAL file if it exists (for consistency)
        wal_path = Path(f"{db_path}-wal")
        if wal_path.exists():
            shutil.copy2(str(wal_path), str(backup_path) + "-wal")

        size = backup_path.stat().st_size

        return {
            "success": True,
            "filename": backup_filename,
            "path": str(backup_path),
            "size_bytes": size,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "filename": "", "size_bytes": 0, "error": str(e)}


def restore_backup(backup_filename: str) -> dict:
    """
    Restore a database from a backup file.
    WARNING: This replaces the current database!

    Returns:
        {"success": bool, "error": str|None}
    """
    try:
        backup_dir = get_backup_dir()
        backup_path = backup_dir / backup_filename

        if not backup_path.exists():
            return {"success": False, "error": f"Backup file not found: {backup_filename}"}

        db_path = _get_db_path()

        # Create a safety backup before restoring
        safety_backup = backup_dir / f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"
        if db_path.exists():
            shutil.copy2(str(db_path), str(safety_backup))

        # Restore
        shutil.copy2(str(backup_path), str(db_path))

        # Restore WAL if it exists in backup
        wal_backup = Path(f"{backup_path}-wal")
        wal_target = Path(f"{db_path}-wal")
        if wal_backup.exists():
            shutil.copy2(str(wal_backup), str(wal_target))
        elif wal_target.exists():
            # Remove stale WAL if backup doesn't have one
            wal_target.unlink()

        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_backups() -> list[dict]:
    """
    List all available backups.

    Returns:
        List of dicts: [{"filename": str, "size_bytes": int, "created": datetime}]
    """
    backup_dir = get_backup_dir()
    backups = []

    for f in sorted(backup_dir.glob("backup_*.db"), reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        })

    return backups


def delete_backup(backup_filename: str) -> bool:
    """Delete a specific backup file."""
    backup_dir = get_backup_dir()
    backup_path = backup_dir / backup_filename
    if backup_path.exists():
        backup_path.unlink()
        # Also delete WAL if present
        wal_path = Path(f"{backup_path}-wal")
        if wal_path.exists():
            wal_path.unlink()
        return True
    return False


def get_db_size() -> int:
    """Get the current database file size in bytes."""
    db_path = _get_db_path()
    if db_path.exists():
        return db_path.stat().st_size
    return 0
