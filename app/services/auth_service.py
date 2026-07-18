"""Authentication service — simple user login with hashed passwords."""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal


class User(Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin")  # admin, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User(username={self.username!r}, role={self.role})>"


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt, hashed = password_hash.split(":")
        check = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return check == hashed
    except (ValueError, AttributeError):
        return False


def create_user(session: Session, username: str, password: str, role: str = "admin") -> User:
    """Create a new user account."""
    user = User(
        username=username.strip().lower(),
        password_hash=_hash_password(password),
        role=role,
    )
    session.add(user)
    session.commit()
    return user


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Authenticate a user. Returns the User if valid, None otherwise."""
    user = session.query(User).filter(
        User.username == username.strip().lower(),
        User.is_active == True,
    ).first()
    if user and _verify_password(password, user.password_hash):
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        return user
    return None


def get_user_count(session: Session) -> int:
    """Get the number of registered users."""
    return session.query(User).count()


def change_password(session: Session, user_id: int, new_password: str) -> bool:
    """Change a user's password."""
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.password_hash = _hash_password(new_password)
        session.commit()
        return True
    return False


def is_auth_enabled() -> bool:
    """Check if authentication is enabled (at least one user exists)."""
    session = SessionLocal()
    try:
        return session.query(User).count() > 0
    finally:
        session.close()
