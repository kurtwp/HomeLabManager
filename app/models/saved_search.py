"""Saved search queries model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class SavedSearch(Base):
    """A saved search query with filter criteria."""

    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ip, device, network, all
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SavedSearch(name={self.name!r}, type={self.entity_type})>"
