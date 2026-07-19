"""Note model — multiple titled notes per entity."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class Note(Base):
    """A titled note attached to an IP or device."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "ip" or "device"
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Integer, default=0)  # 0=active, 1=archived
    archived_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # Original IP when archived
    archived_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Original hostname
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Note(title={self.title!r}, entity={self.entity_type}:{self.entity_id}, archived={self.is_archived})>"
